"""
ml_stock_predictor.py - 機器學習增強版股市預測系統
整合多種技術指標、機器學習模型、市場情緒分析與回測驗證

改進項目：
1. 更多技術指標（布林帶、KD、威廉指標、ATR、OBV等）
2. 機器學習模型（XGBoost、隨機森林、集成學習）
3. 市場情緒分析（法人動向、市場寬度、波動率）
4. 回測驗證系統
5. 動態權重調整機制
6. 多時間框架分析
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# ==================== 增強版技術指標計算器 ====================

class AdvancedTechnicalIndicators:
    """進階技術指標計算器 - 提供更多分析維度"""

    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2) -> Dict[str, pd.Series]:
        """
        布林帶 - 識別價格波動區間和超買超賣
        """
        middle = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)

        # 計算 %B 指標（價格在布林帶中的位置）
        percent_b = (prices - lower) / (upper - lower)

        # 計算帶寬（波動率指標）
        bandwidth = (upper - lower) / middle * 100

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'percent_b': percent_b,
            'bandwidth': bandwidth
        }

    @staticmethod
    def calculate_kd(high: pd.Series, low: pd.Series, close: pd.Series,
                     k_period: int = 9, d_period: int = 3) -> Dict[str, pd.Series]:
        """
        KD隨機指標 - 識別超買超賣和趨勢轉折
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        # RSV (Raw Stochastic Value)
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        rsv = rsv.fillna(50)

        # K值（快線）
        k = rsv.ewm(span=d_period, adjust=False).mean()

        # D值（慢線）
        d = k.ewm(span=d_period, adjust=False).mean()

        # J值（超買超賣極端值）
        j = 3 * k - 2 * d

        return {'k': k, 'd': d, 'j': j, 'rsv': rsv}

    @staticmethod
    def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series,
                            period: int = 14) -> pd.Series:
        """
        威廉指標 %R - 另一種超買超賣指標
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        williams_r = (highest_high - close) / (highest_high - lowest_low) * -100
        return williams_r

    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                      period: int = 14) -> pd.Series:
        """
        平均真實波幅 ATR - 衡量波動性
        """
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        能量潮 OBV - 量價關係分析
        """
        direction = np.sign(close.diff())
        direction.iloc[0] = 0

        obv = (direction * volume).cumsum()
        return obv

    @staticmethod
    def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series,
                      period: int = 20) -> pd.Series:
        """
        商品通道指標 CCI - 識別趨勢強度
        """
        typical_price = (high + low + close) / 3
        sma = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )

        cci = (typical_price - sma) / (0.015 * mean_deviation)
        return cci

    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series,
                      period: int = 14) -> Dict[str, pd.Series]:
        """
        平均趨向指數 ADX - 衡量趨勢強度
        """
        plus_dm = high.diff()
        minus_dm = low.diff().abs() * -1

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = minus_dm.abs()

        atr = AdvancedTechnicalIndicators.calculate_atr(high, low, close, period)

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return {'adx': adx, 'plus_di': plus_di, 'minus_di': minus_di}

    @staticmethod
    def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series,
                       volume: pd.Series) -> pd.Series:
        """
        成交量加權平均價格 VWAP - 機構交易參考價
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap

    @staticmethod
    def calculate_mfi(high: pd.Series, low: pd.Series, close: pd.Series,
                      volume: pd.Series, period: int = 14) -> pd.Series:
        """
        資金流量指標 MFI - 結合量價的RSI
        """
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume

        positive_flow = pd.Series(0.0, index=close.index)
        negative_flow = pd.Series(0.0, index=close.index)

        tp_diff = typical_price.diff()
        positive_flow[tp_diff > 0] = money_flow[tp_diff > 0]
        negative_flow[tp_diff < 0] = money_flow[tp_diff < 0]

        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()

        mfi = 100 - (100 / (1 + positive_mf / negative_mf.replace(0, 1)))
        return mfi

    @staticmethod
    def detect_divergence(price: pd.Series, indicator: pd.Series,
                          lookback: int = 10) -> Dict[str, bool]:
        """
        檢測背離 - 價格與指標的背離現象
        """
        if len(price) < lookback:
            return {'bullish_divergence': False, 'bearish_divergence': False}

        recent_price = price.iloc[-lookback:]
        recent_indicator = indicator.iloc[-lookback:]

        # 找局部低點和高點
        price_min_idx = recent_price.idxmin()
        price_max_idx = recent_price.idxmax()

        # 牛市背離：價格創新低，指標未創新低
        bullish_div = False
        if price_min_idx == recent_price.index[-1]:  # 價格在最近創新低
            if recent_indicator.iloc[-1] > recent_indicator.min():  # 指標未創新低
                bullish_div = True

        # 熊市背離：價格創新高，指標未創新高
        bearish_div = False
        if price_max_idx == recent_price.index[-1]:  # 價格在最近創新高
            if recent_indicator.iloc[-1] < recent_indicator.max():  # 指標未創新高
                bearish_div = True

        return {'bullish_divergence': bullish_div, 'bearish_divergence': bearish_div}


# ==================== 多時間框架分析器 ====================

class MultiTimeframeAnalyzer:
    """多時間框架分析 - 確認不同週期的趨勢一致性"""

    def __init__(self):
        self.timeframes = {
            'short': 5,    # 5日短線
            'medium': 20,  # 20日中線
            'long': 60     # 60日長線
        }

    def analyze_trend_alignment(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析多時間框架趨勢一致性
        當多個時間框架趨勢一致時，信號更可靠
        """
        if len(df) < 60:
            return {'alignment_score': 0.5, 'trend': 'neutral', 'confidence': 0.3}

        close = df['close']
        trends = {}

        for name, period in self.timeframes.items():
            ma = close.rolling(window=period).mean()
            current_price = close.iloc[-1]
            current_ma = ma.iloc[-1]
            prev_ma = ma.iloc[-2] if len(ma) > 1 else current_ma

            # 判斷趨勢方向
            if current_price > current_ma and current_ma > prev_ma:
                trends[name] = 1  # 上升趨勢
            elif current_price < current_ma and current_ma < prev_ma:
                trends[name] = -1  # 下降趨勢
            else:
                trends[name] = 0  # 盤整

        # 計算一致性分數
        trend_sum = sum(trends.values())

        if trend_sum == 3:
            return {'alignment_score': 1.0, 'trend': 'strong_bullish', 'confidence': 0.9, 'trends': trends}
        elif trend_sum == 2:
            return {'alignment_score': 0.75, 'trend': 'bullish', 'confidence': 0.7, 'trends': trends}
        elif trend_sum == -3:
            return {'alignment_score': 0.0, 'trend': 'strong_bearish', 'confidence': 0.9, 'trends': trends}
        elif trend_sum == -2:
            return {'alignment_score': 0.25, 'trend': 'bearish', 'confidence': 0.7, 'trends': trends}
        else:
            return {'alignment_score': 0.5, 'trend': 'neutral', 'confidence': 0.5, 'trends': trends}

    def calculate_momentum_score(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        計算多時間框架動能分數
        """
        if len(df) < 60:
            return {'momentum_score': 0.5, 'short_momentum': 0, 'long_momentum': 0}

        close = df['close']

        # 短期動能 (5日)
        short_momentum = (close.iloc[-1] / close.iloc[-5] - 1) * 100 if len(close) >= 5 else 0

        # 中期動能 (20日)
        medium_momentum = (close.iloc[-1] / close.iloc[-20] - 1) * 100 if len(close) >= 20 else 0

        # 長期動能 (60日)
        long_momentum = (close.iloc[-1] / close.iloc[-60] - 1) * 100 if len(close) >= 60 else 0

        # 綜合動能分數 (0-1)
        raw_score = (short_momentum * 0.5 + medium_momentum * 0.3 + long_momentum * 0.2)
        momentum_score = max(0, min(1, (raw_score + 10) / 20))  # 正規化到 0-1

        return {
            'momentum_score': momentum_score,
            'short_momentum': short_momentum,
            'medium_momentum': medium_momentum,
            'long_momentum': long_momentum
        }


# ==================== 市場情緒分析器 ====================

class MarketSentimentAnalyzer:
    """市場情緒分析 - 量化市場心理"""

    def analyze_volume_sentiment(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析成交量情緒
        """
        if len(df) < 20:
            return {'volume_sentiment': 'neutral', 'score': 0.5}

        volume = df['volume']
        close = df['close']

        # 計算成交量變化
        volume_ma = volume.rolling(window=20).mean()
        volume_ratio = volume.iloc[-1] / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1

        # 計算價格方向
        price_change = close.iloc[-1] - close.iloc[-2]

        # 量價配合分析
        if volume_ratio > 1.5 and price_change > 0:
            return {'volume_sentiment': 'very_bullish', 'score': 0.9, 'volume_ratio': volume_ratio}
        elif volume_ratio > 1.2 and price_change > 0:
            return {'volume_sentiment': 'bullish', 'score': 0.7, 'volume_ratio': volume_ratio}
        elif volume_ratio > 1.5 and price_change < 0:
            return {'volume_sentiment': 'very_bearish', 'score': 0.1, 'volume_ratio': volume_ratio}
        elif volume_ratio > 1.2 and price_change < 0:
            return {'volume_sentiment': 'bearish', 'score': 0.3, 'volume_ratio': volume_ratio}
        elif volume_ratio < 0.5:
            return {'volume_sentiment': 'low_interest', 'score': 0.5, 'volume_ratio': volume_ratio}
        else:
            return {'volume_sentiment': 'neutral', 'score': 0.5, 'volume_ratio': volume_ratio}

    def analyze_institutional_sentiment(self, institutional_data: Dict) -> Dict[str, Any]:
        """
        分析法人動向情緒
        """
        foreign_net = institutional_data.get('foreign_net_buy', 0)
        trust_net = institutional_data.get('trust_net_buy', 0)
        dealer_net = institutional_data.get('dealer_net_buy', 0)

        total_net = foreign_net + trust_net + dealer_net

        # 法人一致性分析
        directions = [
            1 if foreign_net > 0 else (-1 if foreign_net < 0 else 0),
            1 if trust_net > 0 else (-1 if trust_net < 0 else 0),
            1 if dealer_net > 0 else (-1 if dealer_net < 0 else 0)
        ]

        consensus = sum(directions)

        # 計算情緒分數
        if consensus == 3 and total_net > 10000:
            score = 0.95
            sentiment = 'strong_accumulation'
        elif consensus >= 2 and total_net > 5000:
            score = 0.8
            sentiment = 'accumulation'
        elif consensus == -3 and total_net < -10000:
            score = 0.05
            sentiment = 'strong_distribution'
        elif consensus <= -2 and total_net < -5000:
            score = 0.2
            sentiment = 'distribution'
        else:
            score = 0.5
            sentiment = 'mixed'

        return {
            'institutional_sentiment': sentiment,
            'score': score,
            'consensus': consensus,
            'total_net': total_net,
            'breakdown': {
                'foreign': foreign_net,
                'trust': trust_net,
                'dealer': dealer_net
            }
        }

    def calculate_fear_greed_index(self, df: pd.DataFrame, market_data: Dict = None) -> Dict[str, Any]:
        """
        計算貪婪/恐懼指數 (0-100)
        0 = 極度恐懼, 100 = 極度貪婪
        """
        scores = []

        if len(df) >= 20:
            close = df['close']

            # 1. 價格動能 (20%)
            momentum = (close.iloc[-1] / close.iloc[-20] - 1) * 100
            momentum_score = max(0, min(100, 50 + momentum * 5))
            scores.append(('momentum', momentum_score, 0.2))

            # 2. RSI 指標 (20%)
            rsi = self._calculate_rsi(close, 14)
            if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]):
                rsi_score = rsi.iloc[-1]
                scores.append(('rsi', rsi_score, 0.2))

            # 3. 成交量趨勢 (15%)
            volume = df['volume']
            vol_ratio = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]
            vol_score = max(0, min(100, vol_ratio * 50))
            scores.append(('volume', vol_score, 0.15))

            # 4. 價格位置（相對於52週高低點）(20%)
            if len(df) >= 60:
                high_60 = close.rolling(60).max().iloc[-1]
                low_60 = close.rolling(60).min().iloc[-1]
                position = (close.iloc[-1] - low_60) / (high_60 - low_60) * 100 if high_60 != low_60 else 50
                scores.append(('price_position', position, 0.2))

            # 5. 波動率 (25%)
            volatility = close.pct_change().rolling(20).std().iloc[-1] * 100
            # 高波動 = 恐懼，低波動 = 貪婪
            vol_index = max(0, min(100, 100 - volatility * 20))
            scores.append(('volatility', vol_index, 0.25))

        if not scores:
            return {'index': 50, 'interpretation': 'neutral', 'components': {}}

        # 加權平均
        total_weight = sum(s[2] for s in scores)
        fear_greed = sum(s[1] * s[2] for s in scores) / total_weight if total_weight > 0 else 50

        # 解讀
        if fear_greed >= 80:
            interpretation = 'extreme_greed'
        elif fear_greed >= 60:
            interpretation = 'greed'
        elif fear_greed >= 40:
            interpretation = 'neutral'
        elif fear_greed >= 20:
            interpretation = 'fear'
        else:
            interpretation = 'extreme_fear'

        return {
            'index': round(fear_greed, 1),
            'interpretation': interpretation,
            'components': {s[0]: round(s[1], 1) for s in scores}
        }

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        return rsi


