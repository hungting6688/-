"""
backtest_reporter.py - 自動回測報告系統
追蹤預測準確率並生成定期報告

功能：
1. 記錄每日預測
2. 驗證預測準確率
3. 生成週報/月報
4. 績效分析與優化建議
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PredictionTracker:
    """
    預測追蹤器
    記錄和追蹤所有預測結果
    """

    def __init__(self, data_dir: str = './data/predictions'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.predictions_file = os.path.join(data_dir, 'predictions.json')
        self.results_file = os.path.join(data_dir, 'results.json')

        self.predictions = self._load_predictions()
        self.results = self._load_results()

    def _load_predictions(self) -> List[Dict]:
        """載入預測記錄"""
        if os.path.exists(self.predictions_file):
            try:
                with open(self.predictions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _load_results(self) -> List[Dict]:
        """載入驗證結果"""
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_predictions(self):
        """保存預測記錄"""
        with open(self.predictions_file, 'w', encoding='utf-8') as f:
            json.dump(self.predictions, f, ensure_ascii=False, indent=2)

    def _save_results(self):
        """保存驗證結果"""
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

    def record_prediction(self, prediction: Dict[str, Any]):
        """
        記錄新預測

        prediction 應包含:
        - stock_code: str
        - stock_name: str
        - prediction_date: str (YYYY-MM-DD)
        - prediction_type: str ('short_term' or 'long_term')
        - direction: str ('bullish', 'bearish', 'neutral')
        - score: float
        - target_price: float
        - entry_price: float
        - confidence: float
        - reasoning: List[str]
        """
        prediction['id'] = f"{prediction['stock_code']}_{prediction['prediction_date']}_{len(self.predictions)}"
        prediction['recorded_at'] = datetime.now().isoformat()
        prediction['verified'] = False

        self.predictions.append(prediction)
        self._save_predictions()

        logger.info(f"記錄預測: {prediction['stock_code']} - {prediction['direction']}")

    def verify_predictions(self, current_prices: Dict[str, float],
                          days_elapsed: int = 5):
        """
        驗證過期預測

        Args:
            current_prices: {stock_code: current_price}
            days_elapsed: 預測後經過的天數
        """
        today = datetime.now().date()

        for pred in self.predictions:
            if pred.get('verified'):
                continue

            # 檢查是否到驗證時間
            pred_date = datetime.strptime(pred['prediction_date'], '%Y-%m-%d').date()
            if pred['prediction_type'] == 'short_term':
                verify_after = 5  # 短線5天後驗證
            else:
                verify_after = 20  # 長線20天後驗證

            if (today - pred_date).days < verify_after:
                continue

            stock_code = pred['stock_code']
            if stock_code not in current_prices:
                continue

            current_price = current_prices[stock_code]
            entry_price = pred['entry_price']

            # 計算實際報酬
            actual_return = (current_price / entry_price - 1) * 100

            # 判斷預測是否正確
            predicted_direction = pred['direction']
            if predicted_direction == 'bullish':
                is_correct = actual_return > 0
            elif predicted_direction == 'bearish':
                is_correct = actual_return < 0
            else:
                is_correct = abs(actual_return) < 3  # 中性預測，波動小於3%

            # 記錄結果
            result = {
                'prediction_id': pred['id'],
                'stock_code': stock_code,
                'stock_name': pred.get('stock_name', ''),
                'prediction_date': pred['prediction_date'],
                'verify_date': today.isoformat(),
                'predicted_direction': predicted_direction,
                'predicted_score': pred['score'],
                'entry_price': entry_price,
                'exit_price': current_price,
                'actual_return': round(actual_return, 2),
                'is_correct': is_correct,
                'prediction_type': pred['prediction_type']
            }

            self.results.append(result)
            pred['verified'] = True

            logger.info(f"驗證完成: {stock_code} - {'正確' if is_correct else '錯誤'} ({actual_return:.2f}%)")

        self._save_predictions()
        self._save_results()


class BacktestAnalyzer:
    """
    回測分析器
    分析預測績效
    """

    def __init__(self, results: List[Dict]):
        self.results = results
        self.df = pd.DataFrame(results) if results else pd.DataFrame()

    def calculate_accuracy(self, prediction_type: str = None) -> Dict[str, float]:
        """
        計算預測準確率

        Returns:
            {
                'total_predictions': int,
                'correct_predictions': int,
                'accuracy': float,
                'bullish_accuracy': float,
                'bearish_accuracy': float
            }
        """
        if self.df.empty:
            return {'accuracy': 0, 'total_predictions': 0}

        df = self.df
        if prediction_type:
            df = df[df['prediction_type'] == prediction_type]

        if len(df) == 0:
            return {'accuracy': 0, 'total_predictions': 0}

        total = len(df)
        correct = df['is_correct'].sum()
        accuracy = correct / total if total > 0 else 0

        # 分方向計算
        bullish = df[df['predicted_direction'] == 'bullish']
        bullish_acc = bullish['is_correct'].mean() if len(bullish) > 0 else 0

        bearish = df[df['predicted_direction'] == 'bearish']
        bearish_acc = bearish['is_correct'].mean() if len(bearish) > 0 else 0

        return {
            'total_predictions': total,
            'correct_predictions': int(correct),
            'accuracy': round(accuracy, 4),
            'bullish_accuracy': round(bullish_acc, 4),
            'bearish_accuracy': round(bearish_acc, 4)
        }

    def calculate_returns(self, prediction_type: str = None) -> Dict[str, float]:
        """
        計算報酬統計
        """
        if self.df.empty:
            return {}

        df = self.df
        if prediction_type:
            df = df[df['prediction_type'] == prediction_type]

        if len(df) == 0:
            return {}

        returns = df['actual_return']

        # 策略報酬（按預測方向操作）
        strategy_returns = []
        for _, row in df.iterrows():
            if row['predicted_direction'] == 'bullish':
                strategy_returns.append(row['actual_return'])
            elif row['predicted_direction'] == 'bearish':
                strategy_returns.append(-row['actual_return'])

        strategy_returns = np.array(strategy_returns) if strategy_returns else np.array([0])

        return {
            'avg_return': round(returns.mean(), 2),
            'max_return': round(returns.max(), 2),
            'min_return': round(returns.min(), 2),
            'std_return': round(returns.std(), 2),
            'strategy_avg_return': round(strategy_returns.mean(), 2),
            'strategy_total_return': round(strategy_returns.sum(), 2),
            'sharpe_ratio': round(strategy_returns.mean() / strategy_returns.std() * np.sqrt(252/5), 2) if strategy_returns.std() > 0 else 0,
            'win_rate': round((strategy_returns > 0).mean(), 4) if len(strategy_returns) > 0 else 0
        }

    def analyze_by_confidence(self) -> Dict[str, Dict]:
        """
        按信心度分析準確率
        """
        if self.df.empty or 'predicted_score' not in self.df.columns:
            return {}

        results = {}

        # 高信心預測 (>70)
        high_conf = self.df[self.df['predicted_score'] > 70]
        if len(high_conf) > 0:
            results['high_confidence'] = {
                'count': len(high_conf),
                'accuracy': round(high_conf['is_correct'].mean(), 4),
                'avg_return': round(high_conf['actual_return'].mean(), 2)
            }

        # 中信心預測 (50-70)
        mid_conf = self.df[(self.df['predicted_score'] >= 50) & (self.df['predicted_score'] <= 70)]
        if len(mid_conf) > 0:
            results['medium_confidence'] = {
                'count': len(mid_conf),
                'accuracy': round(mid_conf['is_correct'].mean(), 4),
                'avg_return': round(mid_conf['actual_return'].mean(), 2)
            }

        # 低信心預測 (<50)
        low_conf = self.df[self.df['predicted_score'] < 50]
        if len(low_conf) > 0:
            results['low_confidence'] = {
                'count': len(low_conf),
                'accuracy': round(low_conf['is_correct'].mean(), 4),
                'avg_return': round(low_conf['actual_return'].mean(), 2)
            }

        return results

    def get_top_performers(self, n: int = 10) -> List[Dict]:
        """
        獲取表現最好的預測
        """
        if self.df.empty:
            return []

        top = self.df.nlargest(n, 'actual_return')
        return top.to_dict('records')

    def get_worst_performers(self, n: int = 10) -> List[Dict]:
        """
        獲取表現最差的預測
        """
        if self.df.empty:
            return []

        worst = self.df.nsmallest(n, 'actual_return')
        return worst.to_dict('records')


class BacktestReportGenerator:
    """
    回測報告生成器
    生成週報/月報
    """

    def __init__(self, tracker: PredictionTracker):
        self.tracker = tracker

    def generate_weekly_report(self) -> Dict[str, Any]:
        """
        生成週報
        """
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        # 篩選本週結果
        week_results = [
            r for r in self.tracker.results
            if datetime.strptime(r['verify_date'], '%Y-%m-%d').date() >= week_ago
        ]

        analyzer = BacktestAnalyzer(week_results)

        # 計算各項指標
        accuracy = analyzer.calculate_accuracy()
        short_term_acc = analyzer.calculate_accuracy('short_term')
        long_term_acc = analyzer.calculate_accuracy('long_term')
        returns = analyzer.calculate_returns()
        confidence_analysis = analyzer.analyze_by_confidence()

        report = {
            'report_type': 'weekly',
            'report_date': today.isoformat(),
            'period': {
                'start': week_ago.isoformat(),
                'end': today.isoformat()
            },
            'summary': {
                'total_predictions': accuracy['total_predictions'],
                'overall_accuracy': accuracy['accuracy'],
                'short_term_accuracy': short_term_acc.get('accuracy', 0),
                'long_term_accuracy': long_term_acc.get('accuracy', 0)
            },
            'returns': returns,
            'confidence_analysis': confidence_analysis,
            'top_performers': analyzer.get_top_performers(5),
            'worst_performers': analyzer.get_worst_performers(5),
            'recommendations': self._generate_recommendations(accuracy, returns, confidence_analysis)
        }

        return report

    def generate_monthly_report(self) -> Dict[str, Any]:
        """
        生成月報
        """
        today = datetime.now().date()
        month_ago = today - timedelta(days=30)

        # 篩選本月結果
        month_results = [
            r for r in self.tracker.results
            if datetime.strptime(r['verify_date'], '%Y-%m-%d').date() >= month_ago
        ]

        analyzer = BacktestAnalyzer(month_results)

        accuracy = analyzer.calculate_accuracy()
        returns = analyzer.calculate_returns()

        # 按週分析趨勢
        weekly_trend = self._analyze_weekly_trend(month_results)

        report = {
            'report_type': 'monthly',
            'report_date': today.isoformat(),
            'period': {
                'start': month_ago.isoformat(),
                'end': today.isoformat()
            },
            'summary': {
                'total_predictions': accuracy['total_predictions'],
                'overall_accuracy': accuracy['accuracy'],
                'bullish_accuracy': accuracy.get('bullish_accuracy', 0),
                'bearish_accuracy': accuracy.get('bearish_accuracy', 0)
            },
            'returns': returns,
            'weekly_trend': weekly_trend,
            'confidence_analysis': analyzer.analyze_by_confidence(),
            'recommendations': self._generate_recommendations(accuracy, returns, {})
        }

        return report

    def _analyze_weekly_trend(self, results: List[Dict]) -> List[Dict]:
        """分析週趨勢"""
        if not results:
            return []

        df = pd.DataFrame(results)
        df['verify_date'] = pd.to_datetime(df['verify_date'])
        df['week'] = df['verify_date'].dt.isocalendar().week

        weekly_stats = []
        for week, group in df.groupby('week'):
            weekly_stats.append({
                'week': int(week),
                'count': len(group),
                'accuracy': round(group['is_correct'].mean(), 4),
                'avg_return': round(group['actual_return'].mean(), 2)
            })

        return weekly_stats

    def _generate_recommendations(self, accuracy: Dict,
                                  returns: Dict,
                                  confidence_analysis: Dict) -> List[str]:
        """生成優化建議"""
        recommendations = []

        # 基於準確率
        if accuracy.get('accuracy', 0) < 0.5:
            recommendations.append("整體準確率偏低，建議檢視技術指標權重設定")

        if accuracy.get('bullish_accuracy', 0) < accuracy.get('bearish_accuracy', 0):
            recommendations.append("看多預測準確率較低，建議提高看多信號閾值")
        elif accuracy.get('bearish_accuracy', 0) < accuracy.get('bullish_accuracy', 0):
            recommendations.append("看空預測準確率較低，建議提高看空信號閾值")

        # 基於報酬
        if returns.get('strategy_avg_return', 0) < 0:
            recommendations.append("策略平均報酬為負，建議重新評估進出場條件")

        if returns.get('sharpe_ratio', 0) < 0.5:
            recommendations.append("夏普比率偏低，建議增加風險控制機制")

        # 基於信心度
        high_conf = confidence_analysis.get('high_confidence', {})
        low_conf = confidence_analysis.get('low_confidence', {})

        if high_conf.get('accuracy', 0) <= low_conf.get('accuracy', 0):
            recommendations.append("高信心預測準確率未優於低信心，建議調整評分機制")

        if not recommendations:
            recommendations.append("系統運作正常，繼續維持現有策略")

        return recommendations

    def format_report_text(self, report: Dict) -> str:
        """
        格式化報告為文字
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"📊 預測績效{'週報' if report['report_type'] == 'weekly' else '月報'}")
        lines.append(f"報告日期: {report['report_date']}")
        lines.append(f"統計期間: {report['period']['start']} ~ {report['period']['end']}")
        lines.append("=" * 60)

        # 摘要
        summary = report['summary']
        lines.append("\n📈 績效摘要")
        lines.append(f"總預測次數: {summary['total_predictions']}")
        lines.append(f"整體準確率: {summary['overall_accuracy']:.1%}")

        if 'short_term_accuracy' in summary:
            lines.append(f"短線準確率: {summary['short_term_accuracy']:.1%}")
        if 'long_term_accuracy' in summary:
            lines.append(f"長線準確率: {summary['long_term_accuracy']:.1%}")

        # 報酬統計
        if report.get('returns'):
            returns = report['returns']
            lines.append("\n💰 報酬統計")
            lines.append(f"策略平均報酬: {returns.get('strategy_avg_return', 0):.2f}%")
            lines.append(f"策略累計報酬: {returns.get('strategy_total_return', 0):.2f}%")
            lines.append(f"勝率: {returns.get('win_rate', 0):.1%}")
            lines.append(f"夏普比率: {returns.get('sharpe_ratio', 0):.2f}")

        # 信心度分析
        if report.get('confidence_analysis'):
            lines.append("\n🎯 信心度分析")
            for level, stats in report['confidence_analysis'].items():
                level_name = {'high_confidence': '高信心', 'medium_confidence': '中信心', 'low_confidence': '低信心'}.get(level, level)
                lines.append(f"{level_name}: 準確率 {stats['accuracy']:.1%}, 平均報酬 {stats['avg_return']:.2f}%")

        # 優化建議
        if report.get('recommendations'):
            lines.append("\n💡 優化建議")
            for rec in report['recommendations']:
                lines.append(f"• {rec}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)


class AutoBacktestRunner:
    """
    自動回測執行器
    定期執行回測並發送報告
    """

    def __init__(self, data_dir: str = './data/predictions'):
        self.tracker = PredictionTracker(data_dir)
        self.report_generator = BacktestReportGenerator(self.tracker)

    def run_daily_verification(self, current_prices: Dict[str, float]):
        """
        執行每日驗證
        """
        self.tracker.verify_predictions(current_prices)
        logger.info("每日預測驗證完成")

    def generate_and_save_report(self, report_type: str = 'weekly') -> str:
        """
        生成並保存報告

        Returns:
            報告文字內容
        """
        if report_type == 'weekly':
            report = self.report_generator.generate_weekly_report()
        else:
            report = self.report_generator.generate_monthly_report()

        # 保存 JSON
        report_file = os.path.join(
            self.tracker.data_dir,
            f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 生成文字報告
        text_report = self.report_generator.format_report_text(report)

        logger.info(f"{report_type} 報告已生成: {report_file}")

        return text_report

    def get_current_stats(self) -> Dict[str, Any]:
        """
        獲取當前統計資訊
        """
        analyzer = BacktestAnalyzer(self.tracker.results)

        return {
            'total_predictions': len(self.tracker.predictions),
            'verified_predictions': len(self.tracker.results),
            'pending_verification': len([p for p in self.tracker.predictions if not p.get('verified')]),
            'accuracy': analyzer.calculate_accuracy(),
            'returns': analyzer.calculate_returns()
        }


# ==================== 測試 ====================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("📊 回測報告系統測試")
    print("=" * 60)

    # 創建測試數據
    tracker = PredictionTracker('./data/test_predictions')

    # 模擬一些預測
    test_predictions = [
        {
            'stock_code': '2330',
            'stock_name': '台積電',
            'prediction_date': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
            'prediction_type': 'short_term',
            'direction': 'bullish',
            'score': 75,
            'target_price': 600,
            'entry_price': 580,
            'confidence': 0.8,
            'reasoning': ['MACD 金叉', '外資買超']
        },
        {
            'stock_code': '2317',
            'stock_name': '鴻海',
            'prediction_date': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
            'prediction_type': 'short_term',
            'direction': 'bearish',
            'score': 35,
            'target_price': 95,
            'entry_price': 105,
            'confidence': 0.6,
            'reasoning': ['RSI 超買', '成交量萎縮']
        },
        {
            'stock_code': '2454',
            'stock_name': '聯發科',
            'prediction_date': (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d'),
            'prediction_type': 'short_term',
            'direction': 'bullish',
            'score': 68,
            'target_price': 1000,
            'entry_price': 980,
            'confidence': 0.7,
            'reasoning': ['突破均線']
        }
    ]

    for pred in test_predictions:
        tracker.record_prediction(pred)

    print(f"\n記錄了 {len(test_predictions)} 筆預測")

    # 模擬驗證
    current_prices = {
        '2330': 595,  # 上漲
        '2317': 102,  # 下跌
        '2454': 990   # 上漲
    }

    tracker.verify_predictions(current_prices)
    print(f"驗證完成，結果: {len(tracker.results)} 筆")

    # 生成報告
    runner = AutoBacktestRunner('./data/test_predictions')
    report = runner.generate_and_save_report('weekly')
    print("\n" + report)

    # 當前統計
    stats = runner.get_current_stats()
    print("\n當前統計:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
