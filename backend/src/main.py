import logging
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime, time, date
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
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
    """WSLスリープ復帰対策: データが古ければ即時更新"""
    if not _is_trading_day():
        return
    if not _should_have_run_today():
        return
    if not _data_is_stale():
        return
    logger.info("[watchdog] Stale data detected after sleep/resume, running catch-up update")
    scheduled_update()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    Base.metadata.create_all(bind=engine)

    # 簡易マイグレーション: signals テーブルに新列追加
    new_columns = [
        ("signal_strength", "INTEGER"),
        ("active_signals", "VARCHAR(100)"),
        ("target_price", "FLOAT"),
        ("stop_loss_price", "FLOAT"),
        ("support_price", "FLOAT"),
        ("resistance_price", "FLOAT"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in new_columns:
            try:
                conn.execute(text(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}"))
                print(f"[migration] Added column signals.{col_name}")
            except Exception:
                pass  # 既に存在する場合はスキップ
        conn.commit()

    # 簡易マイグレーション: settings.value 列幅拡張
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE settings ALTER COLUMN value TYPE VARCHAR(500)"))
            print("[migration] Expanded settings.value to VARCHAR(500)")
        except Exception:
            pass
        conn.commit()

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

    # 起動時キャッチアップ: 平日でスケジュール時刻を過ぎていればデータ鮮度チェック
    if _should_have_run_today() and _data_is_stale():
        logger.info("[startup] Catch-up: data is stale, running update now")
        scheduler.add_job(scheduled_update, id='startup_catchup')
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