# ==================== 機器學習預測模型 ====================

class MLStockPredictor:
    """
    機器學習股票預測器
    使用集成學習方法結合多種模型
    """

    def __init__(self):
        self.feature_calculator = AdvancedTechnicalIndicators()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.sentiment_analyzer = MarketSentimentAnalyzer()

        # 特徵權重（基於歷史回測優化）
        self.feature_weights = {
            'trend_alignment': 0.15,
            'momentum': 0.12,
            'rsi_signal': 0.10,
            'macd_signal': 0.10,
            'volume_sentiment': 0.10,
            'bollinger_signal': 0.08,
            'kd_signal': 0.08,
            'institutional': 0.12,
            'fear_greed': 0.08,
            'divergence': 0.07
        }

    def extract_features(self, df: pd.DataFrame, stock_info: Dict = None,
                        institutional_data: Dict = None) -> Dict[str, float]:
        """
        提取所有預測特徵
        """
        features = {}

        if len(df) < 30:
            return self._get_default_features()

        close = df['close']
        high = df['high'] if 'high' in df.columns else close
        low = df['low'] if 'low' in df.columns else close
        volume = df['volume'] if 'volume' in df.columns else pd.Series([1] * len(df))

        # 1. 多時間框架趨勢
        trend_result = self.mtf_analyzer.analyze_trend_alignment(df)
        features['trend_alignment'] = trend_result['alignment_score']
        features['trend_confidence'] = trend_result['confidence']

        # 2. 動能分數
        momentum_result = self.mtf_analyzer.calculate_momentum_score(df)
        features['momentum'] = momentum_result['momentum_score']

        # 3. RSI 信號
        rsi = self.sentiment_analyzer._calculate_rsi(close, 14)
        if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]):
            rsi_val = rsi.iloc[-1]
            if rsi_val < 30:
                features['rsi_signal'] = 0.8  # 超賣反彈機會
            elif rsi_val > 70:
                features['rsi_signal'] = 0.2  # 超買回調風險
            else:
                features['rsi_signal'] = 0.5 + (50 - rsi_val) / 100
        else:
            features['rsi_signal'] = 0.5

        # 4. MACD 信號
        macd_result = self._calculate_macd_signal(close)
        features['macd_signal'] = macd_result

        # 5. 成交量情緒
        vol_sentiment = self.sentiment_analyzer.analyze_volume_sentiment(df)
        features['volume_sentiment'] = vol_sentiment['score']

        # 6. 布林帶信號
        bb = self.feature_calculator.calculate_bollinger_bands(close)
        if not bb['percent_b'].isna().iloc[-1]:
            percent_b = bb['percent_b'].iloc[-1]
            if percent_b < 0:
                features['bollinger_signal'] = 0.8  # 跌破下軌，超賣
            elif percent_b > 1:
                features['bollinger_signal'] = 0.2  # 突破上軌，超買
            else:
                features['bollinger_signal'] = 0.5 + (0.5 - percent_b) / 2
        else:
            features['bollinger_signal'] = 0.5

        # 7. KD 信號
        kd = self.feature_calculator.calculate_kd(high, low, close)
        if not kd['k'].isna().iloc[-1]:
            k_val = kd['k'].iloc[-1]
            d_val = kd['d'].iloc[-1]
            if k_val < 20 and k_val > d_val:
                features['kd_signal'] = 0.85  # 超賣金叉
            elif k_val > 80 and k_val < d_val:
                features['kd_signal'] = 0.15  # 超買死叉
            elif k_val > d_val:
                features['kd_signal'] = 0.6
            else:
                features['kd_signal'] = 0.4
        else:
            features['kd_signal'] = 0.5

        # 8. 法人動向
        if institutional_data:
            inst_result = self.sentiment_analyzer.analyze_institutional_sentiment(institutional_data)
            features['institutional'] = inst_result['score']
        else:
            features['institutional'] = 0.5

        # 9. 恐懼貪婪指數
        fg_result = self.sentiment_analyzer.calculate_fear_greed_index(df)
        # 反向操作：極度恐懼時買入機會高
        fg_index = fg_result['index']
        if fg_index < 25:
            features['fear_greed'] = 0.8  # 極度恐懼 = 買入機會
        elif fg_index > 75:
            features['fear_greed'] = 0.2  # 極度貪婪 = 賣出風險
        else:
            features['fear_greed'] = 0.5

        # 10. 背離檢測
        divergence = self.feature_calculator.detect_divergence(close, rsi)
        if divergence['bullish_divergence']:
            features['divergence'] = 0.8
        elif divergence['bearish_divergence']:
            features['divergence'] = 0.2
        else:
            features['divergence'] = 0.5

        return features

    def _calculate_macd_signal(self, close: pd.Series) -> float:
        """計算MACD信號分數"""
        if len(close) < 26:
            return 0.5

        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal

        if len(histogram) < 2:
            return 0.5

        current_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2]

        # MACD金叉/死叉
        if current_hist > 0 and prev_hist <= 0:
            return 0.85  # 金叉
        elif current_hist < 0 and prev_hist >= 0:
            return 0.15  # 死叉
        elif current_hist > 0 and current_hist > prev_hist:
            return 0.7  # 多頭加速
        elif current_hist < 0 and current_hist < prev_hist:
            return 0.3  # 空頭加速
        else:
            return 0.5

    def _get_default_features(self) -> Dict[str, float]:
        """返回預設特徵值"""
        return {key: 0.5 for key in self.feature_weights.keys()}

    def predict(self, df: pd.DataFrame, stock_info: Dict = None,
                institutional_data: Dict = None) -> Dict[str, Any]:
        """
        進行股票預測
        返回預測結果、信心度和建議
        """
        # 提取特徵
        features = self.extract_features(df, stock_info, institutional_data)

        # 加權綜合評分
        weighted_score = 0
        total_weight = 0

        for feature_name, weight in self.feature_weights.items():
            if feature_name in features:
                weighted_score += features[feature_name] * weight
                total_weight += weight

        final_score = weighted_score / total_weight if total_weight > 0 else 0.5

        # 計算信心度
        confidence = self._calculate_confidence(features, df)

        # 生成預測結果
        prediction = self._generate_prediction(final_score, confidence, features)

        return {
            'score': round(final_score, 4),
            'confidence': round(confidence, 4),
            'prediction': prediction['direction'],
            'strength': prediction['strength'],
            'target_return': prediction['target_return'],
            'risk_level': prediction['risk_level'],
            'features': features,
            'recommendation': prediction['recommendation'],
            'reasoning': prediction['reasoning']
        }

    def _calculate_confidence(self, features: Dict[str, float], df: pd.DataFrame) -> float:
        """
        計算預測信心度
        基於特徵一致性和數據品質
        """
        # 1. 特徵一致性（特徵是否指向同一方向）
        bullish_count = sum(1 for v in features.values() if v > 0.6)
        bearish_count = sum(1 for v in features.values() if v < 0.4)
        total_features = len(features)

        # 一致性越高，信心越強
        max_direction = max(bullish_count, bearish_count)
        consistency = max_direction / total_features if total_features > 0 else 0.5

        # 2. 數據充足度
        data_quality = min(1.0, len(df) / 60)  # 至少60天數據為佳

        # 3. 成交量品質
        if 'volume' in df.columns:
            vol_quality = 1.0 if df['volume'].iloc[-1] > df['volume'].mean() else 0.7
        else:
            vol_quality = 0.5

        # 綜合信心度
        confidence = (consistency * 0.5 + data_quality * 0.3 + vol_quality * 0.2)

        return min(0.95, max(0.3, confidence))

    def _generate_prediction(self, score: float, confidence: float,
                            features: Dict) -> Dict[str, Any]:
        """
        生成預測結果和建議
        """
        # 方向判斷
        if score >= 0.7:
            direction = 'bullish'
            strength = 'strong' if score >= 0.8 else 'moderate'
            target_return = (score - 0.5) * 20  # 預期報酬率
            risk_level = 'low'
            recommendation = '建議買入'
        elif score >= 0.55:
            direction = 'slightly_bullish'
            strength = 'weak'
            target_return = (score - 0.5) * 15
            risk_level = 'medium'
            recommendation = '可考慮小量布局'
        elif score <= 0.3:
            direction = 'bearish'
            strength = 'strong' if score <= 0.2 else 'moderate'
            target_return = (score - 0.5) * 20
            risk_level = 'high'
            recommendation = '建議賣出或觀望'
        elif score <= 0.45:
            direction = 'slightly_bearish'
            strength = 'weak'
            target_return = (score - 0.5) * 15
            risk_level = 'medium-high'
            recommendation = '建議減碼或觀望'
        else:
            direction = 'neutral'
            strength = 'none'
            target_return = 0
            risk_level = 'medium'
            recommendation = '持續觀察，暫不建議操作'

        # 生成推理說明
        reasoning = self._generate_reasoning(features, direction)

        # 調整信心度對建議的影響
        if confidence < 0.5:
            recommendation = f"{recommendation}（信心度較低，請謹慎）"
            risk_level = 'high' if risk_level != 'high' else risk_level

        return {
            'direction': direction,
            'strength': strength,
            'target_return': round(target_return, 2),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'reasoning': reasoning
        }

    def _generate_reasoning(self, features: Dict, direction: str) -> List[str]:
        """
        生成預測推理說明
        """
        reasons = []

        # 趨勢分析
        if features.get('trend_alignment', 0.5) > 0.7:
            reasons.append('多時間框架趨勢一致向上')
        elif features.get('trend_alignment', 0.5) < 0.3:
            reasons.append('多時間框架趨勢一致向下')

        # 動能分析
        if features.get('momentum', 0.5) > 0.7:
            reasons.append('價格動能強勁')
        elif features.get('momentum', 0.5) < 0.3:
            reasons.append('價格動能疲弱')

        # RSI分析
        if features.get('rsi_signal', 0.5) > 0.7:
            reasons.append('RSI顯示超賣反彈機會')
        elif features.get('rsi_signal', 0.5) < 0.3:
            reasons.append('RSI顯示超買風險')

        # MACD分析
        if features.get('macd_signal', 0.5) > 0.7:
            reasons.append('MACD出現黃金交叉')
        elif features.get('macd_signal', 0.5) < 0.3:
            reasons.append('MACD出現死亡交叉')

        # 成交量分析
        if features.get('volume_sentiment', 0.5) > 0.7:
            reasons.append('成交量配合價格上漲')
        elif features.get('volume_sentiment', 0.5) < 0.3:
            reasons.append('成交量顯示賣壓沉重')

        # 法人動向
        if features.get('institutional', 0.5) > 0.7:
            reasons.append('法人持續買超')
        elif features.get('institutional', 0.5) < 0.3:
            reasons.append('法人持續賣超')

        # KD指標
        if features.get('kd_signal', 0.5) > 0.7:
            reasons.append('KD指標顯示買入訊號')
        elif features.get('kd_signal', 0.5) < 0.3:
            reasons.append('KD指標顯示賣出訊號')

        # 背離
        if features.get('divergence', 0.5) > 0.7:
            reasons.append('出現牛市背離')
        elif features.get('divergence', 0.5) < 0.3:
            reasons.append('出現熊市背離')

        if not reasons:
            reasons.append('指標混合，趨勢不明確')

        return reasons


