from sqlalchemy.orm import Session
from src.models.stock import Alert, AlertHistory, Stock, StockPrice, Signal


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def get_alerts(self) -> list[dict]:
        """全アラートを取得"""
        alerts = self.db.query(Alert).order_by(Alert.created_at.desc()).all()
        result = []
        for a in alerts:
            stock = self.db.query(Stock).filter(Stock.code == a.code).first()
            result.append({
                'id': a.id,
                'code': a.code,
                'name': stock.name if stock else f'銘柄{a.code}',
                'alertType': a.alert_type,
                'conditionValue': a.condition_value,
                'isActive': a.is_active,
                'createdAt': a.created_at.isoformat() if a.created_at else '',
            })
        return result

    def create_alert(self, code: str, alert_type: str, condition_value: float | None) -> dict:
        """アラートを作成"""
        alert = Alert(
            code=code,
            alert_type=alert_type,
            condition_value=condition_value,
            is_active=True,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        stock = self.db.query(Stock).filter(Stock.code == code).first()
        return {
            'id': alert.id,
            'code': alert.code,
            'name': stock.name if stock else f'銘柄{code}',
            'alertType': alert.alert_type,
            'conditionValue': alert.condition_value,
            'isActive': alert.is_active,
            'createdAt': alert.created_at.isoformat() if alert.created_at else '',
        }

    def delete_alert(self, alert_id: int) -> bool:
        """アラートを削除"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return False
        self.db.delete(alert)
        self.db.commit()
        return True

    def get_alert_history(self) -> list[dict]:
        """アラート履歴を取得"""
        history = self.db.query(AlertHistory).order_by(AlertHistory.triggered_at.desc()).limit(100).all()
        result = []
        for h in history:
            stock = self.db.query(Stock).filter(Stock.code == h.code).first()
            result.append({
                'id': h.id,
                'alertId': h.alert_id,
                'code': h.code,
                'name': stock.name if stock else f'銘柄{h.code}',
                'message': h.message,
                'alertType': h.alert_type,
                'signalBefore': h.signal_before,
                'signalAfter': h.signal_after,
                'priceAtTrigger': h.price_at_trigger,
                'isRead': h.is_read,
                'triggeredAt': h.triggered_at.isoformat() if h.triggered_at else '',
            })
        return result

    def mark_read(self, alert_history_ids: list[int]) -> int:
        """アラート履歴を既読にする"""
        count = self.db.query(AlertHistory).filter(
            AlertHistory.id.in_(alert_history_ids)
        ).update({AlertHistory.is_read: True}, synchronize_session='fetch')
        self.db.commit()
        return count

    def get_unread_count(self) -> int:
        """未読アラート数を取得"""
        return self.db.query(AlertHistory).filter(AlertHistory.is_read == False).count()

    def check_alerts(self):
        """全アクティブアラートをチェックし、条件を満たしたらアラート履歴に追加"""
        active_alerts = self.db.query(Alert).filter(Alert.is_active == True).all()

        for alert in active_alerts:
            latest_price = self.db.query(StockPrice).filter(
                StockPrice.code == alert.code
            ).order_by(StockPrice.date.desc()).first()

            if not latest_price:
                continue

            current_price = latest_price.close
            triggered = False
            message = ''

            if alert.alert_type == 'price_above' and alert.condition_value:
                if current_price >= alert.condition_value:
                    triggered = True
                    message = f'{alert.code} が ¥{alert.condition_value:,.0f} 以上になりました（現在 ¥{current_price:,.0f}）'

            elif alert.alert_type == 'price_below' and alert.condition_value:
                if current_price <= alert.condition_value:
                    triggered = True
                    message = f'{alert.code} が ¥{alert.condition_value:,.0f} 以下になりました（現在 ¥{current_price:,.0f}）'

            elif alert.alert_type == 'signal_change':
                latest_signal = self.db.query(Signal).filter(
                    Signal.code == alert.code
                ).order_by(Signal.date.desc()).first()
                prev_signal = self.db.query(Signal).filter(
                    Signal.code == alert.code
                ).order_by(Signal.date.desc()).offset(1).first()

                if latest_signal and prev_signal and latest_signal.signal_type != prev_signal.signal_type:
                    # 既に同じ変化を記録済みかチェック
                    existing = self.db.query(AlertHistory).filter(
                        AlertHistory.alert_id == alert.id,
                        AlertHistory.signal_before == prev_signal.signal_type,
                        AlertHistory.signal_after == latest_signal.signal_type,
                    ).first()
                    if not existing:
                        triggered = True
                        signal_labels = {'buy': '買い', 'sell': '売り', 'hold': '様子見'}
                        before = signal_labels.get(prev_signal.signal_type, prev_signal.signal_type)
                        after = signal_labels.get(latest_signal.signal_type, latest_signal.signal_type)
                        message = f'{alert.code} のシグナルが {before} → {after} に変化しました'

            if triggered:
                latest_signal = self.db.query(Signal).filter(
                    Signal.code == alert.code
                ).order_by(Signal.date.desc()).first()
                prev_signal = self.db.query(Signal).filter(
                    Signal.code == alert.code
                ).order_by(Signal.date.desc()).offset(1).first()

                history = AlertHistory(
                    alert_id=alert.id,
                    code=alert.code,
                    message=message,
                    alert_type=alert.alert_type,
                    signal_before=prev_signal.signal_type if prev_signal else None,
                    signal_after=latest_signal.signal_type if latest_signal else None,
                    price_at_trigger=current_price,
                    is_read=False,
                )
                self.db.add(history)

                # price系アラートは一度発火したら無効化
                if alert.alert_type in ('price_above', 'price_below'):
                    alert.is_active = False

        self.db.commit()
