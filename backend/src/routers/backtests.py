from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.schemas import (
    BacktestCreateRequest, BacktestSummary, BacktestDetailResponse,
    BacktestTradeResponse, BacktestSnapshotResponse,
    BacktestCompareRequest, BacktestCompareResponse, MessageResponse,
)
from src.services.backtest_service import BacktestService

router = APIRouter(prefix='/api/backtests', tags=['backtests'])


@router.get('', response_model=list[BacktestSummary])
def get_backtests(db: Session = Depends(get_db)):
    """バックテスト一覧を取得"""
    service = BacktestService(db)
    return service.get_backtests()


@router.post('', response_model=BacktestDetailResponse)
def create_backtest(request: BacktestCreateRequest, db: Session = Depends(get_db)):
    """バックテストを作成・実行"""
    service = BacktestService(db)
    return service.create_backtest(
        name=request.name,
        start_date=request.startDate,
        end_date=request.endDate,
        initial_capital=request.initialCapital,
        codes=request.codes,
        strategy_params=request.strategyParams,
    )


@router.get('/{backtest_id}', response_model=BacktestDetailResponse)
def get_backtest(backtest_id: int, db: Session = Depends(get_db)):
    """バックテスト詳細を取得"""
    service = BacktestService(db)
    result = service.get_backtest(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail='バックテストが見つかりません')
    return result


@router.delete('/{backtest_id}', response_model=MessageResponse)
def delete_backtest(backtest_id: int, db: Session = Depends(get_db)):
    """バックテストを削除"""
    service = BacktestService(db)
    if not service.delete_backtest(backtest_id):
        raise HTTPException(status_code=404, detail='バックテストが見つかりません')
    return {'message': '削除しました'}


@router.get('/{backtest_id}/trades', response_model=list[BacktestTradeResponse])
def get_backtest_trades(backtest_id: int, db: Session = Depends(get_db)):
    """バックテストの取引一覧"""
    service = BacktestService(db)
    return service.get_trades(backtest_id)


@router.get('/{backtest_id}/snapshots', response_model=list[BacktestSnapshotResponse])
def get_backtest_snapshots(backtest_id: int, db: Session = Depends(get_db)):
    """バックテストの資産推移"""
    service = BacktestService(db)
    return service.get_snapshots(backtest_id)


@router.post('/compare', response_model=BacktestCompareResponse)
def compare_backtests(request: BacktestCompareRequest, db: Session = Depends(get_db)):
    """複数バックテストの比較"""
    service = BacktestService(db)
    results = service.compare_backtests(request.ids)
    return {'backtests': results}