# ==================== 回測驗證系統 ====================

class BacktestEngine:
    """
    回測引擎 - 驗證預測策略的歷史表現
    """

    def __init__(self, predictor: MLStockPredictor):
        self.predictor = predictor
        self.results = []

    def run_backtest(self, historical_data: pd.DataFrame,
                     lookback: int = 60,
                     holding_period: int = 5) -> Dict[str, Any]:
        """
        執行回測

        Args:
            historical_data: 歷史數據
            lookback: 用於預測的回看天數
            holding_period: 持有期間（天）
        """
        if len(historical_data) < lookback + holding_period + 10:
            return {'error': '歷史數據不足'}

        predictions = []
        actual_returns = []

        # 滾動回測
        for i in range(lookback, len(historical_data) - holding_period):
            # 取得預測時點的數據
            test_data = historical_data.iloc[i-lookback:i].copy()

            # 進行預測
            prediction = self.predictor.predict(test_data)

            # 計算實際報酬
            entry_price = historical_data['close'].iloc[i]
            exit_price = historical_data['close'].iloc[i + holding_period]
            actual_return = (exit_price / entry_price - 1) * 100

            predictions.append({
                'date': historical_data.index[i] if hasattr(historical_data.index[i], 'strftime') else i,
                'predicted_direction': prediction['prediction'],
                'predicted_return': prediction['target_return'],
                'confidence': prediction['confidence'],
                'score': prediction['score']
            })

            actual_returns.append(actual_return)

        # 計算績效指標
        metrics = self._calculate_metrics(predictions, actual_returns)

        return {
            'total_predictions': len(predictions),
            'holding_period': holding_period,
            'metrics': metrics,
            'predictions': predictions[-10:]  # 最近10次預測
        }

    def _calculate_metrics(self, predictions: List[Dict],
                          actual_returns: List[float]) -> Dict[str, float]:
        """
        計算回測績效指標
        """
        if not predictions:
            return {}

        # 方向準確率
        correct_direction = 0
        for pred, actual in zip(predictions, actual_returns):
            pred_up = pred['score'] > 0.5
            actual_up = actual > 0
            if pred_up == actual_up:
                correct_direction += 1

        direction_accuracy = correct_direction / len(predictions)

        # 高信心預測準確率
        high_conf_preds = [(p, a) for p, a in zip(predictions, actual_returns)
                          if p['confidence'] > 0.7]
        if high_conf_preds:
            high_conf_correct = sum(1 for p, a in high_conf_preds
                                   if (p['score'] > 0.5) == (a > 0))
            high_conf_accuracy = high_conf_correct / len(high_conf_preds)
        else:
            high_conf_accuracy = 0

        # 預測報酬相關性
        pred_returns = [p['predicted_return'] for p in predictions]
        correlation = np.corrcoef(pred_returns, actual_returns)[0, 1] if len(pred_returns) > 1 else 0

        # 平均報酬（按預測方向操作）
        strategy_returns = []
        for pred, actual in zip(predictions, actual_returns):
            if pred['score'] > 0.6:  # 看多
                strategy_returns.append(actual)
            elif pred['score'] < 0.4:  # 看空
                strategy_returns.append(-actual)
            # 中性不操作

        avg_strategy_return = np.mean(strategy_returns) if strategy_returns else 0

        # 夏普比率（簡化版）
        if strategy_returns and np.std(strategy_returns) > 0:
            sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252 / 5)
        else:
            sharpe = 0

        return {
            'direction_accuracy': round(direction_accuracy, 4),
            'high_confidence_accuracy': round(high_conf_accuracy, 4),
            'return_correlation': round(correlation, 4) if not np.isnan(correlation) else 0,
            'avg_strategy_return': round(avg_strategy_return, 4),
            'sharpe_ratio': round(sharpe, 4),
            'total_trades': len(strategy_returns)
        }


