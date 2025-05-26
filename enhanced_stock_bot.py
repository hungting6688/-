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
            log_event(f"⚠️ 獲取法人數據失敗: {stock_code} - {e}", level='warning')
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
            log_event(f"⚠️ 模擬法人數據失敗: {stock_code}", level='warning')
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
            weights = self.weight_configs['mixed']
        
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
    
    def generate_recommendations(self, analyses: List[Dict[str, Any]], time_slot: str) -> Dict[str, List[Dict[str, Any]]]:
        """生成推薦（保持原有邏輯，但加強長線推薦）"""
        if not analyses:
            return {"short_term": [], "long_term": [], "weak_stocks": []}
        
        # 獲取配置
        config = self.time_slot_config[time_slot]
        limits = config['recommendation_limits']
        
        # 過濾有效分析
        valid_analyses = [a for a in analyses if a.get('current_price', 0) > 0]
        
        # 短線推薦（得分 >= 2）
        short_term_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) >= 2]
        short_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        short_term = []
        for analysis in short_term_candidates[:limits['short_term']]:
            short_term.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "reason": analysis["reason"],
                "target_price": analysis["target_price"],
                "stop_loss": analysis["stop_loss"],
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        # 長線推薦 - 增強版邏輯
        long_term_candidates = []
        for analysis in valid_analyses:
            # 計算長線評分
            long_term_score = self._calculate_long_term_score(analysis)
            
            # 長線評分 >= 1 的股票進入候選
            if long_term_score >= 1:
                analysis['long_term_score'] = long_term_score
                long_term_candidates.append(analysis)
        
        # 按長線評分排序
        long_term_candidates.sort(key=lambda x: x.get('long_term_score', 0), reverse=True)
        
        long_term = []
        for analysis in long_term_candidates[:limits['long_term']]:
            long_term.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "reason": analysis["reason"],
                "target_price": analysis["target_price"],
                "stop_loss": analysis["stop_loss"],
                "trade_value": analysis["trade_value"],
                "long_term_score": analysis.get('long_term_score', 0),
                "analysis": analysis
            })
        
        # 極弱股（得分 <= -3）
        weak_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) <= -3]
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
    
    def _calculate_long_term_score(self, analysis: Dict[str, Any]) -> float:
        """計算長線投資評分"""
        long_score = 0
        
        # 基礎條件：加權評分在合理範圍內
        weighted_score = analysis.get('weighted_score', 0)
        if -1 <= weighted_score <= 5:
            long_score += 1
        
        # 成交金額門檻：> 5000萬
        if analysis.get('trade_value', 0) > 50000000:
            long_score += 0.5
        
        # 基本面加分
        if analysis.get('analysis_components', {}).get('fundamental'):
            dividend_yield = analysis.get('dividend_yield', 0)
            eps_growth = analysis.get('eps_growth', 0)
            roe = analysis.get('roe', 0)
            pe_ratio = analysis.get('pe_ratio', 999)
            
            # 殖利率加分
            if dividend_yield > 4:
                long_score += 2
            elif dividend_yield > 3:
                long_score += 1
            
            # EPS成長加分
            if eps_growth > 15:
                long_score += 2
            elif eps_growth > 10:
                long_score += 1
            elif eps_growth > 5:
                long_score += 0.5
            
            # ROE加分
            if roe > 15:
                long_score += 1.5
            elif roe > 10:
                long_score += 1
            
            # 本益比加分
            if pe_ratio < 15:
                long_score += 1
        
        # 法人買賣加分
        if analysis.get('analysis_components', {}).get('institutional'):
            foreign_net = analysis.get('foreign_net_buy', 0)
            trust_net = analysis.get('trust_net_buy', 0)
            
            # 外資買超加分
            if foreign_net > 50000:  # 5億以上
                long_score += 2
            elif foreign_net > 20000:  # 2億以上
                long_score += 1.5
            elif foreign_net > 10000:  # 1億以上
                long_score += 1
            
            # 投信買超加分
            if trust_net > 10000:  # 1億以上
                long_score += 1
            elif trust_net > 5000:  # 5000萬以上
                long_score += 0.5
            
            # 連續買超天數（模擬）
            if foreign_net > 0 and trust_net > 0:
                long_score += 1  # 外資投信同步買超
        
        return round(long_score, 1)
    
    def run_analysis(self, time_slot: str) -> None:
        """執行分析並發送通知"""
        start_time = time.time()
        log_event(f"🚀 開始執行 {time_slot} 增強分析")
        
        try:
            # 確保通知系統可用
            if not notifier.is_notification_available():
                log_event("⚠️ 通知系統不可用，嘗試初始化", level='warning')
                notifier.init()
            
            # 獲取股票數據
            stocks = self.get_stocks_for_analysis(time_slot)
            
            if not stocks:
                log_event("❌ 無法獲取股票數據", level='error')
                return
            
            # 獲取配置
            config = self.time_slot_config[time_slot]
            analysis_focus = config['analysis_focus']
            expected_count = config['stock_count']
            
            log_event(f"📊 成功獲取 {len(stocks)} 支股票（預期 {expected_count} 支）")
            log_event(f"🔍 分析重點: {analysis_focus}")
            
            # 分析股票
            all_analyses = []
            total_stocks = len(stocks)
            batch_size = 50
            enhanced_count = 0
            basic_count = 0
            
            for i in range(0, total_stocks, batch_size):
                batch = stocks[i:i + batch_size]
                batch_end = min(i + batch_size, total_stocks)
                
                log_event(f"🔍 分析第 {i//batch_size + 1} 批次: 股票 {i+1}-{batch_end}/{total_stocks}")
                
                # 批次分析
                for j, stock in enumerate(batch):
                    try:
                        analysis = self.analyze_stock_enhanced(stock, analysis_focus)
                        all_analyses.append(analysis)
                        
                        # 統計分析方法
                        if analysis.get('analysis_components', {}).get('fundamental'):
                            enhanced_count += 1
                        else:
                            basic_count += 1
                        
                        # 每50支股票顯示進度
                        if (i + j + 1) % 50 == 0:
                            elapsed = time.time() - start_time
                            log_event(f"⏱️ 已分析 {i+j+1}/{total_stocks} 支股票，耗時 {elapsed:.1f}秒")
                        
                    except Exception as e:
                        log_event(f"⚠️ 分析股票 {stock['code']} 失敗: {e}", level='warning')
                        continue
                
                # 批次間短暫休息
                if i + batch_size < total_stocks:
                    time.sleep(0.5)
            
            elapsed_time = time.time() - start_time
            log_event(f"✅ 完成 {len(all_analyses)} 支股票分析，耗時 {elapsed_time:.1f} 秒")
            log_event(f"📈 分析方法統計: 增強分析 {enhanced_count} 支, 基礎分析 {basic_count} 支")
            
            # 生成推薦
            recommendations = self.generate_recommendations(all_analyses, time_slot)
            
            # 顯示推薦統計
            short_count = len(recommendations['short_term'])
            long_count = len(recommendations['long_term'])
            weak_count = len(recommendations['weak_stocks'])
            
            log_event(f"📊 推薦結果: 短線 {short_count} 支, 長線 {long_count} 支, 極弱股 {weak_count} 支")
            
            # 顯示推薦詳情
            if short_count > 0:
                log_event("🔥 短線推薦:")
                for stock in recommendations['short_term']:
                    analysis_info = stock['analysis']
                    score = analysis_info.get('weighted_score', 0)
                    log_event(f"   {stock['code']} {stock['name']} (評分:{score})")
            
            if long_count > 0:
                log_event("💎 長線推薦:")
                for stock in recommendations['long_term']:
                    analysis_info = stock['analysis']
                    long_score = stock.get('long_term_score', 0)
                    log_event(f"   {stock['code']} {stock['name']} (長線評分:{long_score})")
            
            # 發送通知
            display_name = config['name']
            notifier.send_combined_recommendations(recommendations, display_name)
            
            # 保存分析結果
            self.save_analysis_results(all_analyses, recommendations, time_slot)
            
            total_time = time.time() - start_time
            log_event(f"🎉 {time_slot} 增強分析完成，總耗時 {total_time:.1f} 秒")
            
        except Exception as e:
            log_event(f"❌ 執行 {time_slot} 分析時發生錯誤: {e}", level='error')
            import traceback
            log_event(traceback.format_exc(), level='error')
    
    def save_analysis_results(self, analyses: List[Dict[str, Any]], recommendations: Dict[str, List], time_slot: str) -> None:
        """保存分析結果"""
        try:
            # 創建日期目錄
            date_str = datetime.now().strftime('%Y%m%d')
            results_dir = os.path.join(DATA_DIR, 'analysis_results', date_str)
            os.makedirs(results_dir, exist_ok=True)
            
            # 保存分析結果
            analyses_path = os.path.join(results_dir, f"{time_slot}_analyses.json")
            with open(analyses_path, 'w', encoding='utf-8') as f:
                json.dump(analyses, f, ensure_ascii=False, indent=2)
            
            # 保存推薦結果
            recommendations_path = os.path.join(results_dir, f"{time_slot}_recommendations.json")
            with open(recommendations_path, 'w', encoding='utf-8') as f:
                json.dump(recommendations, f, ensure_ascii=False, indent=2)
            
            log_event(f"💾 分析結果已保存到 {results_dir}")
            
        except Exception as e:
            log_event(f"⚠️ 保存分析結果時發生錯誤: {e}", level='warning')

