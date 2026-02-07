from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.schemas import (
    AlertCreateRequest, AlertResponse, AlertHistoryResponse,
    MarkReadRequest, UnreadCountResponse, MessageResponse,
)
from src.services.alert_service import AlertService

router = APIRouter(prefix='/api/alerts', tags=['alerts'])


@router.get('', response_model=list[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    """アラート一覧を取得"""
    service = AlertService(db)
    return service.get_alerts()


@router.post('', response_model=AlertResponse)
def create_alert(request: AlertCreateRequest, db: Session = Depends(get_db)):
    """アラートを作成"""
    service = AlertService(db)
    return service.create_alert(request.code, request.alertType, request.conditionValue)


@router.delete('/{alert_id}', response_model=MessageResponse)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """アラートを削除"""
    service = AlertService(db)
    if not service.delete_alert(alert_id):
        raise HTTPException(status_code=404, detail='アラートが見つかりません')
    return {'message': '削除しました'}


@router.get('/history', response_model=list[AlertHistoryResponse])
def get_alert_history(db: Session = Depends(get_db)):
    """アラート履歴を取得"""
    service = AlertService(db)
    return service.get_alert_history()


@router.post('/mark-read', response_model=MessageResponse)
def mark_read(request: MarkReadRequest, db: Session = Depends(get_db)):
    """アラートを既読にする"""
    service = AlertService(db)
    count = service.mark_read(request.ids)
    return {'message': f'{count}件を既読にしました'}


@router.get('/unread-count', response_model=UnreadCountResponse)
def get_unread_count(db: Session = Depends(get_db)):
    """未読アラート数を取得"""
    service = AlertService(db)
    return {'count': service.get_unread_count()}
