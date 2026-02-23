from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.schemas import (
    AutoTradeConfigResponse, AutoTradeConfigUpdateRequest,
    AutoTradeToggleRequest, AutoTradeStockSettingResponse,
    AutoTradeStockUpdateRequest, AutoTradeLogResponse,
    VirtualPortfolioResponse, MessageResponse,
)
from src.services.auto_trade_service import AutoTradeService

router = APIRouter(prefix='/api/auto-trade', tags=['auto-trade'])


@router.get('/config', response_model=AutoTradeConfigResponse)
def get_config(db: Session = Depends(get_db)):
    service = AutoTradeService(db)
    return service.get_config()


@router.put('/config', response_model=AutoTradeConfigResponse)
def update_config(request: AutoTradeConfigUpdateRequest, db: Session = Depends(get_db)):
    service = AutoTradeService(db)
    data = request.model_dump(exclude_none=True)
    return service.update_config(data)


@router.post('/toggle', response_model=AutoTradeConfigResponse)
def toggle(request: AutoTradeToggleRequest, db: Session = Depends(get_db)):
    service = AutoTradeService(db)
    return service.toggle(request.enabled)


@router.get('/log', response_model=list[AutoTradeLogResponse])
def get_log(limit: int = 50, db: Session = Depends(get_db)):
    service = AutoTradeService(db)
    return service.get_logs(limit)


@router.get('/virtual-portfolio', response_model=VirtualPortfolioResponse)
def get_virtual_portfolio(db: Session = Depends(get_db)):
    service = AutoTradeService(db)
    return service.get_virtual_portfolio()


@router.post('/run', response_model=MessageResponse)
def run_now(db: Session = Depends(get_db)):
    """手動で自動売買処理を1回実行（ロックをバイパス）"""
    service = AutoTradeService(db)
    service._cleanup_old_locks()
    # 現在時間のロックを削除してから実行
    from sqlalchemy import text
    from datetime import datetime
    lock_key = f"auto_trade_lock_{datetime.now().strftime('%Y%m%d_%H')}"
    db.execute(text("DELETE FROM auto_trade_config WHERE key = :key"), {'key': lock_key})
    db.commit()
    service.process_auto_trades()
    return {'message': '手動実行完了'}


@router.get('/stocks', response_model=list[AutoTradeStockSettingResponse])
def get_stock_settings(db: Session = Depends(get_db)):
    service = AutoTradeService(db)
    return service.get_stock_settings()


@router.put('/stocks/{code}', response_model=AutoTradeStockSettingResponse)
def update_stock_setting(code: str, request: AutoTradeStockUpdateRequest, db: Session = Depends(get_db)):
    service = AutoTradeService(db)
    try:
        return service.update_stock_setting(code, request.enabled)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
