"""
unified_stock_analyzer.py - 統一股票分析系統
整合基礎、增強、精準、優化四種分析模式的完整股票分析系統

主要功能：
1. 多層次分析架構：基礎、增強、精準、優化四種模式
2. 智能權重配置：根據投資時間長短動態調整分析權重
3. 綜合評分系統：技術面、基本面、法人動向、風險評估
4. 自動排程執行：支持多時段自動掃描和推薦
5. 多元通知系統：郵件、簡訊等多種通知方式
6. 完整數據管理：緩存、導出、歷史記錄管理

作者：AI Assistant
版本：1.0.0
"""

import os
import sys
import time
import json
import schedule
import argparse
import logging
import importlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Callable
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== 配置和工具函數 ====================

def setup_logging(log_level='INFO', log_file=None):
    """設置日誌系統"""
    log_format = '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logging.basicConfig(
            filename=log_file,
            level=getattr(logging, log_level),
            format=log_format,
            filemode='a',
            encoding='utf-8'
        )
    else:
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format
        )
    
    # 添加控制台輸出
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, log_level))
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(console)

def log_event(message: str, level: str = 'info'):
    """統一的日誌記錄函數"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    emoji_map = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌',
        'success': '✅',
        'debug': '🔍'
    }
    
    emoji = emoji_map.get(level, 'ℹ️')
    console_msg = f"[{timestamp}] {emoji} {message}"
    
    if level == 'error':
        logging.error(message)
        print(console_msg)
    elif level == 'warning':
        logging.warning(message)
        print(console_msg)
    elif level == 'debug':
        logging.debug(message)
        print(console_msg)
    elif level == 'success':
        logging.info(message)
        print(console_msg)
    else:
        logging.info(message)
        print(console_msg)

# ==================== 基礎分析器 ====================

class BaseStockAnalyzer:
    """基礎股票分析器"""
    
    def __init__(self):
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
            'score': 0,
            'analysis_method': 'basic'
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
        
        try:
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
        except Exception as e:
            log_event(f"計算技術指標時發生錯誤: {e}", 'warning')
        
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
        
        # 均線突破
        if 'ma20' in indicators and current_close > indicators['ma20'] and prev_close <= indicators['ma20']:
            patterns.append('突破20日均線')
        
        if 'ma60' in indicators and current_close > indicators['ma60'] and prev_close <= indicators['ma60']:
            patterns.append('突破60日均線')
        
        # 成交量突破
        if 'volume_ratio' in indicators and indicators['volume_ratio'] > 2:
            patterns.append('成交量突破')
        
        # RSI信號
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if rsi > 70:
                patterns.append('RSI超買')
            elif rsi < 30:
                patterns.append('RSI超賣')
        
        return patterns
    
    def _generate_signals(self, stock_data: Dict, indicators: Dict, patterns: List[str]) -> List[str]:
        """生成交易信號"""
        signals = []
        
        # 強勢突破信號
        if '突破20日均線' in patterns and '成交量突破' in patterns:
            signals.append('強勢突破信號')
        
        # 超賣反彈信號
        if 'RSI超賣' in patterns:
            signals.append('超賣反彈信號')
        
        # 強勢上漲信號
        change_percent = stock_data.get('change_percent', 0)
        volume_ratio = indicators.get('volume_ratio', 1)
        if change_percent > 5 and volume_ratio > 2:
            signals.append('強勢上漲信號')
        
        return signals
    
    def _calculate_score(self, indicators: Dict, patterns: List[str], signals: List[str]) -> float:
        """計算綜合評分（0-100）"""
        score = 50
        
        # RSI評分
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if 30 <= rsi <= 70:
                score += 5
            elif rsi < 30:
                score += 10
            else:
                score -= 5
        
        # 形態評分
        positive_patterns = ['突破20日均線', '突破60日均線', '成交量突破']
        for pattern in patterns:
            if pattern in positive_patterns:
                score += 5
        
        # 信號評分
        positive_signals = ['強勢突破信號', '超賣反彈信號', '強勢上漲信號']
        for signal in signals:
            if signal in positive_signals:
                score += 8
        
        return max(0, min(100, score))

# ==================== 增強分析器 ====================

class EnhancedStockAnalyzer:
    """增強版股票分析器"""
    
    def __init__(self):
        self.weight_configs = {
            'short_term': {
                'base_score': 1.0,
                'technical': 0.8,
                'fundamental': 0.3,
                'institutional': 0.4
            },
            'long_term': {
                'base_score': 0.4,
                'technical': 0.3,
                'fundamental': 1.2,
                'institutional': 0.8
            },
            'mixed': {
                'base_score': 0.7,
                'technical': 0.6,
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
            fundamental_analysis = self._get_enhanced_fundamental_analysis(stock_code)
            institutional_analysis = self._get_enhanced_institutional_analysis(stock_code)
            
            final_analysis = self._combine_analysis_enhanced(
                base_analysis, technical_analysis, fundamental_analysis, 
                institutional_analysis, analysis_type
            )
            
            final_analysis['analysis_method'] = 'enhanced'
            return final_analysis
            
        except Exception as e:
            log_event(f"增強分析失敗，返回基礎分析: {stock_code} - {e}", 'warning')
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
            
            technical_data = self._fetch_technical_data(stock_code, stock_info)
            
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
            log_event(f"獲取技術面數據失敗: {stock_code} - {e}", 'warning')
            return {'available': False}
    
    def _get_enhanced_fundamental_analysis(self, stock_code: str) -> Dict[str, Any]:
        """獲取增強版基本面分析"""
        try:
            cache_key = f"fundamental_enhanced_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            fundamental_data = self._fetch_enhanced_fundamental_data(stock_code)
            
            if not fundamental_data:
                return {'available': False}
            
            fund_score = 0
            
            # 殖利率評分（權重提高）
            dividend_yield = fundamental_data.get('dividend_yield', 0)
            if dividend_yield > 6:
                fund_score += 4.0
            elif dividend_yield > 4:
                fund_score += 3.0
            elif dividend_yield > 2.5:
                fund_score += 2.0
            elif dividend_yield > 1:
                fund_score += 1.0
            
            # EPS 成長評分（權重提高）
            eps_growth = fundamental_data.get('eps_growth', 0)
            if eps_growth > 30:
                fund_score += 4.0
            elif eps_growth > 20:
                fund_score += 3.5
            elif eps_growth > 10:
                fund_score += 3.0
            elif eps_growth > 5:
                fund_score += 2.0
            elif eps_growth > 0:
                fund_score += 1.0
            elif eps_growth < -10:
                fund_score -= 3.0
            elif eps_growth < 0:
                fund_score -= 1.5
            
            # PE 比率評分
            pe_ratio = fundamental_data.get('pe_ratio', 999)
            if pe_ratio < 8:
                fund_score += 2.5
            elif pe_ratio < 12:
                fund_score += 2.0
            elif pe_ratio < 18:
                fund_score += 1.5
            elif pe_ratio < 25:
                fund_score += 0.5
            elif pe_ratio > 35:
                fund_score -= 2.0
            
            # ROE 評分
            roe = fundamental_data.get('roe', 0)
            if roe > 25:
                fund_score += 3.0
            elif roe > 20:
                fund_score += 2.5
            elif roe > 15:
                fund_score += 2.0
            elif roe > 10:
                fund_score += 1.0
            elif roe < 5:
                fund_score -= 1.5
            
            # 營收成長評分
            revenue_growth = fundamental_data.get('revenue_growth', 0)
            if revenue_growth > 20:
                fund_score += 2.0
            elif revenue_growth > 10:
                fund_score += 1.5
            elif revenue_growth > 5:
                fund_score += 1.0
            elif revenue_growth < -10:
                fund_score -= 2.0
            elif revenue_growth < 0:
                fund_score -= 1.0
            
            # 股息連續配發年數
            dividend_years = fundamental_data.get('dividend_consecutive_years', 0)
            if dividend_years > 10:
                fund_score += 2.0
            elif dividend_years > 5:
                fund_score += 1.5
            elif dividend_years > 3:
                fund_score += 1.0
            
            result = {
                'available': True,
                'fund_score': round(fund_score, 1),
                'dividend_yield': dividend_yield,
                'eps_growth': eps_growth,
                'pe_ratio': pe_ratio,
                'roe': roe,
                'revenue_growth': revenue_growth,
                'dividend_consecutive_years': dividend_years
            }
            
            self.data_cache[cache_key] = result
            return result
            
        except Exception as e:
            log_event(f"獲取基本面數據失敗: {stock_code} - {e}", 'warning')
            return {'available': False}
    
    def _get_enhanced_institutional_analysis(self, stock_code: str) -> Dict[str, Any]:
        """獲取增強版法人買賣分析"""
        try:
            cache_key = f"institutional_enhanced_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            institutional_data = self._fetch_enhanced_institutional_data(stock_code)
            
            if not institutional_data:
                return {'available': False}
            
            inst_score = 0
            
            # 外資買賣評分（權重提高）
            foreign_net = institutional_data.get('foreign_net_buy', 0)
            if foreign_net > 100000:
                inst_score += 5.0
            elif foreign_net > 50000:
                inst_score += 4.0
            elif foreign_net > 20000:
                inst_score += 3.0
            elif foreign_net > 10000:
                inst_score += 2.5
            elif foreign_net > 5000:
                inst_score += 2.0
            elif foreign_net > 0:
                inst_score += 1.0
            elif foreign_net < -100000:
                inst_score -= 5.0
            elif foreign_net < -50000:
                inst_score -= 4.0
            elif foreign_net < -20000:
                inst_score -= 3.0
            elif foreign_net < -10000:
                inst_score -= 2.5
            elif foreign_net < 0:
                inst_score -= 1.0
            
            # 投信買賣評分
            trust_net = institutional_data.get('trust_net_buy', 0)
            if trust_net > 50000:
                inst_score += 3.5
            elif trust_net > 20000:
                inst_score += 3.0
            elif trust_net > 10000:
                inst_score += 2.5
            elif trust_net > 5000:
                inst_score += 2.0
            elif trust_net > 1000:
                inst_score += 1.5
            elif trust_net > 0:
                inst_score += 1.0
            elif trust_net < -50000:
                inst_score -= 3.5
            elif trust_net < -20000:
                inst_score -= 3.0
            elif trust_net < -10000:
                inst_score -= 2.5
            elif trust_net < -1000:
                inst_score -= 1.5
            elif trust_net < 0:
                inst_score -= 1.0
            
            # 自營商買賣評分
            dealer_net = institutional_data.get('dealer_net_buy', 0)
            if dealer_net > 20000:
                inst_score += 2.0
            elif dealer_net > 10000:
                inst_score += 1.5
            elif dealer_net > 5000:
                inst_score += 1.0
            elif dealer_net < -20000:
                inst_score -= 2.0
            elif dealer_net < -10000:
                inst_score -= 1.5
            elif dealer_net < -5000:
                inst_score -= 1.0
            
            # 三大法人合計評分
            total_institutional = foreign_net + trust_net + dealer_net
            if total_institutional > 150000:
                inst_score += 3.0
            elif total_institutional > 100000:
                inst_score += 2.0
            elif total_institutional > 50000:
                inst_score += 1.0
            elif total_institutional < -150000:
                inst_score -= 3.0
            elif total_institutional < -100000:
                inst_score -= 2.0
            elif total_institutional < -50000:
                inst_score -= 1.0
            
            # 持續買超天數
            consecutive_buy_days = institutional_data.get('consecutive_buy_days', 0)
            if consecutive_buy_days > 10:
                inst_score += 2.0
            elif consecutive_buy_days > 5:
                inst_score += 1.5
            elif consecutive_buy_days > 3:
                inst_score += 1.0
            
            result = {
                'available': True,
                'inst_score': round(inst_score, 1),
                'foreign_net_buy': foreign_net,
                'trust_net_buy': trust_net,
                'dealer_net_buy': dealer_net,
                'total_institutional': total_institutional,
                'consecutive_buy_days': consecutive_buy_days
            }
            
            self.data_cache[cache_key] = result
            return result
            
        except Exception as e:
            log_event(f"獲取法人數據失敗: {stock_code} - {e}", 'warning')
            return {'available': False}
    
    def _fetch_technical_data(self, stock_code: str, stock_info: Dict[str, Any]) -> Optional[Dict]:
        """獲取技術指標數據"""
        try:
            current_price = stock_info['close']
            change_percent = stock_info['change_percent']
            
            # 模擬技術指標數據
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
            log_event(f"模擬技術數據失敗: {stock_code}", 'warning')
            return None
    
    def _fetch_enhanced_fundamental_data(self, stock_code: str) -> Optional[Dict]:
        """獲取增強版基本面數據"""
        try:
            # 預設股票基本面數據
            enhanced_fundamental_data = {
                '2330': {'dividend_yield': 2.3, 'eps_growth': 12.8, 'pe_ratio': 18.2, 'roe': 23.5, 'revenue_growth': 8.5, 'dividend_consecutive_years': 15},
                '2317': {'dividend_yield': 4.8, 'eps_growth': 15.2, 'pe_ratio': 11.5, 'roe': 16.8, 'revenue_growth': 12.3, 'dividend_consecutive_years': 12},
                '2454': {'dividend_yield': 3.2, 'eps_growth': 22.1, 'pe_ratio': 16.8, 'roe': 19.3, 'revenue_growth': 18.7, 'dividend_consecutive_years': 8},
                '2609': {'dividend_yield': 7.2, 'eps_growth': 35.6, 'pe_ratio': 8.9, 'roe': 18.4, 'revenue_growth': 28.9, 'dividend_consecutive_years': 5},
                '2615': {'dividend_yield': 6.8, 'eps_growth': 42.3, 'pe_ratio': 7.3, 'roe': 24.7, 'revenue_growth': 35.2, 'dividend_consecutive_years': 6},
                '2603': {'dividend_yield': 5.9, 'eps_growth': 28.1, 'pe_ratio': 9.8, 'roe': 16.2, 'revenue_growth': 22.4, 'dividend_consecutive_years': 7},
                '2882': {'dividend_yield': 6.2, 'eps_growth': 8.5, 'pe_ratio': 11.3, 'roe': 13.8, 'revenue_growth': 6.7, 'dividend_consecutive_years': 18},
                '1301': {'dividend_yield': 5.1, 'eps_growth': 12.7, 'pe_ratio': 12.8, 'roe': 14.2, 'revenue_growth': 9.3, 'dividend_consecutive_years': 20},
                '2412': {'dividend_yield': 4.9, 'eps_growth': 6.8, 'pe_ratio': 13.2, 'roe': 11.5, 'revenue_growth': 4.2, 'dividend_consecutive_years': 22},
            }
            
            if stock_code not in enhanced_fundamental_data:
                import random
                random.seed(hash(stock_code) % 1000)
                
                return {
                    'dividend_yield': round(random.uniform(1.5, 6.5), 1),
                    'eps_growth': round(random.uniform(-5.0, 25.0), 1),
                    'pe_ratio': round(random.uniform(8.0, 25.0), 1),
                    'roe': round(random.uniform(8.0, 20.0), 1),
                    'revenue_growth': round(random.uniform(-2.0, 15.0), 1),
                    'dividend_consecutive_years': random.randint(3, 15)
                }
            
            return enhanced_fundamental_data[stock_code]
            
        except Exception as e:
            log_event(f"獲取基本面數據失敗: {stock_code}", 'warning')
            return None
    
    def _fetch_enhanced_institutional_data(self, stock_code: str) -> Optional[Dict]:
        """獲取增強版法人買賣數據"""
        try:
            import random
            random.seed(hash(stock_code) % 1000)
            
            # 針對不同股票設定不同的法人偏好
            if stock_code in ['2330', '2317', '2454']:
                base_foreign = random.randint(20000, 80000)
                base_trust = random.randint(-10000, 30000)
                base_dealer = random.randint(-5000, 15000)
                consecutive_days = random.randint(1, 8)
            elif stock_code in ['2609', '2615', '2603']:
                base_foreign = random.randint(-30000, 60000)
                base_trust = random.randint(-20000, 40000)
                base_dealer = random.randint(-10000, 20000)
                consecutive_days = random.randint(0, 5)
            else:
                base_foreign = random.randint(-20000, 40000)
                base_trust = random.randint(-15000, 25000)
                base_dealer = random.randint(-8000, 12000)
                consecutive_days = random.randint(0, 6)
            
            return {
                'foreign_net_buy': base_foreign,
                'trust_net_buy': base_trust,
                'dealer_net_buy': base_dealer,
                'consecutive_buy_days': consecutive_days
            }
            
        except Exception as e:
            log_event(f"模擬法人數據失敗: {stock_code}", 'warning')
            return None
    
    def _combine_analysis_enhanced(self, base_analysis: Dict, technical_analysis: Dict, 
                                 fundamental_analysis: Dict, institutional_analysis: Dict,
                                 analysis_type: str) -> Dict[str, Any]:
        """使用增強權重綜合所有分析結果"""
        
        weights = self.weight_configs.get(analysis_type, self.weight_configs['mixed'])
        
        final_score = base_analysis['base_score'] * weights['base_score']
        
        # 添加技術面得分
        if technical_analysis.get('available'):
            tech_contribution = technical_analysis['tech_score'] * weights['technical']
            final_score += tech_contribution
            base_analysis['analysis_components']['technical'] = True
            base_analysis['technical_score'] = technical_analysis['tech_score']
            base_analysis['technical_signals'] = technical_analysis['signals']
        
        # 添加基本面得分
        if fundamental_analysis.get('available'):
            fund_contribution = fundamental_analysis['fund_score'] * weights['fundamental']
            final_score += fund_contribution
            base_analysis['analysis_components']['fundamental'] = True
            base_analysis['fundamental_score'] = fundamental_analysis['fund_score']
            base_analysis['dividend_yield'] = fundamental_analysis['dividend_yield']
            base_analysis['eps_growth'] = fundamental_analysis['eps_growth']
            base_analysis['pe_ratio'] = fundamental_analysis['pe_ratio']
            base_analysis['roe'] = fundamental_analysis['roe']
            base_analysis['revenue_growth'] = fundamental_analysis.get('revenue_growth', 0)
            base_analysis['dividend_consecutive_years'] = fundamental_analysis.get('dividend_consecutive_years', 0)
        
        # 添加法人買賣得分
        if institutional_analysis.get('available'):
            inst_contribution = institutional_analysis['inst_score'] * weights['institutional']
            final_score += inst_contribution
            base_analysis['analysis_components']['institutional'] = True
            base_analysis['institutional_score'] = institutional_analysis['inst_score']
            base_analysis['foreign_net_buy'] = institutional_analysis['foreign_net_buy']
            base_analysis['trust_net_buy'] = institutional_analysis['trust_net_buy']
            base_analysis['total_institutional'] = institutional_analysis.get('total_institutional', 0)
            base_analysis['consecutive_buy_days'] = institutional_analysis.get('consecutive_buy_days', 0)
        
        base_analysis['weighted_score'] = round(final_score, 1)
        base_analysis['analysis_type'] = analysis_type
        
        # 根據分析類型和得分確定趨勢和建議
        trend, suggestion, target_price, stop_loss = self._determine_recommendation(
            final_score, analysis_type, base_analysis['current_price']
        )
        
        base_analysis['trend'] = trend
        base_analysis['suggestion'] = suggestion
        base_analysis['target_price'] = target_price
        base_analysis['stop_loss'] = stop_loss
        base_analysis['analysis_time'] = datetime.now().isoformat()
        base_analysis['reason'] = self._generate_enhanced_reason(base_analysis, analysis_type)
        
        return base_analysis
    
    def _determine_recommendation(self, final_score: float, analysis_type: str, current_price: float) -> Tuple[str, str, Optional[float], float]:
        """根據得分和分析類型確定推薦"""
        if analysis_type == 'long_term':
            if final_score >= 12:
                return ("長線強烈看漲", "適合大幅加碼長期持有", 
                       round(current_price * 1.25, 1), round(current_price * 0.90, 1))
            elif final_score >= 8:
                return ("長線看漲", "適合中長期投資", 
                       round(current_price * 1.18, 1), round(current_price * 0.92, 1))
            elif final_score >= 4:
                return ("長線中性偏多", "適合定期定額投資", 
                       round(current_price * 1.12, 1), round(current_price * 0.93, 1))
            elif final_score >= 0:
                return ("長線中性", "持續觀察基本面變化", 
                       round(current_price * 1.08, 1), round(current_price * 0.95, 1))
            else:
                return ("長線看跌", "不建議長期投資", 
                       None, round(current_price * 0.95, 1))
        else:
            if final_score >= 8:
                return ("強烈看漲", "適合積極買入", 
                       round(current_price * 1.10, 1), round(current_price * 0.95, 1))
            elif final_score >= 4:
                return ("看漲", "可考慮買入", 
                       round(current_price * 1.06, 1), round(current_price * 0.97, 1))
            elif final_score >= 1:
                return ("中性偏多", "適合中長期投資", 
                       round(current_price * 1.08, 1), round(current_price * 0.95, 1))
            elif final_score > -1:
                return ("中性", "觀望為宜", 
                       None, round(current_price * 0.95, 1))
            elif final_score >= -4:
                return ("看跌", "建議減碼", 
                       None, round(current_price * 0.97, 1))
            else:
                return ("強烈看跌", "建議賣出", 
                       None, round(current_price * 0.98, 1))
    
    def _generate_enhanced_reason(self, analysis: Dict[str, Any], analysis_type: str) -> str:
        """生成增強的推薦理由"""
        reasons = []
        
        change_percent = analysis['change_percent']
        current_price = analysis['current_price']
        
        if analysis_type == 'long_term':
            # 長線重視基本面理由
            if 'dividend_yield' in analysis and analysis['dividend_yield'] > 0:
                dividend_yield = analysis['dividend_yield']
                if dividend_yield > 5:
                    reasons.append(f"高殖利率 {dividend_yield:.1f}%，現金流回報佳")
                elif dividend_yield > 3:
                    reasons.append(f"殖利率 {dividend_yield:.1f}%，穩定配息")
                elif dividend_yield > 1.5:
                    reasons.append(f"殖利率 {dividend_yield:.1f}%")
            
            if 'eps_growth' in analysis and analysis['eps_growth'] > 0:
                eps_growth = analysis['eps_growth']
                if eps_growth > 25:
                    reasons.append(f"EPS高速成長 {eps_growth:.1f}%，獲利大幅提升")
                elif eps_growth > 15:
                    reasons.append(f"EPS穩健成長 {eps_growth:.1f}%，獲利持續改善")
                elif eps_growth > 8:
                    reasons.append(f"EPS成長 {eps_growth:.1f}%，獲利向上")
            
            if 'foreign_net_buy' in analysis:
                foreign_net = analysis['foreign_net_buy']
                trust_net = analysis.get('trust_net_buy', 0)
                total_net = analysis.get('total_institutional', 0)
                
                if total_net > 50000:
                    reasons.append("三大法人大幅買超，籌碼穩定")
                elif foreign_net > 20000:
                    reasons.append("外資持續買超，國際資金青睞")
                elif trust_net > 10000:
                    reasons.append("投信買超，法人看好")
            
            if 'roe' in analysis and analysis['roe'] > 15:
                roe = analysis['roe']
                reasons.append(f"ROE {roe:.1f}%，獲利能力優秀")
        else:
            # 短線理由
            if abs(change_percent) > 3:
                reasons.append(f"今日{'大漲' if change_percent > 0 else '大跌'} {abs(change_percent):.1f}%")
            elif abs(change_percent) > 1:
                reasons.append(f"今日{'上漲' if change_percent > 0 else '下跌'} {abs(change_percent):.1f}%")
            
            if 'foreign_net_buy' in analysis and analysis['foreign_net_buy'] > 10000:
                reasons.append("外資買超支撐")
            
            if analysis['analysis_components'].get('technical'):
                signals = analysis.get('technical_signals', {})
                if signals.get('macd_golden_cross'):
                    reasons.append("MACD出現黃金交叉")
                elif signals.get('ma20_bullish'):
                    reasons.append("站穩20日均線")
        
        # 成交量理由
        if analysis['trade_value'] > 5000000000:
            reasons.append("成交金額龐大")
        elif analysis['trade_value'] > 1000000000:
            reasons.append("成交活躍")
        
        if not reasons:
            if analysis_type == 'long_term':
                reasons.append(f"現價 {current_price} 元，基本面穩健")
            else:
                reasons.append(f"現價 {current_price} 元，綜合指標顯示投資機會")
        
        return "，".join(reasons)
    
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

# ==================== 精準分析器 ====================

class PreciseStockAnalyzer:
    """精準版股票分析器"""
    
    def __init__(self):
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
            'action_suggestions': self._get_short_term_actions(total_score, grade),
            'analysis_method': 'precise'
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
            'action_suggestions': self._get_long_term_actions(total_score, grade),
            'analysis_method': 'precise'
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
        
        # 技術信號加分
        technical_signals = stock_info.get('technical_signals', {})
        if technical_signals.get('macd_golden_cross'):
            score += 1.5
        if technical_signals.get('rsi_healthy'):
            score += 1.0
        if technical_signals.get('ma_golden_cross'):
            score += 1.0
        
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

# ==================== 統一股票分析系統 ====================

class UnifiedStockAnalyzer:
    """統一股票分析系統 - 整合所有分析模式的主系統"""
    
    def __init__(self, mode='basic', data_dir='data'):
        """
        初始化統一分析系統
        
        參數:
        - mode: 分析模式 ('basic', 'enhanced', 'precise', 'optimized')
        - data_dir: 數據目錄
        """
        self.mode = mode
        self.data_dir = data_dir
        
        # 確保數據目錄存在
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, 'cache'), exist_ok=True)
        os.makedirs(os.path.join(data_dir, 'results'), exist_ok=True)
        os.makedirs(os.path.join(data_dir, 'logs'), exist_ok=True)
        
        # 初始化各種分析器
        self.base_analyzer = BaseStockAnalyzer()
        self.enhanced_analyzer = EnhancedStockAnalyzer()
        self.precise_analyzer = PreciseStockAnalyzer()
        
        # 初始化數據獲取器
        self.data_fetcher = None
        self._init_data_fetcher()
        
        # 初始化通知系統
        self.notifier = None
        self._init_notifier()
        
        # 時段配置
        self.time_slot_config = {
            'morning_scan': {
                'name': '早盤掃描',
                'stock_count': self._get_stock_count('morning'),
                'analysis_focus': 'short_term',
                'recommendation_limits': self._get_recommendation_limits('morning')
            },
            'mid_morning_scan': {
                'name': '盤中掃描',
                'stock_count': self._get_stock_count('mid_morning'),
                'analysis_focus': 'short_term',
                'recommendation_limits': self._get_recommendation_limits('mid_morning')
            },
            'mid_day_scan': {
                'name': '午間掃描',
                'stock_count': self._get_stock_count('mid_day'),
                'analysis_focus': 'mixed',
                'recommendation_limits': self._get_recommendation_limits('mid_day')
            },
            'afternoon_scan': {
                'name': '盤後掃描',
                'stock_count': self._get_stock_count('afternoon'),
                'analysis_focus': 'mixed',
                'recommendation_limits': self._get_recommendation_limits('afternoon')
            },
            'weekly_summary': {
                'name': '週末總結',
                'stock_count': self._get_stock_count('weekly'),
                'analysis_focus': 'long_term',
                'recommendation_limits': self._get_recommendation_limits('weekly')
            }
        }
        
        log_event(f"統一股票分析系統初始化完成 (模式: {mode.upper()})", 'success')
    
    def _get_stock_count(self, time_period: str) -> int:
        """根據模式和時段獲取股票數量"""
        base_counts = {
            'morning': 100,
            'mid_morning': 150,
            'mid_day': 150,
            'afternoon': 500,
            'weekly': 500
        }
        
        multiplier = {
            'basic': 1.0,
            'enhanced': 1.5,
            'precise': 1.2,
            'optimized': 2.0
        }
        
        return int(base_counts[time_period] * multiplier.get(self.mode, 1.0))
    
    def _get_recommendation_limits(self, time_period: str) -> Dict[str, int]:
        """根據模式和時段獲取推薦數量限制"""
        base_limits = {
            'morning': {'short_term': 3, 'long_term': 2, 'weak_stocks': 2},
            'mid_morning': {'short_term': 3, 'long_term': 2, 'weak_stocks': 1},
            'mid_day': {'short_term': 3, 'long_term': 3, 'weak_stocks': 2},
            'afternoon': {'short_term': 3, 'long_term': 3, 'weak_stocks': 2},
            'weekly': {'short_term': 2, 'long_term': 4, 'weak_stocks': 3}
        }
        
        limits = base_limits[time_period].copy()
        
        # 優化模式增加長線推薦
        if self.mode == 'optimized':
            limits['long_term'] += 1
            if time_period == 'weekly':
                limits['long_term'] += 1
        
        return limits
    
    def _init_data_fetcher(self):
        """初始化數據獲取器"""
        try:
            from twse_data_fetcher import TWStockDataFetcher
            self.data_fetcher = TWStockDataFetcher()
            log_event("數據獲取器初始化成功", 'success')
        except Exception as e:
            log_event(f"數據獲取器初始化失敗: {e}", 'warning')
    
    def _init_notifier(self):
        """初始化通知系統"""
        try:
            import notifier
            self.notifier = notifier
            notifier.init()
            log_event("通知系統初始化成功", 'success')
        except Exception as e:
            log_event(f"通知系統初始化失敗: {e}", 'warning')
    
    def get_stocks_for_analysis(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """獲取要分析的股票"""
        log_event(f"開始獲取 {time_slot} 時段的股票數據", 'info')
        
        try:
            if self.data_fetcher:
                stocks = self.data_fetcher.get_stocks_by_time_slot(time_slot, date)
            else:
                stocks = self._create_mock_stocks()
            
            # 基本過濾條件
            valid_stocks = []
            for stock in stocks:
                if (stock.get('close', 0) > 0 and 
                    stock.get('volume', 0) > 1000 and
                    stock.get('trade_value', 0) > 100000):
                    valid_stocks.append(stock)
            
            log_event(f"獲取了 {len(valid_stocks)} 支有效股票", 'success')
            return valid_stocks
            
        except Exception as e:
            log_event(f"獲取股票數據失敗: {e}", 'error')
            return self._create_mock_stocks()
    
    def _create_mock_stocks(self) -> List[Dict[str, Any]]:
        """創建模擬股票數據"""
        import random
        
        mock_stocks = []
        stock_list = [
            ('2330', '台積電'), ('2317', '鴻海'), ('2454', '聯發科'),
            ('2881', '富邦金'), ('2882', '國泰金'), ('2609', '陽明'),
            ('2603', '長榮'), ('2615', '萬海'), ('1301', '台塑'),
            ('1303', '南亞'), ('2002', '中鋼'), ('2412', '中華電')
        ]
        
        for code, name in stock_list:
            stock = {
                'code': code,
                'name': name,
                'close': round(random.uniform(50, 600), 1),
                'change': round(random.uniform(-30, 30), 1),
                'change_percent': round(random.uniform(-5, 5), 2),
                'volume': random.randint(10000, 100000),
                'trade_value': random.randint(1000000, 10000000000)
            }
            mock_stocks.append(stock)
        
        return mock_stocks
    
    def analyze_stock_unified(self, stock_info: Dict[str, Any], analysis_focus: str = 'mixed', 
                            historical_data: pd.DataFrame = None) -> Dict[str, Any]:
        """統一股票分析接口"""
        
        analysis_result = {
            'stock_info': {
                'code': stock_info.get('code'),
                'name': stock_info.get('name'),
                'close': stock_info.get('close'),
                'change': stock_info.get('change', 0),
                'change_percent': stock_info.get('change_percent', 0),
                'volume': stock_info.get('volume'),
                'trade_value': stock_info.get('trade_value')
            },
            'analysis_mode': self.mode,
            'analysis_focus': analysis_focus,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if self.mode == 'precise':
                # 精準分析模式
                if analysis_focus == 'short_term':
                    precise_result = self.precise_analyzer.analyze_short_term_precision(stock_info)
                    analysis_result['precise_analysis'] = precise_result
                    analysis_result['weighted_score'] = precise_result['total_score']
                elif analysis_focus == 'long_term':
                    precise_result = self.precise_analyzer.analyze_long_term_precision(stock_info)
                    analysis_result['precise_analysis'] = precise_result
                    analysis_result['weighted_score'] = precise_result['total_score']
                else:
                    # 混合模式
                    short_result = self.precise_analyzer.analyze_short_term_precision(stock_info)
                    long_result = self.precise_analyzer.analyze_long_term_precision(stock_info)
                    analysis_result['precise_analysis'] = {
                        'short_term': short_result,
                        'long_term': long_result,
                        'combined_score': round((short_result['total_score'] + long_result['total_score']) / 2, 2)
                    }
                    analysis_result['weighted_score'] = analysis_result['precise_analysis']['combined_score']
                
            elif self.mode in ['enhanced', 'optimized']:
                # 增強/優化分析模式
                enhanced_result = self.enhanced_analyzer.analyze_stock_enhanced(stock_info, analysis_focus)
                analysis_result['enhanced_analysis'] = enhanced_result
                analysis_result['weighted_score'] = enhanced_result.get('weighted_score', 0)
                
                # 複製重要字段到頂層
                for key in ['trend', 'suggestion', 'reason', 'target_price', 'stop_loss']:
                    if key in enhanced_result:
                        analysis_result[key] = enhanced_result[key]
                
            else:
                # 基礎分析模式
                if historical_data is not None:
                    basic_result = self.base_analyzer.analyze_single_stock(stock_info, historical_data)
                    analysis_result['basic_analysis'] = basic_result
                    analysis_result['weighted_score'] = basic_result.get('score', 0) / 10  # 轉換為0-10分
                else:
                    # 沒有歷史數據時的簡化分析
                    basic_analysis = self._simple_basic_analysis(stock_info)
                    analysis_result['basic_analysis'] = basic_analysis
                    analysis_result['weighted_score'] = basic_analysis.get('score', 0)
            
            # 生成最終建議
            analysis_result['final_recommendation'] = self._generate_unified_recommendation(analysis_result)
            
        except Exception as e:
            log_event(f"分析股票 {stock_info.get('code', 'Unknown')} 時發生錯誤: {e}", 'error')
            # 回退到最基本的分析
            basic_analysis = self._simple_basic_analysis(stock_info)
            analysis_result['basic_analysis'] = basic_analysis
            analysis_result['weighted_score'] = basic_analysis.get('score', 0)
            analysis_result['error_info'] = str(e)
        
        return analysis_result
    
    def _simple_basic_analysis(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """簡化的基礎分析（無歷史數據）"""
        change_percent = stock_info.get('change_percent', 0)
        trade_value = stock_info.get('trade_value', 0)
        name = stock_info.get('name', '')
        
        score = 0
        
        # 價格變動評分
        if change_percent > 5:
            score += 4
        elif change_percent > 3:
            score += 3
        elif change_percent > 1:
            score += 2
        elif change_percent > 0:
            score += 1
        elif change_percent < -5:
            score -= 4
        elif change_percent < -3:
            score -= 3
        elif change_percent < -1:
            score -= 2
        elif change_percent < 0:
            score -= 1
        
        # 成交量評分
        if trade_value > 5000000000:
            score += 2
        elif trade_value > 1000000000:
            score += 1
        elif trade_value < 10000000:
            score -= 1
        
        # 特殊股票加權
        if any(keyword in name for keyword in ['台積電', '聯發科', '鴻海']):
            score += 0.5
        elif any(keyword in name for keyword in ['航運', '海運']):
            score += 0.5
        
        return {
            'score': round(score, 1),
            'change_percent': change_percent,
            'trade_value': trade_value,
            'analysis_method': 'simple_basic'
        }
    
    def _generate_unified_recommendation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成統一的推薦"""
        
        recommendation = {
            'action': '觀望',
            'confidence': 'low',
            'reasoning': [],
            'risk_level': 'medium'
        }
        
        try:
            score = analysis_result.get('weighted_score', 0)
            mode = analysis_result.get('analysis_mode', 'basic')
            
            # 根據不同模式和得分生成建議
            if mode == 'precise':
                precision_data = analysis_result.get('precise_analysis', {})
                
                if isinstance(precision_data, dict) and 'combined_score' in precision_data:
                    # 混合精準分析
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
                else:
                    # 單一精準分析
                    single_data = precision_data if 'grade' in precision_data else list(precision_data.values())[0]
                    grade = single_data.get('grade', 'C')
                    
                    if grade == 'A+':
                        recommendation['action'] = '強烈推薦'
                        recommendation['confidence'] = 'high'
                    elif grade == 'A':
                        recommendation['action'] = '推薦'
                        recommendation['confidence'] = 'medium'
                    elif grade == 'B':
                        recommendation['action'] = '觀察'
                        recommendation['confidence'] = 'medium'
                    else:
                        recommendation['action'] = '避免'
                        recommendation['confidence'] = 'low'
            
            elif mode in ['enhanced', 'optimized']:
                # 增強/優化分析
                if score >= 8:
                    recommendation['action'] = '強烈推薦'
                    recommendation['confidence'] = 'high'
                elif score >= 4:
                    recommendation['action'] = '推薦'
                    recommendation['confidence'] = 'medium'
                elif score >= 1:
                    recommendation['action'] = '觀察'
                    recommendation['confidence'] = 'medium'
                elif score >= -2:
                    recommendation['action'] = '觀望'
                    recommendation['confidence'] = 'low'
                else:
                    recommendation['action'] = '避免'
                    recommendation['confidence'] = 'low'
                
                # 從增強分析中提取理由
                enhanced_data = analysis_result.get('enhanced_analysis', {})
                if 'reason' in enhanced_data:
                    recommendation['reasoning'].append(enhanced_data['reason'])
            
            else:
                # 基礎分析
                if score >= 4:
                    recommendation['action'] = '推薦'
                    recommendation['confidence'] = 'medium'
                elif score >= 2:
                    recommendation['action'] = '觀察'
                    recommendation['confidence'] = 'medium'
                elif score >= 0:
                    recommendation['action'] = '觀望'
                    recommendation['confidence'] = 'low'
                else:
                    recommendation['action'] = '避免'
                    recommendation['confidence'] = 'low'
            
            # 設定風險等級
            if score >= 6:
                recommendation['risk_level'] = 'low'
            elif score >= 2:
                recommendation['risk_level'] = 'medium'
            else:
                recommendation['risk_level'] = 'high'
        
        except Exception as e:
            log_event(f"生成推薦時發生錯誤: {e}", 'warning')
        
        return recommendation
    
    def batch_analyze_stocks(self, stocks_data: List[Dict[str, Any]], 
                           analysis_focus: str = 'mixed',
                           get_historical_func: Optional[Callable] = None,
                           max_workers: int = 4) -> List[Dict[str, Any]]:
        """批量分析股票（支援多線程）"""
        
        results = []
        total_stocks = len(stocks_data)
        
        log_event(f"開始批量分析 {total_stocks} 支股票 (模式: {self.mode.upper()})", 'info')
        
        if max_workers > 1 and total_stocks > 10:
            # 使用多線程處理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_stock = {}
                
                for stock_data in stocks_data:
                    # 獲取歷史數據
                    historical_data = None
                    if get_historical_func:
                        try:
                            historical_data = get_historical_func(stock_data['code'])
                        except:
                            pass
                    
                    # 提交分析任務
                    future = executor.submit(
                        self.analyze_stock_unified, 
                        stock_data, 
                        analysis_focus, 
                        historical_data
                    )
                    future_to_stock[future] = stock_data
                
                # 收集結果
                completed = 0
                for future in as_completed(future_to_stock):
                    try:
                        analysis = future.result()
                        results.append(analysis)
                        completed += 1
                        
                        if completed % 20 == 0:
                            log_event(f"已完成 {completed}/{total_stocks} 支股票的分析", 'info')
                            
                    except Exception as e:
                        stock_data = future_to_stock[future]
                        log_event(f"分析股票 {stock_data.get('code', 'Unknown')} 時發生錯誤: {e}", 'warning')
                        continue
        else:
            # 單線程處理
            for i, stock_data in enumerate(stocks_data):
                try:
                    # 獲取歷史數據
                    historical_data = None
                    if get_historical_func:
                        try:
                            historical_data = get_historical_func(stock_data['code'])
                        except:
                            pass
                    
                    # 執行分析
                    analysis = self.analyze_stock_unified(stock_data, analysis_focus, historical_data)
                    results.append(analysis)
                    
                    # 記錄進度
                    if (i + 1) % 20 == 0:
                        log_event(f"已完成 {i + 1}/{total_stocks} 支股票的分析", 'info')
                    
                except Exception as e:
                    log_event(f"分析股票 {stock_data.get('code', 'Unknown')} 時發生錯誤: {e}", 'warning')
                    continue
        
        log_event(f"批量分析完成，共處理 {len(results)} 支股票", 'success')
        return results
    
    def generate_recommendations(self, analysis_results: List[Dict[str, Any]], 
                               time_slot: str) -> Dict[str, List[Dict[str, Any]]]:
        """生成推薦列表"""
        
        if not analysis_results:
            return {"short_term": [], "long_term": [], "weak_stocks": []}
        
        # 獲取配置
        config = self.time_slot_config[time_slot]
        limits = config['recommendation_limits']
        
        # 過濾有效分析
        valid_analyses = [a for a in analysis_results if a.get('weighted_score') is not None]
        
        # 提取分數用於排序
        for analysis in valid_analyses:
            # 確保每個分析都有必要的字段
            stock_info = analysis.get('stock_info', {})
            analysis['code'] = stock_info.get('code', '')
            analysis['name'] = stock_info.get('name', '')
            analysis['current_price'] = stock_info.get('close', 0)
            analysis['change_percent'] = stock_info.get('change_percent', 0)
            analysis['trade_value'] = stock_info.get('trade_value', 0)
            
            # 生成推薦理由
            if 'reason' not in analysis:
                analysis['reason'] = self._generate_reason_from_analysis(analysis)
        
        # 短線推薦（高分）
        score_threshold = 4 if self.mode == 'optimized' else 2
        short_term_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) >= score_threshold]
        short_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        short_term = []
        for analysis in short_term_candidates[:limits['short_term']]:
            short_term.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "reason": analysis["reason"],
                "target_price": analysis.get("target_price"),
                "stop_loss": analysis.get("stop_loss"),
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        # 長線推薦（根據模式調整標準）
        if self.mode == 'optimized':
            # 優化模式：更嚴格的長線篩選條件
            long_term_candidates = self._filter_optimized_long_term(valid_analyses)
        else:
            # 其他模式：基本長線篩選
            long_term_candidates = [a for a in valid_analyses 
                                  if 0 <= a.get('weighted_score', 0) < score_threshold 
                                  and a.get('trade_value', 0) > 100000000]
        
        long_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        long_term = []
        for analysis in long_term_candidates[:limits['long_term']]:
            long_term.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "reason": analysis["reason"],
                "target_price": analysis.get("target_price"),
                "stop_loss": analysis.get("stop_loss"),
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        # 極弱股（低分警示）
        weak_threshold = -3 if self.mode in ['enhanced', 'optimized'] else -2
        weak_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) <= weak_threshold]
        weak_candidates.sort(key=lambda x: x.get('weighted_score', 0))
        
        weak_stocks = []
        for analysis in weak_candidates[:limits['weak_stocks']]:
            weak_stocks.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "alert_reason": analysis["reason"],
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        return {
            "short_term": short_term,
            "long_term": long_term,
            "weak_stocks": weak_stocks
        }
    
    def _filter_optimized_long_term(self, valid_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """優化模式的長線篩選條件"""
        long_term_candidates = []
        
        for analysis in valid_analyses:
            score = analysis.get('weighted_score', 0)
            
            # 長線推薦條件評估
            conditions_met = 0
            
            # 1. 基本評分條件
            if score >= 2:
                conditions_met += 1
            
            # 2. 基本面條件（從enhanced_analysis中提取）
            enhanced_data = analysis.get('enhanced_analysis', {})
            if enhanced_data.get('dividend_yield', 0) > 2.5:
                conditions_met += 2
            if enhanced_data.get('eps_growth', 0) > 8:
                conditions_met += 2
            if enhanced_data.get('roe', 0) > 12:
                conditions_met += 1
            if enhanced_data.get('pe_ratio', 999) < 20:
                conditions_met += 1
            
            # 3. 法人買超條件
            foreign_net = enhanced_data.get('foreign_net_buy', 0)
            trust_net = enhanced_data.get('trust_net_buy', 0)
            if foreign_net > 5000 or trust_net > 3000:
                conditions_met += 2
            if foreign_net > 20000 or trust_net > 10000:
                conditions_met += 1
            
            # 4. 成交量條件
            if analysis.get('trade_value', 0) > 50000000:
                conditions_met += 1
            
            # 5. 股息穩定性
            if enhanced_data.get('dividend_consecutive_years', 0) > 5:
                conditions_met += 1
            
            # 滿足條件數量 >= 4 且評分 >= 0 才納入長線推薦
            if conditions_met >= 4 and score >= 0:
                long_term_score = score + (conditions_met - 4) * 0.5
                analysis['long_term_score'] = long_term_score
                long_term_candidates.append(analysis)
        
        return long_term_candidates
    
    def _generate_reason_from_analysis(self, analysis: Dict[str, Any]) -> str:
        """從分析結果生成推薦理由"""
        reasons = []
        
        # 基本價格變動
        change_percent = analysis.get('change_percent', 0)
        if abs(change_percent) > 3:
            direction = '大漲' if change_percent > 0 else '大跌'
            reasons.append(f"今日{direction} {abs(change_percent):.1f}%")
        elif abs(change_percent) > 1:
            direction = '上漲' if change_percent > 0 else '下跌'
            reasons.append(f"今日{direction} {abs(change_percent):.1f}%")
        
        # 成交量
        trade_value = analysis.get('trade_value', 0)
        if trade_value > 5000000000:
            reasons.append("成交金額龐大")
        elif trade_value > 1000000000:
            reasons.append("成交活躍")
        
        # 從不同分析模式中提取特定理由
        if self.mode in ['enhanced', 'optimized']:
            enhanced_data = analysis.get('enhanced_analysis', {})
            if 'reason' in enhanced_data:
                reasons.append(enhanced_data['reason'])
        
        elif self.mode == 'precise':
            precise_data = analysis.get('precise_analysis', {})
            if isinstance(precise_data, dict):
                if 'signals' in precise_data:
                    signals = precise_data['signals']
                    if signals:
                        reasons.extend(signals[:2])  # 最多取2個信號
        
        # 如果沒有理由，給個基本描述
        if not reasons:
            price = analysis.get('current_price', 0)
            reasons.append(f"現價 {price} 元，綜合指標顯示投資機會")
        
        return "，".join(reasons)
    
    def run_analysis(self, time_slot: str) -> None:
        """執行完整的分析流程"""
        start_time = time.time()
        log_event(f"開始執行 {time_slot} 分析 (模式: {self.mode.upper()})", 'info')
        
        try:
            # 確保通知系統可用
            if self.notifier and hasattr(self.notifier, 'is_notification_available'):
                if not self.notifier.is_notification_available():
                    log_event("通知系統不可用，嘗試初始化", 'warning')
                    self.notifier.init()
            
            # 獲取股票數據
            stocks = self.get_stocks_for_analysis(time_slot)
            
            if not stocks:
                log_event("無法獲取股票數據", 'error')
                return
            
            # 獲取配置
            config = self.time_slot_config[time_slot]
            analysis_focus = config['analysis_focus']
            expected_count = config['stock_count']
            
            log_event(f"成功獲取 {len(stocks)} 支股票（預期 {expected_count} 支）", 'info')
            log_event(f"分析重點: {analysis_focus}", 'info')
            log_event(f"分析模式: {self.mode.upper()}", 'info')
            
            # 批量分析股票
            analysis_results = self.batch_analyze_stocks(
                stocks, 
                analysis_focus,
                max_workers=4 if len(stocks) > 50 else 1
            )
            
            elapsed_time = time.time() - start_time
            log_event(f"完成 {len(analysis_results)} 支股票分析，耗時 {elapsed_time:.1f} 秒", 'success')
            
            # 統計分析方法
            method_count = {}
            for result in analysis_results:
                method = result.get('analysis_mode', 'unknown')
                method_count[method] = method_count.get(method, 0) + 1
            
            method_stats = [f"{method}:{count}支" for method, count in method_count.items()]
            log_event(f"分析方法統計: {', '.join(method_stats)}", 'info')
            
            # 生成推薦
            recommendations = self.generate_recommendations(analysis_results, time_slot)
            
            # 顯示推薦統計
            short_count = len(recommendations['short_term'])
            long_count = len(recommendations['long_term'])
            weak_count = len(recommendations['weak_stocks'])
            
            log_event(f"推薦結果: 短線 {short_count} 支, 長線 {long_count} 支, 極弱股 {weak_count} 支", 'info')
            
            # 顯示推薦詳情
            if short_count > 0:
                log_event("🔥 短線推薦:", 'info')
                for stock in recommendations['short_term']:
                    analysis_info = stock['analysis']
                    score = analysis_info.get('weighted_score', 0)
                    log_event(f"   {stock['code']} {stock['name']} (評分:{score:.1f})", 'info')
            
            if long_count > 0 and self.mode == 'optimized':
                log_event("💎 長線推薦詳情:", 'info')
                for i, stock in enumerate(recommendations['long_term']):
                    analysis_info = stock['analysis']
                    enhanced_data = analysis_info.get('enhanced_analysis', {})
                    score = analysis_info.get('weighted_score', 0)
                    dividend_yield = enhanced_data.get('dividend_yield', 0)
                    eps_growth = enhanced_data.get('eps_growth', 0)
                    foreign_net = enhanced_data.get('foreign_net_buy', 0)
                    
                    log_event(f"   {i+1}. {stock['code']} {stock['name']} (評分:{score:.1f})", 'info')
                    log_event(f"      殖利率:{dividend_yield:.1f}% | EPS成長:{eps_growth:.1f}% | 外資:{foreign_net//10000:.0f}億", 'info')
            
            # 發送通知
            display_name = config['name']
            self._send_notifications(recommendations, display_name)
            
            # 保存分析結果
            self.save_analysis_results(analysis_results, recommendations, time_slot)
            
            total_time = time.time() - start_time
            log_event(f"{time_slot} 分析完成，總耗時 {total_time:.1f} 秒", 'success')
            
        except Exception as e:
            log_event(f"執行 {time_slot} 分析時發生錯誤: {e}", 'error')
            import traceback
            log_event(traceback.format_exc(), 'error')
    
    def _send_notifications(self, recommendations: Dict[str, List], display_name: str):
        """發送通知"""
        if not self.notifier:
            log_event("通知系統不可用，跳過發送通知", 'warning')
            return
        
        try:
            if hasattr(self.notifier, 'send_combined_recommendations'):
                self.notifier.send_combined_recommendations(recommendations, display_name)
                log_event("推薦通知已發送", 'success')
            else:
                log_event("通知系統不支持發送推薦", 'warning')
        except Exception as e:
            log_event(f"發送通知失敗: {e}", 'error')
    
    def save_analysis_results(self, analyses: List[Dict[str, Any]], 
                            recommendations: Dict[str, List], time_slot: str) -> None:
        """保存分析結果"""
        try:
            # 創建日期目錄
            date_str = datetime.now().strftime('%Y%m%d')
            results_dir = os.path.join(self.data_dir, 'results', date_str)
            os.makedirs(results_dir, exist_ok=True)
            
            # 保存分析結果
            analyses_path = os.path.join(results_dir, f"{time_slot}_analyses_{self.mode}.json")
            with open(analyses_path, 'w', encoding='utf-8') as f:
                json.dump(analyses, f, ensure_ascii=False, indent=2)
            
            # 保存推薦結果
            recommendations_path = os.path.join(results_dir, f"{time_slot}_recommendations_{self.mode}.json")
            with open(recommendations_path, 'w', encoding='utf-8') as f:
                json.dump(recommendations, f, ensure_ascii=False, indent=2)
            
            log_event(f"分析結果已保存到 {results_dir}", 'success')
            
        except Exception as e:
            log_event(f"保存分析結果時發生錯誤: {e}", 'warning')
    
    def export_analysis_results(self, analysis_results: List[Dict[str, Any]], 
                              file_path: str, format: str = 'json') -> bool:
        """導出分析結果"""
        try:
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(analysis_results, f, ensure_ascii=False, indent=2)
            
            elif format.lower() == 'csv':
                # 將結果轉換為DataFrame並導出CSV
                flattened_data = []
                for result in analysis_results:
                    stock_info = result['stock_info']
                    flat_record = {
                        'code': stock_info['code'],
                        'name': stock_info['name'],
                        'close': stock_info['close'],
                        'change_percent': stock_info['change_percent'],
                        'volume': stock_info['volume'],
                        'trade_value': stock_info['trade_value'],
                        'analysis_mode': result.get('analysis_mode', ''),
                        'analysis_focus': result.get('analysis_focus', ''),
                        'weighted_score': result.get('weighted_score', 0),
                        'recommendation': result.get('final_recommendation', {}).get('action', ''),
                        'confidence': result.get('final_recommendation', {}).get('confidence', ''),
                        'timestamp': result.get('timestamp', '')
                    }
                    
                    # 添加增強分析的特定字段
                    if 'enhanced_analysis' in result:
                        enhanced_data = result['enhanced_analysis']
                        flat_record.update({
                            'dividend_yield': enhanced_data.get('dividend_yield', 0),
                            'eps_growth': enhanced_data.get('eps_growth', 0),
                            'pe_ratio': enhanced_data.get('pe_ratio', 0),
                            'roe': enhanced_data.get('roe', 0),
                            'foreign_net_buy': enhanced_data.get('foreign_net_buy', 0),
                            'trust_net_buy': enhanced_data.get('trust_net_buy', 0)
                        })
                    
                    flattened_data.append(flat_record)
                
                df = pd.DataFrame(flattened_data)
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            log_event(f"分析結果已成功導出至: {file_path}", 'success')
            return True
            
        except Exception as e:
            log_event(f"導出分析結果失敗: {e}", 'error')
            return False
    
    def get_top_recommendations(self, analysis_results: List[Dict[str, Any]], 
                              recommendation_type: str = 'short_term',
                              limit: int = 5) -> List[Dict[str, Any]]:
        """獲取頂級推薦股票"""
        scored_stocks = []
        
        for result in analysis_results:
            try:
                score = result.get('weighted_score', 0)
                
                if score > 0:
                    scored_stocks.append({
                        'stock_info': result['stock_info'],
                        'score': score,
                        'analysis_data': result
                    })
                    
            except Exception as e:
                log_event(f"處理推薦時發生錯誤: {e}", 'warning')
                continue
        
        # 按分數排序並限制數量
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = scored_stocks[:limit]
        
        log_event(f"生成 {len(top_recommendations)} 個 {recommendation_type} 推薦", 'info')
        return top_recommendations

# ==================== 排程和系統管理 ====================

def setup_schedule(analyzer: UnifiedStockAnalyzer):
    """設置排程任務"""
    try:
        # 嘗試從配置文件讀取排程
        try:
            from config import NOTIFICATION_SCHEDULE
        except ImportError:
            # 默認時間表
            NOTIFICATION_SCHEDULE = {
                'morning_scan': '09:00',
                'mid_morning_scan': '10:30',
                'mid_day_scan': '12:30',
                'afternoon_scan': '15:00',
                'weekly_summary': '17:00',
                'heartbeat': '08:30'
            }
        
        log_event("設置排程任務...", 'info')
        
        # 工作日排程
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        
        # 早盤掃描
        for day in weekdays:
            getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['morning_scan']).do(
                analyzer.run_analysis, 'morning_scan'
            )
        
        # 盤中掃描
        for day in weekdays:
            getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(
                analyzer.run_analysis, 'mid_morning_scan'
            )
        
        # 午間掃描
        for day in weekdays:
            getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(
                analyzer.run_analysis, 'mid_day_scan'
            )
        
        # 盤後掃描
        for day in weekdays:
            getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(
                analyzer.run_analysis, 'afternoon_scan'
            )
        
        # 週末總結
        schedule.every().friday.at(NOTIFICATION_SCHEDULE['weekly_summary']).do(
            analyzer.run_analysis, 'weekly_summary'
        )
        
        # 心跳檢測
        if analyzer.notifier and hasattr(analyzer.notifier, 'send_heartbeat'):
            schedule.every().day.at(NOTIFICATION_SCHEDULE['heartbeat']).do(
                analyzer.notifier.send_heartbeat
            )
        
        log_event("排程任務設置完成", 'success')
        return True
        
    except Exception as e:
        log_event(f"排程設置失敗: {e}", 'error')
        return False

