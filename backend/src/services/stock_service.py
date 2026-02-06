import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Literal
from sqlalchemy.orm import Session
from src.models.stock import Stock, StockPrice, Signal, Setting
from src.config import settings as app_settings


def _import_yfinance():
    """yfinanceを遅延インポート（curl_cffi依存のため起動時クラッシュ防止）"""
    import yfinance as yf
    return yf


def _import_pandas_ta():
    """pandas_taを遅延インポート"""
    import pandas_ta as ta
    return ta

# 銘柄名マスタ（モック用）
STOCK_NAMES = {
    '7203': 'トヨタ自動車',
    '6758': 'ソニーグループ',
    '9984': 'ソフトバンクグループ',
    '8306': '三菱UFJフィナンシャル・グループ',
    '9432': '日本電信電話',
    '6861': 'キーエンス',
    '7974': '任天堂',
    '4063': '信越化学工業',
    '6098': 'リクルートホールディングス',
    '8035': '東京エレクトロン',
    '6501': '日立製作所',
    '6902': 'デンソー',
    '4568': '第一三共',
    '6920': 'レーザーテック',
    '8058': '三菱商事',
    '9983': 'ファーストリテイリング',
    '4661': 'オリエンタルランド',
    '7741': 'HOYA',
    '6594': 'ニデック',
    '6273': 'SMC',
}


