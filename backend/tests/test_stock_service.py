"""StockService のユニットテスト"""
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from src.models.stock import Stock, StockPrice, Signal, Setting
from src.services.stock_service import StockService


class TestCalculateIndicators:
    """テクニカル指標計算のテスト"""

    def _make_ohlcv(self, n=100, base=1000):
        """テスト用OHLCVデータを生成"""
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=n, freq='B')
        prices = [base]
        for _ in range(n - 1):
            prices.append(prices[-1] + np.random.normal(0, base * 0.01))
        close = np.array(prices)
        return pd.DataFrame({
            'date': dates,
            'open': close * 0.999,
            'high': close * 1.01,
            'low': close * 0.99,
            'close': close,
            'volume': np.random.randint(100000, 1000000, n),
        })

    def test_rsi_calculated(self, db):
        service = StockService(db)
        df = self._make_ohlcv()
        settings = service.get_settings()
        result = service.calculate_indicators(df, settings)
        assert 'rsi' in result.columns
        last_rsi = result['rsi'].iloc[-1]
        assert 0 <= last_rsi <= 100

    def test_macd_calculated(self, db):
        service = StockService(db)
        df = self._make_ohlcv()
        settings = service.get_settings()
        result = service.calculate_indicators(df, settings)
        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_histogram' in result.columns

    def test_sma_calculated(self, db):
        service = StockService(db)
        df = self._make_ohlcv()
        settings = service.get_settings()
        result = service.calculate_indicators(df, settings)
        assert 'sma5' in result.columns
        assert 'sma25' in result.columns
        assert 'sma75' in result.columns
        assert not pd.isna(result['sma5'].iloc[-1])
        assert not pd.isna(result['sma75'].iloc[-1])

    def test_bollinger_bands(self, db):
        service = StockService(db)
        df = self._make_ohlcv()
        settings = service.get_settings()
        result = service.calculate_indicators(df, settings)
        assert 'bb_upper' in result.columns
        assert 'bb_lower' in result.columns
        last = result.iloc[-1]
        assert last['bb_upper'] > last['bb_lower']

    def test_atr_calculated(self, db):
        service = StockService(db)
        df = self._make_ohlcv()
        settings = service.get_settings()
        result = service.calculate_indicators(df, settings)
        assert 'atr' in result.columns
        assert result['atr'].iloc[-1] > 0

    def test_stochastic_and_williams(self, db):
        service = StockService(db)
        df = self._make_ohlcv()
        settings = service.get_settings()
        result = service.calculate_indicators(df, settings)
        assert 'stoch_k' in result.columns
        assert 'stoch_d' in result.columns
        assert 'williams_r' in result.columns

    def test_adx_calculated(self, db):
        service = StockService(db)
        df = self._make_ohlcv()
        settings = service.get_settings()
        result = service.calculate_indicators(df, settings)
        assert 'adx' in result.columns

    def test_insufficient_data(self, db):
        """データが26日未満の場合、指標なしで返す"""
        service = StockService(db)
        df = self._make_ohlcv(n=10)
        settings = service.get_settings()
        result = service.calculate_indicators(df, settings)
        assert 'rsi' not in result.columns


class TestSignalDetails:
    """シグナル判定ロジックのテスト"""

    def _make_ohlcv_with_trend(self, direction='up', n=100, base=1000):
        """トレンド付きOHLCVデータを生成"""
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=n, freq='B')
        trend = np.linspace(0, base * 0.3 * (1 if direction == 'up' else -1), n)
        noise = np.random.normal(0, base * 0.005, n)
        close = base + trend + noise
        return pd.DataFrame({
            'date': dates,
            'open': close * 0.999,
            'high': close * 1.01,
            'low': close * 0.99,
            'close': close,
            'volume': np.random.randint(100000, 1000000, n),
        })

    def test_signal_returns_valid_type(self, db):
        service = StockService(db)
        df = self._make_ohlcv_with_trend()
        settings = service.get_settings()
        df = service.calculate_indicators(df, settings)
        result = service.calculate_signal_details(df, settings)
        assert result['signal_type'] in ('buy', 'sell', 'hold')
        assert result['signal_strength'] in (0, 1, 2, 3)

    def test_signal_score_non_negative(self, db):
        service = StockService(db)
        df = self._make_ohlcv_with_trend()
        settings = service.get_settings()
        df = service.calculate_indicators(df, settings)
        result = service.calculate_signal_details(df, settings)
        assert result['signal_score'] >= 0

    def test_hold_signal_for_short_data(self, db):
        """データ1行のみ → hold"""
        service = StockService(db)
        df = pd.DataFrame({
            'date': [datetime.now()],
            'close': [1000],
        })
        settings = service.get_settings()
        result = service.calculate_signal_details(df, settings)
        assert result['signal_type'] == 'hold'
        assert result['signal_strength'] == 0

    def test_low_volume_filters_signal(self, db):
        """出来高が0.7未満の場合、スコアが0になる"""
        service = StockService(db)
        df = self._make_ohlcv_with_trend(n=100)
        settings = service.get_settings()
        df = service.calculate_indicators(df, settings)
        # 出来高を極端に低く設定
        df['volume_ratio'] = 0.3
        result = service.calculate_signal_details(df, settings)
        if result['signal_type'] != 'hold':
            assert 'LowVolume' in result['active_signals']


class TestSettings:
    """設定CRUD"""

    def test_get_default_settings(self, db):
        service = StockService(db)
        settings = service.get_settings()
        assert settings['rsiBuyThreshold'] == 40
        assert settings['rsiSellThreshold'] == 60
        assert settings['investmentBudget'] == 1000000

    def test_update_settings(self, db):
        service = StockService(db)
        service.update_settings({'rsiBuyThreshold': 35})
        settings = service.get_settings()
        assert settings['rsiBuyThreshold'] == 35

    def test_update_settings_twice(self, db):
        """2回更新しても正しく反映"""
        service = StockService(db)
        service.update_settings({'rsiBuyThreshold': 35})
        service.update_settings({'rsiBuyThreshold': 30})
        settings = service.get_settings()
        assert settings['rsiBuyThreshold'] == 30


class TestStockCRUD:
    """銘柄の追加/削除（モックモード）"""

    def test_add_stock(self, db):
        service = StockService(db)
        result = service.add_stock('7203')
        assert result is not None
        stock = db.query(Stock).filter(Stock.code == '7203').first()
        assert stock.name == 'トヨタ自動車'

    def test_add_duplicate_stock(self, db):
        service = StockService(db)
        service.add_stock('7203')
        result = service.add_stock('7203')
        assert result is not None  # 既存を返す
        count = db.query(Stock).filter(Stock.code == '7203').count()
        assert count == 1

    def test_delete_stock(self, db):
        service = StockService(db)
        service.add_stock('7203')
        assert service.delete_stock('7203') is True
        assert db.query(Stock).filter(Stock.code == '7203').first() is None

    def test_delete_nonexistent_stock(self, db):
        service = StockService(db)
        assert service.delete_stock('9999') is False
