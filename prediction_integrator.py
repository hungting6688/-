"""
prediction_integrator.py - 預測系統整合器
將 ML 增強版預測系統整合到現有股票分析架構

這個模組作為橋接，讓現有的 enhanced_stock_bot.py 可以使用新的預測功能
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 引入新的預測模組
from ml_stock_predictor import (
    EnhancedStockPredictionSystem,
    MLStockPredictor,
    AdvancedTechnicalIndicators,
    MarketSentimentAnalyzer,
    MultiTimeframeAnalyzer
)
from historical_data_fetcher import HistoricalDataFetcher, InstitutionalDataFetcher

logger = logging.getLogger(__name__)


class PredictionIntegrator:
    """
    預測整合器
    整合 ML 預測系統與現有股票分析架構
    """

    def __init__(self, enable_ml: bool = True, enable_backtest: bool = False):
        """
        初始化整合器

        Args:
            enable_ml: 是否啟用機器學習預測
            enable_backtest: 是否在每次預測時執行回測驗證
        """
        self.enable_ml = enable_ml
        self.enable_backtest = enable_backtest

        # 初始化各模組
        self.prediction_system = EnhancedStockPredictionSystem()
        self.historical_fetcher = HistoricalDataFetcher()
        self.institutional_fetcher = InstitutionalDataFetcher()

        # 預測結果快取
        self.prediction_cache = {}
        self.cache_duration_minutes = 30

    def enhance_stock_analysis(self, stock_info: Dict,
                               existing_analysis: Dict = None,
                               analysis_type: str = 'mixed') -> Dict[str, Any]:
        """
        增強股票分析結果

        Args:
            stock_info: 原始股票資訊 (code, name, close, change_percent, volume, trade_value)
            existing_analysis: 現有分析結果（如果有）
            analysis_type: 分析類型 ('short_term', 'long_term', 'mixed')

        Returns:
            增強後的分析結果
        """
        stock_code = stock_info.get('code', 'unknown')

        # 檢查快取
        cache_key = f"{stock_code}_{analysis_type}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        result = {
            'code': stock_code,
            'name': stock_info.get('name', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'analysis_type': analysis_type,
            'basic_info': stock_info
        }

        try:
            # 獲取歷史數據
            historical_data = self._get_historical_data(stock_info)

            # 獲取法人數據
            institutional_data = self.institutional_fetcher.get_institutional_data(stock_code)

            if self.enable_ml and len(historical_data) >= 30:
                # 執行 ML 預測
                ml_result = self.prediction_system.analyze_stock(
                    historical_data,
                    stock_info,
                    institutional_data
                )

                result['ml_prediction'] = ml_result['prediction']
                result['ml_score'] = ml_result['final_score']
                result['precision_grade'] = ml_result['precision_grade']
                result['action_recommendation'] = ml_result['action_recommendation']
                result['market_sentiment'] = ml_result.get('market_sentiment', {})
                result['multi_timeframe'] = ml_result.get('multi_timeframe', {})

                # 計算增強版評分
                result['enhanced_score'] = self._calculate_enhanced_score(
                    existing_analysis,
                    ml_result,
                    analysis_type
                )

                # 生成增強版推薦理由
                result['enhanced_reasoning'] = self._generate_enhanced_reasoning(
                    ml_result,
                    institutional_data,
                    analysis_type
                )

                # 計算信心加權目標價
                result['target_price'] = self._calculate_target_price(
                    stock_info['close'],
                    ml_result,
                    analysis_type
                )

            else:
                # 回退到基礎分析
                result['ml_prediction'] = None
                result['enhanced_score'] = existing_analysis.get('score', 50) if existing_analysis else 50
                result['precision_grade'] = 'N/A'
                result['enhanced_reasoning'] = ['數據不足，使用基礎分析']

            # 合併現有分析結果
            if existing_analysis:
                result['original_analysis'] = existing_analysis
                result['combined_score'] = (
                    result['enhanced_score'] * 0.6 +
                    existing_analysis.get('score', 50) * 0.4
                )
            else:
                result['combined_score'] = result['enhanced_score']

            # 保存到快取
            self._save_to_cache(cache_key, result)

        except Exception as e:
            logger.error(f"增強分析失敗: {stock_code} - {e}")
            result['error'] = str(e)
            result['enhanced_score'] = existing_analysis.get('score', 50) if existing_analysis else 50

        return result

    def _get_historical_data(self, stock_info: Dict) -> pd.DataFrame:
        """獲取歷史數據（優先真實數據，否則用模擬）"""
        stock_code = stock_info.get('code', '')

        # 嘗試獲取真實歷史數據
        try:
            real_data = self.historical_fetcher.get_stock_history(stock_code, 60)
            if real_data is not None and len(real_data) >= 30:
                return real_data
        except Exception as e:
            logger.warning(f"無法獲取真實歷史數據: {stock_code} - {e}")

        # 使用模擬數據
        return self.historical_fetcher.generate_simulated_history(stock_info, 60)

    def _calculate_enhanced_score(self, existing_analysis: Optional[Dict],
                                  ml_result: Dict,
                                  analysis_type: str) -> float:
        """計算增強版綜合評分"""

        ml_score = ml_result.get('final_score', 50)

        # 根據分析類型調整權重
        if analysis_type == 'short_term':
            # 短線更重視技術面和動能
            prediction = ml_result.get('prediction', {})
            momentum_boost = 0
            if prediction.get('prediction') == 'bullish':
                momentum_boost = 10
            elif prediction.get('prediction') == 'strong_bullish':
                momentum_boost = 15
            elif prediction.get('prediction') == 'bearish':
                momentum_boost = -10

            return min(100, max(0, ml_score + momentum_boost))

        elif analysis_type == 'long_term':
            # 長線更重視趨勢一致性
            mtf = ml_result.get('multi_timeframe', {})
            trend_alignment = mtf.get('alignment_score', 0.5)

            trend_boost = (trend_alignment - 0.5) * 20
            return min(100, max(0, ml_score + trend_boost))

        else:
            # mixed - 平衡計算
            return ml_score

    def _generate_enhanced_reasoning(self, ml_result: Dict,
                                    institutional_data: Dict,
                                    analysis_type: str) -> List[str]:
        """生成增強版推薦理由"""
        reasons = []

        # 從 ML 預測獲取理由
        prediction = ml_result.get('prediction', {})
        ml_reasons = prediction.get('reasoning', [])
        reasons.extend(ml_reasons[:3])  # 最多取3條

        # 添加市場情緒解讀
        sentiment = ml_result.get('market_sentiment', {})
        if sentiment:
            interpretation = sentiment.get('interpretation', '')
            index_val = sentiment.get('index', 50)
            if interpretation == 'extreme_fear':
                reasons.append(f'市場恐懼指數 {index_val}，可能存在超跌反彈機會')
            elif interpretation == 'extreme_greed':
                reasons.append(f'市場貪婪指數 {index_val}，注意追高風險')

        # 添加法人動向
        foreign_net = institutional_data.get('foreign_net_buy', 0)
        trust_net = institutional_data.get('trust_net_buy', 0)

        if foreign_net > 30000:
            reasons.append(f'外資大幅買超 {foreign_net:,} 張')
        elif foreign_net < -30000:
            reasons.append(f'外資大幅賣超 {abs(foreign_net):,} 張')

        if trust_net > 5000:
            reasons.append(f'投信持續買超 {trust_net:,} 張')

        # 添加多時間框架分析
        mtf = ml_result.get('multi_timeframe', {})
        trend = mtf.get('trend', 'neutral')
        if trend == 'strong_bullish':
            reasons.append('多時間框架趨勢一致向上，趨勢強勁')
        elif trend == 'strong_bearish':
            reasons.append('多時間框架趨勢一致向下，建議觀望')
        elif trend == 'bullish':
            reasons.append('短中期趨勢偏多')
        elif trend == 'bearish':
            reasons.append('短中期趨勢偏空')

        return reasons[:5]  # 最多返回5條理由

    def _calculate_target_price(self, current_price: float,
                               ml_result: Dict,
                               analysis_type: str) -> Dict[str, float]:
        """計算目標價"""
        prediction = ml_result.get('prediction', {})
        target_return = prediction.get('target_return', 0)
        confidence = prediction.get('confidence', 0.5)

        # 根據信心度調整目標報酬
        adjusted_return = target_return * (0.5 + confidence * 0.5)

        # 根據分析類型調整時間範圍
        if analysis_type == 'short_term':
            # 短線目標（1-5天）
            target_return_low = adjusted_return * 0.5
            target_return_high = adjusted_return * 1.2
        else:
            # 長線目標（1-3個月）
            target_return_low = adjusted_return * 0.8
            target_return_high = adjusted_return * 1.5

        return {
            'target_low': round(current_price * (1 + target_return_low / 100), 2),
            'target_mid': round(current_price * (1 + adjusted_return / 100), 2),
            'target_high': round(current_price * (1 + target_return_high / 100), 2),
            'expected_return': round(adjusted_return, 2),
            'confidence': round(confidence, 2)
        }

    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """從快取獲取"""
        if key in self.prediction_cache:
            cached = self.prediction_cache[key]
            cache_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
            if (datetime.now() - cache_time).total_seconds() < self.cache_duration_minutes * 60:
                return cached
        return None

    def _save_to_cache(self, key: str, data: Dict):
        """保存到快取"""
        self.prediction_cache[key] = data

    def batch_analyze(self, stocks: List[Dict],
                     analysis_type: str = 'mixed',
                     top_n: int = 10) -> List[Dict]:
        """
        批量分析股票並返回排名

        Args:
            stocks: 股票列表
            analysis_type: 分析類型
            top_n: 返回前N名

        Returns:
            按評分排序的分析結果
        """
        results = []

        for stock in stocks:
            try:
                analysis = self.enhance_stock_analysis(stock, None, analysis_type)
                results.append(analysis)
            except Exception as e:
                logger.warning(f"分析失敗: {stock.get('code')} - {e}")
                continue

        # 按增強評分排序
        results.sort(key=lambda x: x.get('enhanced_score', 0), reverse=True)

        return results[:top_n]

    def get_prediction_summary(self, analysis_result: Dict) -> str:
        """
        生成預測摘要文字

        Args:
            analysis_result: enhance_stock_analysis 的返回結果

        Returns:
            格式化的摘要文字
        """
        code = analysis_result.get('code', 'N/A')
        name = analysis_result.get('name', 'N/A')
        score = analysis_result.get('enhanced_score', 0)
        grade = analysis_result.get('precision_grade', 'N/A')
        reasons = analysis_result.get('enhanced_reasoning', [])
        target = analysis_result.get('target_price', {})
        action = analysis_result.get('action_recommendation', {})

        summary_lines = [
            f"📊 {code} {name}",
            f"評分: {score:.1f}/100 (精準度: {grade})",
        ]

        if action:
            action_type = action.get('type', 'hold')
            action_map = {
                'strong_buy': '強烈買入 🟢🟢',
                'buy': '買入 🟢',
                'hold': '持有/觀望 🟡',
                'sell': '賣出 🔴',
                'strong_sell': '強烈賣出 🔴🔴'
            }
            summary_lines.append(f"建議: {action_map.get(action_type, '觀望')}")

        if target:
            summary_lines.append(
                f"目標價: {target.get('target_mid', 'N/A')} "
                f"(預期報酬: {target.get('expected_return', 0):.1f}%)"
            )

        if reasons:
            summary_lines.append("分析要點:")
            for reason in reasons[:3]:
                summary_lines.append(f"  • {reason}")

        return "\n".join(summary_lines)


class ImprovedRecommendationGenerator:
    """
    改良版推薦生成器
    結合 ML 預測生成更精準的推薦
    """

    def __init__(self):
        self.integrator = PredictionIntegrator(enable_ml=True)

    def generate_recommendations(self, stocks: List[Dict],
                                time_slot: str = 'afternoon_scan') -> Dict[str, List[Dict]]:
        """
        生成推薦列表

        Args:
            stocks: 待分析股票列表
            time_slot: 時段

        Returns:
            分類推薦結果
        """
        # 根據時段決定分析類型
        if time_slot in ['morning_scan', 'mid_morning_scan']:
            analysis_type = 'short_term'
        elif time_slot == 'weekly_summary':
            analysis_type = 'long_term'
        else:
            analysis_type = 'mixed'

        # 批量分析
        all_results = []
        for stock in stocks:
            try:
                result = self.integrator.enhance_stock_analysis(stock, None, analysis_type)
                all_results.append(result)
            except Exception as e:
                logger.warning(f"分析失敗: {stock.get('code')} - {e}")
                continue

        # 分類推薦
        recommendations = {
            'short_term': [],
            'long_term': [],
            'weak_stocks': []
        }

        for result in all_results:
            score = result.get('enhanced_score', 50)
            action = result.get('action_recommendation', {})
            action_type = action.get('type', 'hold')

            if action_type in ['strong_buy', 'buy'] and score >= 65:
                if analysis_type == 'long_term':
                    recommendations['long_term'].append(result)
                else:
                    recommendations['short_term'].append(result)
            elif action_type in ['strong_sell', 'sell'] or score < 35:
                recommendations['weak_stocks'].append(result)

        # 排序
        for key in recommendations:
            if key == 'weak_stocks':
                recommendations[key].sort(key=lambda x: x.get('enhanced_score', 50))
            else:
                recommendations[key].sort(key=lambda x: x.get('enhanced_score', 0), reverse=True)

        # 限制數量
        limits = {
            'morning_scan': {'short_term': 4, 'long_term': 2, 'weak_stocks': 2},
            'mid_morning_scan': {'short_term': 4, 'long_term': 2, 'weak_stocks': 2},
            'mid_day_scan': {'short_term': 3, 'long_term': 3, 'weak_stocks': 2},
            'afternoon_scan': {'short_term': 3, 'long_term': 4, 'weak_stocks': 2},
            'weekly_summary': {'short_term': 2, 'long_term': 5, 'weak_stocks': 3}
        }

        slot_limits = limits.get(time_slot, {'short_term': 3, 'long_term': 3, 'weak_stocks': 2})

        for key, limit in slot_limits.items():
            recommendations[key] = recommendations[key][:limit]

        return recommendations


# 使用範例
if __name__ == '__main__':
    # 模擬股票資料
    test_stocks = [
        {
            'code': '2330',
            'name': '台積電',
            'close': 580,
            'change_percent': 1.5,
            'volume': 25000000,
            'trade_value': 15000000000
        },
        {
            'code': '2317',
            'name': '鴻海',
            'close': 105,
            'change_percent': -0.5,
            'volume': 30000000,
            'trade_value': 3200000000
        },
        {
            'code': '2454',
            'name': '聯發科',
            'close': 980,
            'change_percent': 2.3,
            'volume': 8000000,
            'trade_value': 8000000000
        }
    ]

    # 測試整合器
    integrator = PredictionIntegrator(enable_ml=True)

    print("=" * 70)
    print("📊 ML 增強版股票預測系統測試")
    print("=" * 70)

    for stock in test_stocks:
        result = integrator.enhance_stock_analysis(stock, None, 'mixed')
        summary = integrator.get_prediction_summary(result)
        print("\n" + summary)
        print("-" * 50)

    # 測試推薦生成器
    print("\n" + "=" * 70)
    print("📋 推薦列表生成測試")
    print("=" * 70)

    generator = ImprovedRecommendationGenerator()
    recommendations = generator.generate_recommendations(test_stocks, 'afternoon_scan')

    for category, items in recommendations.items():
        print(f"\n【{category}】({len(items)} 支)")
        for item in items:
            print(f"  • {item['code']} {item['name']} - 評分: {item.get('enhanced_score', 0):.1f}")
