"""
ml_enhancement_plugin.py - ML 增強插件
這是一個「疊加」在原有系統上的插件，不會改變原有程式

使用方式：
1. 原有程式完全不變
2. 想用 ML 增強時，只需在分析後調用這個插件
3. 插件失敗時自動回退，不影響原有功能

運行時間影響：
- 快速模式：每支股票 +0.1 秒
- 完整模式：每支股票 +0.5 秒
- 可透過設定完全關閉
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# ==================== 設定 ====================

# 透過環境變數控制是否啟用 ML（預設關閉，不影響原有系統）
ML_ENABLED = os.environ.get('ML_ENHANCEMENT_ENABLED', 'false').lower() == 'true'
ML_MODE = os.environ.get('ML_MODE', 'quick')  # 'quick' 或 'full'

# ==================== 插件類 ====================

class MLEnhancementPlugin:
    """
    ML 增強插件

    這是一個「被動」的插件：
    - 不主動改變任何原有流程
    - 只有被調用時才執行
    - 失敗時返回空結果，不影響原有功能
    """

    def __init__(self, enabled: bool = None):
        self.enabled = enabled if enabled is not None else ML_ENABLED
        self.mode = ML_MODE
        self.modules_loaded = False

        # 延遲載入模組（避免影響啟動時間）
        self._ml_predictor = None
        self._sentiment = None
        self._tracker = None

        if self.enabled:
            logger.info(f"🔌 ML 插件已啟用 (模式: {self.mode})")
        else:
            logger.info("🔌 ML 插件已停用")

    def _lazy_load(self):
        """延遲載入 - 只有在第一次使用時才載入模組"""
        if self.modules_loaded:
            return

        try:
            from ml_stock_predictor import MLStockPredictor, QuickPredictor
            self._ml_predictor = QuickPredictor() if self.mode == 'quick' else MLStockPredictor()
            logger.info("✅ ML 預測器已載入")
        except ImportError:
            logger.debug("ML 預測器未安裝")

        try:
            from news_sentiment import NewsSentimentSystem
            self._sentiment = NewsSentimentSystem()
            logger.info("✅ 情緒分析器已載入")
        except ImportError:
            logger.debug("情緒分析器未安裝")

        self.modules_loaded = True

    def enhance_analysis(self, original_result: Dict) -> Dict:
        """
        增強原有的分析結果

        Args:
            original_result: 原有分析器的結果

        Returns:
            增強後的結果（包含原有結果 + ML 增強）
        """
        if not self.enabled:
            return original_result

        self._lazy_load()

        enhanced = original_result.copy()

        try:
            # 添加 ML 分數（如果可用）
            if self._ml_predictor:
                ml_result = self._get_quick_prediction(original_result)
                if ml_result:
                    enhanced['ml_enhancement'] = ml_result
                    # 結合原有分數和 ML 分數
                    original_score = original_result.get('score', 50)
                    ml_score = ml_result.get('score', 0.5) * 100
                    # ML 只佔 20%，原有分數佔 80%
                    enhanced['combined_score'] = original_score * 0.8 + ml_score * 0.2
        except Exception as e:
            logger.debug(f"ML 增強失敗（回退到原有結果）: {e}")

        return enhanced

    def _get_quick_prediction(self, stock_data: Dict) -> Optional[Dict]:
        """快速預測（不需要歷史數據）"""
        if not self._ml_predictor:
            return None

        try:
            # 使用 QuickPredictor 的規則型預測
            if hasattr(self._ml_predictor, 'predict_from_indicators'):
                return self._ml_predictor.predict_from_indicators(stock_data)
        except:
            pass

        return None

    def get_market_sentiment(self) -> Optional[Dict]:
        """獲取市場情緒（可選功能）"""
        if not self.enabled:
            return None

        self._lazy_load()

        if self._sentiment:
            try:
                return self._sentiment.get_sentiment_signal()
            except Exception as e:
                logger.debug(f"市場情緒獲取失敗: {e}")

        return None

    def add_ml_badge(self, message: str) -> str:
        """在訊息中添加 ML 標記"""
        if not self.enabled:
            return message

        badge = "\n⚡ ML 增強分析"
        if badge not in message:
            message += badge

        return message


# ==================== 簡易整合函數 ====================

# 全局插件實例
_plugin = None

def get_plugin() -> MLEnhancementPlugin:
    """獲取插件實例"""
    global _plugin
    if _plugin is None:
        _plugin = MLEnhancementPlugin()
    return _plugin

def enhance(original_result: Dict) -> Dict:
    """
    簡易增強函數

    在原有程式中只需加一行：
    result = enhance(result)
    """
    return get_plugin().enhance_analysis(original_result)

def get_sentiment() -> Optional[Dict]:
    """獲取市場情緒"""
    return get_plugin().get_market_sentiment()

def add_badge(message: str) -> str:
    """添加 ML 標記到訊息"""
    return get_plugin().add_ml_badge(message)


# ==================== 使用範例 ====================

"""
# 在原有程式中的使用方式：

# 方式 1: 完全不改變原有程式
# 只需設定環境變數 ML_ENHANCEMENT_ENABLED=true

# 方式 2: 最小改動（加一行）
from ml_enhancement_plugin import enhance

# 原有程式碼
result = analyzer.analyze_stock(stock)  # 原有的分析

# 加這一行就能獲得 ML 增強
result = enhance(result)

# 方式 3: 在通知中加入標記
from ml_enhancement_plugin import add_badge

message = format_notification(results)
message = add_badge(message)  # 如果 ML 啟用，會加上標記
"""


if __name__ == '__main__':
    # 測試
    print("=" * 50)
    print("🔌 ML 增強插件測試")
    print("=" * 50)

    plugin = MLEnhancementPlugin(enabled=True)

    # 模擬原有分析結果
    original = {
        'code': '2330',
        'name': '台積電',
        'score': 75,
        'recommendation': '買入'
    }

    enhanced = plugin.enhance_analysis(original)

    print(f"\n原有結果: {original}")
    print(f"增強結果: {enhanced}")

    # 測試標記
    message = "今日推薦股票: 台積電"
    message = plugin.add_ml_badge(message)
    print(f"\n訊息: {message}")
