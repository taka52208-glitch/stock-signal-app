import asyncio
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from src.models.stock import (
    AutoTradeConfig, AutoTradeStock, AutoTradeLog,
    Stock, Signal, Transaction, StockPrice,
)
from src.services.risk_service import RiskService
from src.services.brokerage_service import BrokerageService
from src.services.stock_service import StockService

DEFAULT_CONFIG = {
    'enabled': 'false',
    'minSignalStrength': '2',
    'maxTradesPerDay': '3',
    'orderType': 'market',
    'dryRun': 'true',
}


class AutoTradeService:
    def __init__(self, db: Session):
        self.db = db

    # --- 設定 CRUD ---

    def get_config(self) -> dict:
        """自動売買設定を取得"""
        result = dict(DEFAULT_CONFIG)
        db_config = self.db.query(AutoTradeConfig).all()
        for c in db_config:
            result[c.key] = c.value
        return {
            'enabled': result['enabled'] == 'true',
            'minSignalStrength': int(result['minSignalStrength']),
            'maxTradesPerDay': int(result['maxTradesPerDay']),
            'orderType': result['orderType'],
            'dryRun': result['dryRun'] == 'true',
        }

    def update_config(self, data: dict) -> dict:
        """自動売買設定を更新"""
        key_map = {
            'enabled': lambda v: str(v).lower(),
            'minSignalStrength': str,
            'maxTradesPerDay': str,
            'orderType': str,
            'dryRun': lambda v: str(v).lower(),
        }
        for key, value in data.items():
            if key not in key_map:
                continue
            str_value = key_map[key](value)
            config = self.db.query(AutoTradeConfig).filter(AutoTradeConfig.key == key).first()
            if config:
                config.value = str_value
            else:
                self.db.add(AutoTradeConfig(key=key, value=str_value))
        self.db.commit()
        return self.get_config()

    def toggle(self, enabled: bool) -> dict:
        """グローバルON/OFF"""
        return self.update_config({'enabled': enabled})

    # --- 銘柄別設定 ---

    def get_stock_settings(self) -> list[dict]:
        """銘柄別自動売買設定を取得"""
        stocks = self.db.query(Stock).all()
        auto_stocks = {
            a.code: a.enabled for a in self.db.query(AutoTradeStock).all()
        }
        return [
            {
                'code': s.code,
                'name': s.name,
                'enabled': auto_stocks.get(s.code, False),
            }
            for s in stocks
        ]

    def update_stock_setting(self, code: str, enabled: bool) -> dict:
        """銘柄別設定を更新"""
        stock = self.db.query(Stock).filter(Stock.code == code).first()
        if not stock:
            raise ValueError(f'銘柄 {code} が見つかりません')

        auto_stock = self.db.query(AutoTradeStock).filter(AutoTradeStock.code == code).first()
        if auto_stock:
            auto_stock.enabled = enabled
        else:
            self.db.add(AutoTradeStock(code=code, enabled=enabled))
        self.db.commit()
        return {'code': code, 'name': stock.name, 'enabled': enabled}

    # --- ログ取得 ---

    def get_logs(self, limit: int = 50) -> list[dict]:
        """実行ログを取得"""
        logs = self.db.query(AutoTradeLog).order_by(
            AutoTradeLog.created_at.desc()
        ).limit(limit).all()
        return [
            {
                'id': log.id,
                'code': log.code,
                'signalType': log.signal_type,
                'signalStrength': log.signal_strength,
                'activeSignals': log.active_signals.split(',') if log.active_signals else [],
                'orderType': log.order_type,
                'orderPrice': log.order_price,
                'quantity': log.quantity,
                'riskPassed': log.risk_passed,
                'riskWarnings': log.risk_warnings,
                'executed': log.executed,
                'dryRun': log.dry_run,
                'resultStatus': log.result_status,
                'resultMessage': log.result_message,
                'transactionId': log.transaction_id,
                'brokerageOrderId': log.brokerage_order_id,
                'createdAt': log.created_at.isoformat() if log.created_at else '',
            }
            for log in logs
        ]

    # --- コア処理 ---

    def _add_log(self, **kwargs) -> AutoTradeLog:
        """ログレコード追加"""
        log = AutoTradeLog(**kwargs)
        self.db.add(log)
        self.db.commit()
        return log

    def _get_today_trade_count(self) -> int:
        """本日の実行済み取引数"""
        today = date.today()
        return self.db.query(AutoTradeLog).filter(
            sql_func.date(AutoTradeLog.created_at) == today,
            AutoTradeLog.executed == True,
        ).count()

    def _get_holding_quantity(self, code: str) -> int:
        """保有数量を計算"""
        transactions = self.db.query(Transaction).filter(Transaction.code == code).all()
        qty = 0
        for t in transactions:
            if t.transaction_type == 'buy':
                qty += t.quantity
            else:
                qty -= t.quantity
        return max(qty, 0)

    def process_auto_trades(self):
        """自動売買メイン処理（scheduled_updateから呼ばれる）"""
        config = self.get_config()

        # 1. 無効なら即return
        if not config['enabled']:
            return

        # 2. 日次上限チェック
        today_count = self._get_today_trade_count()
        if today_count >= config['maxTradesPerDay']:
            print(f"[auto-trade] Daily limit reached ({today_count}/{config['maxTradesPerDay']})")
            return

        # 3. 有効な銘柄を取得
        enabled_stocks = self.db.query(AutoTradeStock).filter(
            AutoTradeStock.enabled == True
        ).all()
        if not enabled_stocks:
            return

        stock_service = StockService(self.db)
        risk_service = RiskService(self.db)
        brokerage_service = BrokerageService(self.db)
        settings = stock_service.get_settings()
        remaining_trades = config['maxTradesPerDay'] - today_count

        for auto_stock in enabled_stocks:
            if remaining_trades <= 0:
                break

            code = auto_stock.code

            # a. 最新シグナル取得
            latest_signal = self.db.query(Signal).filter(
                Signal.code == code
            ).order_by(Signal.date.desc()).first()

            if not latest_signal or latest_signal.signal_type == 'hold':
                continue

            # b. シグナル強度チェック
            strength = latest_signal.signal_strength or 0
            if strength < config['minSignalStrength']:
                self._add_log(
                    code=code,
                    signal_type=latest_signal.signal_type,
                    signal_strength=strength,
                    active_signals=latest_signal.active_signals,
                    result_status='skipped',
                    result_message=f'シグナル強度不足 ({strength} < {config["minSignalStrength"]})',
                    dry_run=config['dryRun'],
                )
                continue

            # c. 数量計算
            latest_price = self.db.query(StockPrice).filter(
                StockPrice.code == code
            ).order_by(StockPrice.date.desc()).first()
            if not latest_price:
                continue

            current_price = latest_price.close
            if latest_signal.signal_type == 'buy':
                budget = settings['investmentBudget'] / 3
                quantity = int(budget / current_price) if current_price > 0 else 0
                if quantity <= 0:
                    self._add_log(
                        code=code,
                        signal_type='buy',
                        signal_strength=strength,
                        active_signals=latest_signal.active_signals,
                        order_price=current_price,
                        quantity=0,
                        result_status='skipped',
                        result_message='予算不足で購入数量が0',
                        dry_run=config['dryRun'],
                    )
                    continue
            else:  # sell
                quantity = self._get_holding_quantity(code)
                if quantity <= 0:
                    self._add_log(
                        code=code,
                        signal_type='sell',
                        signal_strength=strength,
                        active_signals=latest_signal.active_signals,
                        order_price=current_price,
                        quantity=0,
                        result_status='skipped',
                        result_message='保有数量が0のため売却不可',
                        dry_run=config['dryRun'],
                    )
                    continue

            order_price = current_price if config['orderType'] == 'market' else (
                latest_signal.target_price or current_price
            )

            # d. リスク評価
            risk_result = risk_service.evaluate_trade(
                code, latest_signal.signal_type, quantity, current_price
            )
            risk_warnings = [
                {'level': w['level'], 'message': w['message']}
                for w in risk_result['warnings']
            ]

            if not risk_result['passed']:
                self._add_log(
                    code=code,
                    signal_type=latest_signal.signal_type,
                    signal_strength=strength,
                    active_signals=latest_signal.active_signals,
                    order_type=config['orderType'],
                    order_price=order_price,
                    quantity=quantity,
                    risk_passed=False,
                    risk_warnings=risk_warnings,
                    result_status='risk_blocked',
                    result_message='リスク評価で拒否されました',
                    dry_run=config['dryRun'],
                )
                continue

            # e. ドライラン
            if config['dryRun']:
                self._add_log(
                    code=code,
                    signal_type=latest_signal.signal_type,
                    signal_strength=strength,
                    active_signals=latest_signal.active_signals,
                    order_type=config['orderType'],
                    order_price=order_price,
                    quantity=quantity,
                    risk_passed=True,
                    risk_warnings=risk_warnings,
                    executed=False,
                    dry_run=True,
                    result_status='success',
                    result_message='[DRY-RUN] 注文は送信されませんでした',
                )
                remaining_trades -= 1
                continue

            # f. 実注文送信
            try:
                order_result = asyncio.run(
                    brokerage_service.create_order(
                        code=code,
                        order_type=config['orderType'],
                        side=latest_signal.signal_type,
                        quantity=quantity,
                        price=order_price if config['orderType'] == 'limit' else None,
                    )
                )

                # Transaction レコード作成
                transaction = Transaction(
                    code=code,
                    transaction_type=latest_signal.signal_type,
                    quantity=quantity,
                    price=current_price,
                    memo=f'[自動売買] {latest_signal.active_signals}',
                )
                self.db.add(transaction)
                self.db.commit()
                self.db.refresh(transaction)

                self._add_log(
                    code=code,
                    signal_type=latest_signal.signal_type,
                    signal_strength=strength,
                    active_signals=latest_signal.active_signals,
                    order_type=config['orderType'],
                    order_price=order_price,
                    quantity=quantity,
                    risk_passed=True,
                    risk_warnings=risk_warnings,
                    executed=True,
                    dry_run=False,
                    result_status='success',
                    result_message=f'注文送信完了 (Order ID: {order_result.get("brokerageOrderId", "N/A")})',
                    transaction_id=transaction.id,
                    brokerage_order_id=order_result.get('brokerageOrderId'),
                )
                remaining_trades -= 1

            except Exception as e:
                self._add_log(
                    code=code,
                    signal_type=latest_signal.signal_type,
                    signal_strength=strength,
                    active_signals=latest_signal.active_signals,
                    order_type=config['orderType'],
                    order_price=order_price,
                    quantity=quantity,
                    risk_passed=True,
                    risk_warnings=risk_warnings,
                    executed=False,
                    dry_run=False,
                    result_status='failed',
                    result_message=f'注文送信失敗: {str(e)}',
                )

        print(f"[auto-trade] Processing complete. Trades today: {self._get_today_trade_count()}")
