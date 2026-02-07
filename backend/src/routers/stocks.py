from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.schemas import (
    AddStockRequest,
    StockResponse,
    StockDetailResponse,
    ChartDataResponse,
    MessageResponse,
    RecommendationsResponse
)
from src.services.stock_service import StockService

router = APIRouter(prefix='/api', tags=['stocks'])


@router.get('/recommendations', response_model=RecommendationsResponse)
def get_recommendations(db: Session = Depends(get_db)):
    """おすすめ銘柄を取得"""
    service = StockService(db)
    return service.get_recommendations()


@router.get('/stocks', response_model=list[StockResponse])
def get_stocks(db: Session = Depends(get_db)):
    """監視銘柄一覧を取得"""
    service = StockService(db)
    return service.get_all_stocks()


@router.post('/stocks', response_model=StockResponse)
def add_stock(request: AddStockRequest, db: Session = Depends(get_db)):
    """銘柄を追加"""
    service = StockService(db)
    stock = service.add_stock(request.code)
    if not stock:
        raise HTTPException(status_code=400, detail='銘柄の追加に失敗しました')

    stocks = service.get_all_stocks()
    added = next((s for s in stocks if s['code'] == request.code), None)
    if not added:
        raise HTTPException(status_code=500, detail='銘柄の取得に失敗しました')
    return added


@router.delete('/stocks/{code}')
def delete_stock(code: str, db: Session = Depends(get_db)):
    """銘柄を削除"""
    service = StockService(db)
    if not service.delete_stock(code):
        raise HTTPException(status_code=404, detail='銘柄が見つかりません')
    return {'message': '削除しました'}


@router.get('/stocks/{code}', response_model=StockDetailResponse)
def get_stock_detail(code: str, db: Session = Depends(get_db)):
    """銘柄詳細を取得"""
    service = StockService(db)
    detail = service.get_stock_detail(code)
    if not detail:
        raise HTTPException(status_code=404, detail='銘柄が見つかりません')
    return detail


@router.get('/stocks/{code}/chart', response_model=list[ChartDataResponse])
def get_chart_data(code: str, period: str = '3m', db: Session = Depends(get_db)):
    """チャートデータを取得"""
    service = StockService(db)
    return service.get_chart_data(code, period)
