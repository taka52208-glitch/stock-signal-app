import asyncio
import logging
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func, text
from src.models.stock import (
    AutoTradeConfig, AutoTradeStock, AutoTradeLog,
    Stock, Signal, Transaction, StockPrice,
)
from src.services.risk_service import RiskService
from src.services.brokerage_service import BrokerageService
from src.services.stock_service import StockService

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'enabled': 'false',
    'minSignalStrength': '3',
    'maxTradesPerDay': '2',
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
        try:
            db_config = self.db.query(AutoTradeConfig).all()
            for c in db_config:
                result[c.key] = c.value
        except Exception as e:
            logger.error(f"[auto-trade] DB設定読み込み失敗（デフォルト使用）: {e}")
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

    def get_virtual_portfolio(self) -> dict:
        """ドライランの仮想収支を計算"""
        # 重複除外: 同一時間枠(hour)・同一銘柄・同一方向は1件のみ
        logs = self.db.execute(text('''
            SELECT DISTINCT ON (code, signal_type, DATE_TRUNC('hour', created_at))
                code, signal_type, order_price, quantity, created_at
            FROM auto_trade_log
            WHERE result_status = 'success' AND dry_run = true
            ORDER BY code, signal_type, DATE_TRUNC('hour', created_at), created_at
        ''')).fetchall()

        # 仮想ポジション集計
        positions: dict[str, dict] = {}
        trades = []
        realized_pnl = 0.0
        for code, sig, price, qty, created_at in logs:
            if not qty or not price:
                continue
            trades.append({
                'code': code,
                'side': sig,
                'price': float(price),
                'quantity': qty,
                'date': created_at.isoformat(),
            })
            if code not in positions:
                positions[code] = {'qty': 0, 'cost': 0.0}
            if sig == 'buy':
                positions[code]['qty'] += qty
                positions[code]['cost'] += float(price) * qty
            else:
                avg = positions[code]['cost'] / positions[code]['qty'] if positions[code]['qty'] > 0 else 0
                sell_qty = min(qty, positions[code]['qty'])
                realized_pnl += (float(price) - avg) * sell_qty
                positions[code]['qty'] -= sell_qty
                positions[code]['cost'] -= avg * sell_qty

        # 銘柄名・現在価格を取得
        codes = [c for c, p in positions.items() if p['qty'] > 0]
        stock_info = {}
        if codes:
            stocks = self.db.query(Stock).filter(Stock.code.in_(codes)).all()
            stock_info = {s.code: s.name for s in stocks}
            for code in codes:
                latest = self.db.query(StockPrice).filter(
                    StockPrice.code == code
                ).order_by(StockPrice.date.desc()).first()
                if latest:
                    stock_info[code] = {'name': stock_info.get(code, code), 'price': float(latest.close)}

        # レスポンス組み立て
        holdings = []
        total_cost = 0.0
        total_value = 0.0
        for code, pos in sorted(positions.items()):
            if pos['qty'] <= 0:
                continue
            info = stock_info.get(code, {})
            name = info.get('name', code) if isinstance(info, dict) else code
            current_price = info.get('price', 0) if isinstance(info, dict) else 0
            avg_price = pos['cost'] / pos['qty']
            value = current_price * pos['qty']
            pnl = value - pos['cost']
            pnl_pct = (pnl / pos['cost'] * 100) if pos['cost'] > 0 else 0
            total_cost += pos['cost']
            total_value += value
            holdings.append({
                'code': code,
                'name': name,
                'quantity': pos['qty'],
                'averagePrice': round(avg_price, 1),
                'currentPrice': current_price,
                'totalCost': round(pos['cost'], 0),
                'currentValue': round(value, 0),
                'profitLoss': round(pnl, 0),
                'profitLossPercent': round(pnl_pct, 2),
            })

        unrealized_pnl = total_value - total_cost
        unrealized_pnl_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
        total_pnl = realized_pnl + unrealized_pnl
        total_invested = total_cost + realized_pnl  # 実現損益込みの総投入額ベース
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        return {
            'holdings': holdings,
            'totalCost': round(total_cost, 0),
            'totalValue': round(total_value, 0),
            'totalProfitLoss': round(total_pnl, 0),
            'totalProfitLossPercent': round(total_pnl_pct, 2),
            'realizedProfitLoss': round(realized_pnl, 0),
            'unrealizedProfitLoss': round(unrealized_pnl, 0),
            'tradeCount': len(trades),
            'trades': trades,
        }

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

    def _get_entry_price(self, code: str) -> float | None:
        """保有銘柄の平均取得単価を計算"""
        transactions = self.db.query(Transaction).filter(
            Transaction.code == code
        ).order_by(Transaction.transaction_date).all()
        qty = 0
        total_cost = 0.0
        for t in transactions:
            if t.transaction_type == 'buy':
                qty += t.quantity
                total_cost += t.quantity * t.price
            else:
                if qty > 0:
                    avg = total_cost / qty
                    sell_qty = min(t.quantity, qty)
                    qty -= sell_qty
                    total_cost -= sell_qty * avg
        return (total_cost / qty) if qty > 0 else None

    def _acquire_lock(self) -> bool:
        """同一時間枠での重複実行を防止（DBロック）"""
        now = datetime.now()
        lock_key = f"auto_trade_lock_{now.strftime('%Y%m%d_%H')}"
        try:
            existing = self.db.query(AutoTradeConfig).filter(
                AutoTradeConfig.key == lock_key
            ).first()
            if existing:
                logger.info(f"[auto-trade] Lock exists: {lock_key} (already ran this hour)")
                return False
            self.db.add(AutoTradeConfig(key=lock_key, value=now.isoformat()))
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def _cleanup_old_locks(self):
        """前日以前のロックを削除"""
        try:
            self.db.execute(
                text("DELETE FROM auto_trade_config WHERE key LIKE 'auto_trade_lock_%' AND key < :today"),
                {'today': f"auto_trade_lock_{date.today().strftime('%Y%m%d')}"},
            )
            self.db.commit()
        except Exception:
            self.db.rollback()

    def process_auto_trades(self):
        """自動売買メイン処理（scheduled_updateから呼ばれる）"""
        # 重複実行防止
        self._cleanup_old_locks()
        if not self._acquire_lock():
            return

        config = self.get_config()

        logger.info(f"[auto-trade] Processing started (enabled={config['enabled']}, dryRun={config['dryRun']})")

        # 1. 無効なら即return（ログは残す）
        if not config['enabled']:
            logger.info("[auto-trade] Disabled, skipping")
            self._add_log(
                code='SYSTEM',
                signal_type='hold',
                result_status='skipped',
                result_message='自動売買が無効です',
                dry_run=config['dryRun'],
            )
            return

        # 2. 日次上限チェック
        today_count = self._get_today_trade_count()
        if today_count >= config['maxTradesPerDay']:
            logger.info(f"[auto-trade] Daily limit reached ({today_count}/{config['maxTradesPerDay']})")
            self._add_log(
                code='SYSTEM',
                signal_type='hold',
                result_status='skipped',
                result_message=f'日次取引上限到達 ({today_count}/{config["maxTradesPerDay"]})',
                dry_run=config['dryRun'],
            )
            return

        # 3. 有効な銘柄を取得
        enabled_stocks = self.db.query(AutoTradeStock).filter(
            AutoTradeStock.enabled == True
        ).all()
        if not enabled_stocks:
            logger.info("[auto-trade] No enabled stocks")
            self._add_log(
                code='SYSTEM',
                signal_type='hold',
                result_status='skipped',
                result_message='対象銘柄が未設定です',
                dry_run=config['dryRun'],
            )
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

            if not latest_signal:
                self._add_log(
                    code=code,
                    signal_type='hold',
                    result_status='skipped',
                    result_message='シグナルデータなし',
                    dry_run=config['dryRun'],
                )
                continue

            # a.1 最新価格取得
            latest_price = self.db.query(StockPrice).filter(
                StockPrice.code == code
            ).order_by(StockPrice.date.desc()).first()
            if not latest_price:
                self._add_log(
                    code=code,
                    signal_type=latest_signal.signal_type,
                    signal_strength=latest_signal.signal_strength or 0,
                    active_signals=latest_signal.active_signals,
                    result_status='skipped',
                    result_message='価格データなし',
                    dry_run=config['dryRun'],
                )
                continue
            current_price = latest_price.close

            # a.2 holdシグナル → 利益確保チェック（ログのみ）
            if latest_signal.signal_type == 'hold':
                msg = 'holdシグナル（様子見）'
                entry_price = self._get_entry_price(code)
                if entry_price and current_price > 0:
                    gain_pct = ((current_price - entry_price) / entry_price) * 100
                    if gain_pct >= 5.0:
                        recent_2 = self.db.query(StockPrice).filter(
                            StockPrice.code == code
                        ).order_by(StockPrice.date.desc()).limit(2).all()
                        if len(recent_2) == 2 and recent_2[0].close < recent_2[1].close:
                            msg = f'holdだが利益確保売却推奨（含み益 {gain_pct:.1f}%, 直近下落中）'
                    else:
                        msg = f'holdシグナル（含み益 {gain_pct:.1f}%）'
                self._add_log(
                    code=code,
                    signal_type='hold',
                    signal_strength=latest_signal.signal_strength or 0,
                    active_signals=latest_signal.active_signals,
                    order_price=current_price,
                    result_status='skipped',
                    result_message=msg,
                    dry_run=config['dryRun'],
                )
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

            # c. 数量計算（1銘柄あたり20%に制限）
            if latest_signal.signal_type == 'buy':
                budget = settings['investmentBudget'] / 5
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

        logger.info(f"[auto-trade] Processing complete. Trades today: {self._get_today_trade_count()}")
