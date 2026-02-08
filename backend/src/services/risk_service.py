from sqlalchemy.orm import Session
from src.models.stock import RiskRule, Stock, StockPrice, Signal, Transaction


DEFAULT_RISK_RULES = {
    'maxPositionPercent': '30',       # 1銘柄最大ポートフォリオ比率(%)
    'maxLossPerTrade': '5',           # 1取引最大損失率(%)
    'maxPortfolioLoss': '10',         # ポートフォリオ最大損失率(%)
    'maxOpenPositions': '5',          # 最大保有銘柄数
}


class RiskService:
    def __init__(self, db: Session):
        self.db = db

    def get_risk_rules(self) -> dict:
        """リスクルールを取得"""
        result = dict(DEFAULT_RISK_RULES)
        db_rules = self.db.query(RiskRule).all()
        for rule in db_rules:
            result[rule.key] = rule.value
        return {
            'maxPositionPercent': float(result['maxPositionPercent']),
            'maxLossPerTrade': float(result['maxLossPerTrade']),
            'maxPortfolioLoss': float(result['maxPortfolioLoss']),
            'maxOpenPositions': int(result['maxOpenPositions']),
        }

    def update_risk_rules(self, data: dict) -> dict:
        """リスクルールを更新"""
        for key, value in data.items():
            if key not in DEFAULT_RISK_RULES:
                continue
            rule = self.db.query(RiskRule).filter(RiskRule.key == key).first()
            if rule:
                rule.value = str(value)
            else:
                self.db.add(RiskRule(key=key, value=str(value)))
        self.db.commit()
        return self.get_risk_rules()

    def evaluate_trade(self, code: str, trade_type: str, quantity: int, price: float) -> dict:
        """取引前リスク評価"""
        rules = self.get_risk_rules()
        warnings = []
        passed = True
        trade_amount = quantity * price

        # 現在のポートフォリオ状態を計算
        transactions = self.db.query(Transaction).all()
        holdings = {}
        total_value = 0
        for t in transactions:
            if t.code not in holdings:
                holdings[t.code] = {'buy_qty': 0, 'buy_total': 0, 'sell_qty': 0}
            if t.transaction_type == 'buy':
                holdings[t.code]['buy_qty'] += t.quantity
                holdings[t.code]['buy_total'] += t.quantity * t.price
            else:
                holdings[t.code]['sell_qty'] += t.quantity

        active_positions = 0
        for c, data in holdings.items():
            qty = data['buy_qty'] - data['sell_qty']
            if qty > 0:
                active_positions += 1
                latest = self.db.query(StockPrice).filter(
                    StockPrice.code == c
                ).order_by(StockPrice.date.desc()).first()
                if latest:
                    total_value += qty * latest.close

        if trade_type == 'buy':
            # 最大保有銘柄数チェック
            is_new_position = code not in holdings or (
                holdings[code]['buy_qty'] - holdings[code]['sell_qty'] <= 0
            )
            if is_new_position and active_positions >= rules['maxOpenPositions']:
                warnings.append({
                    'level': 'error',
                    'message': f'保有銘柄数が上限（{int(rules["maxOpenPositions"])}銘柄）に達しています',
                })
                passed = False

            # ポジション比率チェック
            if total_value > 0:
                position_pct = (trade_amount / (total_value + trade_amount)) * 100
                if position_pct > rules['maxPositionPercent']:
                    warnings.append({
                        'level': 'error',
                        'message': f'この取引でポートフォリオの{position_pct:.1f}%を占めます'
                              f'（上限{rules["maxPositionPercent"]:.0f}%）',
                    })
                    passed = False

            # 損失リスクチェック
            latest_signal = self.db.query(Signal).filter(
                Signal.code == code
            ).order_by(Signal.date.desc()).first()
            if latest_signal and latest_signal.stop_loss_price:
                potential_loss_pct = ((price - latest_signal.stop_loss_price) / price) * 100
                if potential_loss_pct > rules['maxLossPerTrade']:
                    warnings.append({
                        'level': 'error',
                        'message': f'損切りラインまでの損失率が{potential_loss_pct:.1f}%です'
                              f'（上限{rules["maxLossPerTrade"]:.0f}%）',
                    })
                    passed = False

            # ポートフォリオ全体損失率チェック
            if total_value > 0:
                total_cost = 0.0
                for c, data in holdings.items():
                    qty = data['buy_qty'] - data['sell_qty']
                    if qty > 0 and data['buy_qty'] > 0:
                        avg_cost = data['buy_total'] / data['buy_qty']
                        total_cost += qty * avg_cost
                if total_cost > 0:
                    portfolio_loss_pct = ((total_cost - total_value) / total_cost) * 100
                    if portfolio_loss_pct > rules['maxPortfolioLoss']:
                        warnings.append({
                            'level': 'error',
                            'message': f'ポートフォリオ全体の損失率が{portfolio_loss_pct:.1f}%です'
                                  f'（上限{rules["maxPortfolioLoss"]:.0f}%）',
                        })
                        passed = False

        return {
            'passed': passed,
            'warnings': warnings,
            'tradeAmount': trade_amount,
            'currentPortfolioValue': round(total_value, 2),
            'activePositions': active_positions,
        }

    def get_checklist(self, code: str) -> dict:
        """取引チェックリスト"""
        stock = self.db.query(Stock).filter(Stock.code == code).first()
        latest_signal = self.db.query(Signal).filter(
            Signal.code == code
        ).order_by(Signal.date.desc()).first()
        latest_price = self.db.query(StockPrice).filter(
            StockPrice.code == code
        ).order_by(StockPrice.date.desc()).first()

        items = []

        if latest_signal:
            # シグナル確認
            signal_labels = {'buy': '買い', 'sell': '売り', 'hold': '様子見'}
            label = signal_labels.get(latest_signal.signal_type, latest_signal.signal_type)
            items.append({
                'label': f'現在のシグナル: {label}',
                'status': 'ok' if latest_signal.signal_type in ('buy', 'sell') else 'warning',
                'detail': f'強度: {latest_signal.signal_strength or 0}/3',
            })

            # RSI確認
            if latest_signal.rsi is not None:
                rsi = latest_signal.rsi
                if rsi <= 30:
                    rsi_status = 'ok'
                    rsi_detail = '売られすぎゾーン（買い有利）'
                elif rsi >= 70:
                    rsi_status = 'warning'
                    rsi_detail = '買われすぎゾーン（売り検討）'
                else:
                    rsi_status = 'neutral'
                    rsi_detail = '中立ゾーン'
                items.append({
                    'label': f'RSI: {rsi:.1f}',
                    'status': rsi_status,
                    'detail': rsi_detail,
                })

            # MACD確認
            if latest_signal.macd is not None and latest_signal.macd_signal is not None:
                macd_above = latest_signal.macd > latest_signal.macd_signal
                items.append({
                    'label': f'MACD: {"上回り" if macd_above else "下回り"}',
                    'status': 'ok' if macd_above else 'warning',
                    'detail': f'MACD={latest_signal.macd:.2f} / Signal={latest_signal.macd_signal:.2f}',
                })

            # 目標価格/損切りライン
            if latest_signal.target_price and latest_price:
                upside = ((latest_signal.target_price - latest_price.close) / latest_price.close) * 100
                items.append({
                    'label': f'目標価格: ¥{latest_signal.target_price:,.0f}',
                    'status': 'ok' if upside > 0 else 'warning',
                    'detail': f'上昇余地: {upside:+.1f}%',
                })

            if latest_signal.stop_loss_price and latest_price:
                downside = ((latest_signal.stop_loss_price - latest_price.close) / latest_price.close) * 100
                items.append({
                    'label': f'損切りライン: ¥{latest_signal.stop_loss_price:,.0f}',
                    'status': 'ok' if abs(downside) <= 5 else 'warning',
                    'detail': f'下落リスク: {downside:.1f}%',
                })

        # リスクルール確認
        rules = self.get_risk_rules()
        items.append({
            'label': f'最大保有銘柄数: {int(rules["maxOpenPositions"])}',
            'status': 'neutral',
            'detail': 'リスク管理設定より',
        })

        return {
            'code': code,
            'name': stock.name if stock else f'銘柄{code}',
            'items': items,
        }

    def suggest_prices(self, code: str) -> dict:
        """指値/逆指値の提案"""
        stock = self.db.query(Stock).filter(Stock.code == code).first()
        latest_signal = self.db.query(Signal).filter(
            Signal.code == code
        ).order_by(Signal.date.desc()).first()
        latest_price = self.db.query(StockPrice).filter(
            StockPrice.code == code
        ).order_by(StockPrice.date.desc()).first()

        if not latest_price:
            return {
                'code': code,
                'name': stock.name if stock else f'銘柄{code}',
                'currentPrice': 0,
                'suggestions': [],
            }

        current = latest_price.close
        suggestions = []

        if latest_signal:
            # 指値（買い）提案
            if latest_signal.support_price:
                support = latest_signal.support_price
                suggestions.append({
                    'type': 'limit_buy',
                    'label': '指値（支持線付近）',
                    'price': round(support * 1.005, 1),
                    'reason': f'支持線 ¥{support:,.0f} の少し上で買い指値',
                })

            # 現在値の2%下
            suggestions.append({
                'type': 'limit_buy',
                'label': '指値（現在値-2%）',
                'price': round(current * 0.98, 1),
                'reason': '現在値から2%下落した水準で買い',
            })

            # 逆指値（損切り）提案
            if latest_signal.stop_loss_price:
                suggestions.append({
                    'type': 'stop_loss',
                    'label': '逆指値（損切り）',
                    'price': round(latest_signal.stop_loss_price, 1),
                    'reason': 'テクニカル分析に基づく損切りライン',
                })

            # 逆指値（利確）提案
            if latest_signal.target_price:
                suggestions.append({
                    'type': 'take_profit',
                    'label': '指値（利確）',
                    'price': round(latest_signal.target_price, 1),
                    'reason': 'テクニカル分析に基づく目標価格',
                })

            # 逆指値（トレーリング）
            suggestions.append({
                'type': 'trailing_stop',
                'label': '逆指値（5%ルール）',
                'price': round(current * 0.95, 1),
                'reason': '現在値から5%下落で損切り',
            })

        return {
            'code': code,
            'name': stock.name if stock else f'銘柄{code}',
            'currentPrice': current,
            'suggestions': suggestions,
        }
