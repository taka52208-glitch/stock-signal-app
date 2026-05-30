import asyncio
import logging
from datetime import date, datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func, text
from src.models.stock import (
    AutoTradeConfig, AutoTradeStock, AutoTradeLog,
    Stock, Signal, Transaction, StockPrice, BrokerageOrder,
)
from src.services.risk_service import RiskService
from src.services.brokerage_service import BrokerageService
from src.services.stock_service import StockService

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'enabled': 'true',
    'minSignalStrength': '1',
    'maxTradesPerDay': '15',
    'orderType': 'market',
    'dryRun': 'true',
    'takeProfitPercent': '10.0',
    'stopLossPercent': '-5.0',
    'tradingMode': 'cash',  # cash / margin_system / margin_general
}

# 時間帯重み: 昼休み前後は実行禁止、信頼性の高い時間帯にボーナス
TIME_WEIGHTS = {
    9: {0: 1.1, 30: 1.2},    # 9:00=1.1, 9:30=1.2（寄付き後トレンド確認期）
    10: {0: 1.2, 30: 1.1},   # 10:00=1.2, 10:30=1.1（信頼性高い時間帯）
    11: {0: 0.0, 30: 0.0},   # 11:00=0.0, 11:30=0.0（昼休み前→実行禁止）
    12: {0: 0.0, 30: 0.7},   # 12:00=0.0（昼休み→実行禁止）, 12:30=0.7（後場寄り）
    13: {0: 0.8, 30: 0.9},   # 13:00=0.8, 13:30=0.9
    14: {0: 1.2, 30: 1.2},   # 14:00=1.2, 14:30=1.2（大引け前の動意、信頼性高い）
    15: {0: 1.0, 30: 0.9},   # 15:00=1.0, 15:30=0.9
}


