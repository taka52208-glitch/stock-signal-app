"""テスト共通フィクスチャ — SQLiteインメモリDB（接続共有）を使用"""
import os
import pytest

# テスト用環境変数（config.py読み込み前にセット）
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['MOCK_MODE'] = 'true'
os.environ['CORS_ORIGINS'] = 'http://localhost:3847'

from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from src.models import database as db_module  # noqa: E402
from src.models.database import Base, get_db  # noqa: E402
from src.routers import (  # noqa: E402
    stocks_router, settings_router, transactions_router,
    alerts_router, risk_router, backtests_router, brokerage_router,
    auto_trade_router,
)

# テスト用engine — StaticPool で単一接続を全セッションで共有
_test_engine = create_engine(
    'sqlite://',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# database.py のグローバルengine/SessionLocalをテスト用に差し替え
db_module.engine = _test_engine
db_module.SessionLocal = _TestSession


def _create_test_app() -> FastAPI:
    """lifespan（マイグレーション/スケジューラ）を除外したテスト用app"""
    test_app = FastAPI()
    test_app.include_router(stocks_router)
    test_app.include_router(settings_router)
    test_app.include_router(transactions_router)
    test_app.include_router(alerts_router)
    test_app.include_router(risk_router)
    test_app.include_router(backtests_router)
    test_app.include_router(brokerage_router)
    test_app.include_router(auto_trade_router)

    @test_app.get('/api/health')
    def health_check():
        return {'status': 'healthy'}

    return test_app


test_app = _create_test_app()


@pytest.fixture()
def db():
    """各テストごとにクリーンなDBセッションを提供"""
    Base.metadata.create_all(bind=_test_engine)
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def client(db):
    """FastAPI TestClient（DBをテスト用に差し替え）"""
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    test_app.dependency_overrides[get_db] = _override_get_db
    with TestClient(test_app) as c:
        yield c
    test_app.dependency_overrides.clear()