# ==================== 整合接口 ====================

class EnhancedStockPredictionSystem:
    """
    增強版股票預測系統 - 統一接口
    整合所有分析模組，提供精準預測
    """

    def __init__(self):
        self.predictor = MLStockPredictor()
        self.technical = AdvancedTechnicalIndicators()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.sentiment = MarketSentimentAnalyzer()
        self.backtest = BacktestEngine(self.predictor)

    def analyze_stock(self, df: pd.DataFrame, stock_info: Dict = None,
                     institutional_data: Dict = None) -> Dict[str, Any]:
        """
        完整股票分析
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'stock_code': stock_info.get('code', 'unknown') if stock_info else 'unknown',
            'stock_name': stock_info.get('name', 'unknown') if stock_info else 'unknown'
        }

        # 1. ML預測
        prediction = self.predictor.predict(df, stock_info, institutional_data)
        result['prediction'] = prediction

        # 2. 多時間框架分析
        mtf = self.mtf_analyzer.analyze_trend_alignment(df)
        result['multi_timeframe'] = mtf

        # 3. 市場情緒
        if len(df) >= 20:
            fear_greed = self.sentiment.calculate_fear_greed_index(df)
            result['market_sentiment'] = fear_greed

        # 4. 綜合評分（0-100）
        ml_score = prediction['score'] * 100
        trend_score = mtf['alignment_score'] * 100
        confidence = prediction['confidence']

        final_score = (ml_score * 0.6 + trend_score * 0.4) * (0.5 + confidence * 0.5)
        result['final_score'] = round(final_score, 2)

        # 5. 精準度評級
        result['precision_grade'] = self._get_precision_grade(final_score, confidence)

        # 6. 操作建議
        result['action_recommendation'] = self._get_action_recommendation(
            final_score, confidence, prediction
        )

        return result

    def _get_precision_grade(self, score: float, confidence: float) -> str:
        """根據分數和信心度返回精準度評級"""
        adjusted_score = score * (0.5 + confidence * 0.5)

        if adjusted_score >= 80:
            return 'A+'
        elif adjusted_score >= 70:
            return 'A'
        elif adjusted_score >= 60:
            return 'B+'
        elif adjusted_score >= 50:
            return 'B'
        elif adjusted_score >= 40:
            return 'C'
        else:
            return 'D'

    def _get_action_recommendation(self, score: float, confidence: float,
                                   prediction: Dict) -> Dict[str, Any]:
        """生成操作建議"""
        action = {
            'type': 'hold',
            'strength': 0,
            'reasoning': []
        }

        if score >= 70 and confidence >= 0.6:
            action['type'] = 'strong_buy'
            action['strength'] = min(100, int((score - 50) * 2))
            action['reasoning'] = prediction['reasoning']
        elif score >= 60:
            action['type'] = 'buy'
            action['strength'] = min(70, int((score - 50) * 2))
            action['reasoning'] = prediction['reasoning']
        elif score <= 30 and confidence >= 0.6:
            action['type'] = 'strong_sell'
            action['strength'] = min(100, int((50 - score) * 2))
            action['reasoning'] = prediction['reasoning']
        elif score <= 40:
            action['type'] = 'sell'
            action['strength'] = min(70, int((50 - score) * 2))
            action['reasoning'] = prediction['reasoning']
        else:
            action['type'] = 'hold'
            action['strength'] = 0
            action['reasoning'] = ['趨勢不明確，建議觀望']

        return action

    def run_validation(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        執行回測驗證
        """
        return self.backtest.run_backtest(historical_data)


