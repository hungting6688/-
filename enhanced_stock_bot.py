"""
enhanced_stock_bot.py - 全整合版增強股市機器人
包含基本面、技術面、法人買賣分析的完整版本
增強長線推薦邏輯：納入EPS、法人買超、殖利率高者
"""
import os
import time
import json
import logging
import schedule
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 引入配置和通知
from config import (
    STOCK_ANALYSIS, 
    NOTIFICATION_SCHEDULE, 
    MARKET_HOURS, 
    LOG_CONFIG, 
    DATA_DIR,
    LOG_DIR
)
import notifier

# 引入台股數據獲取器
from twse_data_fetcher import TWStockDataFetcher

# 設置日誌
logging.basicConfig(
    filename=LOG_CONFIG['filename'],
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format']
)

def log_event(message, level='info'):
    """記錄事件並打印到控制台"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    if level == 'error':
        logging.error(message)
        print(f"[{timestamp}] ❌ {message}")
    elif level == 'warning':
        logging.warning(message)
        print(f"[{timestamp}] ⚠️ {message}")
    else:
        logging.info(message)
        print(f"[{timestamp}] ℹ️ {message}")

class EnhancedStockBot:
    """增強版股市機器人 - 整合基本面、技術面、法人分析"""
    
    def __init__(self):
        """初始化機器人"""
        self.data_fetcher = TWStockDataFetcher()
        self.cache_dir = os.path.join(DATA_DIR, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 數據快取
        self.data_cache = {}
        self.cache_expire_minutes = 30
        
        # 長短線權重配置
        self.weight_configs = {
            'short_term': {
                'base_score': 1.0,      # 基礎分數權重（價格變動+成交量）
                'technical': 0.8,       # 技術面權重（MA、MACD、RSI）
                'fundamental': 0.2,     # 基本面權重（法人、殖利率、EPS）
                'institutional': 0.3    # 法人買賣權重
            },
            'long_term': {
                'base_score': 0.4,      # 基礎分數權重（降低）
                'technical': 0.3,       # 技術面權重（降低）
                'fundamental': 1.2,     # 基本面權重（大幅提高）
                'institutional': 0.8    # 法人買賣權重（提高）
            },
            'mixed': {
                'base_score': 0.8,
                'technical': 0.6,
                'fundamental': 0.7,     # 增加基本面權重
                'institutional': 0.5
            }
        }
        
        # 時段配置 - 更新掃描股數
        self.time_slot_config = {
            'morning_scan': {
                'name': '早盤掃描',
                'stock_count': 200,          # 早盤：200檔
                'analysis_focus': 'short_term',  # 早盤重技術面
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 2,
                    'weak_stocks': 2
                }
            },
            'mid_morning_scan': {
                'name': '盤中掃描',
                'stock_count': 300,          # 盤中：300檔
                'analysis_focus': 'short_term',
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 2,
                    'weak_stocks': 1
                }
            },
            'mid_day_scan': {
                'name': '午間掃描',
                'stock_count': 300,          # 午間：300檔
                'analysis_focus': 'mixed',  # 午間混合分析
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 3,          # 增加長線推薦數量
                    'weak_stocks': 1
                }
            },
            'afternoon_scan': {
                'name': '盤後掃描',
                'stock_count': 1000,         # 盤後：1000檔
                'analysis_focus': 'mixed',  # 盤後全面分析
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 4,          # 增加長線推薦數量
                    'weak_stocks': 2
                }
            },
            'weekly_summary': {
                'name': '週末總結',
                'stock_count': 500,          # 週末：500檔
                'analysis_focus': 'long_term',  # 週末重基本面
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 5,          # 週末更多長線推薦
                    'weak_stocks': 3
                }
            }
        }
    
    def get_stocks_for_analysis(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """獲取要分析的股票"""
        log_event(f"🔍 開始獲取 {time_slot} 時段的股票數據")
        
        try:
            stocks = self.data_fetcher.get_stocks_by_time_slot(time_slot, date)
            
            # 基本過濾條件
            valid_stocks = []
            for stock in stocks:
                if (stock.get('close', 0) > 0 and 
                    stock.get('volume', 0) > 1000 and
                    stock.get('trade_value', 0) > 100000):
                    valid_stocks.append(stock)
            
            log_event(f"✅ 獲取了 {len(valid_stocks)} 支有效股票")
            return valid_stocks
            
        except Exception as e:
            log_event(f"❌ 獲取股票數據失敗: {e}", level='error')
            return []
    
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
            log_event(f"⚠️ 增強分析失敗，返回基礎分析: {stock_code} - {e}", level='warning')
            return self._get_base_analysis(stock_info)
    
    def _get_base_analysis(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """獲取基礎快速分析（原有邏輯，保證穩定）"""
        stock_code = stock_info['code']
        stock_name = stock_info['name']
        current_price = stock_info['close']
        change_percent = stock_info['change_percent']
        volume = stock_info['volume']
        trade_value = stock_info['trade_value']
        
        # 基礎評分邏輯
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
            log_event(f"⚠️ 獲取技術面數據失敗: {stock_code} - {e}", level='warning')
            return {'available': False}
    
    def _fetch_simple_technical_data(self, stock_code: str, stock_info: Dict[str, Any]) -> Optional[Dict]:
        """獲取簡化的技術指標數據"""
        try:
            # 基於當前數據模擬技術指標
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
            log_event(f"⚠️ 模擬技術數據失敗: {stock_code}", level='warning')
            return None
    
    def _get_fundamental_analysis(self, stock_code: str) -> Dict[str, Any]:
        """獲取基本面分析（殖利率、EPS）- 增強版，更注重長線價值"""
        try:
            # 檢查快取
            cache_key = f"fundamental_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            # 嘗試獲取基本面數據
            fundamental_data = self._fetch_fundamental_data(stock_code)
            
            if not fundamental_data:
                return {'available': False}
            
            # 計算基本面評分 - 加強對長線價值的重視
            fund_score = 0
            
            # 殖利率評分 - 提高權重
            dividend_yield = fundamental_data.get('dividend_yield', 0)
            if dividend_yield > 6:
                fund_score += 4  # 高殖利率股票大加分
            elif dividend_yield > 4:
                fund_score += 3
            elif dividend_yield > 3:
                fund_score += 2.5
            elif dividend_yield > 2:
                fund_score += 1.5
            elif dividend_yield > 1:
                fund_score += 1
            
            # EPS 成長評分 - 提高權重
            eps_growth = fundamental_data.get('eps_growth', 0)
            if eps_growth > 30:
                fund_score += 4  # 高成長股大加分
            elif eps_growth > 20:
                fund_score += 3.5
            elif eps_growth > 15:
                fund_score += 3
            elif eps_growth > 10:
                fund_score += 2.5
            elif eps_growth > 5:
                fund_score += 2
            elif eps_growth > 0:
                fund_score += 1
            elif eps_growth < -10:
                fund_score -= 3  # 負成長大扣分
            elif eps_growth < 0:
                fund_score -= 2
            
            # PE 比率評分
            pe_ratio = fundamental_data.get('pe_ratio', 999)
            if pe_ratio < 8:
                fund_score += 2.5  # 低本益比加分
            elif pe_ratio < 12:
                fund_score += 2
            elif pe_ratio < 15:
                fund_score += 1.5
            elif pe_ratio < 20:
                fund_score += 1
            elif pe_ratio > 40:
                fund_score -= 2  # 高本益比扣分
            elif pe_ratio > 30:
                fund_score -= 1
            
            # ROE 評分 - 提高權重
            roe = fundamental_data.get('roe', 0)
            if roe > 25:
                fund_score += 3  # 高ROE大加分
            elif roe > 20:
                fund_score += 2.5
            elif roe > 15:
                fund_score += 2
            elif roe > 10:
                fund_score += 1.5
            elif roe > 5:
                fund_score += 1
            elif roe < 0:
                fund_score -= 2  # 負ROE扣分
            
            # 新增：財務穩健度評分
            debt_ratio = fundamental_data.get('debt_ratio', 50)
            if debt_ratio < 20:
                fund_score += 1.5  # 低負債比率加分
            elif debt_ratio < 30:
                fund_score += 1
            elif debt_ratio > 70:
                fund_score -= 1.5  # 高負債比率扣分
            elif debt_ratio > 60:
                fund_score -= 1
            
            result = {
                'available': True,
                'fund_score': round(fund_score, 1),
                'dividend_yield': dividend_yield,
                'eps_growth': eps_growth,
                'pe_ratio': pe_ratio,
                'roe': roe,
                'debt_ratio': debt_ratio
            }
            
            # 快取結果
            self.data_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            log_event(f"⚠️ 獲取基本面數據失敗: {stock_code} - {e}", level='warning')
            return {'available': False}
    
    def _fetch_fundamental_data(self, stock_code: str) -> Optional[Dict]:
        """獲取基本面數據 - 增強版，包含更多優質股票"""
        try:
            # 模擬基本面數據（實際使用時可接入真實API）
            # 增加更多具有良好基本面的股票
            mock_data = {
                # 科技股
                '2330': {'dividend_yield': 2.1, 'eps_growth': 12.5, 'pe_ratio': 18.2, 'roe': 23.1, 'debt_ratio': 15.2},
                '2317': {'dividend_yield': 4.2, 'eps_growth': 8.3, 'pe_ratio': 12.1, 'roe': 15.6, 'debt_ratio': 25.3},
                '2454': {'dividend_yield': 2.8, 'eps_growth': 15.2, 'pe_ratio': 16.8, 'roe': 19.3, 'debt_ratio': 18.7},
                '2368': {'dividend_yield': 1.8, 'eps_growth': 22.3, 'pe_ratio': 15.2, 'roe': 18.9, 'debt_ratio': 22.1},
                
                # 金融股（高殖利率）
                '2882': {'dividend_yield': 5.8, 'eps_growth': 6.2, 'pe_ratio': 11.3, 'roe': 13.5, 'debt_ratio': 8.2},
                '2886': {'dividend_yield': 6.2, 'eps_growth': 4.8, 'pe_ratio': 10.8, 'roe': 12.8, 'debt_ratio': 7.5},
                '2891': {'dividend_yield': 5.5, 'eps_growth': 7.1, 'pe_ratio': 12.2, 'roe': 14.2, 'debt_ratio': 9.1},
                '2892': {'dividend_yield': 6.8, 'eps_growth': 5.3, 'pe_ratio': 9.8, 'roe': 11.9, 'debt_ratio': 6.8},
                
                # 傳統產業（穩健型）
                '1301': {'dividend_yield': 4.5, 'eps_growth': 12.8, 'pe_ratio': 13.5, 'roe': 16.2, 'debt_ratio': 28.3},
                '1303': {'dividend_yield': 4.8, 'eps_growth': 9.2, 'pe_ratio': 12.8, 'roe': 14.8, 'debt_ratio': 32.1},
                '2002': {'dividend_yield': 3.8, 'eps_growth': 18.5, 'pe_ratio': 11.2, 'roe': 15.8, 'debt_ratio': 35.6},
                
                # 航運股（高成長+高殖利率）
                '2609': {'dividend_yield': 6.8, 'eps_growth': 25.6, 'pe_ratio': 8.9, 'roe': 18.4, 'debt_ratio': 42.3},
                '2615': {'dividend_yield': 5.2, 'eps_growth': 31.2, 'pe_ratio': 7.3, 'roe': 22.7, 'debt_ratio': 38.9},
                '2603': {'dividend_yield': 4.9, 'eps_growth': 22.1, 'pe_ratio': 9.8, 'roe': 16.2, 'debt_ratio': 45.2},
                
                # 食品股（穩定殖利率）
                '1216': {'dividend_yield': 4.2, 'eps_growth': 8.5, 'pe_ratio': 14.2, 'roe': 12.8, 'debt_ratio': 28.5},
                '1217': {'dividend_yield': 3.8, 'eps_growth': 6.8, 'pe_ratio': 15.8, 'roe': 11.5, 'debt_ratio': 32.8},
                
                # 電信股（高殖利率+穩定）
                '2412': {'dividend_yield': 5.5, 'eps_growth': 3.2, 'pe_ratio': 16.8, 'roe': 8.9, 'debt_ratio': 18.5},
                '4904': {'dividend_yield': 4.8, 'eps_growth': 2.8, 'pe_ratio': 18.2, 'roe': 7.8, 'debt_ratio': 22.3},
                
                # 房地產股（高殖利率）
                '2547': {'dividend_yield': 6.2, 'eps_growth': 15.8, 'pe_ratio': 12.5, 'roe': 14.8, 'debt_ratio': 48.5},
                '9921': {'dividend_yield': 5.8, 'eps_growth': 12.3, 'pe_ratio': 13.8, 'roe': 13.5, 'debt_ratio': 52.3},
            }
            
            # 如果找到特定股票數據就返回，否則生成隨機但合理的數據
            if stock_code in mock_data:
                return mock_data[stock_code]
            else:
                # 根據股票代碼生成相對合理的基本面數據
                import random
                random.seed(hash(stock_code) % 1000)
                
                # 根據行業特性生成不同的基本面數據
                if stock_code.startswith('28'):  # 金融股
                    return {
                        'dividend_yield': random.uniform(4.0, 7.0),
                        'eps_growth': random.uniform(2.0, 10.0),
                        'pe_ratio': random.uniform(8.0, 15.0),
                        'roe': random.uniform(8.0, 16.0),
                        'debt_ratio': random.uniform(5.0, 15.0)
                    }
                elif stock_code.startswith('23'):  # 科技股
                    return {
                        'dividend_yield': random.uniform(1.5, 4.0),
                        'eps_growth': random.uniform(5.0, 25.0),
                        'pe_ratio': random.uniform(12.0, 25.0),
                        'roe': random.uniform(12.0, 25.0),
                        'debt_ratio': random.uniform(15.0, 35.0)
                    }
                else:  # 其他產業
                    return {
                        'dividend_yield': random.uniform(2.0, 5.0),
                        'eps_growth': random.uniform(0.0, 15.0),
                        'pe_ratio': random.uniform(10.0, 20.0),
                        'roe': random.uniform(8.0, 18.0),
                        'debt_ratio': random.uniform(20.0, 50.0)
                    }
            
        except Exception as e:
            log_event(f"⚠️ 模擬基本面數據失敗: {stock_code}", level='warning')
            return None
    
    def _get_institutional_analysis(self, stock_code: str) -> Dict[str, Any]:
        """獲取法人買賣分析 - 增強版，更重視長線法人動向"""
        try:
            # 檢查快取
            cache_key = f"institutional_{stock_code}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            # 嘗試獲取法人買賣數據
            institutional_data = self._fetch_institutional_data(stock_code)
            
            if not institutional_data:
                return {'available': False}
            
            # 計算法人買賣評分 - 加強對長線投資的重視
            inst_score = 0
            
            # 外資買賣評分 - 提高權重
            foreign_net = institutional_data.get('foreign_net_buy', 0)  # 萬元
            if foreign_net > 100000:  # 10億以上
                inst_score += 4  # 大幅買超大加分
            elif foreign_net > 50000:  # 5億以上
                inst_score += 3.5
            elif foreign_net > 20000:  # 2億以上
                inst_score += 3
            elif foreign_net > 10000:  # 1億以上
                inst_score += 2.5
            elif foreign_net > 5000:  # 5000萬以上
                inst_score += 2
            elif foreign_net > 0:
                inst_score += 1
            elif foreign_net < -100000:  # 大量賣出
                inst_score -= 4
            elif foreign_net < -50000:
                inst_score -= 3.5
            elif foreign_net < -20000:
                inst_score -= 3
            elif foreign_net < -10000:
                inst_score -= 2.5
            elif foreign_net < -5000:
                inst_score -= 2
            elif foreign_net < 0:
                inst_score -= 1
            
            # 投信買賣評分 - 提高權重
            trust_net = institutional_data.get('trust_net_buy', 0)
            if trust_net > 50000:  # 5億以上
                inst_score += 3
            elif trust_net > 20000:  # 2億以上
                inst_score += 2.5
            elif trust_net > 10000:  # 1億以上
                inst_score += 2
            elif trust_net > 5000:  # 5000萬以上
                inst_score += 1.5
            elif trust_net > 1000:  # 1000萬以上
                inst_score += 1
            elif trust_net < -50000:
                inst_score -= 3
            elif trust_net < -20000:
                inst_score -= 2.5
            elif trust_net < -10000:
                inst_score -= 2
            elif trust_net < -1000:
                inst_score -= 1


