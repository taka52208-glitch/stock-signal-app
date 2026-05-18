"""AutoTradeService のユニットテスト"""
from datetime import datetime
from src.models.stock import (
    AutoTradeConfig, AutoTradeStock, AutoTradeLog,
    Stock, Signal, Transaction, StockPrice,
)
from src.services.auto_trade_service import AutoTradeService, _get_time_weight


class TestConfig:
    """設定CRUD"""

    def test_get_default_config(self, db):
        service = AutoTradeService(db)
        config = service.get_config()
        assert config['enabled'] is True
        assert config['dryRun'] is True
        assert config['minSignalStrength'] == 1
        assert config['maxTradesPerDay'] == 15
        assert config['orderType'] == 'market'

    def test_update_config(self, db):
        service = AutoTradeService(db)
        service.update_config({'minSignalStrength': 2, 'dryRun': False})
        config = service.get_config()
        assert config['minSignalStrength'] == 2
        assert config['dryRun'] is False

    def test_toggle(self, db):
        service = AutoTradeService(db)
        service.toggle(False)
        config = service.get_config()
        assert config['enabled'] is False
        service.toggle(True)
        config = service.get_config()
        assert config['enabled'] is True

    def test_ignore_unknown_keys(self, db):
        service = AutoTradeService(db)
        service.update_config({'unknownKey': 'value'})
        config = service.get_config()
        assert 'unknownKey' not in config


class TestStockSettings:
    """銘柄別設定"""

    def test_get_stock_settings_empty(self, db):
        service = AutoTradeService(db)
        settings = service.get_stock_settings()
        assert settings == []

    def test_update_stock_setting(self, db):
        db.add(Stock(code='7203', name='トヨタ'))
        db.commit()
        service = AutoTradeService(db)
        result = service.update_stock_setting('7203', True)
        assert result['enabled'] is True

    def test_update_nonexistent_stock_raises(self, db):
        service = AutoTradeService(db)
        with pytest.raises(ValueError, match='見つかりません'):
            service.update_stock_setting('9999', True)


class TestLogs:
    """ログ取得"""

    def test_get_logs_empty(self, db):
        service = AutoTradeService(db)
        logs = service.get_logs()
        assert logs == []

    def test_get_logs_returns_entries(self, db):
        db.add(AutoTradeLog(
            code='7203', signal_type='buy', signal_strength=2,
            order_type='market', order_price=3000.0, quantity=10,
            risk_passed=True, executed=True, dry_run=True,
            result_status='success', result_message='テスト',
        ))
        db.commit()
        service = AutoTradeService(db)
        logs = service.get_logs()
        assert len(logs) == 1
        assert logs[0]['code'] == '7203'
        assert logs[0]['signalStrength'] == 2


class TestHoldingQuantity:
    """保有数量計算"""

    def test_no_transactions(self, db):
        service = AutoTradeService(db)
        assert service._get_holding_quantity('7203') == 0

    def test_buy_only(self, db):
        db.add(Transaction(code='7203', transaction_type='buy', quantity=10, price=3000))
        db.commit()
        service = AutoTradeService(db)
        assert service._get_holding_quantity('7203') == 10

    def test_buy_and_sell(self, db):
        db.add(Transaction(code='7203', transaction_type='buy', quantity=10, price=3000))
        db.add(Transaction(code='7203', transaction_type='sell', quantity=3, price=3100))
        db.commit()
        service = AutoTradeService(db)
        assert service._get_holding_quantity('7203') == 7

    def test_sell_more_than_buy(self, db):
        """売り超過でも0を返す"""
        db.add(Transaction(code='7203', transaction_type='buy', quantity=5, price=3000))
        db.add(Transaction(code='7203', transaction_type='sell', quantity=10, price=3100))
        db.commit()
        service = AutoTradeService(db)
        assert service._get_holding_quantity('7203') == 0


class TestEntryPrice:
    """平均取得単価計算"""

    def test_no_transactions(self, db):
        service = AutoTradeService(db)
        assert service._get_entry_price('7203') is None

    def test_single_buy(self, db):
        db.add(Transaction(code='7203', transaction_type='buy', quantity=10, price=3000))
        db.commit()
        service = AutoTradeService(db)
        assert service._get_entry_price('7203') == 3000.0


class TestTimeWeight:
    """時間帯重みのテスト"""

    def test_returns_float(self):
        weight = _get_time_weight()
        assert isinstance(weight, float)
        assert weight >= 0.0


import pytest  # noqa: E402
