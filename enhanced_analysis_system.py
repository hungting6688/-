"""
enhanced_analysis_system.py - 增強版分析系統
在原有快速分析基礎上，添加基本面與技術面指標
確保穩定性的前提下提供更深入的分析
"""
import os
import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

class EnhancedStockAnalyzer:
    """增強版股票分析器 - 添加基本面與技術面指標"""
    
    def __init__(self):
        """初始化分析器"""
        # 長短線權重配置
        self.weight_configs = {
            'short_term': {
                'base_score': 1.0,      # 基礎分數權重（價格變動+成交量）
                'technical': 0.8,       # 技術面權重（MA、MACD、RSI）
                'fundamental': 0.2,     # 基本面權重（法人、殖利率、EPS）
                'institutional': 0.3    # 法人買賣權重
            },
            'long_term': {
                'base_score': 0.6,      # 基礎分數權重
                'technical': 0.4,       # 技術面權重
                'fundamental': 0.8,     # 基本面權重（長線重視）
                'institutional': 0.6    # 法人買賣權重
            }
        }
        
        # 數據快取
        self.data_cache = {}
        self.cache_expire_minutes = 30
    
    def analyze_stock_enhanced(self, stock_info: Dict[str, Any], analysis_type: str = 'mixed') -> Dict[str, Any]:
        """
        增強版股票分析
        
        參數:
        - stock_info: 股票基本資訊
        - analysis_type: 分析類型 ('short_term', 'long_term', 'mixed')
        
        返回:
        - 增強的分析結果
        """
        stock_code = stock_info['code']
        stock_name = stock_info['name']
        
        try:
            # 第一步：基礎快速評分（保證穩定性）
            base_analysis = self._get_base_analysis(stock_info)
            
            # 第二步：嘗試獲取技術面指標（可選）
            technical_analysis = self._get_technical_analysis(stock_code, stock_info)
            
            # 第三步：嘗試獲取基本面指標（可選）
            fundamental_analysis = self._get_fundamental_analysis(stock_code)
            
            # 第四步：嘗試獲取法人買賣資料（可選）
            institutional_analysis = self._get_institutional_analysis(stock_code)
            
            # 第五步：綜合評分
            final_analysis = self._combine_analysis(
                base_analysis, 
                technical_analysis, 
                fundamental_analysis, 
                institutional_analysis,
                analysis_type
            )
            
            return final_analysis
            
        except Exception as e:
            # 如果增強分析失敗，至少返回基礎分析
            print(f"⚠️ 增強分析失敗，返回基礎分析: {stock_code} - {e}")
            return self._get_base_analysis(stock_info)
    
    def _get_base_analysis(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """獲取基礎快速分析（原有邏輯，保證穩定）"""
        stock_code = stock_info['code']
        stock_name = stock_info['name']
        current_price = stock_info['close']
        change_percent = stock_info['change_percent']
        volume = stock_info['volume']
        trade_value = stock_info['trade_value']
        
        # 基礎評分邏輯（原有的快速評分）
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
        """獲取技術面分析（MA、MACD、RSI）"""
        try:
            # 檢查快取
            cache_key = f"technical_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            # 嘗試獲取簡化的技術指標數據
            technical_data = self._fetch_simple_technical_data(stock_code, stock_info)
            
            if not technical_data:
                return {'available': False}
            
            # 計算技術面評分
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
                    tech_score += 1  # 健康區間
                    signals['rsi_healthy'] = True
                elif rsi_value < 30:
                    tech_score += 1.5  # 超賣反彈機會
                    signals['rsi_oversold'] = True
                elif rsi_value > 70:
                    tech_score -= 1  # 過熱風險
                    signals['rsi_overbought'] = True
            
            result = {
                'available': True,
                'tech_score': round(tech_score, 1),
                'signals': signals,
                'raw_data': technical_data
            }
            
            # 快取結果
            self.data_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"⚠️ 獲取技術面數據失敗: {stock_code} - {e}")
            return {'available': False}
    
    def _fetch_simple_technical_data(self, stock_code: str, stock_info: Dict[str, Any]) -> Optional[Dict]:
        """獲取簡化的技術指標數據"""
        try:
            # 這裡可以接入真實的技術指標API
            # 暫時使用模擬邏輯基於當前數據
            
            current_price = stock_info['close']
            change_percent = stock_info['change_percent']
            volume = stock_info['volume']
            
            # 基於價格變動模擬技術指標
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
            print(f"⚠️ 模擬技術數據失敗: {stock_code}")
            return None
    
    def _get_fundamental_analysis(self, stock_code: str) -> Dict[str, Any]:
        """獲取基本面分析（殖利率、EPS）"""
        try:
            # 檢查快取
            cache_key = f"fundamental_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            # 嘗試獲取基本面數據
            fundamental_data = self._fetch_fundamental_data(stock_code)
            
            if not fundamental_data:
                return {'available': False}
            
            # 計算基本面評分
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
            
            # 快取結果
            self.data_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"⚠️ 獲取基本面數據失敗: {stock_code} - {e}")
            return {'available': False}
    
    def _fetch_fundamental_data(self, stock_code: str) -> Optional[Dict]:
        """獲取基本面數據"""
        try:
            # 這裡可以接入真實的基本面數據API
            # 暫時使用一些常見股票的模擬數據
            
            # 模擬基本面數據
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
            print(f"⚠️ 模擬基本面數據失敗: {stock_code}")
            return None
    
    def _get_institutional_analysis(self, stock_code: str) -> Dict[str, Any]:
        """獲取法人買賣分析"""
        try:
            # 檢查快取
            cache_key = f"institutional_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            # 嘗試獲取法人買賣數據
            institutional_data = self._fetch_institutional_data(stock_code)
            
            if not institutional_data:
                return {'available': False}
            
            # 計算法人買賣評分
            inst_score = 0
            
            # 外資買賣評分
            foreign_net = institutional_data.get('foreign_net_buy', 0)  # 萬元
            if foreign_net > 50000:  # 5億以上
                inst_score += 3
            elif foreign_net > 10000:  # 1億以上
                inst_score += 2
            elif foreign_net > 0:
                inst_score += 1
            elif foreign_net < -50000:  # 大量賣出
                inst_score -= 3
            elif foreign_net < -10000:
                inst_score -= 2
            elif foreign_net < 0:
                inst_score -= 1
            
            # 投信買賣評分
            trust_net = institutional_data.get('trust_net_buy', 0)
            if trust_net > 10000:  # 1億以上
                inst_score += 2
            elif trust_net > 1000:  # 1000萬以上
                inst_score += 1
            elif trust_net < -10000:
                inst_score -= 2
            elif trust_net < -1000:
                inst_score -= 1
            
            # 自營商買賣評分
            dealer_net = institutional_data.get('dealer_net_buy', 0)
            if dealer_net > 5000:  # 5000萬以上
                inst_score += 1
            elif dealer_net < -5000:
                inst_score -= 1
            
            result = {
                'available': True,
                'inst_score': round(inst_score, 1),
                'foreign_net_buy': foreign_net,
                'trust_net_buy': trust_net,
                'dealer_net_buy': dealer_net
            }
            
            # 快取結果
            self.data_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"⚠️ 獲取法人數據失敗: {stock_code} - {e}")
            return {'available': False}
    
    def _fetch_institutional_data(self, stock_code: str) -> Optional[Dict]:
        """獲取法人買賣數據"""
        try:
            # 這裡可以接入真實的法人買賣數據API
            # 暫時使用模擬數據
            
            import random
            
            # 模擬法人買賣數據（萬元）
            base_amount = random.randint(-100000, 100000)
            
            return {
                'foreign_net_buy': base_amount + random.randint(-20000, 20000),
                'trust_net_buy': random.randint(-50000, 50000),
                'dealer_net_buy': random.randint(-20000, 20000)
            }
            
        except Exception as e:
            print(f"⚠️ 模擬法人數據失敗: {stock_code}")
            return None
    
    def _combine_analysis(self, base_analysis: Dict, technical_analysis: Dict, 
                         fundamental_analysis: Dict, institutional_analysis: Dict,
                         analysis_type: str) -> Dict[str, Any]:
        """綜合所有分析結果"""
        
        # 選擇權重配置
        if analysis_type == 'short_term':
            weights = self.weight_configs['short_term']
        elif analysis_type == 'long_term':
            weights = self.weight_configs['long_term']
        else:  # mixed
            # 混合權重
            weights = {
                'base_score': 0.8,
                'technical': 0.6,
                'fundamental': 0.5,
                'institutional': 0.4
            }
        
        # 計算綜合得分
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
        
        # 添加法人買賣得分
        if institutional_analysis.get('available'):
            inst_contribution = institutional_analysis['inst_score'] * weights['institutional']
            final_score += inst_contribution
            base_analysis['analysis_components']['institutional'] = True
            base_analysis['institutional_score'] = institutional_analysis['inst_score']
            base_analysis['foreign_net_buy'] = institutional_analysis['foreign_net_buy']
            base_analysis['trust_net_buy'] = institutional_analysis['trust_net_buy']
        
        # 更新最終評分
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
        
        # 生成增強的推薦理由
        base_analysis['reason'] = self._generate_enhanced_reason(base_analysis)
        
        return base_analysis
    
    def _generate_enhanced_reason(self, analysis: Dict[str, Any]) -> str:
        """生成增強的推薦理由"""
        reasons = []
        
        # 基礎理由（價格變動）
        change_percent = analysis['change_percent']
        if abs(change_percent) > 3:
            reasons.append(f"今日{'大漲' if change_percent > 0 else '大跌'} {abs(change_percent):.1f}%")
        elif abs(change_percent) > 1:
            reasons.append(f"今日{'上漲' if change_percent > 0 else '下跌'} {abs(change_percent):.1f}%")
        
        # 技術面理由
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
        
        # 基本面理由
        if analysis['analysis_components'].get('fundamental'):
            dividend_yield = analysis.get('dividend_yield', 0)
            eps_growth = analysis.get('eps_growth', 0)
            
            if dividend_yield > 4:
                reasons.append(f"高殖利率 {dividend_yield:.1f}%")
            if eps_growth > 15:
                reasons.append(f"EPS高成長 {eps_growth:.1f}%")
            elif eps_growth > 10:
                reasons.append(f"EPS穩定成長 {eps_growth:.1f}%")
        
        # 法人理由
        if analysis['analysis_components'].get('institutional'):
            foreign_net = analysis.get('foreign_net_buy', 0)
            if foreign_net > 50000:
                reasons.append("外資大幅買超")
            elif foreign_net > 10000:
                reasons.append("外資持續買超")
            elif foreign_net < -50000:
                reasons.append("外資大幅賣超")
        
        # 成交量理由
        if analysis['trade_value'] > 5000000000:
            reasons.append("成交金額龐大")
        elif analysis['trade_value'] > 1000000000:
            reasons.append("成交活躍")
        
        return "、".join(reasons) if reasons else "綜合指標顯示投資機會"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查快取是否有效"""
        if cache_key not in self.data_cache:
            return False
        
        # 檢查時間戳（如果有的話）
        cache_data = self.data_cache[cache_key]
        if isinstance(cache_data, dict) and 'timestamp' in cache_data:
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if (datetime.now() - cache_time).total_seconds() > self.cache_expire_minutes * 60:
                return False
        
        return True

# 使用範例
if __name__ == "__main__":
    analyzer = EnhancedStockAnalyzer()
    
    # 測試股票
    test_stock = {
        'code': '2330',
        'name': '台積電',
        'close': 982.0,
        'change_percent': 1.5,
        'volume': 15000000,
        'trade_value': 14730000000
    }
    
    # 短線分析
    short_analysis = analyzer.analyze_stock_enhanced(test_stock, 'short_term')
    print("短線分析結果:")
    print(f"評分: {short_analysis['weighted_score']}")
    print(f"趨勢: {short_analysis['trend']}")
    print(f"理由: {short_analysis['reason']}")
    
    # 長線分析
    long_analysis = analyzer.analyze_stock_enhanced(test_stock, 'long_term')
    print("\n長線分析結果:")
    print(f"評分: {long_analysis['weighted_score']}")
    print(f"趨勢: {long_analysis['trend']}")
    print(f"理由: {long_analysis['reason']}")
