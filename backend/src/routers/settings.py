from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.schemas import SettingsRequest, SettingsResponse
from src.models.stock import Setting
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
    data = {k: v for k, v in request.model_dump().items() if v is not None}
    return service.update_settings(data)


class TunnelUrlRequest(BaseModel):
    url: str


@router.get('/tunnel-url')
def get_tunnel_url(db: Session = Depends(get_db)):
    """トンネルURLを取得"""
    row = db.query(Setting).filter(Setting.key == 'tunnelUrl').first()
    return {'url': row.value if row else ''}


@router.put('/tunnel-url')
def update_tunnel_url(request: TunnelUrlRequest, db: Session = Depends(get_db)):
    """トンネルURLを更新"""
    row = db.query(Setting).filter(Setting.key == 'tunnelUrl').first()
    if row:
        row.value = request.url
    else:
        db.add(Setting(key='tunnelUrl', value=request.url))
    db.commit()
    return {'url': request.url}
