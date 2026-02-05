import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from src.config import settings
from src.models.database import Base, engine, SessionLocal
from src.routers import stocks_router, settings_router, transactions_router
from src.services.stock_service import StockService

scheduler = BackgroundScheduler()


def scheduled_update():
    """定期更新ジョブ"""
    db = SessionLocal()
    try:
        service = StockService(db)
        service.update_all_stocks()
        print("Stock data updated successfully")
    except Exception as e:
        print(f"Scheduled update failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    Base.metadata.create_all(bind=engine)

    # スケジューラー設定（平日 9:30, 12:30, 15:30）
    scheduler.add_job(scheduled_update, 'cron', hour=9, minute=30, day_of_week='mon-fri', id='update_0930')
    scheduler.add_job(scheduled_update, 'cron', hour=12, minute=30, day_of_week='mon-fri', id='update_1230')
    scheduler.add_job(scheduled_update, 'cron', hour=15, minute=30, day_of_week='mon-fri', id='update_1530')
    scheduler.start()
    print("Scheduler started")

    yield

    # 終了時
    scheduler.shutdown()
    print("Scheduler stopped")


app = FastAPI(
    title="Stock Signal API",
    description="日本株の売買シグナル判定API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
origins = settings.cors_origins.split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(stocks_router)
app.include_router(settings_router)
app.include_router(transactions_router)


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
    print("Received SIGTERM, shutting down...")
    scheduler.shutdown(wait=False)
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_sigterm)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8734)
