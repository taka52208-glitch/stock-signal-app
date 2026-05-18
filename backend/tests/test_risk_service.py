"""RiskService のユニットテスト"""
from datetime import datetime
from src.models.stock import RiskRule, Stock, StockPrice, Signal, Transaction
from src.services.risk_service import RiskService


class TestRiskRules:
    """リスクルールCRUD"""

    def test_get_default_rules(self, db):
        service = RiskService(db)
        rules = service.get_risk_rules()
        assert rules['maxPositionPercent'] == 50.0
        assert rules['maxLossPerTrade'] == 10.0
        assert rules['maxPortfolioLoss'] == 20.0
        assert rules['maxOpenPositions'] == 8

    def test_update_rules(self, db):
        service = RiskService(db)
        service.update_risk_rules({'maxOpenPositions': 5})
        rules = service.get_risk_rules()
        assert rules['maxOpenPositions'] == 5

    def test_ignore_unknown_keys(self, db):
        service = RiskService(db)
        service.update_risk_rules({'unknownKey': 99})
        rules = service.get_risk_rules()
        assert 'unknownKey' not in rules


class TestEvaluateTrade:
    """取引リスク評価"""

    def _setup_stock(self, db, code='7203', price=3000.0):
        db.add(Stock(code=code, name='テスト銘柄'))
        db.add(StockPrice(code=code, date=datetime.now().date(),
                          open=price, high=price * 1.01, low=price * 0.99,
                          close=price, volume=500000))
        db.commit()

    def test_first_trade_passes(self, db):
        """初回取引（空ポートフォリオ）は通過する"""
        self._setup_stock(db)
        service = RiskService(db)
        result = service.evaluate_trade('7203', 'buy', 10, 3000.0)
        assert result['passed'] is True
        assert result['tradeAmount'] == 30000.0

    def test_max_open_positions_blocks(self, db):
        """最大保有数に達すると拒否"""
        service = RiskService(db)
        service.update_risk_rules({'maxOpenPositions': 2})

        # 2銘柄保有中
        for code in ['7203', '6758']:
            db.add(Stock(code=code, name=f'銘柄{code}'))
            db.add(StockPrice(code=code, date=datetime.now().date(),
                              open=3000, high=3030, low=2970, close=3000, volume=500000))
            db.add(Transaction(code=code, transaction_type='buy', quantity=10, price=3000.0))
        db.commit()

        # 3銘柄目の購入を試行
        db.add(Stock(code='9984', name='テスト3'))
        db.add(StockPrice(code='9984', date=datetime.now().date(),
                          open=5000, high=5050, low=4950, close=5000, volume=300000))
        db.commit()

        result = service.evaluate_trade('9984', 'buy', 5, 5000.0)
        assert result['passed'] is False
        assert any('上限' in w['message'] for w in result['warnings'])

    def test_loss_per_trade_blocks(self, db):
        """損失率が上限を超えると拒否"""
        self._setup_stock(db, price=3000.0)
        service = RiskService(db)
        service.update_risk_rules({'maxLossPerTrade': 5})

        # 損切りラインが遠い（20%下）シグナルを設定
        db.add(Signal(
            code='7203', date=datetime.now().date(), signal_type='buy',
            stop_loss_price=2400.0,  # 3000 → 2400 = 20% 損失
        ))
        db.commit()

        result = service.evaluate_trade('7203', 'buy', 10, 3000.0)
        assert result['passed'] is False
        assert any('損切り' in w['message'] or '損失率' in w['message'] for w in result['warnings'])


class TestChecklist:
    """チェックリスト取得"""

    def test_checklist_with_signal(self, db):
        db.add(Stock(code='7203', name='トヨタ自動車'))
        db.add(StockPrice(code='7203', date=datetime.now().date(),
                          open=3000, high=3030, low=2970, close=3000, volume=500000))
        db.add(Signal(
            code='7203', date=datetime.now().date(), signal_type='buy',
            rsi=28.5, macd=10.0, macd_signal=8.0, signal_strength=2,
            target_price=3200.0, stop_loss_price=2800.0,
        ))
        db.commit()

        service = RiskService(db)
        result = service.get_checklist('7203')
        assert result['code'] == '7203'
        assert len(result['items']) > 0

    def test_checklist_no_data(self, db):
        db.add(Stock(code='9999', name='テスト'))
        db.commit()
        service = RiskService(db)
        result = service.get_checklist('9999')
        assert result['code'] == '9999'


class TestSuggestPrices:
    """価格提案"""

    def test_suggest_with_signal(self, db):
        db.add(Stock(code='7203', name='トヨタ'))
        db.add(StockPrice(code='7203', date=datetime.now().date(),
                          open=3000, high=3030, low=2970, close=3000, volume=500000))
        db.add(Signal(
            code='7203', date=datetime.now().date(), signal_type='buy',
            target_price=3200.0, stop_loss_price=2800.0,
            support_price=2900.0, resistance_price=3100.0,
        ))
        db.commit()

        service = RiskService(db)
        result = service.suggest_prices('7203')
        assert result['currentPrice'] == 3000.0
        assert len(result['suggestions']) > 0

    def test_suggest_no_price(self, db):
        db.add(Stock(code='7203', name='トヨタ'))
        db.commit()
        service = RiskService(db)
        result = service.suggest_prices('7203')
        assert result['currentPrice'] == 0
        assert result['suggestions'] == []
