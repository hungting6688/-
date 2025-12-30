"""
comprehensive_stock_analyzer.py - 股票綜合分析系統
整合多種分析方法的完整股票分析模組

包含功能：
1. 基礎技術分析 (StockAnalyzer)
2. 增強版分析系統 (EnhancedStockAnalyzer) 
3. 精準版分析系統 (PreciseStockAnalyzer)
4. 分析整合器 (StockAnalyzerIntegrator)
5. 統一接口 (ComprehensiveStockAnalyzer)
"""

import os
import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

# 配置日誌
logger = logging.getLogger(__name__)

# ==================== 基礎技術分析器 ====================

class StockAnalyzer:
    """股票技術分析器 - 基礎版"""
    
    def __init__(self):
        """初始化分析器"""
        self.rsi_period = 14
        self.ma_short = 5
        self.ma_medium = 20
        self.ma_long = 60
        self.volume_ma = 5
        
    def analyze_single_stock(self, stock_data: Dict, historical_data: pd.DataFrame = None) -> Dict:
        """分析單支股票"""
        analysis = {
            'code': stock_data['code'],
            'name': stock_data['name'],
            'close': stock_data['close'],
            'change': stock_data.get('change', 0),
            'change_percent': stock_data.get('change_percent', 0),
            'volume': stock_data['volume'],
            'trade_value': stock_data['trade_value'],
            'signals': [],
            'patterns': [],
            'indicators': {},
            'score': 0
        }
        
        if historical_data is not None and len(historical_data) > 0:
            indicators = self._calculate_indicators(historical_data)
            analysis['indicators'] = indicators
            
            patterns = self._identify_patterns(historical_data, indicators)
            analysis['patterns'] = patterns
            
            signals = self._generate_signals(stock_data, indicators, patterns)
            analysis['signals'] = signals
            
            score = self._calculate_score(indicators, patterns, signals)
            analysis['score'] = score
        
        return analysis
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """計算技術指標"""
        indicators = {}
        
        if len(df) >= self.ma_short:
            indicators['ma5'] = df['close'].rolling(window=self.ma_short).mean().iloc[-1]
        
        if len(df) >= self.ma_medium:
            indicators['ma20'] = df['close'].rolling(window=self.ma_medium).mean().iloc[-1]
        
        if len(df) >= self.ma_long:
            indicators['ma60'] = df['close'].rolling(window=self.ma_long).mean().iloc[-1]
        
        if len(df) >= self.rsi_period + 1:
            rsi = self._calculate_rsi(df['close'], self.rsi_period)
            if len(rsi) > 0:
                indicators['rsi'] = rsi.iloc[-1]
        
        if len(df) >= 26:
            macd, signal, histogram = self._calculate_macd(df['close'])
            if len(macd) > 0:
                indicators['macd'] = macd.iloc[-1]
                indicators['macd_signal'] = signal.iloc[-1]
                indicators['macd_histogram'] = histogram.iloc[-1]
        
        if len(df) >= self.volume_ma:
            indicators['volume_ma'] = df['volume'].rolling(window=self.volume_ma).mean().iloc[-1]
            indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_ma']
        
        return indicators
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """計算MACD指標"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return macd, signal, histogram
    
    def _identify_patterns(self, df: pd.DataFrame, indicators: Dict) -> List[str]:
        """識別技術形態"""
        patterns = []
        
        if len(df) < 2:
            return patterns
        
        current_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        
        if 'ma20' in indicators and current_close > indicators['ma20'] and prev_close <= indicators['ma20']:
            patterns.append('突破20日均線')
        
        if 'ma60' in indicators and current_close > indicators['ma60'] and prev_close <= indicators['ma60']:
            patterns.append('突破60日均線')
        
        if 'volume_ratio' in indicators and indicators['volume_ratio'] > 2:
            patterns.append('成交量突破')
        
        if 'rsi' in indicators:
            if indicators['rsi'] > 70:
                patterns.append('RSI超買')
            elif indicators['rsi'] < 30:
                patterns.append('RSI超賣')
        
        return patterns
    
    def _generate_signals(self, stock_data: Dict, indicators: Dict, patterns: List[str]) -> List[str]:
        """生成交易信號"""
        signals = []
        
        if '突破20日均線' in patterns and '成交量突破' in patterns:
            signals.append('強勢突破信號')
        
        if 'RSI超賣' in patterns:
            signals.append('超賣反彈信號')
        
        if stock_data.get('change_percent', 0) > 5 and indicators.get('volume_ratio', 1) > 2:
            signals.append('強勢上漲信號')
        
        return signals
    
    def _calculate_score(self, indicators: Dict, patterns: List[str], signals: List[str]) -> float:
        """計算綜合評分（0-100）"""
        score = 50
        
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if 30 <= rsi <= 70:
                score += 5
            elif rsi < 30:
                score += 10
            else:
                score -= 5
        
        positive_patterns = ['突破20日均線', '突破60日均線', '成交量突破']
        for pattern in patterns:
            if pattern in positive_patterns:
                score += 5
        
        positive_signals = ['強勢突破信號', '超賣反彈信號', '強勢上漲信號']
        for signal in signals:
            if signal in positive_signals:
                score += 8
        
        return max(0, min(100, score))

# ==================== 增強版分析器 ====================

class EnhancedStockAnalyzer:
    """增強版股票分析器 - 添加基本面與技術面指標"""
    
    def __init__(self):
        """初始化分析器"""
        self.weight_configs = {
            'short_term': {
                'base_score': 1.0,
                'technical': 0.8,
                'fundamental': 0.2,
                'institutional': 0.3
            },
            'long_term': {
                'base_score': 0.6,
                'technical': 0.4,
                'fundamental': 0.8,
                'institutional': 0.6
            }
        }
        self.data_cache = {}
        self.cache_expire_minutes = 30
    
    def analyze_stock_enhanced(self, stock_info: Dict[str, Any], analysis_type: str = 'mixed') -> Dict[str, Any]:
        """增強版股票分析"""
        stock_code = stock_info['code']
        
        try:
            base_analysis = self._get_base_analysis(stock_info)
            technical_analysis = self._get_technical_analysis(stock_code, stock_info)
            fundamental_analysis = self._get_fundamental_analysis(stock_code)
            institutional_analysis = self._get_institutional_analysis(stock_code)
            
            final_analysis = self._combine_analysis(
                base_analysis, technical_analysis, fundamental_analysis, 
                institutional_analysis, analysis_type
            )
            
            return final_analysis
            
        except Exception as e:
            logger.error(f"增強分析失敗，返回基礎分析: {stock_code} - {e}")
            return self._get_base_analysis(stock_info)
    
    def _get_base_analysis(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """獲取基礎快速分析"""
        stock_code = stock_info['code']
        stock_name = stock_info['name']
        current_price = stock_info['close']
        change_percent = stock_info['change_percent']
        volume = stock_info['volume']
        trade_value = stock_info['trade_value']
        
        base_score = 0
        
        # 價格變動評分
        if change_percent > 5:
            base_score += 4
        elif change_percent > 3:
            base_score += 3
        elif change_percent > 1:
            base_score += 2
        elif change_percent > 0:
            base_score += 1
        elif change_percent < -5:
            base_score -= 4
        elif change_percent < -3:
            base_score -= 3
        elif change_percent < -1:
            base_score -= 2
        elif change_percent < 0:
            base_score -= 1
        
        # 成交量評分
        if trade_value > 5000000000:
            base_score += 2
        elif trade_value > 1000000000:
            base_score += 1
        elif trade_value < 10000000:
            base_score -= 1
        
        # 特殊行業加權
        if any(keyword in stock_name for keyword in ['航運', '海運', '長榮', '陽明', '萬海']):
            base_score += 0.5
        elif any(keyword in stock_name for keyword in ['台積電', '聯發科', '鴻海']):
            base_score += 0.5
        
        return {
            'code': stock_code,
            'name': stock_name,
            'current_price': current_price,
            'change_percent': round(change_percent, 1),
            'volume': volume,
            'trade_value': trade_value,
            'base_score': round(base_score, 1),
            'analysis_components': {
                'base': True,
                'technical': False,
                'fundamental': False,
                'institutional': False
            }
        }
    
    def _get_technical_analysis(self, stock_code: str, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """獲取技術面分析"""
        try:
            cache_key = f"technical_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            technical_data = self._fetch_simple_technical_data(stock_code, stock_info)
            
            if not technical_data:
                return {'available': False}
            
            tech_score = 0
            signals = {}
            
            # MA 信號分析
            if 'ma_signals' in technical_data:
                ma_data = technical_data['ma_signals']
                if ma_data.get('price_above_ma5'):
                    tech_score += 1
                    signals['ma5_bullish'] = True
                if ma_data.get('price_above_ma20'):
                    tech_score += 1.5
                    signals['ma20_bullish'] = True
                if ma_data.get('ma5_above_ma20'):
                    tech_score += 1
                    signals['ma_golden_cross'] = True
            
            # MACD 信號分析
            if 'macd_signals' in technical_data:
                macd_data = technical_data['macd_signals']
                if macd_data.get('macd_above_signal'):
                    tech_score += 2
                    signals['macd_bullish'] = True
                if macd_data.get('macd_golden_cross'):
                    tech_score += 2.5
                    signals['macd_golden_cross'] = True
            
            # RSI 信號分析
            if 'rsi_signals' in technical_data:
                rsi_data = technical_data['rsi_signals']
                rsi_value = rsi_data.get('rsi_value', 50)
                
                if 30 <= rsi_value <= 70:
                    tech_score += 1
                    signals['rsi_healthy'] = True
                elif rsi_value < 30:
                    tech_score += 1.5
                    signals['rsi_oversold'] = True
                elif rsi_value > 70:
                    tech_score -= 1
                    signals['rsi_overbought'] = True
            
            result = {
                'available': True,
                'tech_score': round(tech_score, 1),
                'signals': signals,
                'raw_data': technical_data
            }
            
            self.data_cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"獲取技術面數據失敗: {stock_code} - {e}")
            return {'available': False}
    
    def _fetch_simple_technical_data(self, stock_code: str, stock_info: Dict[str, Any]) -> Optional[Dict]:
        """獲取簡化的技術指標數據"""
        try:
            current_price = stock_info['close']
            change_percent = stock_info['change_percent']
            
            simulated_data = {
                'ma_signals': {
                    'price_above_ma5': change_percent > 0,
                    'price_above_ma20': change_percent > 1,
                    'ma5_above_ma20': change_percent > 2
                },
                'macd_signals': {
                    'macd_above_signal': change_percent > 1.5,
                    'macd_golden_cross': change_percent > 3
                },
                'rsi_signals': {
                    'rsi_value': min(max(50 + change_percent * 5, 10), 90)
                }
            }
            
            return simulated_data
            
        except Exception as e:
            logger.error(f"模擬技術數據失敗: {stock_code}")
            return None
    
    def _get_fundamental_analysis(self, stock_code: str) -> Dict[str, Any]:
        """獲取基本面分析"""
        try:
            cache_key = f"fundamental_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            fundamental_data = self._fetch_fundamental_data(stock_code)
            
            if not fundamental_data:
                return {'available': False}
            
            fund_score = 0
            
            # 殖利率評分
            dividend_yield = fundamental_data.get('dividend_yield', 0)
            if dividend_yield > 5:
                fund_score += 2.5
            elif dividend_yield > 3:
                fund_score += 2
            elif dividend_yield > 1:
                fund_score += 1
            
            # EPS 成長評分
            eps_growth = fundamental_data.get('eps_growth', 0)
            if eps_growth > 20:
                fund_score += 3
            elif eps_growth > 10:
                fund_score += 2
            elif eps_growth > 5:
                fund_score += 1
            elif eps_growth < 0:
                fund_score -= 2
            
            # PE 比率評分
            pe_ratio = fundamental_data.get('pe_ratio', 999)
            if pe_ratio < 10:
                fund_score += 2
            elif pe_ratio < 15:
                fund_score += 1
            elif pe_ratio > 30:
                fund_score -= 1
            
            # ROE 評分
            roe = fundamental_data.get('roe', 0)
            if roe > 20:
                fund_score += 2
            elif roe > 15:
                fund_score += 1
            elif roe < 5:
                fund_score -= 1
            
            result = {
                'available': True,
                'fund_score': round(fund_score, 1),
                'dividend_yield': dividend_yield,
                'eps_growth': eps_growth,
                'pe_ratio': pe_ratio,
                'roe': roe
            }
            
            self.data_cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"獲取基本面數據失敗: {stock_code} - {e}")
            return {'available': False}
    
    def _fetch_fundamental_data(self, stock_code: str) -> Optional[Dict]:
        """獲取基本面數據"""
        try:
            mock_data = {
                '2330': {'dividend_yield': 2.1, 'eps_growth': 12.5, 'pe_ratio': 18.2, 'roe': 23.1},
                '2317': {'dividend_yield': 4.2, 'eps_growth': 8.3, 'pe_ratio': 12.1, 'roe': 15.6},
                '2454': {'dividend_yield': 2.8, 'eps_growth': 15.2, 'pe_ratio': 16.8, 'roe': 19.3},
                '2609': {'dividend_yield': 6.8, 'eps_growth': 25.6, 'pe_ratio': 8.9, 'roe': 12.4},
                '2615': {'dividend_yield': 5.2, 'eps_growth': 31.2, 'pe_ratio': 7.3, 'roe': 18.7},
                '2603': {'dividend_yield': 4.9, 'eps_growth': 22.1, 'pe_ratio': 9.8, 'roe': 14.2}
            }
            
            return mock_data.get(stock_code, {
                'dividend_yield': 2.5,
                'eps_growth': 5.0,
                'pe_ratio': 20.0,
                'roe': 12.0
            })
            
        except Exception as e:
            logger.error(f"模擬基本面數據失敗: {stock_code}")
            return None
    
    def _get_institutional_analysis(self, stock_code: str) -> Dict[str, Any]:
        """獲取法人買賣分析"""
        try:
            cache_key = f"institutional_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            institutional_data = self._fetch_institutional_data(stock_code)
            
            if not institutional_data:
                return {'available': False}
            
            inst_score = 0
            
            # 外資買賣評分
            foreign_net = institutional_data.get('foreign_net_buy', 0)
            if foreign_net > 50000:
                inst_score += 3
            elif foreign_net > 10000:
                inst_score += 2
            elif foreign_net > 0:
                inst_score += 1
            elif foreign_net < -50000:
                inst_score -= 3
            elif foreign_net < -10000:
                inst_score -= 2
            elif foreign_net < 0:
                inst_score -= 1
            
            # 投信買賣評分
            trust_net = institutional_data.get('trust_net_buy', 0)
            if trust_net > 10000:
                inst_score += 2
            elif trust_net > 1000:
                inst_score += 1
            elif trust_net < -10000:
                inst_score -= 2
            elif trust_net < -1000:
                inst_score -= 1
            
            result = {
                'available': True,
                'inst_score': round(inst_score, 1),
                'foreign_net_buy': foreign_net,
                'trust_net_buy': trust_net,
                'dealer_net_buy': institutional_data.get('dealer_net_buy', 0)
            }
            
            self.data_cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"獲取法人數據失敗: {stock_code} - {e}")
            return {'available': False}
    
    def _fetch_institutional_data(self, stock_code: str) -> Optional[Dict]:
        """獲取法人買賣數據"""
        try:
            import random
            
            base_amount = random.randint(-100000, 100000)
            
            return {
                'foreign_net_buy': base_amount + random.randint(-20000, 20000),
                'trust_net_buy': random.randint(-50000, 50000),
                'dealer_net_buy': random.randint(-20000, 20000)
            }
            
        except Exception as e:
            logger.error(f"模擬法人數據失敗: {stock_code}")
            return None
    
    def _combine_analysis(self, base_analysis: Dict, technical_analysis: Dict, 
                         fundamental_analysis: Dict, institutional_analysis: Dict,
                         analysis_type: str) -> Dict[str, Any]:
        """綜合所有分析結果"""
        
        if analysis_type == 'short_term':
            weights = self.weight_configs['short_term']
        elif analysis_type == 'long_term':
            weights = self.weight_configs['long_term']
        else:
            weights = {
                'base_score': 0.8,
                'technical': 0.6,
                'fundamental': 0.5,
                'institutional': 0.4
            }
        
        final_score = base_analysis['base_score'] * weights['base_score']
        
        if technical_analysis.get('available'):
            tech_contribution = technical_analysis['tech_score'] * weights['technical']
            final_score += tech_contribution
            base_analysis['analysis_components']['technical'] = True
            base_analysis['technical_score'] = technical_analysis['tech_score']
            base_analysis['technical_signals'] = technical_analysis['signals']
        
        if fundamental_analysis.get('available'):
            fund_contribution = fundamental_analysis['fund_score'] * weights['fundamental']
            final_score += fund_contribution
            base_analysis['analysis_components']['fundamental'] = True
            base_analysis['fundamental_score'] = fundamental_analysis['fund_score']
            base_analysis['dividend_yield'] = fundamental_analysis['dividend_yield']
            base_analysis['eps_growth'] = fundamental_analysis['eps_growth']
            base_analysis['pe_ratio'] = fundamental_analysis['pe_ratio']
            base_analysis['roe'] = fundamental_analysis['roe']
        
        if institutional_analysis.get('available'):
            inst_contribution = institutional_analysis['inst_score'] * weights['institutional']
            final_score += inst_contribution
            base_analysis['analysis_components']['institutional'] = True
            base_analysis['institutional_score'] = institutional_analysis['inst_score']
            base_analysis['foreign_net_buy'] = institutional_analysis['foreign_net_buy']
            base_analysis['trust_net_buy'] = institutional_analysis['trust_net_buy']
        
        base_analysis['weighted_score'] = round(final_score, 1)
        base_analysis['analysis_type'] = analysis_type
        
        # 根據最終得分確定趨勢和建議
        if final_score >= 8:
            trend = "強烈看漲"
            suggestion = "適合積極買入"
            target_price = round(base_analysis['current_price'] * 1.10, 1)
            stop_loss = round(base_analysis['current_price'] * 0.95, 1)
        elif final_score >= 4:
            trend = "看漲"
            suggestion = "可考慮買入"
            target_price = round(base_analysis['current_price'] * 1.06, 1)
            stop_loss = round(base_analysis['current_price'] * 0.97, 1)
        elif final_score >= 1:
            trend = "中性偏多"
            suggestion = "適合中長期投資"
            target_price = round(base_analysis['current_price'] * 1.08, 1)
            stop_loss = round(base_analysis['current_price'] * 0.95, 1)
        elif final_score > -1:
            trend = "中性"
            suggestion = "觀望為宜"
            target_price = None
            stop_loss = round(base_analysis['current_price'] * 0.95, 1)
        elif final_score >= -4:
            trend = "看跌"
            suggestion = "建議減碼"
            target_price = None
            stop_loss = round(base_analysis['current_price'] * 0.97, 1)
        else:
            trend = "強烈看跌"
            suggestion = "建議賣出"
            target_price = None
            stop_loss = round(base_analysis['current_price'] * 0.98, 1)
        
        base_analysis['trend'] = trend
        base_analysis['suggestion'] = suggestion
        base_analysis['target_price'] = target_price
        base_analysis['stop_loss'] = stop_loss
        base_analysis['analysis_time'] = datetime.now().isoformat()
        base_analysis['reason'] = self._generate_enhanced_reason(base_analysis)
        
        return base_analysis
    
    def _generate_enhanced_reason(self, analysis: Dict[str, Any]) -> str:
        """生成增強的推薦理由"""
        reasons = []
        
        change_percent = analysis['change_percent']
        if abs(change_percent) > 3:
            reasons.append(f"今日{'大漲' if change_percent > 0 else '大跌'} {abs(change_percent):.1f}%")
        elif abs(change_percent) > 1:
            reasons.append(f"今日{'上漲' if change_percent > 0 else '下跌'} {abs(change_percent):.1f}%")
        
        if analysis['analysis_components'].get('technical'):
            signals = analysis.get('technical_signals', {})
            if signals.get('macd_golden_cross'):
                reasons.append("MACD出現黃金交叉")
            elif signals.get('macd_bullish'):
                reasons.append("MACD指標轉強")
            
            if signals.get('ma_golden_cross'):
                reasons.append("均線呈多頭排列")
            elif signals.get('ma20_bullish'):
                reasons.append("站穩20日均線")
            
            if signals.get('rsi_oversold'):
                reasons.append("RSI顯示超賣反彈")
            elif signals.get('rsi_healthy'):
                reasons.append("RSI處於健康區間")
        
        if analysis['analysis_components'].get('fundamental'):
            dividend_yield = analysis.get('dividend_yield', 0)
            eps_growth = analysis.get('eps_growth', 0)
            
            if dividend_yield > 4:
                reasons.append(f"高殖利率 {dividend_yield:.1f}%")
            if eps_growth > 15:
                reasons.append(f"EPS高成長 {eps_growth:.1f}%")
            elif eps_growth > 10:
                reasons.append(f"EPS穩定成長 {eps_growth:.1f}%")
        
        if analysis['analysis_components'].get('institutional'):
            foreign_net = analysis.get('foreign_net_buy', 0)
            if foreign_net > 50000:
                reasons.append("外資大幅買超")
            elif foreign_net > 10000:
                reasons.append("外資持續買超")
            elif foreign_net < -50000:
                reasons.append("外資大幅賣超")
        
        if analysis['trade_value'] > 5000000000:
            reasons.append("成交金額龐大")
        elif analysis['trade_value'] > 1000000000:
            reasons.append("成交活躍")
        
        return "、".join(reasons) if reasons else "綜合指標顯示投資機會"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查快取是否有效"""
        if cache_key not in self.data_cache:
            return False
        
        cache_data = self.data_cache[cache_key]
        if isinstance(cache_data, dict) and 'timestamp' in cache_data:
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if (datetime.now() - cache_time).total_seconds() > self.cache_expire_minutes * 60:
                return False
        
        return True

