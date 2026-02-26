import logging
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime, time, date
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from sqlalchemy import text

from src.config import settings
from src.models.database import Base, engine, SessionLocal
from src.routers import (
    stocks_router, settings_router, transactions_router,
    alerts_router, risk_router, backtests_router, brokerage_router,
    auto_trade_router,
)
from src.services.stock_service import StockService
from src.services.alert_service import AlertService
from src.services.auto_trade_service import AutoTradeService

# ロギング設定: stdout + ファイル（日次ローテーション30日保持）
_log_fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

_log_dir = Path(__file__).resolve().parent.parent / "logs"
_log_dir.mkdir(exist_ok=True)

_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(_log_fmt)

_file_handler = TimedRotatingFileHandler(
    _log_dir / "backend.log", when="midnight", backupCount=30, encoding="utf-8",
)
_file_handler.setFormatter(_log_fmt)

_root_logger = logging.getLogger()
_root_logger.setLevel(logging.INFO)
_root_logger.addHandler(_stream_handler)
_root_logger.addHandler(_file_handler)

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

# スケジュール時刻（平日のみ）— 取引時間中は1時間ごと
SCHEDULE_TIMES = [
    time(9, 30), time(10, 30), time(11, 30),
    time(12, 30), time(13, 30), time(14, 30), time(15, 30),
]


def _is_trading_day(d: date = None) -> bool:
    """平日かどうか"""
    return (d or date.today()).weekday() < 5


def _should_have_run_today() -> bool:
    """今日のスケジュール時刻を過ぎているか"""
    if not _is_trading_day():
        return False
    now = datetime.now().time()
    return any(now >= t for t in SCHEDULE_TIMES)


def _data_is_stale() -> bool:
    """最新データが今日より古いか"""
    db = SessionLocal()
    try:
        from src.models.stock import StockPrice
        latest = db.query(StockPrice).order_by(StockPrice.date.desc()).first()
        if not latest:
            return True
        return latest.date < date.today()
    finally:
        db.close()


def _auto_trade_not_run_today() -> bool:
    """今日の自動売買ログが0件か"""
    db = SessionLocal()
    try:
        from src.models.stock import AutoTradeLog
        today_start = datetime.combine(date.today(), time(0, 0))
        count = db.query(AutoTradeLog).filter(AutoTradeLog.created_at >= today_start).count()
        return count == 0
    finally:
        db.close()


def scheduled_update():
    """定期更新ジョブ"""
    logger.info("=== Scheduled update started ===")
    db = SessionLocal()
    try:
        service = StockService(db)
        service.update_all_stocks()
        logger.info("Stock data updated successfully")

        alert_service = AlertService(db)
        alert_service.check_alerts()
        logger.info("Alert check completed")

        auto_trade_service = AutoTradeService(db)
        auto_config = auto_trade_service.get_config()
        logger.info(f"Auto-trade config: enabled={auto_config['enabled']}, dryRun={auto_config['dryRun']}")
        auto_trade_service.process_auto_trades()
        logger.info("Auto-trade processing completed")
    except Exception as e:
        logger.error(f"Scheduled update failed: {e}", exc_info=True)
    finally:
        db.close()
    logger.info("=== Scheduled update finished ===")