def check_environment():
    """檢查環境配置"""
    try:
        # 檢查必要的套件
        import requests
        import pandas
        import numpy
        
        # 檢查環境變數
        if 'GITHUB_ACTIONS' in os.environ or 'CI' in os.environ:
            log_event("檢測到CI環境，使用環境變數配置", 'info')
        
        # 檢查配置文件
        try:
            from config import EMAIL_CONFIG, LOG_DIR, DATA_DIR
            
            if EMAIL_CONFIG['enabled']:
                if not all([EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'], EMAIL_CONFIG['receiver']]):
                    if 'GITHUB_ACTIONS' in os.environ or 'CI' in os.environ:
                        log_event("CI環境中檢測到電子郵件設定不完整", 'warning')
                        log_event(f"EMAIL_SENDER={'已設置' if os.getenv('EMAIL_SENDER') else '未設置'}", 'info')
                        log_event(f"EMAIL_RECEIVER={'已設置' if os.getenv('EMAIL_RECEIVER') else '未設置'}", 'info')
                        log_event(f"EMAIL_PASSWORD={'已設置' if os.getenv('EMAIL_PASSWORD') else '未設置'}", 'info')
                    else:
                        log_event("電子郵件設定不完整，請檢查.env文件", 'warning')
                    return False
            
            # 檢查目錄結構
            for directory in [LOG_DIR, DATA_DIR]:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    log_event(f"已創建目錄: {directory}", 'info')
                    
        except ImportError:
            log_event("無法導入config模組，將使用默認設置", 'warning')
        
        return True
        
    except ImportError as e:
        log_event(f"缺少必要的套件: {e}", 'error')
        log_event("請執行 pip install -r requirements.txt 安裝必要的套件", 'error')
        return False
    
    except Exception as e:
        log_event(f"環境檢查失敗: {e}", 'error')
        return False

# ==================== 命令行界面和主函數 ====================

def run_daemon(mode='basic'):
    """運行後台服務"""
    log_event(f"啟動統一股票分析系統 (模式: {mode.upper()})", 'info')
    print("=" * 60)
    
    # 顯示模式特色
    mode_features = {
        'optimized': [
            "💎 優化版特色:",
            "  • 長線推薦權重優化: 基本面 1.2倍, 法人 0.8倍",
            "  • 重視高殖利率股票 (>2.5% 優先推薦)",
            "  • 重視EPS高成長股票 (>8% 優先推薦)",
            "  • 重視法人買超股票 (>5000萬優先推薦)",
            "  • 強化通知顯示: 詳細基本面資訊"
        ],
        'precise': [
            "🎯 精準版特色:",
            "  • 多維度精準評分系統",
            "  • 短線技術動能分析",
            "  • 長線基本面品質評估",
            "  • A+/A/B/C/D 五級評等",
            "  • 信心指數和風險評估"
        ],
        'enhanced': [
            "🔧 增強版特色:",
            "  • 技術面與基本面雙重分析",
            "  • 智能權重配置系統",
            "  • 法人買賣動向分析",
            "  • 增強版推薦算法"
        ],
        'basic': [
            "⚡ 基礎版特色:",
            "  • 快速技術面分析",
            "  • 穩定可靠的推薦算法",
            "  • 輕量級資源占用",
            "  • 適合快速部署"
        ]
    }
    
    for line in mode_features.get(mode, mode_features['basic']):
        print(line)
    
    print("=" * 60)
    
    # 初始化分析器
    analyzer = UnifiedStockAnalyzer(mode)
    
    # 設置排程
    if not setup_schedule(analyzer):
        print("❌ 排程設置失敗，程序退出")
        return
    
    # 啟動時發送心跳
    if analyzer.notifier and hasattr(analyzer.notifier, 'send_heartbeat'):
        print("💓 發送啟動心跳...")
        try:
            analyzer.notifier.send_heartbeat()
        except:
            pass
    
    print(f"\n🎯 {mode.upper()}模式系統已啟動，開始執行排程任務...")
    print("📝 按 Ctrl+C 停止系統")
    
    # 運行排程循環
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # 每30秒檢查一次
    except KeyboardInterrupt:
        print("\n\n⚠️ 收到用戶中斷信號")
        print("🛑 正在優雅關閉系統...")
        
        # 發送關閉通知
        if analyzer.notifier and hasattr(analyzer.notifier, 'send_notification'):
            try:
                close_message = f"""📴 統一股票分析系統關閉通知

⏰ 關閉時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 運行模式: {mode.upper()}

✅ 系統已安全關閉
感謝使用統一股票分析系統！

祝您投資順利！💰"""
                
                analyzer.notifier.send_notification(close_message, f"📴 {mode.upper()}模式系統關閉通知")
            except:
                pass
        
        print("👋 系統已關閉")
    except Exception as e:
        log_event(f"系統運行出現錯誤: {e}", 'error')
        print("🔄 請檢查錯誤並重新啟動系統")

def run_single_analysis(time_slot, mode='basic'):
    """執行單次分析"""
    print(f"🔍 執行 {mode.upper()} 模式 {time_slot} 分析...")
    
    try:
        # 初始化分析器
        analyzer = UnifiedStockAnalyzer(mode)
        
        # 執行分析
        analyzer.run_analysis(time_slot)
        
        print(f"✅ {time_slot} 分析完成！")
        print("📧 分析報告已發送，請檢查您的郵箱")
        
    except Exception as e:
        log_event(f"分析執行失敗: {e}", 'error')
        import traceback
        print(traceback.format_exc())

def test_notification(test_type='all', mode='basic'):
    """測試通知系統"""
    print(f"📧 測試 {mode.upper()} 模式通知系統...")
    
    try:
        # 初始化分析器
        analyzer = UnifiedStockAnalyzer(mode)
        
        if not analyzer.notifier:
            print("❌ 通知系統不可用")
            return
        
        # 創建測試數據
        test_data = {
            "short_term": [
                {
                    "code": "2330",
                    "name": "台積電", 
                    "current_price": 638.5,
                    "reason": f"{mode.upper()}模式技術面轉強，MACD金叉",
                    "target_price": 670.0,
                    "stop_loss": 620.0,
                    "trade_value": 14730000000,
                    "analysis": {
                        "change_percent": 2.35,
                        "weighted_score": 7.2
                    }
                }
            ],
            "long_term": [
                {
                    "code": "2609",
                    "name": "陽明",
                    "current_price": 91.2,
                    "reason": f"{mode.upper()}模式分析：高殖利率7.2%，EPS成長35.6%",
                    "target_price": 110.0,
                    "stop_loss": 85.0,
                    "trade_value": 4560000000,
                    "analysis": {
                        "change_percent": 1.8,
                        "weighted_score": 6.8
                    }
                }
            ],
            "weak_stocks": []
        }
        
        analyzer._send_notifications(test_data, f"{mode.upper()}模式功能測試")
        
        print("✅ 測試通知已發送！")
        print("📋 請檢查郵箱確認通知內容")
        
    except Exception as e:
        log_event(f"測試通知失敗: {e}", 'error')
        import traceback
        print(traceback.format_exc())

def show_status(mode='basic'):
    """顯示系統狀態"""
    print("📊 統一股票分析系統狀態")
    print("=" * 50)
    print(f"🔧 當前模式: {mode.upper()}")
    
    try:
        # 嘗試初始化分析器
        analyzer = UnifiedStockAnalyzer(mode)
        print("✅ 分析器初始化: 成功")
        
        # 檢查通知狀態
        if analyzer.notifier:
            if hasattr(analyzer.notifier, 'is_notification_available'):
                if analyzer.notifier.is_notification_available():
                    print("📧 通知系統: 可用")
                else:
                    print("⚠️ 通知系統: 不可用")
            else:
                print("📧 通知系統: 已載入")
        else:
            print("❌ 通知系統: 不可用")
        
        # 顯示模式特色
        mode_info = {
            'optimized': {
                'features': [
                    "📈 長線推薦基本面權重: 1.2倍",
                    "🏦 法人買賣權重: 0.8倍",
                    "💸 殖利率 > 2.5% 優先推薦",
                    "📊 EPS成長 > 8% 優先推薦",
                    "💰 法人買超 > 5000萬優先推薦"
                ]
            },
            'precise': {
                'features': [
                    "🎯 多維度精準評分",
                    "📊 A+/A/B/C/D 五級評等",
                    "📈 短線技術動能分析",
                    "📋 長線基本面品質評估",
                    "🔍 信心指數計算"
                ]
            },
            'enhanced': {
                'features': [
                    "🔧 技術面與基本面雙重分析",
                    "⚡ 智能權重配置",
                    "🎯 精確目標價位設定",
                    "📊 增強版推薦算法",
                    "🏦 法人買賣動向分析"
                ]
            },
            'basic': {
                'features': [
                    "⚡ 快速技術面分析",
                    "🛡️ 穩定推薦算法",
                    "💡 輕量級資源占用",
                    "🚀 快速部署",
                    "📊 基礎指標分析"
                ]
            }
        }
        
        print(f"\n💎 {mode.upper()}模式特色:")
        for feature in mode_info[mode]['features']:
            print(f"  {feature}")
        
        print("\n📅 排程時段:")
        config = analyzer.time_slot_config
        for slot, info in config.items():
            stock_count = info['stock_count']
            name = info['name']
            focus = info['analysis_focus']
            print(f"  📊 {name}: {stock_count}支股票 ({focus})")
        
        print(f"\n💾 數據目錄: {analyzer.data_dir}")
        print(f"📋 可用分析器: 基礎、增強、精準")
        
    except Exception as e:
        log_event(f"系統狀態檢查失敗: {e}", 'error')

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='統一台股分析系統 - 支援基礎、增強、精準、優化四種分析模式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 啟動後台服務（優化模式）
  python unified_stock_analyzer.py start --mode optimized
  
  # 執行單次分析
  python unified_stock_analyzer.py run --slot afternoon_scan --mode precise
  
  # 測試通知系統
  python unified_stock_analyzer.py test --mode enhanced
  
  # 查看系統狀態
  python unified_stock_analyzer.py status --mode optimized

分析模式說明:
  basic     - 基礎模式：快速技術面分析
  enhanced  - 增強模式：技術面+基本面+法人分析
  precise   - 精準模式：多維度評分+A-D分級
  optimized - 優化模式：針對長線投資優化的權重配置
        """
    )
    
    parser.add_argument('command', 
                       choices=['start', 'run', 'status', 'test', 'export'],
                       help='執行命令')
    
    parser.add_argument('--mode', '-m',
                       choices=['basic', 'enhanced', 'precise', 'optimized'],
                       default='basic',
                       help='分析模式 (預設: basic)')
    
    parser.add_argument('--slot', '-s',
                       choices=['morning_scan', 'mid_morning_scan', 'mid_day_scan', 
                               'afternoon_scan', 'weekly_summary'],
                       help='分析時段 (配合 run 命令使用)')
    
    parser.add_argument('--test-type', '-t',
                       choices=['all', 'simple', 'combined'],
                       default='all', 
                       help='測試類型')
    
    parser.add_argument('--data-dir', '-d',
                       default='data',
                       help='數據目錄 (預設: data)')
    
    parser.add_argument('--log-level', '-l',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='日誌級別 (預設: INFO)')
    
    parser.add_argument('--output', '-o',
                       help='輸出文件路徑 (配合 export 命令使用)')
    
    parser.add_argument('--format', '-f',
                       choices=['json', 'csv'],
                       default='json',
                       help='導出格式 (預設: json)')
    
    args = parser.parse_args()
    
    # 設置日誌
    log_file = os.path.join(args.data_dir, 'logs', f'unified_analyzer_{datetime.now().strftime("%Y%m%d")}.log')
    setup_logging(args.log_level, log_file)
    
    # 檢查環境
    if not check_environment():
        print("環境檢查失敗，請修復上述問題再嘗試")
        return
    
    # 執行相應的命令
    if args.command == 'start':
        run_daemon(args.mode)
        
    elif args.command == 'run':
        if not args.slot:
            print("❌ 使用 run 命令時必須指定 --slot 參數")
            print("📝 範例: python unified_stock_analyzer.py run --slot afternoon_scan --mode optimized")
            return
        
        run_single_analysis(args.slot, args.mode)
        
    elif args.command == 'status':
        show_status(args.mode)
        
    elif args.command == 'test':
        test_notification(args.test_type, args.mode)
        
    elif args.command == 'export':
        if not args.output:
            print("❌ 使用 export 命令時必須指定 --output 參數")
            return
        
        # 這裡可以添加導出歷史分析結果的功能
        print(f"🔄 導出功能開發中... (目標: {args.output}, 格式: {args.format})")
    
    else:
        parser.print_help()

# ==================== 演示函數 ====================

def demo_unified_analysis():
    """演示統一分析系統的功能"""
    
    print("=== 統一股票分析系統演示 ===\n")
    
    # 測試股票數據
    test_stocks = [
        {
            'code': '2330',
            'name': '台積電',
            'close': 638.0,
            'change': 15.0,
            'change_percent': 2.4,
            'volume': 25000000,
            'trade_value': 15950000000
        },
        {
            'code': '2609',
            'name': '陽明',
            'close': 91.2,
            'change': 1.6,
            'change_percent': 1.8,
            'volume': 50000000,
            'trade_value': 4560000000
        }
    ]
    
    modes = ['basic', 'enhanced', 'precise', 'optimized']
    
    for mode in modes:
        print(f"\n{'='*20} {mode.upper()} 模式演示 {'='*20}")
        
        try:
            # 初始化分析器
            analyzer = UnifiedStockAnalyzer(mode)
            
            # 分析第一支股票
            stock = test_stocks[0]
            result = analyzer.analyze_stock_unified(stock, 'mixed')
            
            print(f"股票: {result['stock_info']['name']} ({result['stock_info']['code']})")
            print(f"現價: {result['stock_info']['close']} 漲跌: {result['stock_info']['change_percent']:.1f}%")
            print(f"分析模式: {result['analysis_mode']}")
            print(f"綜合評分: {result.get('weighted_score', 0):.1f}")
            
            recommendation = result.get('final_recommendation', {})
            print(f"投資建議: {recommendation.get('action', 'N/A')}")
            print(f"信心度: {recommendation.get('confidence', 'N/A')}")
            
            if mode in ['enhanced', 'optimized']:
                enhanced_data = result.get('enhanced_analysis', {})
                if enhanced_data:
                    print(f"推薦理由: {enhanced_data.get('reason', 'N/A')}")
                    print(f"目標價: {enhanced_data.get('target_price', 'N/A')}")
            
            elif mode == 'precise':
                precise_data = result.get('precise_analysis', {})
                if isinstance(precise_data, dict) and 'combined_score' in precise_data:
                    short_grade = precise_data['short_term']['grade']
                    long_grade = precise_data['long_term']['grade']
                    print(f"短線評級: {short_grade}, 長線評級: {long_grade}")
                elif 'grade' in precise_data:
                    print(f"評級: {precise_data['grade']}")
            
        except Exception as e:
            print(f"❌ {mode} 模式演示失敗: {e}")
    
    print(f"\n{'='*60}")
    print("✅ 演示完成！統一分析系統支援多種分析模式，")
    print("可根據不同需求選擇最適合的分析方式。")

if __name__ == "__main__":
    # 檢查是否為演示模式
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        demo_unified_analysis()
    else:
        main()
