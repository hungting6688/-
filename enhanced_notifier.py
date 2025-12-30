"""
enhanced_notifier.py - 增強版推播系統
整合 ML 預測結果到 LINE/Telegram 推播

功能：
1. 增強版訊息格式
2. ML 評分和信心度顯示
3. 互動式按鈕（Telegram）
4. 圖表生成
5. 定期報告推播
"""

import os
import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from io import BytesIO

logger = logging.getLogger(__name__)

# 嘗試導入圖表庫
try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非互動式後端
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.info("matplotlib 未安裝，圖表功能停用")


class EnhancedMessageFormatter:
    """
    增強版訊息格式化器
    """

    def __init__(self):
        # 評級符號
        self.grade_emojis = {
            'A+': '🌟',
            'A': '⭐',
            'B+': '✨',
            'B': '👍',
            'C': '👌',
            'D': '⚠️'
        }

        # 方向符號
        self.direction_emojis = {
            'strong_buy': '🟢🟢',
            'buy': '🟢',
            'hold': '🟡',
            'sell': '🔴',
            'strong_sell': '🔴🔴'
        }

        # 情緒符號
        self.sentiment_emojis = {
            'positive': '😊',
            'negative': '😟',
            'neutral': '😐'
        }

    def format_stock_recommendation(self, analysis: Dict) -> str:
        """
        格式化單支股票推薦
        """
        stock_info = analysis.get('stock_info', {})
        ml_result = analysis.get('ml_enhanced', {})
        prediction = ml_result.get('prediction', {}) if ml_result else {}

        code = stock_info.get('code', 'N/A')
        name = stock_info.get('name', 'N/A')
        price = stock_info.get('close', 0)
        change_pct = stock_info.get('change_percent', 0)

        # 評分和評級
        score = analysis.get('final_score', 50)
        grade = analysis.get('precision_grade', 'N/A')
        grade_emoji = self.grade_emojis.get(grade, '')

        # 建議動作
        action = analysis.get('recommendation', {})
        action_type = action.get('type', 'hold')
        action_emoji = self.direction_emojis.get(action_type, '🟡')

        # 目標價
        target = analysis.get('target_price', {})
        target_mid = target.get('target_mid', price)
        expected_return = target.get('expected_return', 0)

        # 信心度
        confidence = prediction.get('confidence', 0.5)

        # 推理說明
        reasoning = analysis.get('reasoning', [])

        lines = [
            f"{'─' * 28}",
            f"📊 {code} {name}",
            f"現價: ${price:.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)",
            f"",
            f"{grade_emoji} 評級: {grade} | 評分: {score:.1f}/100",
            f"{action_emoji} 建議: {self._get_action_text(action_type)}",
            f"🎯 目標價: ${target_mid:.2f} ({'+' if expected_return >= 0 else ''}{expected_return:.1f}%)",
            f"📈 信心度: {self._format_confidence_bar(confidence)}",
        ]

        if reasoning:
            lines.append("")
            lines.append("💡 分析要點:")
            for reason in reasoning[:3]:
                lines.append(f"  • {reason}")

        return "\n".join(lines)

    def format_daily_report(self, recommendations: Dict[str, List],
                           market_sentiment: Dict = None) -> str:
        """
        格式化每日報告
        """
        lines = []
        lines.append("=" * 30)
        lines.append(f"📈 每日股票推薦報告")
        lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 30)

        # 市場情緒
        if market_sentiment:
            sentiment = market_sentiment.get('sentiment', 'neutral')
            sentiment_emoji = self.sentiment_emojis.get(sentiment, '😐')
            score = market_sentiment.get('overall_score', 0)
            lines.append("")
            lines.append(f"🌡️ 市場情緒: {sentiment_emoji} ({score:+.2f})")
            keywords = market_sentiment.get('keywords', [])[:5]
            if keywords:
                lines.append(f"🔑 熱門關鍵詞: {', '.join(keywords)}")

        # 短線推薦
        short_term = recommendations.get('short_term', [])
        if short_term:
            lines.append("")
            lines.append(f"🚀 短線推薦 ({len(short_term)})")
            for stock in short_term:
                lines.append(self._format_brief_recommendation(stock, 'short'))

        # 長線推薦
        long_term = recommendations.get('long_term', [])
        if long_term:
            lines.append("")
            lines.append(f"📊 長線推薦 ({len(long_term)})")
            for stock in long_term:
                lines.append(self._format_brief_recommendation(stock, 'long'))

        # 弱勢股警示
        weak = recommendations.get('weak_stocks', [])
        if weak:
            lines.append("")
            lines.append(f"⚠️ 弱勢警示 ({len(weak)})")
            for stock in weak:
                lines.append(self._format_brief_recommendation(stock, 'weak'))

        lines.append("")
        lines.append("=" * 30)
        lines.append("⚡ 由 ML 增強版分析系統提供")

        return "\n".join(lines)

    def format_weekly_performance(self, report: Dict) -> str:
        """
        格式化週績效報告
        """
        lines = []
        lines.append("=" * 30)
        lines.append("📊 週績效報告")
        lines.append(f"📅 {report.get('period', {}).get('start', '')} ~ {report.get('period', {}).get('end', '')}")
        lines.append("=" * 30)

        summary = report.get('summary', {})
        returns = report.get('returns', {})

        lines.append("")
        lines.append("📈 預測績效")
        lines.append(f"  總預測: {summary.get('total_predictions', 0)} 次")
        lines.append(f"  準確率: {summary.get('overall_accuracy', 0):.1%}")
        lines.append(f"  短線準確率: {summary.get('short_term_accuracy', 0):.1%}")
        lines.append(f"  長線準確率: {summary.get('long_term_accuracy', 0):.1%}")

        lines.append("")
        lines.append("💰 報酬統計")
        lines.append(f"  策略報酬: {returns.get('strategy_avg_return', 0):+.2f}%")
        lines.append(f"  累計報酬: {returns.get('strategy_total_return', 0):+.2f}%")
        lines.append(f"  勝率: {returns.get('win_rate', 0):.1%}")
        lines.append(f"  夏普比率: {returns.get('sharpe_ratio', 0):.2f}")

        # 優化建議
        recommendations = report.get('recommendations', [])
        if recommendations:
            lines.append("")
            lines.append("💡 優化建議")
            for rec in recommendations[:3]:
                lines.append(f"  • {rec}")

        return "\n".join(lines)

    def _format_brief_recommendation(self, stock: Dict, stock_type: str) -> str:
        """格式化簡短推薦"""
        code = stock.get('code', stock.get('stock_info', {}).get('code', 'N/A'))
        name = stock.get('name', stock.get('stock_info', {}).get('name', 'N/A'))
        score = stock.get('enhanced_score', stock.get('final_score', 50))
        grade = stock.get('precision_grade', 'N/A')

        grade_emoji = self.grade_emojis.get(grade, '')

        if stock_type == 'weak':
            return f"  ⚠️ {code} {name} | 評分: {score:.0f}"
        else:
            return f"  {grade_emoji} {code} {name} | {grade} | {score:.0f}分"

    def _get_action_text(self, action_type: str) -> str:
        """獲取動作文字"""
        action_map = {
            'strong_buy': '強烈買入',
            'buy': '買入',
            'hold': '持有觀望',
            'sell': '賣出',
            'strong_sell': '強烈賣出'
        }
        return action_map.get(action_type, '觀望')

    def _format_confidence_bar(self, confidence: float) -> str:
        """格式化信心度進度條"""
        filled = int(confidence * 10)
        empty = 10 - filled
        return f"[{'█' * filled}{'░' * empty}] {confidence:.0%}"