def watchdog_check():
    """WSLスリープ復帰対策: データが古い or 自動売買未実行なら即時更新"""
    if not _is_trading_day():
        return
    if not _should_have_run_today():
        return
    stale = _data_is_stale()
    no_trade = _auto_trade_not_run_today()
    if not stale and not no_trade:
        return
    reason = []
    if stale:
        reason.append("stale data")
    if no_trade:
        reason.append("no auto-trade logs today")
    logger.info(f"[watchdog] Catch-up needed: {', '.join(reason)}")
    scheduled_update()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    Base.metadata.create_all(bind=engine)

    # 簡易マイグレーション: signals テーブルに新列追加
    new_columns = [
        ("signal_strength", "INTEGER"),
        ("active_signals", "VARCHAR(200)"),
        ("target_price", "FLOAT"),
        ("stop_loss_price", "FLOAT"),
        ("support_price", "FLOAT"),
        ("resistance_price", "FLOAT"),
        ("bb_upper", "FLOAT"),
        ("bb_lower", "FLOAT"),
        ("bb_middle", "FLOAT"),
        ("atr", "FLOAT"),
        ("volume_ratio", "FLOAT"),
        ("signal_score", "FLOAT"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in new_columns:
            try:
                conn.execute(text(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}"))
                logger.info(f"[migration] Added column signals.{col_name}")
            except Exception as e:
                err_msg = str(e).lower()
                if "already exists" in err_msg or "duplicate column" in err_msg:
                    pass  # 既に存在 → 正常
                else:
                    logger.error(f"[migration] Failed to add signals.{col_name}: {e}")
                conn.rollback()
        conn.commit()

    # 簡易マイグレーション: 列幅拡張
    alter_type_queries = [
        ("ALTER TABLE signals ALTER COLUMN active_signals TYPE VARCHAR(200)", "signals.active_signals → VARCHAR(200)"),
        ("ALTER TABLE settings ALTER COLUMN value TYPE VARCHAR(500)", "settings.value → VARCHAR(500)"),
    ]
    for query, desc in alter_type_queries:
        with engine.connect() as conn:
            try:
                conn.execute(text(query))
                conn.commit()
                logger.info(f"[migration] Expanded {desc}")
            except Exception as e:
                conn.rollback()
                err_msg = str(e).lower()
                if "already" not in err_msg:
                    logger.error(f"[migration] Failed to expand {desc}: {e}")

    # マイグレーション検証: 必須列の存在確認
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'signals'"
        ))
        existing_cols = {row[0] for row in result}
        required = {col_name for col_name, _ in new_columns}
        missing = required - existing_cols
        if missing:
            logger.error(f"[migration] CRITICAL: signals table missing columns: {missing}")
        else:
            logger.info(f"[migration] Verified: all {len(required)} columns present")

    # 依存ライブラリチェック
    for lib in ['yfinance', 'pandas_ta', 'curl_cffi']:
        try:
            mod = __import__(lib)
            logger.info(f"[startup] {lib} {getattr(mod, '__version__', 'ok')}")
        except ImportError as e:
            logger.warning(f"[startup] {lib} UNAVAILABLE: {e}")

    # スケジューラー設定（平日 取引時間中1時間ごと）
    for t in SCHEDULE_TIMES:
        job_id = f'update_{t.hour:02d}{t.minute:02d}'
        scheduler.add_job(
            scheduled_update, 'cron', hour=t.hour, minute=t.minute,
            day_of_week='mon-fri', id=job_id, misfire_grace_time=3600,
        )
    # WSLスリープ復帰対策: 5分ごとにデータ鮮度チェック
    scheduler.add_job(
        watchdog_check, 'interval', minutes=5,
        id='watchdog', misfire_grace_time=600,
    )

    scheduler.start()
    logger.info("Scheduler started")

    # 起動時キャッチアップ: 平日でスケジュール時刻を過ぎていれば鮮度 or 自動売買ログをチェック
    if _should_have_run_today():
        stale = _data_is_stale()
        no_trade = _auto_trade_not_run_today()
        if stale or no_trade:
            reason = []
            if stale:
                reason.append("stale data")
            if no_trade:
                reason.append("no auto-trade logs today")
            logger.info(f"[startup] Catch-up needed: {', '.join(reason)}")
            scheduler.add_job(scheduled_update, id='startup_catchup')
        else:
            logger.info("[startup] No catch-up needed")
    else:
        logger.info("[startup] No catch-up needed")

    yield

    # 終了時
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="Stock Signal API",
    description="日本株の売買シグナル判定API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
origins = [o.strip() for o in settings.cors_origins.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(stocks_router)
app.include_router(settings_router)
app.include_router(transactions_router)
app.include_router(alerts_router)
app.include_router(risk_router)
app.include_router(backtests_router)
app.include_router(brokerage_router)
app.include_router(auto_trade_router)


@app.get('/api/health')
def health_check():
    """ヘルスチェック"""
    return {'status': 'healthy'}


@app.post('/api/update')
def trigger_update():
    """手動データ更新"""
    db = SessionLocal()
    try:
        service = StockService(db)
        service.update_all_stocks()
        return {'message': 'データを更新しました'}
    finally:
        db.close()


# グレースフルシャットダウン
def handle_sigterm(signum, frame):
    logger.info("Received SIGTERM, shutting down...")
    scheduler.shutdown(wait=False)
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_sigterm)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8734)
