"""
ml_models.py - 機器學習預測模型
整合 XGBoost、LightGBM、隨機森林等模型

功能：
1. 特徵工程
2. 模型訓練與預測
3. 集成學習
4. 模型評估與選擇
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import os
import pickle
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# 嘗試導入 ML 庫（如果沒有安裝則使用簡化版本）
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn 未安裝，使用簡化版本")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.info("XGBoost 未安裝")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.info("LightGBM 未安裝")


# ==================== 特徵工程 ====================

class FeatureEngineer:
    """
    特徵工程器
    從原始數據提取預測特徵
    """

    def __init__(self):
        self.feature_names = []

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        創建所有特徵

        輸入: DataFrame with columns [date, open, high, low, close, volume]
        輸出: DataFrame with all features
        """
        if len(df) < 30:
            logger.warning("數據不足，無法創建完整特徵")
            return pd.DataFrame()

        features = pd.DataFrame(index=df.index)

        # 1. 價格特徵
        features = self._add_price_features(df, features)

        # 2. 技術指標特徵
        features = self._add_technical_features(df, features)

        # 3. 成交量特徵
        features = self._add_volume_features(df, features)

        # 4. 動能特徵
        features = self._add_momentum_features(df, features)

        # 5. 波動率特徵
        features = self._add_volatility_features(df, features)

        # 6. 週期特徵
        features = self._add_cyclical_features(df, features)

        # 移除空值
        features = features.dropna()

        self.feature_names = features.columns.tolist()

        return features

    def _add_price_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """價格相關特徵"""
        close = df['close']

        # 價格變化
        features['return_1d'] = close.pct_change(1)
        features['return_5d'] = close.pct_change(5)
        features['return_10d'] = close.pct_change(10)
        features['return_20d'] = close.pct_change(20)

        # 價格位置
        features['price_to_high_20d'] = close / close.rolling(20).max()
        features['price_to_low_20d'] = close / close.rolling(20).min()
        features['price_range_20d'] = (close.rolling(20).max() - close.rolling(20).min()) / close

        # 缺口
        features['gap'] = df['open'] / close.shift(1) - 1

        # 實體/影線
        body = abs(df['close'] - df['open'])
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        features['body_ratio'] = body / (df['high'] - df['low'] + 0.001)
        features['upper_shadow_ratio'] = upper_shadow / (df['high'] - df['low'] + 0.001)
        features['lower_shadow_ratio'] = lower_shadow / (df['high'] - df['low'] + 0.001)

        return features

    def _add_technical_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """技術指標特徵"""
        close = df['close']
        high = df['high']
        low = df['low']

        # 移動平均線
        for period in [5, 10, 20, 60]:
            ma = close.rolling(period).mean()
            features[f'ma_{period}_ratio'] = close / ma
            features[f'ma_{period}_slope'] = ma.pct_change(5)

        # MA 交叉
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        features['ma_cross'] = (ma5 - ma20) / close

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 0.001)
        features['rsi'] = 100 - (100 / (1 + rs))
        features['rsi_ma'] = features['rsi'].rolling(5).mean()

        # MACD
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        features['macd'] = macd / close
        features['macd_signal'] = signal / close
        features['macd_hist'] = (macd - signal) / close

        # 布林帶
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        features['bb_upper'] = (bb_mid + 2 * bb_std) / close
        features['bb_lower'] = (bb_mid - 2 * bb_std) / close
        features['bb_width'] = 4 * bb_std / bb_mid
        features['bb_position'] = (close - bb_mid) / (2 * bb_std + 0.001)

        # KD
        low_min = low.rolling(9).min()
        high_max = high.rolling(9).max()
        rsv = (close - low_min) / (high_max - low_min + 0.001) * 100
        features['k'] = rsv.ewm(span=3, adjust=False).mean()
        features['d'] = features['k'].ewm(span=3, adjust=False).mean()
        features['kd_cross'] = features['k'] - features['d']

        # 威廉指標
        features['williams_r'] = (high_max - close) / (high_max - low_min + 0.001) * -100

        # ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        features['atr'] = tr.rolling(14).mean() / close
        features['atr_ratio'] = tr / tr.rolling(14).mean()

        # CCI
        tp = (high + low + close) / 3
        tp_ma = tp.rolling(20).mean()
        tp_std = tp.rolling(20).std()
        features['cci'] = (tp - tp_ma) / (0.015 * tp_std + 0.001)

        return features

    def _add_volume_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """成交量特徵"""
        volume = df['volume']
        close = df['close']

        # 成交量變化
        features['volume_change'] = volume.pct_change()
        features['volume_ma5_ratio'] = volume / volume.rolling(5).mean()
        features['volume_ma20_ratio'] = volume / volume.rolling(20).mean()

        # 量價關係
        features['volume_price_trend'] = (volume * close.pct_change()).cumsum()
        features['volume_price_corr'] = close.pct_change().rolling(10).corr(volume.pct_change())

        # OBV
        obv_direction = np.sign(close.diff())
        features['obv'] = (obv_direction * volume).cumsum()
        features['obv_ma'] = features['obv'].rolling(10).mean()
        features['obv_slope'] = features['obv'].pct_change(5)

        # 成交量趨勢
        features['volume_trend'] = volume.rolling(5).mean() / volume.rolling(20).mean()

        return features

    def _add_momentum_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """動能特徵"""
        close = df['close']

        # ROC (Rate of Change)
        for period in [5, 10, 20]:
            features[f'roc_{period}'] = (close - close.shift(period)) / close.shift(period)

        # 動量
        features['momentum_5'] = close - close.shift(5)
        features['momentum_10'] = close - close.shift(10)

        # 加速度
        features['acceleration'] = features['return_1d'] - features['return_1d'].shift(1)

        # 趨勢強度
        up_moves = (close.diff() > 0).astype(int).rolling(20).sum()
        features['trend_strength'] = up_moves / 20

        return features

    def _add_volatility_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """波動率特徵"""
        close = df['close']

        # 歷史波動率
        features['volatility_5d'] = close.pct_change().rolling(5).std() * np.sqrt(252)
        features['volatility_20d'] = close.pct_change().rolling(20).std() * np.sqrt(252)

        # 波動率變化
        features['volatility_ratio'] = features['volatility_5d'] / (features['volatility_20d'] + 0.001)

        # Parkinson 波動率
        high = df['high']
        low = df['low']
        parkinson = np.sqrt((1 / (4 * np.log(2))) * (np.log(high / low) ** 2))
        features['parkinson_vol'] = parkinson.rolling(20).mean()

        return features

    def _add_cyclical_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """週期特徵"""
        if 'date' in df.columns:
            dates = pd.to_datetime(df['date'])
        else:
            dates = df.index

        # 星期幾
        features['day_of_week'] = dates.dayofweek / 4  # 正規化到 0-1

        # 月份
        features['month'] = dates.month / 12  # 正規化到 0-1

        # 月初/月末效應
        features['is_month_start'] = (dates.day <= 5).astype(int)
        features['is_month_end'] = (dates.day >= 25).astype(int)

        return features

    def create_target(self, df: pd.DataFrame, forward_days: int = 5,
                      threshold: float = 0.02) -> pd.Series:
        """
        創建預測目標

        Args:
            df: 價格數據
            forward_days: 向前看的天數
            threshold: 漲跌判斷閾值

        Returns:
            Series: 1=上漲, 0=持平, -1=下跌
        """
        future_return = df['close'].shift(-forward_days) / df['close'] - 1

        target = pd.Series(0, index=df.index)
        target[future_return > threshold] = 1
        target[future_return < -threshold] = -1

        return target