class EnhancedLineNotifier:
    """
    增強版 LINE 通知器
    """

    def __init__(self, token: str = None):
        self.token = token or os.environ.get('LINE_NOTIFY_TOKEN', '')
        self.api_url = "https://notify-api.line.me/api/notify"
        self.formatter = EnhancedMessageFormatter()

    def send_message(self, message: str) -> bool:
        """發送文字訊息"""
        if not self.token:
            logger.warning("LINE Token 未設定")
            return False

        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        data = {'message': f"\n{message}"}

        try:
            response = requests.post(self.api_url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                logger.info("LINE 訊息發送成功")
                return True
            else:
                logger.error(f"LINE 訊息發送失敗: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"LINE 訊息發送錯誤: {e}")
            return False

    def send_image(self, image_file: str) -> bool:
        """發送圖片"""
        if not self.token:
            return False

        headers = {
            'Authorization': f'Bearer {self.token}'
        }

        try:
            with open(image_file, 'rb') as f:
                files = {'imageFile': f}
                data = {'message': ' '}
                response = requests.post(self.api_url, headers=headers, data=data, files=files, timeout=30)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"LINE 圖片發送錯誤: {e}")
            return False

    def send_daily_report(self, recommendations: Dict[str, List],
                         market_sentiment: Dict = None) -> bool:
        """發送每日報告"""
        message = self.formatter.format_daily_report(recommendations, market_sentiment)
        return self.send_message(message)

    def send_stock_alert(self, analysis: Dict) -> bool:
        """發送個股提醒"""
        message = self.formatter.format_stock_recommendation(analysis)
        return self.send_message(message)

    def send_performance_report(self, report: Dict) -> bool:
        """發送績效報告"""
        message = self.formatter.format_weekly_performance(report)
        return self.send_message(message)


class EnhancedTelegramNotifier:
    """
    增強版 Telegram 通知器
    支援互動式按鈕
    """

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID', '')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.formatter = EnhancedMessageFormatter()

    def send_message(self, message: str, parse_mode: str = 'Markdown',
                    reply_markup: Dict = None) -> bool:
        """發送訊息"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram 設定不完整")
            return False

        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }

        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)

        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info("Telegram 訊息發送成功")
                return True
            else:
                logger.error(f"Telegram 訊息發送失敗: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Telegram 訊息發送錯誤: {e}")
            return False

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """發送圖片"""
        if not self.bot_token or not self.chat_id:
            return False

        url = f"{self.base_url}/sendPhoto"

        try:
            with open(photo_path, 'rb') as f:
                files = {'photo': f}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption
                }
                response = requests.post(url, data=data, files=files, timeout=30)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram 圖片發送錯誤: {e}")
            return False

    def send_with_buttons(self, message: str, buttons: List[List[Dict]]) -> bool:
        """
        發送帶按鈕的訊息

        buttons 格式:
        [[{'text': '按鈕1', 'callback_data': 'action1'}],
         [{'text': '按鈕2', 'callback_data': 'action2'}]]
        """
        reply_markup = {
            'inline_keyboard': buttons
        }
        return self.send_message(message, reply_markup=reply_markup)

    def send_stock_recommendation(self, analysis: Dict) -> bool:
        """發送股票推薦（帶互動按鈕）"""
        message = self.formatter.format_stock_recommendation(analysis)

        stock_code = analysis.get('stock_info', {}).get('code', '')

        # 添加互動按鈕
        buttons = [
            [
                {'text': '📈 詳細分析', 'callback_data': f'detail_{stock_code}'},
                {'text': '📊 技術圖表', 'callback_data': f'chart_{stock_code}'}
            ],
            [
                {'text': '🔔 設定提醒', 'callback_data': f'alert_{stock_code}'},
                {'text': '📰 相關新聞', 'callback_data': f'news_{stock_code}'}
            ]
        ]

        return self.send_with_buttons(message, buttons)

    def send_daily_report(self, recommendations: Dict[str, List],
                         market_sentiment: Dict = None) -> bool:
        """發送每日報告"""
        message = self.formatter.format_daily_report(recommendations, market_sentiment)

        # 報告按鈕
        buttons = [
            [
                {'text': '📊 完整報告', 'callback_data': 'full_report'},
                {'text': '📈 績效統計', 'callback_data': 'performance'}
            ]
        ]

        return self.send_with_buttons(message, buttons)


class ChartGenerator:
    """
    圖表生成器
    生成預測和績效圖表
    """

    def __init__(self, output_dir: str = './data/charts'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_prediction_chart(self, stock_code: str,
                                  historical_data: 'pd.DataFrame',
                                  prediction: Dict) -> Optional[str]:
        """
        生成預測圖表
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[3, 1])

            # 價格圖
            close = historical_data['close'].values[-30:]
            dates = range(len(close))

            ax1.plot(dates, close, 'w-', linewidth=1.5, label='收盤價')

            # 均線
            if len(close) >= 5:
                ma5 = historical_data['close'].rolling(5).mean().values[-30:]
                ax1.plot(dates, ma5, 'y--', linewidth=1, alpha=0.7, label='MA5')

            if len(close) >= 20:
                ma20 = historical_data['close'].rolling(20).mean().values[-30:]
                ax1.plot(dates, ma20, 'c--', linewidth=1, alpha=0.7, label='MA20')

            # 預測方向
            pred_direction = prediction.get('direction', 'neutral')
            target_price = prediction.get('target_price', {}).get('target_mid', close[-1])

            if pred_direction in ['bullish', 'strong_buy', 'buy']:
                ax1.axhline(y=target_price, color='g', linestyle=':', alpha=0.7, label=f'目標價 {target_price:.0f}')
                ax1.fill_between(dates[-5:], close[-5:], target_price, alpha=0.2, color='g')
            elif pred_direction in ['bearish', 'strong_sell', 'sell']:
                ax1.axhline(y=target_price, color='r', linestyle=':', alpha=0.7, label=f'目標價 {target_price:.0f}')
                ax1.fill_between(dates[-5:], close[-5:], target_price, alpha=0.2, color='r')

            ax1.set_title(f'{stock_code} 價格走勢與預測', fontsize=12, color='white')
            ax1.legend(loc='upper left', fontsize=8)
            ax1.grid(True, alpha=0.3)

            # 成交量圖
            if 'volume' in historical_data.columns:
                volume = historical_data['volume'].values[-30:]
                colors = ['g' if close[i] >= close[i-1] else 'r' for i in range(1, len(close))]
                colors.insert(0, 'g')
                ax2.bar(dates, volume, color=colors, alpha=0.7)
                ax2.set_title('成交量', fontsize=10, color='white')
                ax2.grid(True, alpha=0.3)

            plt.tight_layout()

            # 保存
            filepath = os.path.join(self.output_dir, f'{stock_code}_prediction.png')
            plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='#1e1e1e')
            plt.close()

            return filepath

        except Exception as e:
            logger.error(f"圖表生成失敗: {e}")
            return None

    def generate_performance_chart(self, results: List[Dict]) -> Optional[str]:
        """
        生成績效圖表
        """
        if not MATPLOTLIB_AVAILABLE or not results:
            return None

        try:
            import pandas as pd

            df = pd.DataFrame(results)
            df['verify_date'] = pd.to_datetime(df['verify_date'])
            df = df.sort_values('verify_date')

            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

            # 累計報酬
            cumulative_return = df['actual_return'].cumsum()
            ax1.plot(df['verify_date'], cumulative_return, 'g-', linewidth=2)
            ax1.fill_between(df['verify_date'], 0, cumulative_return,
                           where=(cumulative_return >= 0), alpha=0.3, color='g')
            ax1.fill_between(df['verify_date'], 0, cumulative_return,
                           where=(cumulative_return < 0), alpha=0.3, color='r')
            ax1.axhline(y=0, color='white', linestyle='--', alpha=0.5)
            ax1.set_title('累計報酬率 (%)', fontsize=12, color='white')
            ax1.grid(True, alpha=0.3)

            # 準確率滾動
            rolling_accuracy = df['is_correct'].rolling(10).mean()
            ax2.plot(df['verify_date'], rolling_accuracy, 'y-', linewidth=2)
            ax2.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='50%基準')
            ax2.set_title('10日滾動準確率', fontsize=12, color='white')
            ax2.set_ylim(0, 1)
            ax2.grid(True, alpha=0.3)
            ax2.legend()

            plt.tight_layout()

            filepath = os.path.join(self.output_dir, 'performance.png')
            plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='#1e1e1e')
            plt.close()

            return filepath

        except Exception as e:
            logger.error(f"績效圖表生成失敗: {e}")
            return None


