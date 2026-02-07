from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.schemas import (
    RiskRulesResponse, RiskRulesUpdateRequest,
    TradeEvaluationRequest, TradeEvaluationResponse,
    ChecklistResponse, PriceSuggestionsResponse,
)
from src.services.risk_service import RiskService

router = APIRouter(prefix='/api/risk', tags=['risk'])


@router.get('/rules', response_model=RiskRulesResponse)
def get_risk_rules(db: Session = Depends(get_db)):
    """リスクルールを取得"""
    service = RiskService(db)
    return service.get_risk_rules()


@router.put('/rules', response_model=RiskRulesResponse)
def update_risk_rules(request: RiskRulesUpdateRequest, db: Session = Depends(get_db)):
    """リスクルールを更新"""
    service = RiskService(db)
    data = {k: v for k, v in request.model_dump().items() if v is not None}
    return service.update_risk_rules(data)


@router.post('/evaluate-trade', response_model=TradeEvaluationResponse)
def evaluate_trade(request: TradeEvaluationRequest, db: Session = Depends(get_db)):
    """取引前リスク評価"""
    service = RiskService(db)
    return service.evaluate_trade(request.code, request.tradeType, request.quantity, request.price)


@router.get('/checklist/{code}', response_model=ChecklistResponse)
def get_checklist(code: str, db: Session = Depends(get_db)):
    """取引チェックリスト"""
    service = RiskService(db)
    return service.get_checklist(code)


@router.get('/suggest-prices/{code}', response_model=PriceSuggestionsResponse)
def suggest_prices(code: str, db: Session = Depends(get_db)):
    """指値/逆指値の提案"""
    service = RiskService(db)
    return service.suggest_prices(code)