# ==================== ML 模型包裝器 ====================

class MLModelWrapper:
    """
    機器學習模型包裝器
    統一接口管理不同的 ML 模型
    """

    def __init__(self, model_type: str = 'auto'):
        """
        Args:
            model_type: 'xgboost', 'lightgbm', 'random_forest', 'gradient_boosting', 'auto'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.feature_names = []
        self.is_trained = False

        self._init_model()

    def _init_model(self):
        """初始化模型"""
        if self.model_type == 'auto':
            # 自動選擇最佳可用模型
            if XGBOOST_AVAILABLE:
                self.model_type = 'xgboost'
            elif LIGHTGBM_AVAILABLE:
                self.model_type = 'lightgbm'
            elif SKLEARN_AVAILABLE:
                self.model_type = 'gradient_boosting'
            else:
                self.model_type = 'simple'

        if self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss'
            )
            logger.info("使用 XGBoost 模型")

        elif self.model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbose=-1
            )
            logger.info("使用 LightGBM 模型")

        elif self.model_type == 'random_forest' and SKLEARN_AVAILABLE:
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            logger.info("使用 Random Forest 模型")

        elif self.model_type == 'gradient_boosting' and SKLEARN_AVAILABLE:
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            logger.info("使用 Gradient Boosting 模型")

        else:
            logger.warning("使用簡化預測模型")
            self.model = None

    def train(self, X: pd.DataFrame, y: pd.Series,
              test_size: float = 0.2) -> Dict[str, float]:
        """
        訓練模型

        Returns:
            Dict: 訓練指標
        """
        self.feature_names = X.columns.tolist()

        # 移除空值
        valid_idx = ~(X.isna().any(axis=1) | y.isna())
        X_clean = X[valid_idx]
        y_clean = y[valid_idx]

        if len(X_clean) < 50:
            logger.warning("訓練數據不足")
            return {'accuracy': 0, 'error': 'insufficient_data'}

        # 標準化
        if self.scaler:
            X_scaled = self.scaler.fit_transform(X_clean)
        else:
            X_scaled = X_clean.values

        # 分割數據
        if SKLEARN_AVAILABLE:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_clean, test_size=test_size, shuffle=False
            )
        else:
            split_idx = int(len(X_scaled) * (1 - test_size))
            X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_test = y_clean.iloc[:split_idx], y_clean.iloc[split_idx:]

        # 訓練
        if self.model:
            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_test)

            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
                'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
                'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0),
                'train_size': len(X_train),
                'test_size': len(X_test)
            }

            self.is_trained = True
            logger.info(f"模型訓練完成 - 準確率: {metrics['accuracy']:.4f}")

            return metrics
        else:
            return {'accuracy': 0, 'error': 'no_model'}

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """預測"""
        if not self.is_trained or self.model is None:
            # 返回預設預測
            return np.zeros(len(X))

        # 確保特徵順序一致
        X_aligned = X[self.feature_names] if all(f in X.columns for f in self.feature_names) else X

        # 標準化
        if self.scaler:
            X_scaled = self.scaler.transform(X_aligned)
        else:
            X_scaled = X_aligned.values

        return self.model.predict(X_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """預測機率"""
        if not self.is_trained or self.model is None:
            return np.full((len(X), 3), 1/3)

        X_aligned = X[self.feature_names] if all(f in X.columns for f in self.feature_names) else X

        if self.scaler:
            X_scaled = self.scaler.transform(X_aligned)
        else:
            X_scaled = X_aligned.values

        return self.model.predict_proba(X_scaled)

    def get_feature_importance(self) -> Dict[str, float]:
        """獲取特徵重要性"""
        if not self.is_trained or self.model is None:
            return {}

        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
            return dict(zip(self.feature_names, importance))

        return {}

    def save_model(self, filepath: str):
        """保存模型"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'is_trained': self.is_trained
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        logger.info(f"模型已保存: {filepath}")

    def load_model(self, filepath: str):
        """載入模型"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.model_type = model_data['model_type']
        self.is_trained = model_data['is_trained']
        logger.info(f"模型已載入: {filepath}")


# ==================== 集成預測器 ====================

class EnsemblePredictor:
    """
    集成預測器
    結合多個模型的預測結果
    """

    def __init__(self):
        self.models = {}
        self.feature_engineer = FeatureEngineer()
        self.model_weights = {}

    def add_model(self, name: str, model: MLModelWrapper, weight: float = 1.0):
        """添加模型"""
        self.models[name] = model
        self.model_weights[name] = weight

    def train_all(self, df: pd.DataFrame, forward_days: int = 5) -> Dict[str, Dict]:
        """訓練所有模型"""
        # 創建特徵
        features = self.feature_engineer.create_features(df)
        target = self.feature_engineer.create_target(df, forward_days)

        # 對齊數據
        common_idx = features.index.intersection(target.dropna().index)
        X = features.loc[common_idx]
        y = target.loc[common_idx]

        results = {}
        for name, model in self.models.items():
            logger.info(f"訓練模型: {name}")
            metrics = model.train(X, y)
            results[name] = metrics

            # 根據準確率調整權重
            if metrics.get('accuracy', 0) > 0:
                self.model_weights[name] = metrics['accuracy']

        return results

    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        集成預測

        Returns:
            {
                'prediction': int,  # -1, 0, 1
                'probability': Dict,  # 各類別機率
                'confidence': float,  # 信心度
                'individual_predictions': Dict  # 各模型預測
            }
        """
        features = self.feature_engineer.create_features(df)

        if len(features) == 0:
            return {'prediction': 0, 'probability': {}, 'confidence': 0}

        # 取最新一筆
        X = features.tail(1)

        predictions = {}
        probabilities = {}

        for name, model in self.models.items():
            pred = model.predict(X)
            proba = model.predict_proba(X)
            predictions[name] = int(pred[0])
            probabilities[name] = proba[0].tolist()

        # 加權投票
        if predictions:
            weighted_votes = {-1: 0, 0: 0, 1: 0}
            total_weight = sum(self.model_weights.values())

            for name, pred in predictions.items():
                weight = self.model_weights.get(name, 1.0)
                weighted_votes[pred] += weight

            final_pred = max(weighted_votes, key=weighted_votes.get)
            confidence = weighted_votes[final_pred] / total_weight if total_weight > 0 else 0

            # 計算平均機率
            avg_proba = np.mean(list(probabilities.values()), axis=0)

            return {
                'prediction': final_pred,
                'probability': {
                    'down': avg_proba[0] if len(avg_proba) > 0 else 0,
                    'neutral': avg_proba[1] if len(avg_proba) > 1 else 0,
                    'up': avg_proba[2] if len(avg_proba) > 2 else 0
                },
                'confidence': confidence,
                'individual_predictions': predictions
            }

        return {'prediction': 0, 'probability': {}, 'confidence': 0}


