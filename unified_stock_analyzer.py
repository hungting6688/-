#!/usr/bin/env python3
"""
unified_stock_analyzer.py - 統一股票分析器
整合所有分析模組，作為 GitHub Actions 的主入口

功能：
1. 整合 ML 增強預測
2. 新聞情緒分析
3. 回測記錄
4. 增強推播
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==================== 版本和功能標記 ====================

VERSION = "2.0.0-ML"
ML_ENHANCED = True
FEATURES = {
    'ml_prediction': True,
    'news_sentiment': True,
    'backtest_tracking': True,
    'enhanced_notification': True
}

def print_banner():
    """打印啟動橫幅"""
    print("=" * 60)
    print(f"🚀 統一股票分析系統 v{VERSION}")
    print(f"⚡ ML 增強版: {'啟用' if ML_ENHANCED else '停用'}")
    print(f"📅 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if ML_ENHANCED:
        print("✅ 功能狀態:")
        for feature, enabled in FEATURES.items():
            status = "🟢" if enabled else "🔴"
            print(f"   {status} {feature}")
        print()


# ==================== 模組導入 ====================

def import_modules():
    """動態導入模組，處理缺失情況"""
    modules = {}

    # ML 預測模組
    try:
        from ml_stock_predictor import EnhancedStockPredictionSystem
        from prediction_integrator import PredictionIntegrator
        modules['ml_predictor'] = EnhancedStockPredictionSystem
        modules['integrator'] = PredictionIntegrator
        logger.info("✅ ML 預測模組已載入")
    except ImportError as e:
        logger.warning(f"⚠️ ML 預測模組未載入: {e}")

    # 新聞情緒模組
    try:
        from news_sentiment import NewsSentimentSystem
        modules['sentiment'] = NewsSentimentSystem
        logger.info("✅ 新聞情緒模組已載入")
    except ImportError as e:
        logger.warning(f"⚠️ 新聞情緒模組未載入: {e}")

    # 回測模組
    try:
        from backtest_reporter import AutoBacktestRunner, PredictionTracker
        modules['backtest'] = AutoBacktestRunner
        modules['tracker'] = PredictionTracker
        logger.info("✅ 回測模組已載入")
    except ImportError as e:
        logger.warning(f"⚠️ 回測模組未載入: {e}")

    # 增強推播模組
    try:
        from enhanced_notifier import UnifiedNotifier, EnhancedMessageFormatter
        modules['notifier'] = UnifiedNotifier
        modules['formatter'] = EnhancedMessageFormatter
        logger.info("✅ 增強推播模組已載入")
    except ImportError as e:
        logger.warning(f"⚠️ 增強推播模組未載入: {e}")

    # 數據獲取模組
    try:
        from real_data_fetcher import RealTimeDataFetcher
        modules['data_fetcher'] = RealTimeDataFetcher
        logger.info("✅ 真實數據模組已載入")
    except ImportError as e:
        logger.warning(f"⚠️ 真實數據模組未載入: {e}")

    # 原有分析器
    try:
        from comprehensive_stock_analyzer import ComprehensiveStockAnalyzer
        modules['analyzer'] = ComprehensiveStockAnalyzer
        logger.info("✅ 綜合分析器已載入")
    except ImportError as e:
        logger.warning(f"⚠️ 綜合分析器未載入: {e}")

    # 原有通知器
    try:
        from notifier import send_notification
        modules['send_notification'] = send_notification
        logger.info("✅ 原有通知器已載入")
    except ImportError as e:
        logger.warning(f"⚠️ 原有通知器未載入: {e}")

    # 數據獲取器
    try:
        from twse_data_fetcher import TWStockDataFetcher
        modules['twse_fetcher'] = TWStockDataFetcher
        logger.info("✅ TWSE 數據獲取器已載入")
    except ImportError as e:
        logger.warning(f"⚠️ TWSE 數據獲取器未載入: {e}")

    return modules


# ==================== 主分析類 ====================

class UnifiedStockAnalyzer:
    """統一股票分析器"""

    def __init__(self, mode: str = 'optimized'):
        self.mode = mode
        self.modules = import_modules()
        self.ml_enabled = 'ml_predictor' in self.modules

        # 初始化組件
        if 'analyzer' in self.modules:
            self.analyzer = self.modules['analyzer']()
        else:
            self.analyzer = None

        if 'integrator' in self.modules:
            self.integrator = self.modules['integrator'](enable_ml=True)
        else:
            self.integrator = None

        if 'sentiment' in self.modules:
            self.sentiment = self.modules['sentiment']()
        else:
            self.sentiment = None

        if 'tracker' in self.modules:
            self.tracker = self.modules['tracker']('./data/predictions')
        else:
            self.tracker = None

        if 'twse_fetcher' in self.modules:
            self.data_fetcher = self.modules['twse_fetcher']()
        else:
            self.data_fetcher = None

        logger.info(f"統一分析器初始化完成 (ML: {'啟用' if self.ml_enabled else '停用'})")

    def run_analysis(self, time_slot: str = 'afternoon_scan') -> Dict[str, Any]:
        """執行完整分析流程"""
        logger.info(f"開始執行 {time_slot} 分析...")

        result = {
            'timestamp': datetime.now().isoformat(),
            'time_slot': time_slot,
            'mode': self.mode,
            'ml_enhanced': self.ml_enabled,
            'version': VERSION,
            'recommendations': {
                'short_term': [],
                'long_term': [],
                'weak_stocks': []
            },
            'market_sentiment': None,
            'stats': {}
        }

        try:
            # 1. 獲取股票數據
            stocks = self._get_stocks(time_slot)
            result['stats']['total_stocks'] = len(stocks)
            logger.info(f"獲取了 {len(stocks)} 支股票")

            if not stocks:
                logger.warning("無法獲取股票數據")
                return result

            # 2. 市場情緒分析
            if self.sentiment:
                try:
                    market_sentiment = self.sentiment.get_sentiment_signal()
                    result['market_sentiment'] = market_sentiment
                    logger.info(f"市場情緒: {market_sentiment.get('description', 'N/A')}")
                except Exception as e:
                    logger.warning(f"市場情緒分析失敗: {e}")

            # 3. 分析每支股票
            analyzed_stocks = []
            for stock in stocks[:100]:  # 限制分析數量
                try:
                    analysis = self._analyze_stock(stock)
                    if analysis:
                        analyzed_stocks.append(analysis)
                except Exception as e:
                    logger.warning(f"分析失敗 {stock.get('code')}: {e}")
                    continue

            result['stats']['analyzed_stocks'] = len(analyzed_stocks)
            logger.info(f"完成分析 {len(analyzed_stocks)} 支股票")

            # 4. 分類推薦
            result['recommendations'] = self._classify_recommendations(analyzed_stocks, time_slot)

            # 5. 記錄預測（用於回測）
            if self.tracker:
                self._record_predictions(result['recommendations'])

            # 6. 發送通知
            self._send_notifications(result)

        except Exception as e:
            logger.error(f"分析流程出錯: {e}")
            result['error'] = str(e)

        return result

    def _get_stocks(self, time_slot: str) -> List[Dict]:
        """獲取股票數據"""
        if self.data_fetcher:
            try:
                return self.data_fetcher.get_stocks_by_time_slot(time_slot)
            except Exception as e:
                logger.warning(f"數據獲取失敗: {e}")
        return []

    def _analyze_stock(self, stock: Dict) -> Optional[Dict]:
        """分析單支股票"""
        if not self.analyzer:
            return None

        # 使用 ML 增強分析
        if self.ml_enabled and hasattr(self.analyzer, 'analyze_with_ml_enhancement'):
            return self.analyzer.analyze_with_ml_enhancement(stock, 'mixed')

        # 回退到傳統分析
        if hasattr(self.analyzer, 'analyze_stock_comprehensive'):
            return self.analyzer.analyze_stock_comprehensive(stock, 'mixed', precision_mode=True)

        return None

    def _classify_recommendations(self, stocks: List[Dict], time_slot: str) -> Dict[str, List]:
        """分類推薦"""
        recommendations = {
            'short_term': [],
            'long_term': [],
            'weak_stocks': []
        }

        for stock in stocks:
            score = stock.get('final_score', stock.get('enhanced_score', 50))
            recommendation = stock.get('recommendation', {})
            action = recommendation.get('type', 'hold')

            if action in ['strong_buy', 'buy'] or score >= 65:
                if time_slot in ['morning_scan', 'mid_morning_scan']:
                    recommendations['short_term'].append(stock)
                else:
                    recommendations['long_term'].append(stock)
            elif action in ['strong_sell', 'sell'] or score <= 35:
                recommendations['weak_stocks'].append(stock)

        # 排序
        recommendations['short_term'].sort(key=lambda x: x.get('final_score', 0), reverse=True)
        recommendations['long_term'].sort(key=lambda x: x.get('final_score', 0), reverse=True)
        recommendations['weak_stocks'].sort(key=lambda x: x.get('final_score', 100))

        # 限制數量
        limits = {
            'morning_scan': {'short_term': 4, 'long_term': 2, 'weak_stocks': 2},
            'afternoon_scan': {'short_term': 3, 'long_term': 4, 'weak_stocks': 2},
            'weekly_summary': {'short_term': 2, 'long_term': 5, 'weak_stocks': 3}
        }
        slot_limits = limits.get(time_slot, {'short_term': 3, 'long_term': 3, 'weak_stocks': 2})

        for key, limit in slot_limits.items():
            recommendations[key] = recommendations[key][:limit]

        return recommendations

    def _record_predictions(self, recommendations: Dict):
        """記錄預測用於回測"""
        if not self.tracker:
            return

        for category, stocks in recommendations.items():
            if category == 'weak_stocks':
                continue

            for stock in stocks:
                stock_info = stock.get('stock_info', stock)
                prediction = {
                    'stock_code': stock_info.get('code', ''),
                    'stock_name': stock_info.get('name', ''),
                    'prediction_date': datetime.now().strftime('%Y-%m-%d'),
                    'prediction_type': 'short_term' if category == 'short_term' else 'long_term',
                    'direction': 'bullish',
                    'score': stock.get('final_score', 50),
                    'entry_price': stock_info.get('close', 0),
                    'target_price': stock.get('target_price', {}).get('target_mid', 0),
                    'confidence': stock.get('ml_enhanced', {}).get('prediction', {}).get('confidence', 0.5),
                    'reasoning': stock.get('reasoning', [])
                }
                self.tracker.record_prediction(prediction)

    def _send_notifications(self, result: Dict):
        """發送通知"""
        # 生成訊息
        message = self._format_message(result)

        # 使用原有通知器
        if 'send_notification' in self.modules:
            try:
                self.modules['send_notification'](message)
                logger.info("✅ 通知發送成功")
            except Exception as e:
                logger.error(f"通知發送失敗: {e}")

    def _format_message(self, result: Dict) -> str:
        """格式化通知訊息"""
        lines = []
        lines.append("=" * 30)
        lines.append(f"📈 股票推薦報告 v{VERSION}")
        lines.append(f"{'⚡ ML 增強版' if result['ml_enhanced'] else ''}")
        lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 30)

        # 市場情緒
        sentiment = result.get('market_sentiment')
        if sentiment:
            lines.append(f"\n🌡️ 市場情緒: {sentiment.get('description', 'N/A')}")

        # 短線推薦
        short_term = result['recommendations'].get('short_term', [])
        if short_term:
            lines.append(f"\n🚀 短線推薦 ({len(short_term)})")
            for stock in short_term:
                info = stock.get('stock_info', stock)
                score = stock.get('final_score', 50)
                grade = stock.get('precision_grade', 'N/A')
                lines.append(f"  • {info.get('code')} {info.get('name')} | {grade} | {score:.0f}分")

        # 長線推薦
        long_term = result['recommendations'].get('long_term', [])
        if long_term:
            lines.append(f"\n📊 長線推薦 ({len(long_term)})")
            for stock in long_term:
                info = stock.get('stock_info', stock)
                score = stock.get('final_score', 50)
                grade = stock.get('precision_grade', 'N/A')
                lines.append(f"  • {info.get('code')} {info.get('name')} | {grade} | {score:.0f}分")

        # 弱勢警示
        weak = result['recommendations'].get('weak_stocks', [])
        if weak:
            lines.append(f"\n⚠️ 弱勢警示 ({len(weak)})")
            for stock in weak:
                info = stock.get('stock_info', stock)
                lines.append(f"  • {info.get('code')} {info.get('name')}")

        lines.append("\n" + "=" * 30)
        if result['ml_enhanced']:
            lines.append("⚡ ML 增強版分析系統")

        return "\n".join(lines)


# ==================== 命令行入口 ====================

def main():
    parser = argparse.ArgumentParser(description='統一股票分析系統')
    parser.add_argument('command', choices=['run', 'test', 'fix', 'status'],
                       help='執行命令')
    parser.add_argument('--mode', default='optimized',
                       choices=['basic', 'enhanced', 'optimized'],
                       help='分析模式')
    parser.add_argument('--slot', default='afternoon_scan',
                       help='分析時段')
    parser.add_argument('--test-type', default='basic',
                       help='測試類型')

    args = parser.parse_args()

    print_banner()

    if args.command == 'run':
        analyzer = UnifiedStockAnalyzer(args.mode)
        result = analyzer.run_analysis(args.slot)

        print("\n📊 分析完成!")
        print(f"  總股票數: {result['stats'].get('total_stocks', 0)}")
        print(f"  分析完成: {result['stats'].get('analyzed_stocks', 0)}")
        print(f"  短線推薦: {len(result['recommendations']['short_term'])}")
        print(f"  長線推薦: {len(result['recommendations']['long_term'])}")
        print(f"  ML 增強: {'是' if result['ml_enhanced'] else '否'}")

    elif args.command == 'test':
        print("🧪 執行系統測試...")
        modules = import_modules()
        print(f"\n載入模組數: {len(modules)}")
        for name, module in modules.items():
            print(f"  ✅ {name}")

    elif args.command == 'status':
        print("📊 系統狀態:")
        print(f"  版本: {VERSION}")
        print(f"  ML 增強: {'啟用' if ML_ENHANCED else '停用'}")
        for feature, enabled in FEATURES.items():
            print(f"  {feature}: {'🟢' if enabled else '🔴'}")

    elif args.command == 'fix':
        print("🔧 執行系統修復...")
        # 創建必要目錄
        os.makedirs('./data/predictions', exist_ok=True)
        os.makedirs('./data/cache', exist_ok=True)
        os.makedirs('./logs', exist_ok=True)
        print("✅ 目錄結構已修復")


if __name__ == '__main__':
    main()
