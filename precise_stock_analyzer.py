"""
precise_stock_analyzer.py - 精準版股票分析系統
提升長線和短線推薦的精準度
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

class PreciseStockAnalyzer:
    """精準版股票分析器"""
    
    def __init__(self):
        """初始化精準分析器"""
        self.logger = logging.getLogger(__name__)
        
        # 精準分析參數
        self.analysis_weights = {
            'short_term': {
                'technical_momentum': 0.45,    # 技術動能
                'volume_analysis': 0.25,       # 成交量分析
                'price_action': 0.20,          # 價格行為
                'market_sentiment': 0.10       # 市場情緒
            },
            'long_term': {
                'fundamental_quality': 0.40,   # 基本面品質
                'financial_stability': 0.25,   # 財務穩定性
                'growth_potential': 0.20,      # 成長潛力
                'valuation_safety': 0.15       # 估值安全邊際
            }
        }
        
        # 精準評分閾值
        self.precision_thresholds = {
            'short_term': {
                'excellent': 8.5,    # 優秀（強烈推薦）
                'good': 6.5,         # 良好（推薦）
                'moderate': 4.5,     # 中等（觀察）
                'weak': 2.5          # 弱勢（避免）
            },
            'long_term': {
                'excellent': 8.0,    # 優秀（強烈推薦）
                'good': 6.0,         # 良好（推薦）
                'moderate': 4.0,     # 中等（定期定額）
                'weak': 2.0          # 弱勢（避免）
            }
        }
    
    def analyze_short_term_precision(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """精準短線分析"""
        
        # 1. 技術動能分析 (45%)
        technical_score = self._analyze_technical_momentum(stock_info)
        
        # 2. 成交量分析 (25%)
        volume_score = self._analyze_volume_patterns(stock_info)
        
        # 3. 價格行為分析 (20%)
        price_score = self._analyze_price_action(stock_info)
        
        # 4. 市場情緒分析 (10%)
        sentiment_score = self._analyze_market_sentiment(stock_info)
        
        # 計算加權總分
        weights = self.analysis_weights['short_term']
        total_score = (
            technical_score * weights['technical_momentum'] +
            volume_score * weights['volume_analysis'] +
            price_score * weights['price_action'] +
            sentiment_score * weights['market_sentiment']
        )
        
        # 精準分級
        grade = self._get_precision_grade(total_score, 'short_term')
        
        return {
            'category': 'short_term',
            'total_score': round(total_score, 2),
            'grade': grade,
            'confidence_level': self._calculate_confidence(stock_info, 'short_term'),
            'components': {
                'technical_momentum': round(technical_score, 2),
                'volume_analysis': round(volume_score, 2),
                'price_action': round(price_score, 2),
                'market_sentiment': round(sentiment_score, 2)
            },
            'signals': self._generate_short_term_signals(stock_info, total_score),
            'risk_factors': self._identify_short_term_risks(stock_info),
            'time_horizon': '1-5 個交易日',
            'action_suggestions': self._get_short_term_actions(total_score, grade)
        }
    
    def analyze_long_term_precision(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """精準長線分析"""
        
        # 1. 基本面品質分析 (40%)
        fundamental_score = self._analyze_fundamental_quality(stock_info)
        
        # 2. 財務穩定性分析 (25%)
        stability_score = self._analyze_financial_stability(stock_info)
        
        # 3. 成長潛力分析 (20%)
        growth_score = self._analyze_growth_potential(stock_info)
        
        # 4. 估值安全邊際分析 (15%)
        valuation_score = self._analyze_valuation_safety(stock_info)
        
        # 計算加權總分
        weights = self.analysis_weights['long_term']
        total_score = (
            fundamental_score * weights['fundamental_quality'] +
            stability_score * weights['financial_stability'] +
            growth_score * weights['growth_potential'] +
            valuation_score * weights['valuation_safety']
        )
        
        # 精準分級
        grade = self._get_precision_grade(total_score, 'long_term')
        
        return {
            'category': 'long_term',
            'total_score': round(total_score, 2),
            'grade': grade,
            'confidence_level': self._calculate_confidence(stock_info, 'long_term'),
            'components': {
                'fundamental_quality': round(fundamental_score, 2),
                'financial_stability': round(stability_score, 2),
                'growth_potential': round(growth_score, 2),
                'valuation_safety': round(valuation_score, 2)
            },
            'investment_thesis': self._generate_investment_thesis(stock_info, total_score),
            'risk_factors': self._identify_long_term_risks(stock_info),
            'time_horizon': '6-24 個月',
            'action_suggestions': self._get_long_term_actions(total_score, grade)
        }
    
    def _analyze_technical_momentum(self, stock_info: Dict[str, Any]) -> float:
        """分析技術動能 (0-10分)"""
        score = 5.0  # 基準分數
        
        # 價格動能
        change_percent = stock_info.get('change_percent', 0)
        if change_percent > 5:
            score += 2.5
        elif change_percent > 3:
            score += 2.0
        elif change_percent > 1:
            score += 1.5
        elif change_percent > 0:
            score += 1.0
        elif change_percent < -3:
            score -= 2.0
        elif change_percent < 0:
            score -= 1.0
        
        # 技術指標加分
        technical_signals = stock_info.get('technical_signals', {})
        if technical_signals.get('macd_golden_cross'):
            score += 1.5
        if technical_signals.get('rsi_healthy'):
            score += 1.0
        if technical_signals.get('ma_golden_cross'):
            score += 1.0
        
        # RSI 狀態
        rsi = stock_info.get('rsi', 50)
        if 40 <= rsi <= 60:
            score += 0.5  # 健康區間
        elif rsi < 30:
            score += 1.0  # 超賣反彈機會
        elif rsi > 70:
            score -= 1.0  # 過熱風險
        
        return max(0, min(10, score))
    
    def _analyze_volume_patterns(self, stock_info: Dict[str, Any]) -> float:
        """分析成交量模式 (0-10分)"""
        score = 5.0
        
        trade_value = stock_info.get('trade_value', 0)
        volume_ratio = stock_info.get('volume_ratio', 1)
        
        # 成交金額評分
        if trade_value > 5000000000:  # 50億以上
            score += 2.5
        elif trade_value > 1000000000:  # 10億以上
            score += 2.0
        elif trade_value > 500000000:   # 5億以上
            score += 1.5
        elif trade_value > 100000000:   # 1億以上
            score += 1.0
        elif trade_value < 50000000:    # 5000萬以下
            score -= 1.0
        
        # 成交量比率
        if volume_ratio > 3:
            score += 2.0  # 爆量
        elif volume_ratio > 2:
            score += 1.5  # 放量
        elif volume_ratio > 1.5:
            score += 1.0  # 溫和放量
        elif volume_ratio < 0.5:
            score -= 1.5  # 量縮
        
        return max(0, min(10, score))
    
    def _analyze_price_action(self, stock_info: Dict[str, Any]) -> float:
        """分析價格行為 (0-10分)"""
        score = 5.0
        
        current_price = stock_info.get('current_price', 0)
        change_percent = stock_info.get('change_percent', 0)
        
        # 價格強度
        if abs(change_percent) > 5:
            if change_percent > 0:
                score += 2.0  # 強勁上漲
            else:
                score -= 2.0  # 急劇下跌
        elif abs(change_percent) > 3:
            if change_percent > 0:
                score += 1.5
            else:
                score -= 1.5
        
        # 價格位置（假設有高低點數據）
        # 這裡可以加入更多價格行為分析
        
        return max(0, min(10, score))
    
    def _analyze_market_sentiment(self, stock_info: Dict[str, Any]) -> float:
        """分析市場情緒 (0-10分)"""
        score = 5.0
        
        # 法人動向
        foreign_net_buy = stock_info.get('foreign_net_buy', 0)
        trust_net_buy = stock_info.get('trust_net_buy', 0)
        
        if foreign_net_buy > 50000:  # 5億以上
            score += 2.0
        elif foreign_net_buy > 10000:  # 1億以上
            score += 1.5
        elif foreign_net_buy > 0:
            score += 1.0
        elif foreign_net_buy < -50000:
            score -= 2.0
        elif foreign_net_buy < 0:
            score -= 1.0
        
        if trust_net_buy > 20000:  # 2億以上
            score += 1.0
        elif trust_net_buy < -20000:
            score -= 1.0
        
        return max(0, min(10, score))
    
    def _analyze_fundamental_quality(self, stock_info: Dict[str, Any]) -> float:
        """分析基本面品質 (0-10分)"""
        score = 5.0
        
        # ROE 評分
        roe = stock_info.get('roe', 0)
        if roe > 20:
            score += 2.5
        elif roe > 15:
            score += 2.0
        elif roe > 10:
            score += 1.5
        elif roe > 5:
            score += 1.0
        elif roe < 5:
            score -= 1.0
        
        # ROA (如果有的話)
        roa = stock_info.get('roa', 0)
        if roa > 10:
            score += 1.0
        elif roa > 5:
            score += 0.5
        
        # 毛利率 (如果有的話)
        gross_margin = stock_info.get('gross_margin', 0)
        if gross_margin > 30:
            score += 1.0
        elif gross_margin > 20:
            score += 0.5
        
        return max(0, min(10, score))
    
    def _analyze_financial_stability(self, stock_info: Dict[str, Any]) -> float:
        """分析財務穩定性 (0-10分)"""
        score = 5.0
        
        # 負債比率
        debt_ratio = stock_info.get('debt_ratio', 50)
        if debt_ratio < 30:
            score += 2.0
        elif debt_ratio < 50:
            score += 1.0
        elif debt_ratio > 70:
            score -= 2.0
        elif debt_ratio > 60:
            score -= 1.0
        
        # 流動比率
        current_ratio = stock_info.get('current_ratio', 100)
        if current_ratio > 200:
            score += 1.5
        elif current_ratio > 150:
            score += 1.0
        elif current_ratio < 100:
            score -= 2.0
        
        # 連續配息年數
        dividend_years = stock_info.get('dividend_consecutive_years', 0)
        if dividend_years > 10:
            score += 2.0
        elif dividend_years > 5:
            score += 1.5
        elif dividend_years > 3:
            score += 1.0
        
        return max(0, min(10, score))
    
    def _analyze_growth_potential(self, stock_info: Dict[str, Any]) -> float:
        """分析成長潛力 (0-10分)"""
        score = 5.0
        
        # EPS 成長率
        eps_growth = stock_info.get('eps_growth', 0)
        if eps_growth > 30:
            score += 3.0
        elif eps_growth > 20:
            score += 2.5
        elif eps_growth > 15:
            score += 2.0
        elif eps_growth > 10:
            score += 1.5
        elif eps_growth > 5:
            score += 1.0
        elif eps_growth < 0:
            score -= 2.0
        
        # 營收成長率
        revenue_growth = stock_info.get('revenue_growth', 0)
        if revenue_growth > 20:
            score += 2.0
        elif revenue_growth > 10:
            score += 1.5
        elif revenue_growth > 5:
            score += 1.0
        elif revenue_growth < 0:
            score -= 1.5
        
        return max(0, min(10, score))
    
    def _analyze_valuation_safety(self, stock_info: Dict[str, Any]) -> float:
        """分析估值安全邊際 (0-10分)"""
        score = 5.0
        
        # 本益比
        pe_ratio = stock_info.get('pe_ratio', 999)
        if pe_ratio < 10:
            score += 2.5
        elif pe_ratio < 15:
            score += 2.0
        elif pe_ratio < 20:
            score += 1.0
        elif pe_ratio > 30:
            score -= 2.0
        elif pe_ratio > 25:
            score -= 1.0
        
        # 股價淨值比
        pb_ratio = stock_info.get('pb_ratio', 999)
        if pb_ratio < 1.5:
            score += 1.5
        elif pb_ratio < 2.0:
            score += 1.0
        elif pb_ratio > 3.0:
            score -= 1.5
        
        # 殖利率
        dividend_yield = stock_info.get('dividend_yield', 0)
        if dividend_yield > 5:
            score += 2.0
        elif dividend_yield > 3:
            score += 1.5
        elif dividend_yield > 2:
            score += 1.0
        
        return max(0, min(10, score))
    
    def _get_precision_grade(self, score: float, category: str) -> str:
        """獲取精準分級"""
        thresholds = self.precision_thresholds[category]
        
        if score >= thresholds['excellent']:
            return 'A+'
        elif score >= thresholds['good']:
            return 'A'
        elif score >= thresholds['moderate']:
            return 'B'
        elif score >= thresholds['weak']:
            return 'C'
        else:
            return 'D'
    
    def _calculate_confidence(self, stock_info: Dict[str, Any], category: str) -> float:
        """計算信心指數 (0-100%)"""
        base_confidence = 50.0
        
        # 數據完整性
        data_fields = ['close', 'volume', 'trade_value', 'change_percent']
        available_fields = sum(1 for field in data_fields if stock_info.get(field) is not None)
        data_completeness = (available_fields / len(data_fields)) * 30
        
        # 成交量信心度
        trade_value = stock_info.get('trade_value', 0)
        if trade_value > 1000000000:
            volume_confidence = 20
        elif trade_value > 100000000:
            volume_confidence = 15
        elif trade_value > 50000000:
            volume_confidence = 10
        else:
            volume_confidence = 5
        
        total_confidence = base_confidence + data_completeness + volume_confidence
        return min(100, max(0, total_confidence))
    
    def _generate_short_term_signals(self, stock_info: Dict[str, Any], score: float) -> List[str]:
        """生成短線交易信號"""
        signals = []
        
        if score >= 8.5:
            signals.append("強烈買入信號")
        elif score >= 6.5:
            signals.append("買入信號")
        elif score >= 4.5:
            signals.append("觀察信號")
        else:
            signals.append("避免信號")
        
        # 具體信號
        change_percent = stock_info.get('change_percent', 0)
        volume_ratio = stock_info.get('volume_ratio', 1)
        
        if change_percent > 3 and volume_ratio > 2:
            signals.append("放量突破")
        
        if stock_info.get('technical_signals', {}).get('macd_golden_cross'):
            signals.append("MACD金叉")
        
        return signals
    
    def _generate_investment_thesis(self, stock_info: Dict[str, Any], score: float) -> str:
        """生成投資論點"""
        name = stock_info.get('name', '該股票')
        
        if score >= 8.0:
            return f"{name}基本面優異，具備長期投資價值，建議逢低分批布局"
        elif score >= 6.0:
            return f"{name}基本面良好，適合中長期投資，可考慮定期定額"
        elif score >= 4.0:
            return f"{name}基本面尚可，可作為投資組合一部分，需持續觀察"
        else:
            return f"{name}基本面偏弱，不建議長期投資"
    
    def _identify_short_term_risks(self, stock_info: Dict[str, Any]) -> List[str]:
        """識別短線風險"""
        risks = []
        
        rsi = stock_info.get('rsi', 50)
        if rsi > 80:
            risks.append("技術指標過熱")
        
        volume_ratio = stock_info.get('volume_ratio', 1)
        if volume_ratio < 0.5:
            risks.append("成交量萎縮")
        
        change_percent = stock_info.get('change_percent', 0)
        if change_percent < -5:
            risks.append("價格急跌風險")
        
        return risks
    
    def _identify_long_term_risks(self, stock_info: Dict[str, Any]) -> List[str]:
        """識別長線風險"""
        risks = []
        
        debt_ratio = stock_info.get('debt_ratio', 50)
        if debt_ratio > 70:
            risks.append("負債比率過高")
        
        eps_growth = stock_info.get('eps_growth', 0)
        if eps_growth < 0:
            risks.append("獲利能力下滑")
        
        pe_ratio = stock_info.get('pe_ratio', 15)
        if pe_ratio > 30:
            risks.append("估值偏高風險")
        
        return risks
    
    def _get_short_term_actions(self, score: float, grade: str) -> Dict[str, Any]:
        """獲取短線操作建議"""
        if grade == 'A+':
            return {
                'action': '積極買入',
                'position_size': '較大部位',
                'stop_loss': '3-5%',
                'profit_target': '8-12%',
                'holding_period': '1-5天'
            }
        elif grade == 'A':
            return {
                'action': '買入',
                'position_size': '中等部位',
                'stop_loss': '5%',
                'profit_target': '6-10%',
                'holding_period': '3-7天'
            }
        elif grade == 'B':
            return {
                'action': '觀察',
                'position_size': '小部位',
                'stop_loss': '5%',
                'profit_target': '5-8%',
                'holding_period': '視情況而定'
            }
        else:
            return {
                'action': '避免',
                'position_size': '0',
                'stop_loss': 'N/A',
                'profit_target': 'N/A',
                'holding_period': 'N/A'
            }
    
    def _get_long_term_actions(self, score: float, grade: str) -> Dict[str, Any]:
        """獲取長線投資建議"""
        if grade == 'A+':
            return {
                'action': '重點配置',
                'position_size': '核心持股',
                'entry_strategy': '分批進場',
                'rebalance_frequency': '季度檢視',
                'holding_period': '12-24個月'
            }
        elif grade == 'A':
            return {
                'action': '配置',
                'position_size': '標準持股',
                'entry_strategy': '逢低買進',
                'rebalance_frequency': '半年檢視',
                'holding_period': '6-18個月'
            }
        elif grade == 'B':
            return {
                'action': '定期定額',
                'position_size': '小額持股',
                'entry_strategy': '定期定額',
                'rebalance_frequency': '年度檢視',
                'holding_period': '6-12個月'
            }
        else:
            return {
                'action': '避免',
                'position_size': '0',
                'entry_strategy': 'N/A',
                'rebalance_frequency': 'N/A',
                'holding_period': 'N/A'
            }

# 使用範例
def demo_precision_analysis():
    """示範精準分析"""
    analyzer = PreciseStockAnalyzer()
    
    # 測試股票數據
    test_stock = {
        'code': '2330',
        'name': '台積電',
        'current_price': 638.0,
        'change_percent': 2.5,
        'volume': 25000000,
        'trade_value': 15950000000,
        'volume_ratio': 1.8,
        'rsi': 58,
        'technical_signals': {
            'macd_golden_cross': True,
            'rsi_healthy': True,
            'ma_golden_cross': False
        },
        'dividend_yield': 2.1,
        'eps_growth': 12.5,
        'pe_ratio': 18.2,
        'roe': 23.1,
        'foreign_net_buy': 25000,
        'trust_net_buy': 8000,
        'debt_ratio': 25,
        'current_ratio': 180,
        'dividend_consecutive_years': 15
    }
    
    # 短線分析
    short_analysis = analyzer.analyze_short_term_precision(test_stock)
    print("=== 短線精準分析 ===")
    print(f"總分: {short_analysis['total_score']}/10")
    print(f"等級: {short_analysis['grade']}")
    print(f"信心度: {short_analysis['confidence_level']:.1f}%")
    print(f"操作建議: {short_analysis['action_suggestions']['action']}")
    
    # 長線分析
    long_analysis = analyzer.analyze_long_term_precision(test_stock)
    print("\n=== 長線精準分析 ===")
    print(f"總分: {long_analysis['total_score']}/10")
    print(f"等級: {long_analysis['grade']}")
    print(f"信心度: {long_analysis['confidence_level']:.1f}%")
    print(f"投資論點: {long_analysis['investment_thesis']}")

if __name__ == "__main__":
    demo_precision_analysis()
