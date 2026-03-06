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
    # Phase 21 追加 (30銘柄)
    '8316': '三井住友フィナンシャルグループ',
    '8411': 'みずほフィナンシャルグループ',
    '8766': '東京海上ホールディングス',
    '6367': 'ダイキン工業',
    '6971': '京セラ',
    '7267': '本田技研工業',
    '7269': 'スズキ',
    '4755': '楽天グループ',
    '9613': 'NTTデータグループ',
    '4689': 'LINEヤフー',
    '8001': '伊藤忠商事',
    '8031': '三井物産',
    '8053': '住友商事',
    '4502': '武田薬品工業',
    '4503': 'アステラス製薬',
    '9433': 'KDDI',
    '9434': 'ソフトバンク',
    '8830': '住友不動産',
    '3289': '東急不動産ホールディングス',
    '2914': '日本たばこ産業',
    '2802': '味の素',
    '9501': '東京電力ホールディングス',
    '4911': '資生堂',
    '4452': '花王',
    '5401': '日本製鉄',
    '5108': 'ブリヂストン',
    '6762': 'TDK',
    '6981': '村田製作所',
    '9766': 'コナミグループ',
    '3659': 'ネクソン',
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
            'investmentBudget': app_settings.investment_budget,
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

        # ボリンジャーバンド (20日, 2σ)
        bbands = ta.bbands(df['close'], length=20, std=2)
        if bbands is not None:
            df['bb_lower'] = bbands.iloc[:, 0]
            df['bb_middle'] = bbands.iloc[:, 1]
            df['bb_upper'] = bbands.iloc[:, 2]

        # ATR (14日)
        if 'high' in df.columns and 'low' in df.columns:
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

        # 出来高比率 (当日出来高 / 20日平均出来高)
        if 'volume' in df.columns:
            vol_sma20 = ta.sma(df['volume'].astype(float), length=20)
            df['volume_ratio'] = df['volume'].astype(float) / vol_sma20.replace(0, np.nan)

        # ストキャスティクス (%K=14, %D=3)
        if 'high' in df.columns and 'low' in df.columns:
            stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3)
            if stoch is not None:
                df['stoch_k'] = stoch.iloc[:, 0]
                df['stoch_d'] = stoch.iloc[:, 1]

        # ウィリアムズ %R (14日)
        if 'high' in df.columns and 'low' in df.columns:
            willr = ta.willr(df['high'], df['low'], df['close'], length=14)
            if willr is not None:
                df['williams_r'] = willr

        # ADX (14日) - トレンド強度
        if 'high' in df.columns and 'low' in df.columns:
            adx = ta.adx(df['high'], df['low'], df['close'], length=14)
            if adx is not None:
                df['adx'] = adx.iloc[:, 0]  # ADX値

        return df

    def calculate_signal_details(self, df: pd.DataFrame, settings: dict) -> dict:
        """シグナル詳細を計算（加重スコアリング + ADX相場判定 + 確認待ち2日）"""
        if len(df) < 2:
            return {
                'signal_type': 'hold', 'signal_strength': 0, 'active_signals': [],
                'target_price': None, 'stop_loss_price': None,
                'support_price': None, 'resistance_price': None,
                'signal_score': 0.0,
            }

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = latest['close']

        rsi = latest.get('rsi')
        macd_val = latest.get('macd')
        macd_sig = latest.get('macd_signal')
        sma_short = latest.get('sma5')
        sma_mid = latest.get('sma25')
        sma_long = latest.get('sma75')
        prev_sma_short = prev.get('sma5')
        prev_sma_mid = prev.get('sma25')
        bb_upper = latest.get('bb_upper')
        bb_lower = latest.get('bb_lower')
        bb_middle = latest.get('bb_middle')
        atr = latest.get('atr')
        volume_ratio = latest.get('volume_ratio')
        stoch_k = latest.get('stoch_k')
        stoch_d = latest.get('stoch_d')
        prev_stoch_k = prev.get('stoch_k')
        prev_stoch_d = prev.get('stoch_d')
        williams_r = latest.get('williams_r')
        prev_williams_r = prev.get('williams_r')
        adx = latest.get('adx')

        # --- 買いシグナル判定（加重スコア） ---
        buy_signals = []
        buy_score = 0.0

        # RSI (重み 1.0)
        prev_rsi = prev.get('rsi')
        if rsi is not None and not pd.isna(rsi) and rsi <= settings['rsiBuyThreshold']:
            buy_signals.append('RSI')
            buy_score += 1.0
        # RSI モメンタムゾーン (重み 0.7): RSI閾値～閾値+10 かつ上昇中
        elif (rsi is not None and not pd.isna(rsi)
              and settings['rsiBuyThreshold'] < rsi <= settings['rsiBuyThreshold'] + 10
              and prev_rsi is not None and not pd.isna(prev_rsi) and rsi > prev_rsi):
            buy_signals.append('RSI_Rising')
            buy_score += 0.7

        # MACD クロスオーバー (重み 1.5, 確認待ち2日) / ヒストグラム反転 (重み 1.0, 排他)
        macd_histogram = latest.get('macd_histogram')
        prev_histogram = prev.get('macd_histogram')
        if macd_val is not None and macd_sig is not None:
            prev_macd = prev.get('macd', 0) or 0
            prev_sig = prev.get('macd_signal', 0) or 0
            # 確認待ち2日: 前日クロス発生(prev<=prevsig) + 今日維持(macd>sig)
            if prev_macd <= prev_sig and macd_val > macd_sig:
                buy_signals.append('MACD')
                buy_score += 1.5
            elif (macd_histogram is not None and prev_histogram is not None
                  and not pd.isna(macd_histogram) and not pd.isna(prev_histogram)
                  and prev_histogram <= 0 and macd_histogram > 0):
                buy_signals.append('MACD_Hist')
                buy_score += 1.0

        # ゴールデンクロス (重み 1.0, 確認待ち2日) / 価格-MA25クロス (重み 0.5, 排他)
        has_golden_cross = False
        if sma_short is not None and sma_mid is not None:
            if (prev_sma_short is not None and prev_sma_mid is not None):
                if (not pd.isna(prev_sma_short) and not pd.isna(prev_sma_mid)):
                    # 確認待ち2日: 前日未クロス→今日クロス
                    if prev_sma_short <= prev_sma_mid and sma_short > sma_mid:
                        buy_signals.append('GoldenCross')
                        buy_score += 1.0
                        has_golden_cross = True

        # 価格-MA25クロス (重み 0.5): GoldenCrossと排他
        if not has_golden_cross and sma_mid is not None and not pd.isna(sma_mid):
            prev_close = prev.get('close')
            if prev_close is not None and not pd.isna(prev_close):
                if prev_close <= sma_mid and current_price > sma_mid:
                    buy_signals.append('PriceAboveMA25')
                    buy_score += 0.5

        # BB バウンス (重み 0.8): 前日安値がBB下限以下 + 当日終値がBB下限上回り
        if bb_lower is not None and not pd.isna(bb_lower):
            prev_low = prev.get('low')
            if prev_low is not None and not pd.isna(prev_low):
                if prev_low <= bb_lower and current_price > bb_lower:
                    buy_signals.append('BB_Bounce')
                    buy_score += 0.8

        # RSI 50ライン上抜け (重み 0.5): 前日RSI<50 + 当日RSI>50（トレンド転換確認）
        if (rsi is not None and not pd.isna(rsi) and rsi > 50
                and prev_rsi is not None and not pd.isna(prev_rsi) and prev_rsi < 50
                and 'RSI' not in buy_signals and 'RSI_Rising' not in buy_signals):
            buy_signals.append('RSI_Above50')
            buy_score += 0.5

        # Stochastic ゴールデンクロス (重み 1.0, 確認待ち2日): %K<=30 & 前日→今日クロス
        if (stoch_k is not None and stoch_d is not None
                and not pd.isna(stoch_k) and not pd.isna(stoch_d)
                and prev_stoch_k is not None and prev_stoch_d is not None
                and not pd.isna(prev_stoch_k) and not pd.isna(prev_stoch_d)):
            # 確認待ち2日: 前日未クロス→今日クロス、かつ売られすぎゾーン
            if (stoch_k <= 30 and prev_stoch_k <= prev_stoch_d and stoch_k > stoch_d):
                buy_signals.append('Stoch_GC')
                buy_score += 1.0

        # Williams %R 買い (重み 0.5): %R<=-80から上昇
        if (williams_r is not None and prev_williams_r is not None
                and not pd.isna(williams_r) and not pd.isna(prev_williams_r)):
            if prev_williams_r <= -80 and williams_r > prev_williams_r:
                buy_signals.append('WillR_Buy')
                buy_score += 0.5

        # --- 売りシグナル判定（加重スコア） ---
        sell_signals = []
        sell_score = 0.0

        # RSI (重み 1.0)
        if rsi is not None and not pd.isna(rsi) and rsi >= settings['rsiSellThreshold']:
            sell_signals.append('RSI')
            sell_score += 1.0
        # RSI モメンタムゾーン (重み 0.7): RSI閾値-10～閾値 かつ下落中
        elif (rsi is not None and not pd.isna(rsi)
              and settings['rsiSellThreshold'] - 10 <= rsi < settings['rsiSellThreshold']
              and prev_rsi is not None and not pd.isna(prev_rsi) and rsi < prev_rsi):
            sell_signals.append('RSI_Falling')
            sell_score += 0.7

        # MACD デッドクロス (重み 1.5, 確認待ち2日) / ヒストグラム反転 (重み 1.0, 排他)
        if macd_val is not None and macd_sig is not None:
            prev_macd = prev.get('macd', 0) or 0
            prev_sig = prev.get('macd_signal', 0) or 0
            # 確認待ち2日: 前日>=→今日クロス
            if prev_macd >= prev_sig and macd_val < macd_sig:
                sell_signals.append('MACD')
                sell_score += 1.5
            elif (macd_histogram is not None and prev_histogram is not None
                  and not pd.isna(macd_histogram) and not pd.isna(prev_histogram)
                  and prev_histogram >= 0 and macd_histogram < 0):
                sell_signals.append('MACD_Hist')
                sell_score += 1.0

        # デッドクロス (重み 1.0, 確認待ち2日) / 価格-MA25クロス (重み 0.5, 排他)
        has_dead_cross = False
        if sma_short is not None and sma_mid is not None:
            if (prev_sma_short is not None and prev_sma_mid is not None):
                if (not pd.isna(prev_sma_short) and not pd.isna(prev_sma_mid)):
                    # 確認待ち2日: 前日未クロス→今日クロス
                    if prev_sma_short >= prev_sma_mid and sma_short < sma_mid:
                        sell_signals.append('DeadCross')
                        sell_score += 1.0
                        has_dead_cross = True

        # 価格-MA25クロス (重み 0.5): DeadCrossと排他
        if not has_dead_cross and sma_mid is not None and not pd.isna(sma_mid):
            prev_close = prev.get('close')
            if prev_close is not None and not pd.isna(prev_close):
                if prev_close >= sma_mid and current_price < sma_mid:
                    sell_signals.append('PriceBelowMA25')
                    sell_score += 0.5

        # BB タッチ (重み 0.8): 前日高値がBB上限以上 + 当日終値がBB上限下回り
        if bb_upper is not None and not pd.isna(bb_upper):
            prev_high = prev.get('high')
            if prev_high is not None and not pd.isna(prev_high):
                if prev_high >= bb_upper and current_price < bb_upper:
                    sell_signals.append('BB_Touch')
                    sell_score += 0.8

        # RSI 50ライン下抜け (重み 0.5): 前日RSI>50 + 当日RSI<50（トレンド転換確認）
        if (rsi is not None and not pd.isna(rsi) and rsi < 50
                and prev_rsi is not None and not pd.isna(prev_rsi) and prev_rsi > 50
                and 'RSI' not in sell_signals and 'RSI_Falling' not in sell_signals):
            sell_signals.append('RSI_Below50')
            sell_score += 0.5

        # Stochastic デッドクロス (重み 1.0, 確認待ち2日): %K>=70 & 前日→今日クロス
        if (stoch_k is not None and stoch_d is not None
                and not pd.isna(stoch_k) and not pd.isna(stoch_d)
                and prev_stoch_k is not None and prev_stoch_d is not None
                and not pd.isna(prev_stoch_k) and not pd.isna(prev_stoch_d)):
            # 確認待ち2日: 前日未クロス→今日クロス、かつ買われすぎゾーン
            if (stoch_k >= 70 and prev_stoch_k >= prev_stoch_d and stoch_k < stoch_d):
                sell_signals.append('Stoch_DC')
                sell_score += 1.0

        # Williams %R 売り (重み 0.5): %R>=-20から下降
        if (williams_r is not None and prev_williams_r is not None
                and not pd.isna(williams_r) and not pd.isna(prev_williams_r)):
            if prev_williams_r >= -20 and williams_r < prev_williams_r:
                sell_signals.append('WillR_Sell')
                sell_score += 0.5

        # --- ADXベース相場状態判定 + トレンドフィルター ---
        has_adx = adx is not None and not pd.isna(adx)
        has_trend_data = sma_long is not None and not pd.isna(sma_long)

        if has_adx and has_trend_data:
            # ADX > 25: 強いトレンド → トレンドフォロー系を重視、逆張り系をペナルティ
            # ADX < 20: レンジ相場 → 逆張り系を重視、トレンドフォロー系をペナルティ
            trend_follow_buy = {'MACD', 'GoldenCross', 'PriceAboveMA25', 'MACD_Hist'}
            mean_revert_buy = {'RSI', 'RSI_Rising', 'BB_Bounce', 'Stoch_GC', 'WillR_Buy'}
            trend_follow_sell = {'MACD', 'DeadCross', 'PriceBelowMA25', 'MACD_Hist'}
            mean_revert_sell = {'RSI', 'RSI_Falling', 'BB_Touch', 'Stoch_DC', 'WillR_Sell'}

            if adx > 40:
                # 過熱トレンド: 全シグナルにペナルティ（トレンド終了リスク）
                if buy_signals:
                    buy_score *= 0.7
                    buy_signals.append('OverheatedTrend')
                if sell_signals:
                    sell_score *= 0.7
                    sell_signals.append('OverheatedTrend')
                # カウンタートレンドはさらにペナルティ
                if current_price < sma_long and buy_signals:
                    buy_score *= 0.5
                    if 'CounterTrend' not in buy_signals:
                        buy_signals.append('CounterTrend')
                elif current_price > sma_long and sell_signals:
                    sell_score *= 0.5
                    if 'CounterTrend' not in sell_signals:
                        sell_signals.append('CounterTrend')
            elif adx > 25:
                # 強トレンド: 逆張り系 ×0.5、カウンタートレンド ×0.3
                if current_price < sma_long and buy_signals:
                    buy_score *= 0.3
                    buy_signals.append('CounterTrend')
                elif current_price > sma_long and sell_signals:
                    sell_score *= 0.3
                    sell_signals.append('CounterTrend')
                buy_signals.append('StrongTrend')
            elif adx < 20:
                # レンジ相場: トレンドフォロー系 ×0.5
                tf_buy = [s for s in buy_signals if s in trend_follow_buy]
                tf_sell = [s for s in sell_signals if s in trend_follow_sell]
                if tf_buy:
                    buy_score *= 0.5
                    buy_signals.append('RangeMarket')
                if tf_sell:
                    sell_score *= 0.5
                    sell_signals.append('RangeMarket')
            else:
                # ADX 20-25: 中間 → 従来のカウンタートレンドペナルティ
                if current_price < sma_long and buy_signals:
                    buy_score *= 0.5
                    buy_signals.append('CounterTrend')
                elif current_price > sma_long and sell_signals:
                    sell_score *= 0.5
                    sell_signals.append('CounterTrend')
        elif has_trend_data:
            # ADXなし: 従来のペナルティ方式にフォールバック
            TREND_PENALTY = 0.5
            if current_price < sma_long and buy_signals:
                buy_score *= TREND_PENALTY
                buy_signals.append('CounterTrend')
            elif current_price > sma_long and sell_signals:
                sell_score *= TREND_PENALTY
                sell_signals.append('CounterTrend')

        # --- 出来高確認 (重み 1.0) / 出来高不足フィルター ---
        has_vol_data = volume_ratio is not None and not pd.isna(volume_ratio)
        if has_vol_data and volume_ratio >= 2.0:
            # 出来高急増（ブレイクアウト確認）→ 追加ボーナス
            if buy_signals:
                buy_signals.append('VolConfirm')
                buy_score += 1.5
            if sell_signals:
                sell_signals.append('VolConfirm')
                sell_score += 1.5
        elif has_vol_data and volume_ratio >= 1.5:
            # 出来高増加 → シグナル信頼度向上
            if buy_signals:
                buy_signals.append('VolConfirm')
                buy_score += 1.0
            if sell_signals:
                sell_signals.append('VolConfirm')
                sell_score += 1.0
        elif has_vol_data and volume_ratio < 0.7:
            # 出来高不足 → シグナル除外（ダマシの可能性極めて高い）
            if buy_signals:
                buy_score = 0
                buy_signals = ['LowVolume']
            if sell_signals:
                sell_score = 0
                sell_signals = ['LowVolume']
        elif has_vol_data and volume_ratio < 0.8:
            # 出来高やや不足 → スコア半減
            if buy_signals:
                buy_score *= 0.5
                buy_signals.append('LowVolume')
            if sell_signals:
                sell_score *= 0.5
                sell_signals.append('LowVolume')
        elif not has_vol_data:
            # 出来高データなし → シグナル信頼性不明のためペナルティ
            if buy_signals:
                buy_score *= 0.5
                buy_signals.append('NoVolData')
            if sell_signals:
                sell_score *= 0.5
                sell_signals.append('NoVolData')

        # --- トレンド整合 (重み 0.5) ---
        if has_trend_data:
            if buy_signals and current_price > sma_long:
                buy_signals.append('TrendAlign')
                buy_score += 0.5
            if sell_signals and current_price < sma_long:
                sell_signals.append('TrendAlign')
                sell_score += 0.5

        # --- 支持線・抵抗線（直近25日の安値・高値） ---
        recent = df.tail(25)
        support_price = float(recent['low'].min())
        resistance_price = float(recent['high'].max())

        # --- シグナル判定 + スコアマッピング ---
        if buy_score > sell_score and buy_signals:
            signal_type = 'buy'
            active = buy_signals
            signal_score = buy_score

            # ATR ベース目標価格/損切り (R/R比 1:2 = 5×ATR利確 / 2.5×ATR損切り)
            if atr is not None and not pd.isna(atr) and atr > 0:
                target_price = current_price + 5 * atr
                stop_loss_price = current_price - 2.5 * atr
            else:
                # フォールバック: 従来ロジック
                candidates = [resistance_price]
                if sma_long is not None and not pd.isna(sma_long) and sma_long > current_price:
                    candidates.append(float(sma_long))
                candidates.append(current_price * 1.10)
                target_price = max(candidates)
                stop_loss_price = max(support_price, current_price * 0.95)
        elif sell_score > buy_score and sell_signals:
            signal_type = 'sell'
            active = sell_signals
            signal_score = sell_score
            target_price = support_price
            stop_loss_price = resistance_price
        else:
            signal_type = 'hold'
            active = []
            signal_score = 0.0
            target_price = None
            stop_loss_price = None

        # signal_score → signal_strength マッピング: <1.0→1, <2.5→2, >=2.5→3
        if signal_score >= 2.5:
            signal_strength = 3
        elif signal_score >= 1.0:
            signal_strength = 2
        elif signal_score > 0:
            signal_strength = 1
        else:
            signal_strength = 0

        return {
            'signal_type': signal_type,
            'signal_strength': signal_strength,
            'active_signals': active,
            'target_price': round(target_price, 1) if target_price else None,
            'stop_loss_price': round(stop_loss_price, 1) if stop_loss_price else None,
            'support_price': round(support_price, 1),
            'resistance_price': round(resistance_price, 1),
            'signal_score': round(signal_score, 2),
        }

    def determine_signal(self, df: pd.DataFrame, settings: dict) -> Literal['buy', 'sell', 'hold']:
        """シグナルを判定（後方互換ラッパー）"""
        details = self.calculate_signal_details(df, settings)
        return details['signal_type']

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
        details = self.calculate_signal_details(df, settings)
        self.db.query(Signal).filter(Signal.code == code, Signal.date == today).delete()

        def _safe_float(val):
            """NaN/None安全なfloat変換"""
            if val is None:
                return None
            try:
                f = float(val)
                return None if pd.isna(f) else f
            except (ValueError, TypeError):
                return None

        signal = Signal(
            code=code,
            date=today,
            signal_type=details['signal_type'],
            rsi=_safe_float(latest.get('rsi')),
            macd=_safe_float(latest.get('macd')),
            macd_signal=_safe_float(latest.get('macd_signal')),
            macd_histogram=_safe_float(latest.get('macd_histogram')),
            sma5=_safe_float(latest.get('sma5')),
            sma25=_safe_float(latest.get('sma25')),
            sma75=_safe_float(latest.get('sma75')),
            signal_strength=details['signal_strength'],
            active_signals=','.join(details['active_signals']) if details['active_signals'] else None,
            target_price=details['target_price'],
            stop_loss_price=details['stop_loss_price'],
            support_price=details['support_price'],
            resistance_price=details['resistance_price'],
            bb_upper=_safe_float(latest.get('bb_upper')),
            bb_lower=_safe_float(latest.get('bb_lower')),
            bb_middle=_safe_float(latest.get('bb_middle')),
            atr=_safe_float(latest.get('atr')),
            volume_ratio=_safe_float(latest.get('volume_ratio')),
            signal_score=details.get('signal_score'),
            stoch_k=_safe_float(latest.get('stoch_k')),
            stoch_d=_safe_float(latest.get('stoch_d')),
            williams_r=_safe_float(latest.get('williams_r')),
            adx=_safe_float(latest.get('adx')),
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

                active_signals_list = (
                    latest_signal.active_signals.split(',') if latest_signal and latest_signal.active_signals else []
                )
                result.append({
                    'id': stock.id,
                    'code': stock.code,
                    'name': stock.name,
                    'currentPrice': current,
                    'previousClose': prev_close,
                    'changePercent': round(change, 2),
                    'signal': latest_signal.signal_type if latest_signal else 'hold',
                    'rsi': round(latest_signal.rsi, 1) if latest_signal and latest_signal.rsi else 50.0,
                    'signalStrength': latest_signal.signal_strength if latest_signal and latest_signal.signal_strength else 0,
                    'activeSignals': active_signals_list,
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

        active_signals_list = (
            latest_signal.active_signals.split(',') if latest_signal and latest_signal.active_signals else []
        )
        return {
            'id': stock.id,
            'code': stock.code,
            'name': stock.name,
            'currentPrice': current,
            'previousClose': prev_close,
            'changePercent': round(change, 2),
            'signal': latest_signal.signal_type if latest_signal else 'hold',
            'rsi': round(latest_signal.rsi, 1) if latest_signal and latest_signal.rsi else 50.0,
            'signalStrength': latest_signal.signal_strength if latest_signal and latest_signal.signal_strength else 0,
            'activeSignals': active_signals_list,
            'macd': round(latest_signal.macd, 2) if latest_signal and latest_signal.macd else 0.0,
            'macdSignal': round(latest_signal.macd_signal, 2) if latest_signal and latest_signal.macd_signal else 0.0,
            'macdHistogram': round(latest_signal.macd_histogram, 2) if latest_signal and latest_signal.macd_histogram else 0.0,
            'sma5': round(latest_signal.sma5, 0) if latest_signal and latest_signal.sma5 else 0,
            'sma25': round(latest_signal.sma25, 0) if latest_signal and latest_signal.sma25 else 0,
            'sma75': round(latest_signal.sma75, 0) if latest_signal and latest_signal.sma75 else 0,
            'targetPrice': latest_signal.target_price if latest_signal else None,
            'stopLossPrice': latest_signal.stop_loss_price if latest_signal else None,
            'supportPrice': latest_signal.support_price if latest_signal else None,
            'resistancePrice': latest_signal.resistance_price if latest_signal else None,
            'bbUpper': round(latest_signal.bb_upper, 1) if latest_signal and latest_signal.bb_upper else None,
            'bbLower': round(latest_signal.bb_lower, 1) if latest_signal and latest_signal.bb_lower else None,
            'bbMiddle': round(latest_signal.bb_middle, 1) if latest_signal and latest_signal.bb_middle else None,
            'atr': round(latest_signal.atr, 1) if latest_signal and latest_signal.atr else None,
            'volumeRatio': round(latest_signal.volume_ratio, 2) if latest_signal and latest_signal.volume_ratio else None,
            'signalScore': round(latest_signal.signal_score, 2) if latest_signal and latest_signal.signal_score else None,
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

        # ボリンジャーバンド (20日, 2σ)
        if len(df) >= 20:
            bbands = ta.bbands(df['close'], length=20, std=2)
            if bbands is not None:
                df['bb_lower'] = bbands.iloc[:, 0]
                df['bb_upper'] = bbands.iloc[:, 2]

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
                'bbUpper': round(row['bb_upper'], 0) if pd.notna(row.get('bb_upper')) else None,
                'bbLower': round(row['bb_lower'], 0) if pd.notna(row.get('bb_lower')) else None,
            })
        return result

    def get_recommendations(self) -> dict:
        """おすすめ銘柄を取得"""
        settings = self.get_settings()
        budget = settings['investmentBudget']
        stocks = self.get_all_stocks()

        buy_recs = []
        sell_recs = []

        for s in stocks:
            if s['signal'] == 'buy' and s['currentPrice'] > 0:
                latest_signal = self.db.query(Signal).filter(
                    Signal.code == s['code']
                ).order_by(Signal.date.desc()).first()

                target = latest_signal.target_price if latest_signal else None
                stop_loss = latest_signal.stop_loss_price if latest_signal else None
                current = s['currentPrice']

                # 予算を最大3銘柄に均等配分
                max_stocks = 3
                buy_count = min(len([x for x in stocks if x['signal'] == 'buy']), max_stocks)
                budget_per_stock = budget / buy_count if buy_count > 0 else budget
                quantity = int(budget_per_stock / current) if current > 0 else 0
                amount = round(quantity * current)

                expected_profit = round((target - current) * quantity, 1) if target and quantity > 0 else None
                expected_profit_pct = round((target - current) / current * 100, 1) if target and current > 0 else None
                risk_amount = round((current - stop_loss) * quantity, 1) if stop_loss and quantity > 0 else None

                buy_recs.append({
                    'code': s['code'],
                    'name': s['name'],
                    'currentPrice': current,
                    'signal': 'buy',
                    'signalStrength': s['signalStrength'],
                    'activeSignals': s['activeSignals'],
                    'targetPrice': target,
                    'stopLossPrice': stop_loss,
                    'suggestedQuantity': quantity,
                    'suggestedAmount': amount,
                    'expectedProfit': expected_profit,
                    'expectedProfitPercent': expected_profit_pct,
                    'riskAmount': risk_amount,
                    'rsi': s['rsi'],
                })

            elif s['signal'] == 'sell':
                latest_signal = self.db.query(Signal).filter(
                    Signal.code == s['code']
                ).order_by(Signal.date.desc()).first()

                sell_recs.append({
                    'code': s['code'],
                    'name': s['name'],
                    'currentPrice': s['currentPrice'],
                    'signal': 'sell',
                    'signalStrength': s['signalStrength'],
                    'activeSignals': s['activeSignals'],
                    'targetPrice': latest_signal.target_price if latest_signal else None,
                    'stopLossPrice': latest_signal.stop_loss_price if latest_signal else None,
                    'suggestedQuantity': None,
                    'suggestedAmount': None,
                    'expectedProfit': None,
                    'expectedProfitPercent': None,
                    'riskAmount': None,
                    'rsi': s['rsi'],
                })

        # シグナル強度降順でソート
        buy_recs.sort(key=lambda x: x['signalStrength'], reverse=True)
        sell_recs.sort(key=lambda x: x['signalStrength'], reverse=True)

        return {
            'buyRecommendations': buy_recs[:3],
            'sellRecommendations': sell_recs,
            'investmentBudget': budget,
        }

    def update_all_stocks(self):
        """全銘柄のデータを更新"""
        stocks = self.db.query(Stock).all()
        for stock in stocks:
            try:
                self.update_stock_data(stock.code)
            except Exception as e:
                print(f"Failed to update {stock.code}: {e}")