class StockService:
    def __init__(self, db: Session):
        self.db = db
        self.mock_mode = app_settings.mock_mode

    def _generate_mock_data(self, code: str, days: int = 180) -> pd.DataFrame:
        """モック株価データを生成"""
        np.random.seed(int(code))
        base_price = 1000 + int(code) % 5000
        dates = pd.date_range(end=datetime.now(), periods=days, freq='B')

        prices = [base_price]
        for _ in range(days - 1):
            change = np.random.normal(0, base_price * 0.02)
            prices.append(max(prices[-1] + change, base_price * 0.5))

        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
            'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
            'close': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
            'volume': [int(np.random.uniform(100000, 1000000)) for _ in prices],
        })
        return df

    def get_settings(self) -> dict:
        """設定を取得"""
        defaults = {
            'rsiBuyThreshold': app_settings.rsi_buy_threshold,
            'rsiSellThreshold': app_settings.rsi_sell_threshold,
            'smaShortPeriod': app_settings.sma_short_period,
            'smaMidPeriod': app_settings.sma_mid_period,
            'smaLongPeriod': app_settings.sma_long_period,
        }
        db_settings = self.db.query(Setting).all()
        for s in db_settings:
            if s.key in defaults:
                defaults[s.key] = int(s.value)
        return defaults

    def update_settings(self, data: dict) -> dict:
        """設定を更新"""
        for key, value in data.items():
            setting = self.db.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = str(value)
            else:
                self.db.add(Setting(key=key, value=str(value)))
        self.db.commit()
        return self.get_settings()

    def fetch_stock_info(self, code: str) -> Optional[dict]:
        """銘柄情報を取得"""
        # モックモード
        if self.mock_mode:
            name = STOCK_NAMES.get(code, f'銘柄{code}')
            return {'code': code, 'name': name}

        # 実データ取得
        import time
        yf = _import_yfinance()
        ticker = yf.Ticker(f"{code}.T")

        try:
            time.sleep(1)
            df = ticker.history(period='5d')
            if df.empty:
                return None
        except Exception:
            return None

        name = STOCK_NAMES.get(code, f'銘柄{code}')
        try:
            info = ticker.info
            name = info.get('longName') or info.get('shortName') or name
        except Exception:
            pass

        return {'code': code, 'name': name}

    def fetch_stock_data(self, code: str, period: str = '6mo') -> Optional[pd.DataFrame]:
        """株価データを取得"""
        period_days = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365}
        days = period_days.get(period, 180)

        # モックモード
        if self.mock_mode:
            return self._generate_mock_data(code, days)

        # 実データ取得
        import time
        yf = _import_yfinance()
        try:
            time.sleep(1)
            ticker = yf.Ticker(f"{code}.T")
            df = ticker.history(period=period)
            if df.empty:
                return None
            df = df.reset_index()
            df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            if 'date' not in df.columns and 'datetime' in df.columns:
                df = df.rename(columns={'datetime': 'date'})
            return df[['date', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            print(f"fetch_stock_data error: {e}")
            return None

    def calculate_indicators(self, df: pd.DataFrame, settings: dict) -> pd.DataFrame:
        """テクニカル指標を計算"""
        if len(df) < 26:  # MACD計算に最低26日必要
            return df

        ta = _import_pandas_ta()

        # RSI
        df['rsi'] = ta.rsi(df['close'], length=14)

        # MACD
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df['macd'] = macd.iloc[:, 0]  # MACD line
            df['macd_histogram'] = macd.iloc[:, 1]  # Histogram
            df['macd_signal'] = macd.iloc[:, 2]  # Signal line

        # 移動平均線
        df['sma5'] = ta.sma(df['close'], length=settings['smaShortPeriod'])
        df['sma25'] = ta.sma(df['close'], length=settings['smaMidPeriod'])
        df['sma75'] = ta.sma(df['close'], length=settings['smaLongPeriod'])

        return df

    def determine_signal(self, df: pd.DataFrame, settings: dict) -> Literal['buy', 'sell', 'hold']:
        """シグナルを判定"""
        if len(df) < 2:
            return 'hold'

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        rsi = latest.get('rsi')
        macd = latest.get('macd')
        macd_signal = latest.get('macd_signal')
        sma_short = latest.get('sma5')
        sma_mid = latest.get('sma25')
        prev_sma_short = prev.get('sma5')
        prev_sma_mid = prev.get('sma25')

        # 買いシグナル判定
        buy_signals = []
        if rsi is not None and rsi <= settings['rsiBuyThreshold']:
            buy_signals.append('RSI')
        if macd is not None and macd_signal is not None:
            if prev.get('macd', 0) <= prev.get('macd_signal', 0) and macd > macd_signal:
                buy_signals.append('MACD')
        if sma_short is not None and sma_mid is not None:
            if prev_sma_short is not None and prev_sma_mid is not None:
                if prev_sma_short <= prev_sma_mid and sma_short > sma_mid:
                    buy_signals.append('GoldenCross')

        # 売りシグナル判定
        sell_signals = []
        if rsi is not None and rsi >= settings['rsiSellThreshold']:
            sell_signals.append('RSI')
        if macd is not None and macd_signal is not None:
            if prev.get('macd', 0) >= prev.get('macd_signal', 0) and macd < macd_signal:
                sell_signals.append('MACD')
        if sma_short is not None and sma_mid is not None:
            if prev_sma_short is not None and prev_sma_mid is not None:
                if prev_sma_short >= prev_sma_mid and sma_short < sma_mid:
                    sell_signals.append('DeadCross')

        if buy_signals:
            return 'buy'
        if sell_signals:
            return 'sell'
        return 'hold'

    def add_stock(self, code: str) -> Optional[Stock]:
        """銘柄を追加"""
        existing = self.db.query(Stock).filter(Stock.code == code).first()
        if existing:
            return existing

        info = self.fetch_stock_info(code)
        if not info:
            return None

        stock = Stock(code=code, name=info['name'])
        self.db.add(stock)
        self.db.commit()
        self.db.refresh(stock)

        # 初回データ取得
        self.update_stock_data(code)
        return stock

    def delete_stock(self, code: str) -> bool:
        """銘柄を削除"""
        stock = self.db.query(Stock).filter(Stock.code == code).first()
        if not stock:
            return False

        self.db.query(StockPrice).filter(StockPrice.code == code).delete()
        self.db.query(Signal).filter(Signal.code == code).delete()
        self.db.delete(stock)
        self.db.commit()
        return True

    def update_stock_data(self, code: str):
        """銘柄の株価データとシグナルを更新"""
        settings = self.get_settings()
        df = self.fetch_stock_data(code)
        if df is None or df.empty:
            return

        df = self.calculate_indicators(df, settings)

        # 最新データをDBに保存
        latest = df.iloc[-1]
        today = latest['date'].date() if hasattr(latest['date'], 'date') else latest['date']

        # 既存のデータを削除して再挿入（簡易実装）
        self.db.query(StockPrice).filter(StockPrice.code == code).delete()
        for _, row in df.iterrows():
            row_date = row['date'].date() if hasattr(row['date'], 'date') else row['date']
            price = StockPrice(
                code=code,
                date=row_date,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=int(row['volume'])
            )
            self.db.add(price)

        # シグナル保存
        signal_type = self.determine_signal(df, settings)
        self.db.query(Signal).filter(Signal.code == code, Signal.date == today).delete()
        signal = Signal(
            code=code,
            date=today,
            signal_type=signal_type,
            rsi=latest.get('rsi'),
            macd=latest.get('macd'),
            macd_signal=latest.get('macd_signal'),
            macd_histogram=latest.get('macd_histogram'),
            sma5=latest.get('sma5'),
            sma25=latest.get('sma25'),
            sma75=latest.get('sma75')
        )
        self.db.add(signal)
        self.db.commit()

    def get_all_stocks(self) -> list[dict]:
        """全銘柄の一覧を取得"""
        stocks = self.db.query(Stock).all()
        result = []
        for stock in stocks:
            latest_signal = self.db.query(Signal).filter(
                Signal.code == stock.code
            ).order_by(Signal.date.desc()).first()

            latest_price = self.db.query(StockPrice).filter(
                StockPrice.code == stock.code
            ).order_by(StockPrice.date.desc()).first()

            prev_price = self.db.query(StockPrice).filter(
                StockPrice.code == stock.code
            ).order_by(StockPrice.date.desc()).offset(1).first()

            if latest_price:
                current = latest_price.close
                prev_close = prev_price.close if prev_price else current
                change = ((current - prev_close) / prev_close * 100) if prev_close else 0

                result.append({
                    'id': stock.id,
                    'code': stock.code,
                    'name': stock.name,
                    'currentPrice': current,
                    'previousClose': prev_close,
                    'changePercent': round(change, 2),
                    'signal': latest_signal.signal_type if latest_signal else 'hold',
                    'rsi': round(latest_signal.rsi, 1) if latest_signal and latest_signal.rsi else 50.0,
                    'updatedAt': latest_price.date.isoformat() if latest_price else ''
                })
        return result

    def get_stock_detail(self, code: str) -> Optional[dict]:
        """銘柄詳細を取得"""
        stock = self.db.query(Stock).filter(Stock.code == code).first()
        if not stock:
            return None

        latest_signal = self.db.query(Signal).filter(
            Signal.code == code
        ).order_by(Signal.date.desc()).first()

        latest_price = self.db.query(StockPrice).filter(
            StockPrice.code == code
        ).order_by(StockPrice.date.desc()).first()

        prev_price = self.db.query(StockPrice).filter(
            StockPrice.code == code
        ).order_by(StockPrice.date.desc()).offset(1).first()

        if not latest_price:
            return None

        current = latest_price.close
        prev_close = prev_price.close if prev_price else current
        change = ((current - prev_close) / prev_close * 100) if prev_close else 0

        return {
            'id': stock.id,
            'code': stock.code,
            'name': stock.name,
            'currentPrice': current,
            'previousClose': prev_close,
            'changePercent': round(change, 2),
            'signal': latest_signal.signal_type if latest_signal else 'hold',
            'rsi': round(latest_signal.rsi, 1) if latest_signal and latest_signal.rsi else 50.0,
            'macd': round(latest_signal.macd, 2) if latest_signal and latest_signal.macd else 0.0,
            'macdSignal': round(latest_signal.macd_signal, 2) if latest_signal and latest_signal.macd_signal else 0.0,
            'macdHistogram': round(latest_signal.macd_histogram, 2) if latest_signal and latest_signal.macd_histogram else 0.0,
            'sma5': round(latest_signal.sma5, 0) if latest_signal and latest_signal.sma5 else 0,
            'sma25': round(latest_signal.sma25, 0) if latest_signal and latest_signal.sma25 else 0,
            'sma75': round(latest_signal.sma75, 0) if latest_signal and latest_signal.sma75 else 0,
            'updatedAt': latest_price.date.isoformat() if latest_price else ''
        }

    def get_chart_data(self, code: str, period: str = '3m') -> list[dict]:
        """チャートデータを取得"""
        period_days = {'1m': 30, '3m': 90, '6m': 180, '1y': 365}
        days = period_days.get(period, 90)

        prices = self.db.query(StockPrice).filter(
            StockPrice.code == code
        ).order_by(StockPrice.date.desc()).limit(days).all()

        prices = list(reversed(prices))
        settings = self.get_settings()

        if not prices:
            return []

        # DataFrameでSMAを計算
        df = pd.DataFrame([{
            'date': p.date,
            'open': p.open,
            'high': p.high,
            'low': p.low,
            'close': p.close,
            'volume': p.volume
        } for p in prices])

        ta = _import_pandas_ta()
        if len(df) >= settings['smaShortPeriod']:
            df['sma5'] = ta.sma(df['close'], length=settings['smaShortPeriod'])
        if len(df) >= settings['smaMidPeriod']:
            df['sma25'] = ta.sma(df['close'], length=settings['smaMidPeriod'])
        if len(df) >= settings['smaLongPeriod']:
            df['sma75'] = ta.sma(df['close'], length=settings['smaLongPeriod'])

        result = []
        for _, row in df.iterrows():
            result.append({
                'date': row['date'].strftime('%m/%d'),
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': int(row['volume']),
                'sma5': round(row['sma5'], 0) if pd.notna(row.get('sma5')) else None,
                'sma25': round(row['sma25'], 0) if pd.notna(row.get('sma25')) else None,
                'sma75': round(row['sma75'], 0) if pd.notna(row.get('sma75')) else None,
            })
        return result

    def update_all_stocks(self):
        """全銘柄のデータを更新"""
        stocks = self.db.query(Stock).all()
        for stock in stocks:
            try:
                self.update_stock_data(stock.code)
            except Exception as e:
                print(f"Failed to update {stock.code}: {e}")