# ==================== 精準版分析器 ====================

class PreciseStockAnalyzer:
    """精準版股票分析器"""
    
    def __init__(self):
        """初始化精準分析器"""
        self.analysis_weights = {
            'short_term': {
                'technical_momentum': 0.45,
                'volume_analysis': 0.25,
                'price_action': 0.20,
                'market_sentiment': 0.10
            },
            'long_term': {
                'fundamental_quality': 0.40,
                'financial_stability': 0.25,
                'growth_potential': 0.20,
                'valuation_safety': 0.15
            }
        }
        
        self.precision_thresholds = {
            'short_term': {
                'excellent': 8.5,
                'good': 6.5,
                'moderate': 4.5,
                'weak': 2.5
            },
            'long_term': {
                'excellent': 8.0,
                'good': 6.0,
                'moderate': 4.0,
                'weak': 2.0
            }
        }
    
    def analyze_short_term_precision(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """精準短線分析"""
        
        technical_score = self._analyze_technical_momentum(stock_info)
        volume_score = self._analyze_volume_patterns(stock_info)
        price_score = self._analyze_price_action(stock_info)
        sentiment_score = self._analyze_market_sentiment(stock_info)
        
        weights = self.analysis_weights['short_term']
        total_score = (
            technical_score * weights['technical_momentum'] +
            volume_score * weights['volume_analysis'] +
            price_score * weights['price_action'] +
            sentiment_score * weights['market_sentiment']
        )
        
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
        
        fundamental_score = self._analyze_fundamental_quality(stock_info)
        stability_score = self._analyze_financial_stability(stock_info)
        growth_score = self._analyze_growth_potential(stock_info)
        valuation_score = self._analyze_valuation_safety(stock_info)
        
        weights = self.analysis_weights['long_term']
        total_score = (
            fundamental_score * weights['fundamental_quality'] +
            stability_score * weights['financial_stability'] +
            growth_score * weights['growth_potential'] +
            valuation_score * weights['valuation_safety']
        )
        
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
        score = 5.0
        
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
        
        technical_signals = stock_info.get('technical_signals', {})
        if technical_signals.get('macd_golden_cross'):
            score += 1.5
        if technical_signals.get('rsi_healthy'):
            score += 1.0
        if technical_signals.get('ma_golden_cross'):
            score += 1.0
        
        rsi = stock_info.get('rsi', 50)
        if 40 <= rsi <= 60:
            score += 0.5
        elif rsi < 30:
            score += 1.0
        elif rsi > 70:
            score -= 1.0
        
        return max(0, min(10, score))
    
    def _analyze_volume_patterns(self, stock_info: Dict[str, Any]) -> float:
        """分析成交量模式 (0-10分)"""
        score = 5.0
        
        trade_value = stock_info.get('trade_value', 0)
        volume_ratio = stock_info.get('volume_ratio', 1)
        
        if trade_value > 5000000000:
            score += 2.5
        elif trade_value > 1000000000:
            score += 2.0
        elif trade_value > 500000000:
            score += 1.5
        elif trade_value > 100000000:
            score += 1.0
        elif trade_value < 50000000:
            score -= 1.0
        
        if volume_ratio > 3:
            score += 2.0
        elif volume_ratio > 2:
            score += 1.5
        elif volume_ratio > 1.5:
            score += 1.0
        elif volume_ratio < 0.5:
            score -= 1.5
        
        return max(0, min(10, score))
    
    def _analyze_price_action(self, stock_info: Dict[str, Any]) -> float:
        """分析價格行為 (0-10分)"""
        score = 5.0
        
        change_percent = stock_info.get('change_percent', 0)
        
        if abs(change_percent) > 5:
            if change_percent > 0:
                score += 2.0
            else:
                score -= 2.0
        elif abs(change_percent) > 3:
            if change_percent > 0:
                score += 1.5
            else:
                score -= 1.5
        
        return max(0, min(10, score))
    
    def _analyze_market_sentiment(self, stock_info: Dict[str, Any]) -> float:
        """分析市場情緒 (0-10分)"""
        score = 5.0
        
        foreign_net_buy = stock_info.get('foreign_net_buy', 0)
        trust_net_buy = stock_info.get('trust_net_buy', 0)
        
        if foreign_net_buy > 50000:
            score += 2.0
        elif foreign_net_buy > 10000:
            score += 1.5
        elif foreign_net_buy > 0:
            score += 1.0
        elif foreign_net_buy < -50000:
            score -= 2.0
        elif foreign_net_buy < 0:
            score -= 1.0
        
        if trust_net_buy > 20000:
            score += 1.0
        elif trust_net_buy < -20000:
            score -= 1.0
        
        return max(0, min(10, score))
    
    def _analyze_fundamental_quality(self, stock_info: Dict[str, Any]) -> float:
        """分析基本面品質 (0-10分)"""
        score = 5.0
        
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
        
        roa = stock_info.get('roa', 0)
        if roa > 10:
            score += 1.0
        elif roa > 5:
            score += 0.5
        
        gross_margin = stock_info.get('gross_margin', 0)
        if gross_margin > 30:
            score += 1.0
        elif gross_margin > 20:
            score += 0.5
        
        return max(0, min(10, score))
    
    def _analyze_financial_stability(self, stock_info: Dict[str, Any]) -> float:
        """分析財務穩定性 (0-10分)"""
        score = 5.0
        
        debt_ratio = stock_info.get('debt_ratio', 50)
        if debt_ratio < 30:
            score += 2.0
        elif debt_ratio < 50:
            score += 1.0
        elif debt_ratio > 70:
            score -= 2.0
        elif debt_ratio > 60:
            score -= 1.0
        
        current_ratio = stock_info.get('current_ratio', 100)
        if current_ratio > 200:
            score += 1.5
        elif current_ratio > 150:
            score += 1.0
        elif current_ratio < 100:
            score -= 2.0
        
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
        
        pb_ratio = stock_info.get('pb_ratio', 999)
        if pb_ratio < 1.5:
            score += 1.5
        elif pb_ratio < 2.0:
            score += 1.0
        elif pb_ratio > 3.0:
            score -= 1.5
        
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
        
        data_fields = ['close', 'volume', 'trade_value', 'change_percent']
        available_fields = sum(1 for field in data_fields if stock_info.get(field) is not None)
        data_completeness = (available_fields / len(data_fields)) * 30
        
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

# ==================== 分析整合器 ====================

class StockAnalyzerIntegrator:
    """股票分析整合器"""
    
    def __init__(self, data_dir='data'):
        """初始化分析整合器"""
        self.data_dir = data_dir
    
    def get_stock_list_for_time_slot(self, time_slot: str, all_stocks: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """根據時段選擇要分析的股票"""
        
        # 根據時段設定掃描限制
        if time_slot == 'morning_scan':
            limit = 100
        elif time_slot in ['mid_morning_scan', 'mid_day_scan']:
            limit = 150
        elif time_slot == 'afternoon_scan':
            limit = 450
        else:
            limit = 100
        
        logger.info(f"時段 {time_slot} 將掃描 {limit} 支股票")
        
        return all_stocks[:min(limit, len(all_stocks))]
    
    def get_recommendation_limits(self, time_slot: str) -> Dict[str, int]:
        """獲取推薦數量限制"""
        
        if time_slot == 'morning_scan':
            rec_limits = {
                'long_term': 2,
                'short_term': 3,
                'weak_stocks': 2
            }
        elif time_slot == 'mid_morning_scan':
            rec_limits = {
                'long_term': 3,
                'short_term': 2,
                'weak_stocks': 0
            }
        elif time_slot == 'mid_day_scan':
            rec_limits = {
                'long_term': 3,
                'short_term': 2,
                'weak_stocks': 0
            }
        elif time_slot == 'afternoon_scan':
            rec_limits = {
                'long_term': 3,
                'short_term': 3,
                'weak_stocks': 0
            }
        else:
            rec_limits = {
                'long_term': 3,
                'short_term': 3,
                'weak_stocks': 2
            }
        
        return rec_limits
    
    def fetch_taiwan_stocks(self) -> List[Dict[str, str]]:
        """獲取台灣股市的股票列表"""
        
        # 嘗試從本地文件加載
        try:
            stock_list_path = os.path.join(self.data_dir, 'stock_list.json')
            if os.path.exists(stock_list_path):
                with open(stock_list_path, 'r', encoding='utf-8') as f:
                    stocks = json.load(f)
                logger.info(f"從本地文件加載 {len(stocks)} 支股票")
                return stocks
        except Exception as e:
            logger.error(f"從本地文件加載股票列表失敗: {e}")
        
        # 如果本地文件不存在，返回默認的股票列表
        default_stocks = [
            {"code": "2330", "name": "台積電"},
            {"code": "2317", "name": "鴻海"},
            {"code": "2454", "name": "聯發科"},
            {"code": "2412", "name": "中華電"},
            {"code": "2308", "name": "台達電"},
            {"code": "2303", "name": "聯電"},
            {"code": "1301", "name": "台塑"},
            {"code": "1303", "name": "南亞"},
            {"code": "2002", "name": "中鋼"},
            {"code": "2882", "name": "國泰金"},
            {"code": "2609", "name": "陽明"},
            {"code": "2615", "name": "萬海"},
            {"code": "2603", "name": "長榮"},
            {"code": "2891", "name": "中信金"},
            {"code": "2886", "name": "兆豐金"}
        ]
        logger.warning(f"使用默認的股票列表 ({len(default_stocks)} 支股票)")
        return default_stocks

# ==================== 綜合分析器 (統一接口) ====================

class ComprehensiveStockAnalyzer:
    """股票綜合分析系統 - 統一接口"""
    
    def __init__(self, data_dir='data'):
        """初始化綜合分析器"""
        self.data_dir = data_dir
        
        # 初始化各種分析器
        self.basic_analyzer = StockAnalyzer()
        self.enhanced_analyzer = EnhancedStockAnalyzer()
        self.precise_analyzer = PreciseStockAnalyzer()
        self.integrator = StockAnalyzerIntegrator(data_dir)
        
        logger.info("綜合股票分析系統已初始化")
    
    def analyze_stock_comprehensive(self, 
                                   stock_data: Dict[str, Any], 
                                   analysis_type: str = 'mixed',
                                   precision_mode: bool = False,
                                   historical_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        股票綜合分析
        
        參數:
        - stock_data: 股票數據
        - analysis_type: 分析類型 ('short_term', 'long_term', 'mixed')
        - precision_mode: 是否使用精準模式
        - historical_data: 歷史數據 (可選)
        
        返回:
        - 綜合分析結果
        """
        
        analysis_result = {
            'stock_info': {
                'code': stock_data.get('code'),
                'name': stock_data.get('name'),
                'close': stock_data.get('close'),
                'change': stock_data.get('change', 0),
                'change_percent': stock_data.get('change_percent', 0),
                'volume': stock_data.get('volume'),
                'trade_value': stock_data.get('trade_value')
            },
            'analysis_mode': 'precision' if precision_mode else 'enhanced',
            'analysis_type': analysis_type,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if precision_mode:
                # 使用精準分析模式
                if analysis_type == 'short_term':
                    precision_result = self.precise_analyzer.analyze_short_term_precision(stock_data)
                    analysis_result['precision_analysis'] = precision_result
                elif analysis_type == 'long_term':
                    precision_result = self.precise_analyzer.analyze_long_term_precision(stock_data)
                    analysis_result['precision_analysis'] = precision_result
                else:
                    # 混合模式：同時進行短線和長線精準分析
                    short_result = self.precise_analyzer.analyze_short_term_precision(stock_data)
                    long_result = self.precise_analyzer.analyze_long_term_precision(stock_data)
                    analysis_result['precision_analysis'] = {
                        'short_term': short_result,
                        'long_term': long_result,
                        'combined_score': round((short_result['total_score'] + long_result['total_score']) / 2, 2)
                    }
                
            else:
                # 使用增強分析模式
                enhanced_result = self.enhanced_analyzer.analyze_stock_enhanced(stock_data, analysis_type)
                analysis_result['enhanced_analysis'] = enhanced_result
            
            # 如果有歷史數據，進行基礎技術分析
            if historical_data is not None:
                basic_result = self.basic_analyzer.analyze_single_stock(stock_data, historical_data)
                analysis_result['technical_analysis'] = basic_result
            
            # 生成最終建議
            analysis_result['final_recommendation'] = self._generate_final_recommendation(analysis_result)
            
        except Exception as e:
            logger.error(f"綜合分析過程中發生錯誤: {e}")
            # 發生錯誤時，至少提供基本分析
            if historical_data is not None:
                basic_result = self.basic_analyzer.analyze_single_stock(stock_data, historical_data)
                analysis_result['technical_analysis'] = basic_result
                analysis_result['error_info'] = str(e)
        
        return analysis_result
    
    def batch_analyze_stocks(self, 
                           stocks_data: List[Dict[str, Any]], 
                           analysis_type: str = 'mixed',
                           precision_mode: bool = False,
                           get_historical_func: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        批量分析股票
        
        參數:
        - stocks_data: 股票數據列表
        - analysis_type: 分析類型
        - precision_mode: 是否使用精準模式
        - get_historical_func: 獲取歷史數據的函數
        
        返回:
        - 分析結果列表
        """
        
        results = []
        
        for i, stock_data in enumerate(stocks_data):
            try:
                # 獲取歷史數據
                historical_data = None
                if get_historical_func:
                    historical_data = get_historical_func(stock_data['code'])
                
                # 執行綜合分析
                analysis = self.analyze_stock_comprehensive(
                    stock_data, analysis_type, precision_mode, historical_data
                )
                
                results.append(analysis)
                
                # 記錄進度
                if (i + 1) % 10 == 0:
                    logger.info(f"已完成 {i + 1}/{len(stocks_data)} 支股票的分析")
                
            except Exception as e:
                logger.error(f"分析股票 {stock_data.get('code', 'Unknown')} 時發生錯誤: {e}")
                # 即使出錯也記錄基本信息
                results.append({
                    'stock_info': stock_data,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        logger.info(f"批量分析完成，共處理 {len(results)} 支股票")
        return results
    
    def get_top_recommendations(self, 
                              analysis_results: List[Dict[str, Any]], 
                              recommendation_type: str = 'short_term',
                              limit: int = 5) -> List[Dict[str, Any]]:
        """
        獲取頂級推薦股票
        
        參數:
        - analysis_results: 分析結果列表
        - recommendation_type: 推薦類型 ('short_term', 'long_term')
        - limit: 推薦數量限制
        
        返回:
        - 排序後的推薦列表
        """
        
        scored_stocks = []
        
        for result in analysis_results:
            try:
                score = 0
                
                # 從不同分析結果中提取分數
                if 'precision_analysis' in result:
                    precision_data = result['precision_analysis']
                    if recommendation_type in precision_data:
                        score = precision_data[recommendation_type]['total_score']
                    elif 'combined_score' in precision_data:
                        score = precision_data['combined_score']
                
                elif 'enhanced_analysis' in result:
                    enhanced_data = result['enhanced_analysis']
                    score = enhanced_data.get('weighted_score', 0)
                
                elif 'technical_analysis' in result:
                    technical_data = result['technical_analysis']
                    score = technical_data.get('score', 0) / 10  # 轉換為0-10分
                
                if score > 0:
                    scored_stocks.append({
                        'stock_info': result['stock_info'],
                        'score': score,
                        'analysis_data': result
                    })
                    
            except Exception as e:
                logger.error(f"處理推薦時發生錯誤: {e}")
                continue
        
        # 按分數排序並限制數量
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = scored_stocks[:limit]
        
        logger.info(f"生成 {len(top_recommendations)} 個 {recommendation_type} 推薦")
        return top_recommendations
    
    def _generate_final_recommendation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成最終推薦"""
        
        recommendation = {
            'action': '觀望',
            'confidence': 'low',
            'reasoning': [],
            'risk_level': 'medium'
        }
        
        try:
            # 從精準分析中提取建議
            if 'precision_analysis' in analysis_result:
                precision_data = analysis_result['precision_analysis']
                
                if 'short_term' in precision_data and 'long_term' in precision_data:
                    # 混合分析
                    short_grade = precision_data['short_term']['grade']
                    long_grade = precision_data['long_term']['grade']
                    
                    if short_grade in ['A+', 'A'] and long_grade in ['A+', 'A']:
                        recommendation['action'] = '強烈推薦'
                        recommendation['confidence'] = 'high'
                    elif short_grade in ['A+', 'A'] or long_grade in ['A+', 'A']:
                        recommendation['action'] = '推薦'
                        recommendation['confidence'] = 'medium'
                
                else:
                    # 單一分析
                    single_data = precision_data if 'grade' in precision_data else list(precision_data.values())[0]
                    grade = single_data['grade']
                    
                    if grade == 'A+':
                        recommendation['action'] = '強烈推薦'
                        recommendation['confidence'] = 'high'
                    elif grade == 'A':
                        recommendation['action'] = '推薦'
                        recommendation['confidence'] = 'medium'
                    elif grade == 'B':
                        recommendation['action'] = '觀察'
                        recommendation['confidence'] = 'medium'
            
            # 從增強分析中提取建議
            elif 'enhanced_analysis' in analysis_result:
                enhanced_data = analysis_result['enhanced_analysis']
                score = enhanced_data.get('weighted_score', 0)
                
                if score >= 8:
                    recommendation['action'] = '強烈推薦'
                    recommendation['confidence'] = 'high'
                elif score >= 6:
                    recommendation['action'] = '推薦'
                    recommendation['confidence'] = 'medium'
                elif score >= 4:
                    recommendation['action'] = '觀察'
                    recommendation['confidence'] = 'medium'
                else:
                    recommendation['action'] = '避免'
                    recommendation['confidence'] = 'low'
                
                if 'reason' in enhanced_data:
                    recommendation['reasoning'].append(enhanced_data['reason'])
            
            # 從技術分析中補充信息
            if 'technical_analysis' in analysis_result:
                technical_data = analysis_result['technical_analysis']
                signals = technical_data.get('signals', [])
                patterns = technical_data.get('patterns', [])
                
                if signals:
                    recommendation['reasoning'].extend([f"技術信號: {signal}" for signal in signals])
                if patterns:
                    recommendation['reasoning'].extend([f"技術形態: {pattern}" for pattern in patterns])
        
        except Exception as e:
            logger.error(f"生成最終推薦時發生錯誤: {e}")
        
        return recommendation
    
    def export_analysis_results(self, 
                              analysis_results: List[Dict[str, Any]], 
                              file_path: str,
                              format: str = 'json') -> bool:
        """
        導出分析結果
        
        參數:
        - analysis_results: 分析結果列表
        - file_path: 導出文件路徑
        - format: 導出格式 ('json', 'csv')
        
        返回:
        - 是否成功導出
        """
        
        try:
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(analysis_results, f, ensure_ascii=False, indent=2)
            
            elif format.lower() == 'csv':
                # 將結果轉換為DataFrame並導出CSV
                flattened_data = []
                for result in analysis_results:
                    flat_record = {
                        'code': result['stock_info']['code'],
                        'name': result['stock_info']['name'],
                        'close': result['stock_info']['close'],
                        'change_percent': result['stock_info']['change_percent'],
                        'analysis_mode': result.get('analysis_mode', ''),
                        'analysis_type': result.get('analysis_type', ''),
                        'recommendation': result.get('final_recommendation', {}).get('action', ''),
                        'confidence': result.get('final_recommendation', {}).get('confidence', ''),
                        'timestamp': result.get('timestamp', '')
                    }
                    flattened_data.append(flat_record)
                
                df = pd.DataFrame(flattened_data)
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            logger.info(f"分析結果已成功導出至: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"導出分析結果失敗: {e}")
            return False

    def analyze_with_ml_enhancement(self,
                                    stock_data: Dict[str, Any],
                                    analysis_type: str = 'mixed') -> Dict[str, Any]:
        """
        使用 ML 增強版進行股票分析

        這個方法整合了新的機器學習預測系統，提供更精準的分析結果

        參數:
        - stock_data: 股票數據
        - analysis_type: 分析類型 ('short_term', 'long_term', 'mixed')

        返回:
        - 包含 ML 預測的增強分析結果
        """
        try:
            # 嘗試導入 ML 預測整合器
            from prediction_integrator import PredictionIntegrator

            integrator = PredictionIntegrator(enable_ml=True)

            # 先執行傳統分析
            traditional_result = self.analyze_stock_comprehensive(
                stock_data,
                analysis_type,
                precision_mode=True
            )

            # 執行 ML 增強分析
            ml_result = integrator.enhance_stock_analysis(
                stock_data,
                traditional_result,
                analysis_type
            )

            # 合併結果
            combined_result = {
                'stock_info': traditional_result.get('stock_info', {}),
                'traditional_analysis': traditional_result,
                'ml_enhanced': ml_result,
                'final_score': ml_result.get('combined_score', 50),
                'precision_grade': ml_result.get('precision_grade', 'N/A'),
                'recommendation': ml_result.get('action_recommendation', {}),
                'reasoning': ml_result.get('enhanced_reasoning', []),
                'target_price': ml_result.get('target_price', {}),
                'market_sentiment': ml_result.get('market_sentiment', {}),
                'analysis_type': analysis_type,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"ML 增強分析完成: {stock_data.get('code')} - 評分: {combined_result['final_score']}")
            return combined_result

        except ImportError as e:
            logger.warning(f"ML 預測模組未安裝，使用傳統分析: {e}")
            return self.analyze_stock_comprehensive(stock_data, analysis_type, precision_mode=True)
        except Exception as e:
            logger.error(f"ML 增強分析失敗: {e}")
            return self.analyze_stock_comprehensive(stock_data, analysis_type, precision_mode=True)

    def batch_analyze_with_ml(self,
                             stocks: List[Dict[str, Any]],
                             analysis_type: str = 'mixed',
                             top_n: int = 10) -> List[Dict[str, Any]]:
        """
        批量執行 ML 增強分析

        參數:
        - stocks: 股票列表
        - analysis_type: 分析類型
        - top_n: 返回前N名

        返回:
        - 按評分排序的分析結果列表
        """
        results = []

        for stock in stocks:
            try:
                result = self.analyze_with_ml_enhancement(stock, analysis_type)
                results.append(result)
            except Exception as e:
                logger.warning(f"分析失敗: {stock.get('code')} - {e}")
                continue

        # 按最終評分排序
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)

        return results[:top_n]

# ==================== 使用範例 ====================

def demo_comprehensive_analysis():
    """示範綜合分析功能"""
    
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 創建綜合分析器
    analyzer = ComprehensiveStockAnalyzer()
    
    # 測試股票數據
    test_stocks = [
        {
            'code': '2330',
            'name': '台積電',
            'close': 638.0,
            'change': 15.0,
            'change_percent': 2.4,
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
            'trust_net_buy': 8000
        },
        {
            'code': '2317',
            'name': '鴻海',
            'close': 185.0,
            'change': -2.5,
            'change_percent': -1.3,
            'volume': 35000000,
            'trade_value': 6475000000,
            'volume_ratio': 1.2,
            'rsi': 45,
            'dividend_yield': 4.2,
            'eps_growth': 8.3,
            'pe_ratio': 12.1,
            'roe': 15.6,
            'foreign_net_buy': -15000,
            'trust_net_buy': 2000
        }
    ]
    
    print("=== 股票綜合分析系統示範 ===\n")
    
    # 1. 單支股票綜合分析（增強模式）
    print("1. 增強模式分析:")
    enhanced_result = analyzer.analyze_stock_comprehensive(
        test_stocks[0], 
        analysis_type='mixed', 
        precision_mode=False
    )
    
    enhanced_analysis = enhanced_result['enhanced_analysis']
    print(f"股票: {enhanced_analysis['name']} ({enhanced_analysis['code']})")
    print(f"現價: {enhanced_analysis['current_price']} 漲跌: {enhanced_analysis['change_percent']}%")
    print(f"綜合評分: {enhanced_analysis['weighted_score']}")
    print(f"投資建議: {enhanced_analysis['suggestion']}")
    print(f"推薦理由: {enhanced_analysis['reason']}")
    print()
    
    # 2. 單支股票綜合分析（精準模式）
    print("2. 精準模式分析:")
    precision_result = analyzer.analyze_stock_comprehensive(
        test_stocks[0], 
        analysis_type='mixed', 
        precision_mode=True
    )
    
    precision_analysis = precision_result['precision_analysis']
    print(f"短線分析: 評分 {precision_analysis['short_term']['total_score']}, 等級 {precision_analysis['short_term']['grade']}")
    print(f"長線分析: 評分 {precision_analysis['long_term']['total_score']}, 等級 {precision_analysis['long_term']['grade']}")
    print(f"綜合評分: {precision_analysis['combined_score']}")
    print(f"最終建議: {precision_result['final_recommendation']['action']}")
    print()
    
    # 3. 批量分析
    print("3. 批量分析:")
    batch_results = analyzer.batch_analyze_stocks(
        test_stocks,
        analysis_type='short_term',
        precision_mode=True
    )
    
    for result in batch_results:
        stock_info = result['stock_info']
        recommendation = result['final_recommendation']
        print(f"{stock_info['name']}: {recommendation['action']} (信心度: {recommendation['confidence']})")
    print()
    
    # 4. 獲取推薦排行
    print("4. 推薦排行:")
    top_recommendations = analyzer.get_top_recommendations(
        batch_results,
        recommendation_type='short_term',
        limit=3
    )
    
    for i, rec in enumerate(top_recommendations, 1):
        stock_info = rec['stock_info']
        score = rec['score']
        print(f"第{i}名: {stock_info['name']} (評分: {score:.2f})")
    
    # 5. 導出結果
    print("\n5. 導出分析結果:")
    success = analyzer.export_analysis_results(
        batch_results,
        'analysis_results.json',
        format='json'
    )
    
    if success:
        print("分析結果已成功導出至 analysis_results.json")
    else:
        print("導出失敗")

if __name__ == "__main__":
    demo_comprehensive_analysis()