class UnifiedNotifier:
    """
    統一通知器
    整合所有推播渠道
    """

    def __init__(self, config: Dict = None):
        config = config or {}

        self.line = EnhancedLineNotifier(config.get('line_token'))
        self.telegram = EnhancedTelegramNotifier(
            config.get('telegram_bot_token'),
            config.get('telegram_chat_id')
        )
        self.chart_generator = ChartGenerator()
        self.formatter = EnhancedMessageFormatter()

        # 啟用的渠道
        self.enabled_channels = config.get('enabled_channels', ['line', 'telegram'])

    def send_all(self, message: str) -> Dict[str, bool]:
        """發送到所有渠道"""
        results = {}

        if 'line' in self.enabled_channels:
            results['line'] = self.line.send_message(message)

        if 'telegram' in self.enabled_channels:
            results['telegram'] = self.telegram.send_message(message)

        return results

    def send_daily_report(self, recommendations: Dict[str, List],
                         market_sentiment: Dict = None) -> Dict[str, bool]:
        """發送每日報告到所有渠道"""
        results = {}

        if 'line' in self.enabled_channels:
            results['line'] = self.line.send_daily_report(recommendations, market_sentiment)

        if 'telegram' in self.enabled_channels:
            results['telegram'] = self.telegram.send_daily_report(recommendations, market_sentiment)

        return results

    def send_alert(self, analysis: Dict, with_chart: bool = True,
                  historical_data: 'pd.DataFrame' = None) -> Dict[str, bool]:
        """發送個股提醒"""
        results = {}

        # 生成圖表
        chart_path = None
        if with_chart and historical_data is not None:
            stock_code = analysis.get('stock_info', {}).get('code', '')
            prediction = analysis.get('ml_enhanced', {}).get('prediction', {})
            chart_path = self.chart_generator.generate_prediction_chart(
                stock_code, historical_data, prediction
            )

        if 'line' in self.enabled_channels:
            results['line'] = self.line.send_stock_alert(analysis)
            if chart_path:
                self.line.send_image(chart_path)

        if 'telegram' in self.enabled_channels:
            results['telegram'] = self.telegram.send_stock_recommendation(analysis)
            if chart_path:
                self.telegram.send_photo(chart_path)

        return results