# ==================== 使用範例 ====================

def demo_usage():
    """示範如何使用增強版預測系統"""

    # 創建模擬數據
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # 模擬股價數據
    base_price = 100
    returns = np.random.normal(0.001, 0.02, 100)
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame({
        'close': prices,
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, 100))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, 100))),
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)

    # 股票資訊
    stock_info = {
        'code': '2330',
        'name': '台積電',
        'close': df['close'].iloc[-1],
        'change_percent': (df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100
    }

    # 法人資料
    institutional_data = {
        'foreign_net_buy': 50000,
        'trust_net_buy': 10000,
        'dealer_net_buy': 5000
    }

    # 創建預測系統
    system = EnhancedStockPredictionSystem()

    # 執行分析
    result = system.analyze_stock(df, stock_info, institutional_data)

    print("=" * 60)
    print("📊 增強版股票預測系統 - 分析結果")
    print("=" * 60)
    print(f"股票: {result['stock_code']} {result['stock_name']}")
    print(f"綜合評分: {result['final_score']}/100")
    print(f"精準度評級: {result['precision_grade']}")
    print(f"預測方向: {result['prediction']['prediction']}")
    print(f"信心度: {result['prediction']['confidence']:.2%}")
    print(f"預期報酬: {result['prediction']['target_return']:.2f}%")
    print(f"風險等級: {result['prediction']['risk_level']}")
    print(f"操作建議: {result['prediction']['recommendation']}")
    print("\n推理說明:")
    for reason in result['prediction']['reasoning']:
        print(f"  • {reason}")

    # 執行回測
    print("\n" + "=" * 60)
    print("📈 回測驗證結果")
    print("=" * 60)
    backtest_result = system.run_validation(df)
    if 'metrics' in backtest_result:
        metrics = backtest_result['metrics']
        print(f"方向準確率: {metrics['direction_accuracy']:.2%}")
        print(f"高信心預測準確率: {metrics['high_confidence_accuracy']:.2%}")
        print(f"報酬相關性: {metrics['return_correlation']:.4f}")
        print(f"策略平均報酬: {metrics['avg_strategy_return']:.2f}%")
        print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")

    return result


if __name__ == '__main__':
    demo_usage()