def _get_time_weight() -> float:
    """現在時刻の時間帯重みを返す"""
    now = datetime.now()
    hour_weights = TIME_WEIGHTS.get(now.hour)
    if not hour_weights:
        return 1.0
    minute_key = 30 if now.minute >= 30 else 0
    return hour_weights.get(minute_key, 1.0)


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
        trading_mode = result.get('tradingMode', 'cash')
        if trading_mode not in ('cash', 'margin_system', 'margin_general'):
            trading_mode = 'cash'
        return {
            'enabled': result['enabled'] == 'true',
            'minSignalStrength': int(result['minSignalStrength']),
            'maxTradesPerDay': int(result['maxTradesPerDay']),
            'orderType': result['orderType'],
            'dryRun': result['dryRun'] == 'true',
            'takeProfitPercent': float(result['takeProfitPercent']),
            'stopLossPercent': float(result['stopLossPercent']),
            'tradingMode': trading_mode,
        }

    def update_config(self, data: dict) -> dict:
        """自動売買設定を更新"""
        key_map = {
            'enabled': lambda v: str(v).lower(),
            'minSignalStrength': str,
            'maxTradesPerDay': str,
            'orderType': str,
            'dryRun': lambda v: str(v).lower(),
            'takeProfitPercent': str,
            'stopLossPercent': str,
            'tradingMode': str,
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

    def _get_today_trade_count(self, dry_run: bool = False) -> int:
        """本日の実行済み取引数"""
        today = date.today()
        query = self.db.query(AutoTradeLog).filter(
            sql_func.date(AutoTradeLog.created_at) == today,
        )
        if dry_run:
            query = query.filter(
                AutoTradeLog.dry_run == True,
                AutoTradeLog.result_status == 'success',
            )
        else:
            query = query.filter(AutoTradeLog.executed == True)
        return query.count()

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

    def _has_today_buy_order(self, code: str) -> bool:
        """本日この銘柄に対する買い注文が既に存在するか（status不問、failedも含む）"""
        today_start = datetime.combine(date.today(), time(0, 0))
        return self.db.query(BrokerageOrder).filter(
            BrokerageOrder.code == code,
            BrokerageOrder.side == 'buy',
            BrokerageOrder.created_at >= today_start,
        ).first() is not None

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

    def _get_dry_run_holding_quantity(self, code: str) -> int:
        """ドライランの仮想保有数量を計算（auto_trade_logから）"""
        logs = self.db.execute(text('''
            SELECT DISTINCT ON (code, signal_type, DATE_TRUNC('hour', created_at))
                signal_type, quantity
            FROM auto_trade_log
            WHERE code = :code AND result_status = 'success' AND dry_run = true
            ORDER BY code, signal_type, DATE_TRUNC('hour', created_at), created_at
        '''), {'code': code}).fetchall()
        qty = 0
        for sig, q in logs:
            if not q:
                continue
            if sig == 'buy':
                qty += q
            else:
                qty -= q
        return max(qty, 0)

    def _get_dry_run_entry_price(self, code: str) -> float | None:
        """ドライランの仮想平均取得単価を計算（auto_trade_logから）"""
        logs = self.db.execute(text('''
            SELECT DISTINCT ON (code, signal_type, DATE_TRUNC('hour', created_at))
                signal_type, order_price, quantity
            FROM auto_trade_log
            WHERE code = :code AND result_status = 'success' AND dry_run = true
            ORDER BY code, signal_type, DATE_TRUNC('hour', created_at), created_at
        '''), {'code': code}).fetchall()
        qty = 0
        total_cost = 0.0
        for sig, price, q in logs:
            if not q or not price:
                continue
            if sig == 'buy':
                qty += q
                total_cost += float(price) * q
            else:
                if qty > 0:
                    avg = total_cost / qty
                    sell_qty = min(q, qty)
                    qty -= sell_qty
                    total_cost -= sell_qty * avg
        return (total_cost / qty) if qty > 0 else None

    def _acquire_lock(self) -> bool:
        """同一時間枠での重複実行を防止（DBロック）"""
        now = datetime.now()
        lock_key = f"auto_trade_lock_{now.strftime('%Y%m%d_%H%M')}"
        try:
            existing = self.db.query(AutoTradeConfig).filter(
                AutoTradeConfig.key == lock_key
            ).first()
            if existing:
                logger.info(f"[auto-trade] Lock exists: {lock_key} (already ran this slot)")
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
        today_count = self._get_today_trade_count(dry_run=config['dryRun'])
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
        # 実資金モードで使う実残高（kabu接続OK後に取得）
        cash_balance: float | None = None

        # 実資金モード: 取引時間チェック + kabu STATION接続確認
        if not config['dryRun']:
            now = datetime.now()
            market_open = time(9, 0)
            market_close = time(15, 30)
            if not (market_open <= now.time() <= market_close):
                logger.info(f"[auto-trade] 取引時間外 ({now.strftime('%H:%M')}). 実資金注文をスキップ")
                self._add_log(
                    code='SYSTEM', signal_type='hold',
                    result_status='skipped',
                    result_message=f'取引時間外 ({now.strftime("%H:%M")})',
                    dry_run=False,
                )
                return
            # 昼休み (11:30-12:25) は注文を控える
            if time(11, 30) <= now.time() <= time(12, 25):
                logger.info(f"[auto-trade] 昼休み中 ({now.strftime('%H:%M')}). 実資金注文をスキップ")
                self._add_log(
                    code='SYSTEM', signal_type='hold',
                    result_status='skipped',
                    result_message=f'昼休み中 ({now.strftime("%H:%M")})',
                    dry_run=False,
                )
                return
            try:
                conn_result = asyncio.run(brokerage_service.connect())
                if not conn_result.get('connected'):
                    logger.error(f"[auto-trade] kabu STATION接続失敗: {conn_result.get('message')}. 全銘柄スキップ")
                    self._add_log(
                        code='SYSTEM', signal_type='hold',
                        result_status='failed',
                        result_message=f'kabu STATION接続失敗: {conn_result.get("message")}',
                        dry_run=False,
                    )
                    return
                logger.info("[auto-trade] kabu STATION接続確認OK")
                # 既存の submitted 注文の約定状態を同期（submitted→filled/cancelled）
                # 収支集計を正確に保つため。失敗しても発注処理は続行する。
                try:
                    sync_result = asyncio.run(brokerage_service.sync_orders())
                    if sync_result.get('updated'):
                        logger.info(f"[auto-trade] 注文状態を同期: {sync_result['message']}")
                except Exception as e:
                    logger.warning(f"[auto-trade] 注文状態の同期に失敗（続行）: {e}")
            except Exception as e:
                logger.error(f"[auto-trade] kabu STATION接続エラー: {e}. 全銘柄スキップ")
                self._add_log(
                    code='SYSTEM', signal_type='hold',
                    result_status='failed',
                    result_message=f'kabu STATION接続エラー: {str(e)}',
                    dry_run=False,
                )
                return
            # 実残高取得（数量計算と発注前検証に使用）
            # tradingMode=margin_* のときは信用余力(MarginAccountWallet) を effective_budget に使う。
            # kabu の get_balance() は cashBalance と marginBalance を返す（brokerage_service:320-322）。
            try:
                balance_data = asyncio.run(brokerage_service.get_balance())
                cash_balance = float(balance_data.get('cashBalance') or 0)
                margin_balance = float(balance_data.get('marginBalance') or 0)
                if config.get('tradingMode') in ('margin_system', 'margin_general') and margin_balance > 0:
                    cash_balance = margin_balance
                    logger.info(f"[auto-trade] 信用余力: {cash_balance:,.0f}円 (mode={config['tradingMode']})")
                else:
                    logger.info(f"[auto-trade] 実残高: {cash_balance:,.0f}円")
            except Exception as e:
                logger.error(f"[auto-trade] 残高取得エラー: {e}. 全銘柄スキップ")
                self._add_log(
                    code='SYSTEM', signal_type='hold',
                    result_status='failed',
                    result_message=f'残高取得エラー: {str(e)}',
                    dry_run=False,
                )
                return

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

            # a.2 保有中 → シグナル種別に関係なく自動利確・損切りチェック（ATR動的閾値 + トレーリングストップ）
            # BUG FIX: 以前は hold シグナル限定だったため、株価下落→RSI低下→buyシグナル発生時に
            # 損切りチェックがバイパスされていた。全シグナルで保有チェックを実行する。
            if config['dryRun']:
                entry_price = self._get_dry_run_entry_price(code)
                hold_qty = self._get_dry_run_holding_quantity(code)
            else:
                entry_price = self._get_entry_price(code)
                hold_qty = self._get_holding_quantity(code)

            if hold_qty > 0:
                take_profit_pct = config['takeProfitPercent']
                stop_loss_pct = config['stopLossPercent']
                sell_reason = None

                # ATR値を取得（動的閾値用）
                sig_atr = latest_signal.atr if hasattr(latest_signal, 'atr') else None

                if entry_price and current_price > 0 and hold_qty > 0:
                    gain_pct = ((current_price - entry_price) / entry_price) * 100

                    if sig_atr and sig_atr > 0:
                        # --- ATR動的閾値 + 3段階利確 + トレーリングストップ ---
                        atr_take_profit = entry_price + 4 * sig_atr
                        atr_stop_loss = entry_price - 2 * sig_atr
                        # 損切りは設定値(stopLossPercent)を上限に締める。
                        # ATRが広い銘柄でも最大損失を設定%（例 -5%）以内に抑える。
                        fixed_stop = entry_price * (1 + stop_loss_pct / 100)
                        atr_stop_loss = max(atr_stop_loss, fixed_stop)
                        atr_gain = current_price - entry_price
                        # 3段階利確閾値
                        atr_stage1 = 1.5 * sig_atr  # 第1段階: 33%利確
                        atr_stage2 = 2.5 * sig_atr  # 第2段階: 33%利確
                        atr_stage3 = 4.0 * sig_atr  # 第3段階: 全量利確
                        atr_trailing_threshold = 2.5 * sig_atr
                        atr_breakeven_threshold = 3.0 * sig_atr

                        if current_price >= atr_take_profit:
                            # 第3段階: entry + 5*ATR 到達 → 全量利確
                            sell_reason = (
                                f'ATR利確・第3段階（現在値 {current_price:.0f} >= 目標 {atr_take_profit:.0f}, '
                                f'含み益 {gain_pct:.1f}%）'
                            )
                        elif atr_gain >= atr_stage2:
                            # 第2段階: 含み益 >= 2.5*ATR → 33%利確（最低1株）
                            partial_qty = max(hold_qty // 3, 1)
                            if partial_qty < hold_qty:
                                sell_reason = (
                                    f'段階的利確・第2段階（含み益 {gain_pct:.1f}%, '
                                    f'{atr_gain:.0f} >= 2.5×ATR {atr_stage2:.0f}, '
                                    f'{partial_qty}/{hold_qty}株売却）'
                                )
                                hold_qty = partial_qty
                            else:
                                sell_reason = (
                                    f'段階的利確・第2段階（含み益 {gain_pct:.1f}%, '
                                    f'{atr_gain:.0f} >= 2.5×ATR {atr_stage2:.0f}, '
                                    f'全{hold_qty}株売却）'
                                )
                        elif atr_gain >= atr_stage1:
                            # 第1段階: 含み益 >= 1.5*ATR → 33%利確（最低1株）
                            partial_qty = max(hold_qty // 3, 1)
                            if partial_qty < hold_qty:
                                sell_reason = (
                                    f'段階的利確・第1段階（含み益 {gain_pct:.1f}%, '
                                    f'{atr_gain:.0f} >= 1.5×ATR {atr_stage1:.0f}, '
                                    f'{partial_qty}/{hold_qty}株売却→残りトレーリング）'
                                )
                                hold_qty = partial_qty
                            else:
                                sell_reason = (
                                    f'段階的利確・第1段階（含み益 {gain_pct:.1f}%, '
                                    f'{atr_gain:.0f} >= 1.5×ATR {atr_stage1:.0f}, '
                                    f'全{hold_qty}株売却）'
                                )

                        elif atr_gain >= atr_breakeven_threshold:
                            # ブレークイーブンストップ: 含み益 >= 3*ATR到達後、entry価格まで戻ったら売り
                            if current_price <= entry_price:
                                sell_reason = (
                                    f'ブレークイーブンストップ（現在値 {current_price:.0f} <= '
                                    f'取得単価 {entry_price:.0f}）'
                                )
                        elif atr_gain >= atr_trailing_threshold:
                            # トレーリングストップ: 含み益 >= 2.5*ATR → current - 2*ATR を下回ったら売り
                            trailing_stop = current_price - 2.0 * sig_atr
                            recent_prices = self.db.query(StockPrice).filter(
                                StockPrice.code == code
                            ).order_by(StockPrice.date.desc()).limit(2).all()
                            if len(recent_prices) >= 2 and recent_prices[0].low <= trailing_stop:
                                sell_reason = (
                                    f'トレーリングストップ（安値 {recent_prices[0].low:.0f} <= '
                                    f'トレーリング {trailing_stop:.0f}, 含み益 {gain_pct:.1f}%）'
                                )
                        elif current_price <= atr_stop_loss:
                            # ATR損切り: entry - 2.5*ATR
                            sell_reason = (
                                f'ATR損切り（現在値 {current_price:.0f} <= 損切り {atr_stop_loss:.0f}, '
                                f'含み損 {gain_pct:.1f}%）'
                            )
                    else:
                        # --- フォールバック: 従来の固定%ロジック ---
                        # 大幅利益 → 無条件利確
                        if gain_pct >= take_profit_pct * 2.0:
                            sell_reason = f'自動利確（含み益 {gain_pct:.1f}% >= {take_profit_pct * 2.0:.1f}%）'
                        # 利確閾値超え + 直近下落 → 利確
                        elif gain_pct >= take_profit_pct:
                            recent_2 = self.db.query(StockPrice).filter(
                                StockPrice.code == code
                            ).order_by(StockPrice.date.desc()).limit(2).all()
                            if len(recent_2) == 2 and recent_2[0].close < recent_2[1].close:
                                sell_reason = f'自動利確（含み益 {gain_pct:.1f}%, 直近下落中）'
                        # 損切り
                        elif gain_pct <= stop_loss_pct:
                            sell_reason = f'自動損切り（含み損 {gain_pct:.1f}% <= {stop_loss_pct:.1f}%）'

                if sell_reason and hold_qty > 0:
                    # 利確・損切り売り実行
                    logger.info(
                        f"[auto-trade] {code}: EXIT {sell_reason} "
                        f"(signal={latest_signal.signal_type}, entry={entry_price:.0f}, "
                        f"current={current_price:.0f}, qty={hold_qty})"
                    )
                    if config['dryRun']:
                        self._add_log(
                            code=code,
                            signal_type='sell',
                            signal_strength=latest_signal.signal_strength or 0,
                            active_signals=latest_signal.active_signals,
                            order_type=config['orderType'],
                            order_price=current_price,
                            quantity=hold_qty,
                            risk_passed=True,
                            executed=False,
                            dry_run=True,
                            result_status='success',
                            result_message=f'[DRY-RUN] {sell_reason}',
                        )
                        remaining_trades -= 1
                    else:
                        try:
                            order_result = asyncio.run(
                                brokerage_service.create_order(
                                    code=code, order_type=config['orderType'],
                                    side='sell', quantity=hold_qty,
                                    price=current_price if config['orderType'] == 'limit' else None,
                                    trading_mode=config.get('tradingMode', 'cash'),
                                )
                            )
                            if order_result.get('status') == 'failed':
                                raise RuntimeError(f"売注文がfailedステータスで返却 (id={order_result.get('id')})")
                            transaction = Transaction(
                                code=code, transaction_type='sell',
                                quantity=hold_qty, price=current_price,
                                memo=f'[自動売買] {sell_reason}',
                            )
                            self.db.add(transaction)
                            self.db.commit()
                            self.db.refresh(transaction)
                            self._add_log(
                                code=code, signal_type='sell',
                                signal_strength=latest_signal.signal_strength or 0,
                                active_signals=latest_signal.active_signals,
                                order_type=config['orderType'], order_price=current_price,
                                quantity=hold_qty, risk_passed=True,
                                executed=True, dry_run=False,
                                result_status='success',
                                result_message=f'{sell_reason} (Order: {order_result.get("brokerageOrderId", "N/A")})',
                                transaction_id=transaction.id,
                                brokerage_order_id=order_result.get('brokerageOrderId'),
                            )
                            remaining_trades -= 1
                        except Exception as e:
                            self._add_log(
                                code=code, signal_type='sell',
                                signal_strength=latest_signal.signal_strength or 0,
                                active_signals=latest_signal.active_signals,
                                order_price=current_price, quantity=hold_qty,
                                executed=False, dry_run=False,
                                result_status='failed',
                                result_message=f'{sell_reason} 注文失敗: {str(e)}',
                            )
                    continue

                # イグジット未発動 → 保有状況ログ出力
                gain_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price else 0
                atr_info = ''
                if sig_atr and sig_atr > 0 and entry_price:
                    atr_sl = entry_price - 2 * sig_atr
                    atr_tp = entry_price + 4 * sig_atr
                    atr_info = f', ATR={sig_atr:.0f}, SL={atr_sl:.0f}, TP={atr_tp:.0f}'
                entry_str = f'{entry_price:.0f}' if entry_price else 'N/A'
                logger.info(
                    f"[auto-trade] {code}: HOLD (signal={latest_signal.signal_type}, "
                    f"entry={entry_str}, current={current_price:.0f}, "
                    f"gain={gain_pct:+.1f}%, qty={hold_qty}{atr_info})"
                )

                # holdシグナルなら様子見ログ、buy/sellシグナルなら保有中スキップ
                if latest_signal.signal_type == 'hold':
                    msg = f'holdシグナル（含み益 {gain_pct:+.1f}%）'
                elif latest_signal.signal_type == 'buy':
                    msg = f'既に保有中（{hold_qty}株, 含み益 {gain_pct:+.1f}%）'
                else:
                    # sellシグナルだがイグジット条件未達 → 通常sell処理へ進む
                    pass

                if latest_signal.signal_type in ('hold', 'buy'):
                    self._add_log(
                        code=code,
                        signal_type=latest_signal.signal_type,
                        signal_strength=latest_signal.signal_strength or 0,
                        active_signals=latest_signal.active_signals,
                        order_price=current_price,
                        result_status='skipped',
                        result_message=msg,
                        dry_run=config['dryRun'],
                    )
                    continue
                # sellシグナルの場合はイグジット未発動でも通常sell処理に進む
            elif latest_signal.signal_type == 'hold':
                # 未保有 + holdシグナル → 何もしない
                self._add_log(
                    code=code,
                    signal_type='hold',
                    signal_strength=latest_signal.signal_strength or 0,
                    active_signals=latest_signal.active_signals,
                    order_price=current_price,
                    result_status='skipped',
                    result_message='holdシグナル（様子見）',
                    dry_run=config['dryRun'],
                )
                continue

            # b. 時間帯重み適用 + シグナル強度チェック
            time_weight = _get_time_weight()
            raw_score = latest_signal.signal_score or 0
            adjusted_score = raw_score * time_weight
            # 調整後スコアで強度を再計算
            if adjusted_score >= 2.5:
                strength = 3
            elif adjusted_score >= 1.0:
                strength = 2
            elif adjusted_score > 0:
                strength = 1
            else:
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

            # c. 数量計算（1銘柄あたり = 予算 / 最大保有銘柄数）
            if latest_signal.signal_type == 'buy':
                # 重複買い防止: 既に保有中の銘柄はスキップ
                existing_qty = (self._get_dry_run_holding_quantity(code) if config['dryRun']
                                else self._get_holding_quantity(code))
                if existing_qty > 0:
                    self._add_log(
                        code=code, signal_type='buy', signal_strength=strength,
                        active_signals=latest_signal.active_signals,
                        order_price=current_price, quantity=0,
                        result_status='skipped',
                        result_message=f'既に保有中（{existing_qty}株）',
                        dry_run=config['dryRun'],
                    )
                    continue
                # 実資金モード: 当日その銘柄に既に発注済み（pending/submitted/filled/failed）ならスキップ
                # → 同一スロットや次スロットで同じバグ注文を繰り返さないため
                if not config['dryRun'] and self._has_today_buy_order(code):
                    self._add_log(
                        code=code, signal_type='buy', signal_strength=strength,
                        active_signals=latest_signal.active_signals,
                        order_price=current_price, quantity=0,
                        result_status='skipped',
                        result_message='本日この銘柄に発注済み（重複防止）',
                        dry_run=False,
                    )
                    continue
                risk_rules = risk_service.get_risk_rules()
                max_positions = risk_rules['maxOpenPositions'] or 5
                # 実資金モードでは実残高で予算をクランプ
                effective_budget = settings['investmentBudget']
                if not config['dryRun'] and cash_balance is not None:
                    effective_budget = min(effective_budget, cash_balance)
                budget = effective_budget / max_positions
                raw_qty = int(budget / current_price) if current_price > 0 else 0
                quantity = (raw_qty // 100) * 100  # 単元株（100株）の倍数に切り捨て
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
                # 実資金モード: 注文額が実残高(5%バッファ)を超えるなら数量を下げる
                if not config['dryRun'] and cash_balance is not None:
                    affordable_qty = int((cash_balance * 0.95) / current_price) if current_price > 0 else 0
                    affordable_qty = (affordable_qty // 100) * 100
                    if affordable_qty < quantity:
                        if affordable_qty <= 0:
                            self._add_log(
                                code=code, signal_type='buy', signal_strength=strength,
                                active_signals=latest_signal.active_signals,
                                order_price=current_price, quantity=0,
                                result_status='skipped',
                                result_message=f'残高不足（残高{cash_balance:,.0f}円, 単価{current_price:.0f}円）',
                                dry_run=False,
                            )
                            continue
                        logger.info(f"[auto-trade] {code}: 残高により数量を {quantity}→{affordable_qty} に縮小")
                        quantity = affordable_qty
            else:  # sell
                if config['dryRun']:
                    quantity = self._get_dry_run_holding_quantity(code)
                else:
                    quantity = self._get_holding_quantity(code)
                if quantity <= 0:
                    logger.debug(f"[auto-trade] {code}: sell skipped (no holdings)")
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
                code, latest_signal.signal_type, quantity, current_price,
                dry_run=config['dryRun'],
            )
            risk_warnings = [
                {'level': w['level'], 'message': w['message']}
                for w in risk_result['warnings']
            ]

            if not risk_result['passed']:
                warn_msgs = [w['message'] for w in risk_warnings]
                logger.info(
                    f"[auto-trade] {code}: RISK_BLOCKED {latest_signal.signal_type} "
                    f"(strength={strength}, price={current_price:.0f}, qty={quantity}, "
                    f"reasons={warn_msgs})"
                )
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
                logger.info(
                    f"[auto-trade] {code}: EXECUTE {latest_signal.signal_type} "
                    f"(strength={strength}, price={current_price:.0f}, qty={quantity}, "
                    f"signals={latest_signal.active_signals})"
                )
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
                        trading_mode=config.get('tradingMode', 'cash'),
                    )
                )

                # 注文ステータス確認（failedならTransaction作成しない）
                if order_result.get('status') == 'failed':
                    raise RuntimeError(f"注文がfailedステータスで返却 (id={order_result.get('id')})")

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

        logger.info(f"[auto-trade] Processing complete. Trades today: {self._get_today_trade_count(dry_run=config['dryRun'])}")
