from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.schemas import SettingsRequest, SettingsResponse
from src.services.stock_service import StockService

router = APIRouter(prefix='/api/settings', tags=['settings'])


@router.get('', response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """設定を取得"""
    service = StockService(db)
    return service.get_settings()


@router.put('', response_model=SettingsResponse)
def update_settings(request: SettingsRequest, db: Session = Depends(get_db)):
    """設定を更新"""
    service = StockService(db)
    return service.update_settings(request.model_dump())