# ==================== 測試 ====================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("📱 增強版推播系統測試")
    print("=" * 60)

    # 測試訊息格式化
    formatter = EnhancedMessageFormatter()

    # 模擬分析結果
    test_analysis = {
        'stock_info': {
            'code': '2330',
            'name': '台積電',
            'close': 580,
            'change_percent': 2.5
        },
        'final_score': 78.5,
        'precision_grade': 'A',
        'recommendation': {
            'type': 'buy',
            'strength': 0.75
        },
        'target_price': {
            'target_mid': 620,
            'expected_return': 6.9
        },
        'ml_enhanced': {
            'prediction': {
                'confidence': 0.82
            }
        },
        'reasoning': [
            'MACD 出現黃金交叉',
            '外資連續買超',
            '突破20日均線'
        ]
    }

    print("\n1. 個股推薦訊息:")
    print(formatter.format_stock_recommendation(test_analysis))

    # 模擬推薦列表
    recommendations = {
        'short_term': [
            {'code': '2330', 'name': '台積電', 'enhanced_score': 78, 'precision_grade': 'A'},
            {'code': '2454', 'name': '聯發科', 'enhanced_score': 72, 'precision_grade': 'B+'}
        ],
        'long_term': [
            {'code': '2317', 'name': '鴻海', 'enhanced_score': 68, 'precision_grade': 'B'}
        ],
        'weak_stocks': [
            {'code': '2409', 'name': '友達', 'enhanced_score': 35, 'precision_grade': 'D'}
        ]
    }

    market_sentiment = {
        'sentiment': 'positive',
        'overall_score': 0.35,
        'keywords': ['上漲', '買超', '突破', '成長']
    }

    print("\n2. 每日報告:")
    print(formatter.format_daily_report(recommendations, market_sentiment))

    # 測試週報格式
    test_report = {
        'period': {'start': '2024-01-01', 'end': '2024-01-07'},
        'summary': {
            'total_predictions': 25,
            'overall_accuracy': 0.72,
            'short_term_accuracy': 0.68,
            'long_term_accuracy': 0.78
        },
        'returns': {
            'strategy_avg_return': 2.5,
            'strategy_total_return': 15.3,
            'win_rate': 0.65,
            'sharpe_ratio': 1.2
        },
        'recommendations': ['系統運作正常']
    }

    print("\n3. 週績效報告:")
    print(formatter.format_weekly_performance(test_report))