# ==================== 快速預測器（不需要訓練）====================

class QuickPredictor:
    """
    快速預測器
    使用規則和統計方法，不需要訓練
    """

    def __init__(self):
        self.feature_engineer = FeatureEngineer()

    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        快速預測

        基於技術指標組合給出預測
        """
        if len(df) < 30:
            return {'prediction': 0, 'confidence': 0, 'signals': []}

        features = self.feature_engineer.create_features(df)
        if len(features) == 0:
            return {'prediction': 0, 'confidence': 0, 'signals': []}

        latest = features.iloc[-1]
        signals = []
        score = 0

        # RSI 信號
        if 'rsi' in latest:
            rsi = latest['rsi']
            if rsi < 30:
                signals.append(('RSI 超賣', 2))
                score += 2
            elif rsi > 70:
                signals.append(('RSI 超買', -2))
                score -= 2

        # MACD 信號
        if 'macd_hist' in latest:
            macd_hist = latest['macd_hist']
            if macd_hist > 0:
                signals.append(('MACD 正值', 1))
                score += 1
            else:
                signals.append(('MACD 負值', -1))
                score -= 1

        # 均線信號
        if 'ma_cross' in latest:
            ma_cross = latest['ma_cross']
            if ma_cross > 0.02:
                signals.append(('短期均線上穿', 1.5))
                score += 1.5
            elif ma_cross < -0.02:
                signals.append(('短期均線下穿', -1.5))
                score -= 1.5

        # KD 信號
        if 'kd_cross' in latest:
            kd = latest['kd_cross']
            if kd > 10:
                signals.append(('KD 金叉', 1))
                score += 1
            elif kd < -10:
                signals.append(('KD 死叉', -1))
                score -= 1

        # 布林帶信號
        if 'bb_position' in latest:
            bb = latest['bb_position']
            if bb < -1:
                signals.append(('跌破布林下軌', 1.5))
                score += 1.5
            elif bb > 1:
                signals.append(('突破布林上軌', -0.5))
                score -= 0.5

        # 成交量信號
        if 'volume_ma5_ratio' in latest:
            vol_ratio = latest['volume_ma5_ratio']
            if vol_ratio > 2:
                signals.append(('成交量放大', 0.5))
                score += 0.5

        # 動能信號
        if 'momentum_5' in latest and 'momentum_10' in latest:
            if latest['momentum_5'] > 0 and latest['momentum_10'] > 0:
                signals.append(('動能向上', 1))
                score += 1
            elif latest['momentum_5'] < 0 and latest['momentum_10'] < 0:
                signals.append(('動能向下', -1))
                score -= 1

        # 計算預測
        if score >= 3:
            prediction = 1
        elif score <= -3:
            prediction = -1
        else:
            prediction = 0

        confidence = min(abs(score) / 8, 1.0)

        return {
            'prediction': prediction,
            'score': score,
            'confidence': confidence,
            'signals': [(s[0], s[1]) for s in signals],
            'features': {k: float(v) for k, v in latest.to_dict().items()
                        if not pd.isna(v)}
        }


# ==================== 測試 ====================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # 創建模擬數據
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='D')
    prices = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, 200))

    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, 200)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.015, 200))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.015, 200))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 200)
    })

    print("=" * 60)
    print("📊 ML 模型測試")
    print("=" * 60)

    # 測試特徵工程
    print("\n1. 特徵工程測試")
    fe = FeatureEngineer()
    features = fe.create_features(df)
    print(f"創建了 {len(features.columns)} 個特徵")
    print(f"特徵列表: {features.columns.tolist()[:10]}...")

    # 測試快速預測器
    print("\n2. 快速預測器測試")
    quick = QuickPredictor()
    result = quick.predict(df)
    print(f"預測: {result['prediction']}")
    print(f"信心度: {result['confidence']:.2f}")
    print(f"信號: {result['signals']}")

    # 測試 ML 模型
    if SKLEARN_AVAILABLE:
        print("\n3. ML 模型測試")
        model = MLModelWrapper(model_type='auto')
        target = fe.create_target(df, forward_days=5)

        common_idx = features.index.intersection(target.dropna().index)
        X = features.loc[common_idx]
        y = target.loc[common_idx]

        metrics = model.train(X, y)
        print(f"訓練結果: {metrics}")

        # 特徵重要性
        importance = model.get_feature_importance()
        if importance:
            top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"Top 5 重要特徵: {top_features}")
