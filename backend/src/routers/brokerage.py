from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.schemas import (
    BrokerageConfigResponse, BrokerageConfigUpdateRequest,
    BrokerageConnectResponse, BrokerageBalanceResponse,
    BrokeragePositionResponse, OrderCreateRequest, OrderResponse,
    MessageResponse,
)
from src.services.brokerage_service import BrokerageService

router = APIRouter(prefix='/api/brokerage', tags=['brokerage'])


@router.get('/config', response_model=BrokerageConfigResponse)
def get_config(db: Session = Depends(get_db)):
    """接続設定を取得"""
    service = BrokerageService(db)
    return service.get_config()


@router.put('/config', response_model=BrokerageConfigResponse)
def update_config(request: BrokerageConfigUpdateRequest, db: Session = Depends(get_db)):
    """接続設定を更新"""
    service = BrokerageService(db)
    data = {k: v for k, v in request.model_dump().items() if v is not None}
    return service.update_config(data)


@router.post('/connect', response_model=BrokerageConnectResponse)
async def connect(db: Session = Depends(get_db)):
    """接続テスト"""
    service = BrokerageService(db)
    return await service.connect()


@router.get('/balance', response_model=BrokerageBalanceResponse)
async def get_balance(db: Session = Depends(get_db)):
    """残高照会"""
    service = BrokerageService(db)
    try:
        return await service.get_balance()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'残高取得エラー: {str(e)}')


@router.get('/positions', response_model=list[BrokeragePositionResponse])
async def get_positions(db: Session = Depends(get_db)):
    """保有銘柄照会"""
    service = BrokerageService(db)
    try:
        return await service.get_positions()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'ポジション取得エラー: {str(e)}')


@router.get('/orders', response_model=list[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    """注文一覧を取得"""
    service = BrokerageService(db)
    return service.get_orders()


@router.post('/orders', response_model=OrderResponse)
async def create_order(request: OrderCreateRequest, db: Session = Depends(get_db)):
    """注文を送信"""
    service = BrokerageService(db)
    return await service.create_order(
        code=request.code,
        order_type=request.orderType,
        side=request.side,
        quantity=request.quantity,
        price=request.price,
    )


@router.delete('/orders/{order_id}', response_model=MessageResponse)
async def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """注文をキャンセル"""
    service = BrokerageService(db)
    if not await service.cancel_order(order_id):
        raise HTTPException(status_code=404, detail='注文が見つかりません')
    return {'message': '注文をキャンセルしました'}


@router.post('/sync', response_model=MessageResponse)
async def sync_positions(db: Session = Depends(get_db)):
    """ポジション同期"""
    service = BrokerageService(db)
    try:
        return await service.sync_positions()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'同期エラー: {str(e)}')