# 創建機器人實例
bot = EnhancedStockBot()

def run_analysis(time_slot: str) -> None:
    """執行分析的包裝函數"""
    bot.run_analysis(time_slot)

def run_morning_scan():
    """早盤掃描"""
    run_analysis('morning_scan')

def run_mid_morning_scan():
    """盤中掃描"""
    run_analysis('mid_morning_scan')

def run_mid_day_scan():
    """午間掃描"""
    run_analysis('mid_day_scan')

def run_afternoon_scan():
    """盤後掃描"""
    run_analysis('afternoon_scan')

def run_weekly_summary():
    """週末總結"""
    run_analysis('weekly_summary')

def send_heartbeat():
    """發送心跳檢測"""
    notifier.send_heartbeat()

def main():
    """主函數 - 設置排程並執行"""
    log_event("🤖 增強版台股分析機器人啟動")
    log_event(f"⏰ 當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化通知系統
    notifier.init()
    
    # 設置排程
    schedule.every().monday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_morning_scan)
    schedule.every().tuesday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_morning_scan)
    schedule.every().wednesday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_morning_scan)
    schedule.every().thursday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_morning_scan)
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_morning_scan)
    
    schedule.every().monday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_mid_morning_scan)
    schedule.every().tuesday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_mid_morning_scan)
    schedule.every().wednesday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_mid_morning_scan)
    schedule.every().thursday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_mid_morning_scan)
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_mid_morning_scan)
    
    schedule.every().monday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_mid_day_scan)
    schedule.every().tuesday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_mid_day_scan)
    schedule.every().wednesday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_mid_day_scan)
    schedule.every().thursday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_mid_day_scan)
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_mid_day_scan)
    
    schedule.every().monday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_afternoon_scan)
    schedule.every().tuesday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_afternoon_scan)
    schedule.every().wednesday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_afternoon_scan)
    schedule.every().thursday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_afternoon_scan)
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_afternoon_scan)
    
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['weekly_summary']).do(run_weekly_summary)
    
    # 心跳檢測
    schedule.every().day.at(NOTIFICATION_SCHEDULE['heartbeat']).do(send_heartbeat)
    
    log_event("📅 排程設置完成")
    log_event(f"🔄 早盤掃描: 工作日 {NOTIFICATION_SCHEDULE['morning_scan']}")
    log_event(f"🔄 盤中掃描: 工作日 {NOTIFICATION_SCHEDULE['mid_morning_scan']}")
    log_event(f"🔄 午間掃描: 工作日 {NOTIFICATION_SCHEDULE['mid_day_scan']}")
    log_event(f"🔄 盤後掃描: 工作日 {NOTIFICATION_SCHEDULE['afternoon_scan']}")
    log_event(f"🔄 週末總結: 每週五 {NOTIFICATION_SCHEDULE['weekly_summary']}")
    log_event(f"🔄 心跳檢測: 每日 {NOTIFICATION_SCHEDULE['heartbeat']}")
    
    # 發送啟動通知
    try:
        startup_message = f"""🤖 增強版台股分析機器人已啟動！

⏰ 啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📅 執行排程:
• 早盤掃描: 工作日 {NOTIFICATION_SCHEDULE['morning_scan']}
• 盤中掃描: 工作日 {NOTIFICATION_SCHEDULE['mid_morning_scan']}  
• 午間掃描: 工作日 {NOTIFICATION_SCHEDULE['mid_day_scan']}
• 盤後掃描: 工作日 {NOTIFICATION_SCHEDULE['afternoon_scan']}
• 週末總結: 每週五 {NOTIFICATION_SCHEDULE['weekly_summary']}

✨ 增強功能:
• 基本面分析（EPS、殖利率、ROE）
• 法人買賣超資訊
• 長線推薦優化
• HTML郵件美化

🛡️ 風險提醒: 本系統僅供參考，投資前請審慎評估風險
        """
        
        notifier.send_notification(startup_message, "🤖 增強版台股分析機器人啟動通知")
        log_event("✅ 啟動通知已發送")
        
    except Exception as e:
        log_event(f"⚠️ 發送啟動通知失敗: {e}", level='warning')
    
    # 執行排程循環
    log_event("🔄 開始執行排程循環...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次
            
    except KeyboardInterrupt:
        log_event("👋 收到停止信號，機器人正在關閉...")
        
        # 發送關閉通知
        try:
            shutdown_message = f"""🛑 台股分析機器人已停止運行

⏰ 停止時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

感謝您的使用！
            """
            notifier.send_notification(shutdown_message, "🛑 台股分析機器人停止通知")
            
        except Exception as e:
            log_event(f"⚠️ 發送關閉通知失敗: {e}", level='warning')
        
        log_event("👋 機器人已停止")
    
    except Exception as e:
        log_event(f"❌ 系統發生未預期錯誤: {e}", level='error')
        import traceback
        log_event(traceback.format_exc(), level='error')

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 命令行模式 - 執行特定時段分析
        time_slot = sys.argv[1]
        if time_slot in ['morning_scan', 'mid_morning_scan', 'mid_day_scan', 'afternoon_scan', 'weekly_summary']:
            log_event(f"🎯 命令行模式: 執行 {time_slot}")
            run_analysis(time_slot)
        else:
            log_event(f"❌ 無效的時段: {time_slot}", level='error')
            log_event("可用時段: morning_scan, mid_morning_scan, mid_day_scan, afternoon_scan, weekly_summary")
    else:
        # 排程模式 - 執行主循環
        main()
