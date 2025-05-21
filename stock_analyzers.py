"""
stock_analyzers.py - 擴展的股票分析模組
提供更多維度的股票分析方法，包括基本面、技術面和量化指標
"""
import os
import json
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional

# 配置日誌
logger = logging.getLogger(__name__)

class AdvancedStockAnalyzer:
    """股票進階分析器"""
    
    def __init__(self, data_dir: str = 'data'):
        """
        初始化分析器
        
        參數:
        - data_dir: 數據存儲目錄
        """
        self.data_dir = data_dir
        self.weight_configs = {
            'short_term': {
                'technical': 0.7,  # 技術分析權重
                'fundamental': 0.1,  # 基本面權重
                'quantitative': 0.2,  # 量化指標權重
            },
            'long_term': {
                'technical': 0.3,  # 技術分析權重
                'fundamental': 0.5,  # 基本面權重
                'quantitative': 0.2,  # 量化指標權重
            }
        }
        
        # 創建數據目錄
        os.makedirs(os.path.join(self.data_dir, 'fundamental'), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'technical'), exist_ok=True)
        
        # 加載基本面數據
        self._load_fundamental_data()
    
    def _load_fundamental_data(self) -> None:
        """加載基本面數據"""
        fundamental_path = os.path.join(self.data_dir, 'fundamental', 'stocks_fundamental.json')
        
        if os.path.exists(fundamental_path):
            try:
                with open(fundamental_path, 'r', encoding='utf-8') as f:
                    self.fundamental_data = json.load(f)
                logger.info(f"已加載基本面數據，共 {len(self.fundamental_data)} 支股票")
            except Exception as e:
                logger.error(f"加載基本面數據失敗: {e}")
                self.fundamental_data = {}
        else:
            # 如果文件不存在，則創建一個空的數據字典
            self.fundamental_data = {}
            logger.warning(f"基本面數據文件不存在，已創建空數據字典")
    
    def _save_fundamental_data(self) -> None:
        """保存基本面數據"""
        fundamental_path = os.path.join(self.data_dir, 'fundamental', 'stocks_fundamental.json')
        
        try:
            with open(fundamental_path, 'w', encoding='utf-8') as f:
                json.dump(self.fundamental_data, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存基本面數據，共 {len(self.fundamental_data)} 支股票")
        except Exception as e:
            logger.error(f"保存基本面數據失敗: {e}")
    
    def update_stock_fundamental(self, stock_code: str, fundamental_data: Dict[str, Any]) -> None:
        """
        更新股票基本面數據
        
        參數:
        - stock_code: 股票代碼
        - fundamental_data: 基本面數據字典
        """
        if stock_code not in self.fundamental_data:
            self.fundamental_data[stock_code] = {}
        
        # 更新數據
        self.fundamental_data[stock_code].update(fundamental_data)
        
        # 添加更新時間
        self.fundamental_data[stock_code]['last_updated'] = datetime.now().isoformat()
        
        # 保存到文件
        self._save_fundamental_data()
    
    def fetch_taiwan_stocks_list(self, market_type: str = 'TSE') -> List[Dict[str, str]]:
        """
        獲取台灣股市的股票列表
        
        參數:
        - market_type: 市場類型 (TSE: 上市, OTC: 上櫃)
        
        返回:
        - 股票列表，每個元素是包含 code 和 name 的字典
        """
        stocks = []
        
        try:
            # 嘗試從財務部證券交易所獲取股票列表
            if market_type == 'TSE':
                url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=json"
            else:  # OTC
                url = "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d=111/06/16&se=EW&o=htm"
            
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                if market_type == 'TSE' and 'data' in data:
                    for stock in data['data']:
                        # 股票代碼通常是第一個元素，股票名稱是第二個元素
                        code = stock[0].strip()
                        name = stock[1].strip()
                        stocks.append({"code": code, "name": name})
                # OTC 市場的數據結構可能不同，需要根據實際情況調整
            else:
                logger.warning(f"獲取股票列表失敗，狀態碼: {response.status_code}")
                
        except Exception as e:
            logger.error(f"獲取股票列表時發生錯誤: {e}")
        
        # 如果API獲取失敗，返回一些常見的台股作為備用
        if not stocks:
            logger.info("返回預設的股票列表作為備用")
            stocks = [
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
                {"code": "2881", "name": "富邦金"},
                {"code": "2886", "name": "兆豐金"},
                {"code": "2891", "name": "中信金"},
                {"code": "2884", "name": "玉山金"},
                {"code": "3008", "name": "大立光"},
                {"code": "2892", "name": "第一金"},
                {"code": "2327", "name": "國巨"},
                {"code": "1216", "name": "統一"},
                {"code": "2474", "name": "可成"},
                {"code": "1101", "name": "台泥"}
            ]
        
        return stocks
    
    def analyze_technical(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析技術指標
        
        參數:
        - df: 包含股票價格和指標的DataFrame
        
        返回:
        - 技術分析結果字典
        """
        # 這部分可以保留原始的技術分析邏輯
        if df.empty:
            return {"status": "error", "message": "沒有數據可供分析"}
        
        # 獲取最新數據
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # 獲取股票代碼
        stock_code = latest['code']
        
        # 計算各類指標信號
        signals = {}
        
        # 價格與均線關係
        signals['price_above_ma5'] = latest['close'] > latest['ma5']
        signals['price_above_ma10'] = latest['close'] > latest['ma10']
        signals['price_above_ma20'] = latest['close'] > latest['ma20']
        signals['ma5_above_ma20'] = latest['ma5'] > latest['ma20']
        signals['ma5_above_ma10'] = latest['ma5'] > latest['ma10']
        signals['ma10_above_ma20'] = latest['ma10'] > latest['ma20']
        
        # 均線交叉信號
        signals['ma5_crosses_above_ma20'] = (prev['ma5'] <= prev['ma20']) and (latest['ma5'] > latest['ma20'])
        signals['ma5_crosses_below_ma20'] = (prev['ma5'] >= prev['ma20']) and (latest['ma5'] < latest['ma20'])
        
        # MACD信號
        signals['macd_above_signal'] = latest['macd'] > latest['signal']
        signals['macd_crosses_above_signal'] = (prev['macd'] <= prev['signal']) and (latest['macd'] > latest['signal'])
        signals['macd_crosses_below_signal'] = (prev['macd'] >= prev['signal']) and (latest['macd'] < latest['signal'])
        
        # RSI信號
        signals['rsi_oversold'] = latest['rsi'] < 30
        signals['rsi_overbought'] = latest['rsi'] > 70
        signals['rsi_bullish'] = 30 <= latest['rsi'] <= 50 and latest['rsi'] > prev['rsi']
        signals['rsi_bearish'] = 50 <= latest['rsi'] <= 70 and latest['rsi'] < prev['rsi']
        
        # 布林帶信號
        signals['price_above_upper_band'] = latest['close'] > latest['upper_band']
        signals['price_below_lower_band'] = latest['close'] < latest['lower_band']
        signals['price_near_upper_band'] = 0.95 * latest['upper_band'] <= latest['close'] <= latest['upper_band']
        signals['price_near_lower_band'] = latest['lower_band'] <= latest['close'] <= 1.05 * latest['lower_band']
        
        # 成交量信號
        signals['volume_spike'] = latest['volume'] > 2 * df['volume'].mean()
        signals['volume_increasing'] = latest['volume'] > prev['volume'] * 1.2
        
        # 價格變動信號
        signals['price_up'] = latest['close'] > prev['close']
        signals['price_down'] = latest['close'] < prev['close']
        signals['price_unchanged'] = latest['close'] == prev['close']
        
        # 根據信號生成整體分析
        bullish_signals = sum(1 for k, v in signals.items() if 'bullish' in k.lower() and v) + \
                          sum(1 for k, v in signals.items() if 'above' in k.lower() and v) + \
                          signals['price_below_lower_band'] + \
                          signals['macd_crosses_above_signal'] + \
                          signals['rsi_oversold']
                          
        bearish_signals = sum(1 for k, v in signals.items() if 'bearish' in k.lower() and v) + \
                         sum(1 for k, v in signals.items() if 'below' in k.lower() and v) + \
                         signals['price_above_upper_band'] + \
                         signals['macd_crosses_below_signal'] + \
                         signals['rsi_overbought']
        
        # 對所有信號加權得分
        signal_weights = {
            'price_above_ma5': 1, 'price_above_ma10': 1, 'price_above_ma20': 2,
            'ma5_above_ma20': 2, 'ma5_above_ma10': 1, 'ma10_above_ma20': 1,
            'ma5_crosses_above_ma20': 3, 'ma5_crosses_below_ma20': -3,
            'macd_above_signal': 2, 'macd_crosses_above_signal': 3, 'macd_crosses_below_signal': -3,
            'rsi_oversold': 2, 'rsi_overbought': -2, 'rsi_bullish': 2, 'rsi_bearish': -2,
            'price_above_upper_band': -2, 'price_below_lower_band': 2,
            'price_near_upper_band': -1, 'price_near_lower_band': 1,
            'volume_spike': 1, 'volume_increasing': 1,
            'price_up': 1, 'price_down': -1, 'price_unchanged': 0
        }
        
        weighted_score = sum(signal_weights.get(k, 0) * v for k, v in signals.items())
        
        # 根據得分確定整體趨勢
        if weighted_score >= 10:
            trend = "強烈看漲"
        elif weighted_score >= 5:
            trend = "看漲"
        elif weighted_score >= 2:
            trend = "輕度看漲"
        elif weighted_score > -2:
            trend = "中性"
        elif weighted_score > -5:
            trend = "輕度看跌"
        elif weighted_score > -10:
            trend = "看跌"
        else:
            trend = "強烈看跌"
        
        # 整合分析結果
        result = {
            "code": stock_code,
            "current_price": round(latest['close'], 2),
            "change_percent": round(latest['price_change'], 2),
            "volume": latest['volume'],
            "volume_change": round(latest['volume_change'], 2),
            "ma5": round(latest['ma5'], 2),
            "ma20": round(latest['ma20'], 2),
            "rsi": round(latest['rsi'], 2),
            "macd": round(latest['macd'], 4),
            "signals": signals,
            "bullish_count": bullish_signals,
            "bearish_count": bearish_signals,
            "weighted_score": weighted_score,
            "trend": trend,
            "analysis_time": datetime.now().isoformat()
        }
        
        return result
    
    def analyze_fundamental(self, stock_code: str) -> Dict[str, Any]:
        """
        分析基本面數據
        
        參數:
        - stock_code: 股票代碼
        
        返回:
        - 基本面分析結果字典
        """
        # 從預先保存的數據獲取基本面信息
        fund_data = self.fundamental_data.get(stock_code, {})
        
        if not fund_data:
            return {"status": "warning", "message": "沒有基本面數據"}
        
        # 分析結果
        result = {
            "code": stock_code,
            "pe_ratio": fund_data.get('pe_ratio', None),
            "pb_ratio": fund_data.get('pb_ratio', None),
            "dividend_yield": fund_data.get('dividend_yield', None),
            "eps": fund_data.get('eps', None),
            "eps_growth": fund_data.get('eps_growth', None),
            "revenue_growth": fund_data.get('revenue_growth', None),
            "debt_ratio": fund_data.get('debt_ratio', None),
            "gross_margin": fund_data.get('gross_margin', None),
            "net_margin": fund_data.get('net_margin', None),
            "roe": fund_data.get('roe', None),
            "industry": fund_data.get('industry', None),
            "market_cap": fund_data.get('market_cap', None),
            "analysis_time": datetime.now().isoformat()
        }
        
        # 計算綜合得分
        score = 0
        
        # PE 比率評分
        if result['pe_ratio'] is not None:
            pe = float(result['pe_ratio'])
            if pe < 10:
                score += 3  # 低PE，較為便宜
            elif pe < 15:
                score += 2  # 合理PE
            elif pe < 20:
                score += 1  # 略高PE
            else:
                score -= 1  # 高PE
        
        # 股息率評分
        if result['dividend_yield'] is not None:
            div_yield = float(result['dividend_yield'])
            if div_yield > 5:
                score += 3  # 高股息
            elif div_yield > 3:
                score += 2  # 不錯的股息
            elif div_yield > 1.5:
                score += 1  # 有股息
        
        # EPS 成長評分
        if result['eps_growth'] is not None:
            eps_growth = float(result['eps_growth'])
            if eps_growth > 20:
                score += 3  # 高成長
            elif eps_growth > 10:
                score += 2  # 不錯的成長
            elif eps_growth > 5:
                score += 1  # 有成長
            elif eps_growth < 0:
                score -= 2  # 負成長
        
        # ROE 評分
        if result['roe'] is not None:
            roe = float(result['roe'])
            if roe > 20:
                score += 3  # 高ROE
            elif roe > 15:
                score += 2  # 不錯的ROE
            elif roe > 10:
                score += 1  # 合理ROE
            elif roe < 5:
                score -= 1  # 低ROE
        
        # 更新綜合得分
        result['fundamental_score'] = score
        
        return result
    
    def analyze_relative_strength(self, df: pd.DataFrame, benchmark_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        分析相對強弱指標 (RS)
        
        參數:
        - df: 個股價格數據
        - benchmark_df: 大盤指數數據 (可選)
        
        返回:
        - RS分析結果字典
        """
        if df.empty:
            return {"status": "error", "message": "沒有數據可供分析"}
        
        # 如果沒有提供大盤數據，則計算單純的RS分數
        if benchmark_df is None or benchmark_df.empty:
            # 計算20日和60日動量
            df['momentum_20'] = df['close'].pct_change(periods=20) * 100
            df['momentum_60'] = df['close'].pct_change(periods=60) * 100
            
            # 獲取最新數據
            latest = df.iloc[-1]
            
            # 計算RS分數 (20日動量占60%，60日動量占40%)
            rs_score = 0.6 * latest['momentum_20'] + 0.4 * latest['momentum_60']
            
            result = {
                "code": latest['code'],
                "rs_score": round(rs_score, 2),
                "momentum_20d": round(latest['momentum_20'], 2),
                "momentum_60d": round(latest['momentum_60'], 2),
                "analysis_time": datetime.now().isoformat()
            }
        else:
            # 確保日期對齊
            aligned_data = pd.merge(
                df[['date', 'close']].rename(columns={'close': 'stock_price'}),
                benchmark_df[['date', 'close']].rename(columns={'close': 'benchmark_price'}),
                on='date', how='inner'
            )
            
            if len(aligned_data) == 0:
                return {"status": "error", "message": "無法對齊股票和大盤數據"}
            
            # 計算相對績效
            aligned_data['stock_return'] = aligned_data['stock_price'].pct_change()
            aligned_data['benchmark_return'] = aligned_data['benchmark_price'].pct_change()
            aligned_data['relative_return'] = aligned_data['stock_return'] - aligned_data['benchmark_return']
            
            # 計算20日和60日相對強弱
            aligned_data['rs_20'] = aligned_data['relative_return'].rolling(window=20).sum() * 100
            aligned_data['rs_60'] = aligned_data['relative_return'].rolling(window=60).sum() * 100
            
            # 獲取最新數據
            latest = aligned_data.iloc[-1]
            
            # 計算RS分數 (20日相對強弱占60%，60日相對強弱占40%)
            rs_score = 0.6 * latest['rs_20'] + 0.4 * latest['rs_60']
            
            result = {
                "code": df.iloc[-1]['code'],
                "rs_score": round(rs_score, 2),
                "rs_20d": round(latest['rs_20'], 2),
                "rs_60d": round(latest['rs_60'], 2),
                "relative_to_market": True,
                "analysis_time": datetime.now().isoformat()
            }
        
        return result
    
    def analyze_stock_comprehensive(self, 
                                   technical_data: Dict[str, Any], 
                                   fundamental_data: Dict[str, Any] = None,
                                   rs_data: Dict[str, Any] = None,
                                   analysis_type: str = 'short_term') -> Dict[str, Any]:
        """
        綜合分析股票
        
        參數:
        - technical_data: 技術分析結果
        - fundamental_data: 基本面分析結果 (可選)
        - rs_data: 相對強弱分析結果 (可選)
        - analysis_type: 分析類型 ('short_term' 或 'long_term')
        
        返回:
        - 綜合分析結果
        """
        # 獲取權重配置
        weights = self.weight_configs.get(analysis_type, self.weight_configs['short_term'])
        
        # 初始化綜合分數
        comprehensive_score = 0
        
        # 添加技術分析得分 (歸一化到 -10 到 10 的範圍)
        tech_score = technical_data.get('weighted_score', 0)
        normalized_tech_score = max(min(tech_score, 10), -10)
        comprehensive_score += weights['technical'] * normalized_tech_score
        
        # 如果有基本面數據，添加基本面得分
        if fundamental_data and 'fundamental_score' in fundamental_data:
            # 基本面得分歸一化到 -10 到 10 的範圍
            fund_score = fundamental_data['fundamental_score']
            normalized_fund_score = min(max(fund_score, -10), 10)
            comprehensive_score += weights['fundamental'] * normalized_fund_score
        
        # 如果有相對強弱數據，添加RS得分
        rs_contribution = 0
        if rs_data and 'rs_score' in rs_data:
            # RS分數歸一化，強弱分數範圍假設為 -30 到 30
            rs_score = rs_data['rs_score']
            normalized_rs_score = min(max(rs_score / 3, -10), 10)
            rs_contribution = weights['quantitative'] * normalized_rs_score
            comprehensive_score += rs_contribution
        
        # 根據綜合得分確定整體趨勢
        if comprehensive_score >= 7:
            trend = "強烈看漲"
            suggestion = "適合積極買入"
        elif comprehensive_score >= 4:
            trend = "看漲"
            suggestion = "適合短線買入"
        elif comprehensive_score >= 2:
            trend = "輕度看漲"
            suggestion = "可考慮買入持有"
        elif comprehensive_score > -2:
            trend = "中性"
            suggestion = "觀望為宜"
        elif comprehensive_score > -4:
            trend = "輕度看跌"
            suggestion = "持有者應保持警覺"
        elif comprehensive_score > -7:
            trend = "看跌"
            suggestion = "建議減碼"
        else:
            trend = "強烈看跌"
            suggestion = "建議賣出"
        
        # 目標價和止損價計算
        current_price = technical_data.get('current_price', 0)
        
        if comprehensive_score >= 4:
            target_price = round(current_price * 1.05, 2)  # 目標5%收益
            stop_loss = round(current_price * 0.97, 2)     # 止損3%
        elif comprehensive_score >= 2:
            target_price = round(current_price * 1.10, 2)  # 目標10%收益
            stop_loss = round(current_price * 0.95, 2)     # 止損5%
        elif comprehensive_score > -4:
            target_price = None                           # 中性或輕度看跌不設目標價
            stop_loss = round(current_price * 0.95, 2)     # 止損5%
        else:
            target_price = None                           # 看跌或強烈看跌不設目標價
            stop_loss = round(current_price * 0.98, 2)     # 止損2%
        
        # 整合結果
        result = {
            "code": technical_data.get('code'),
            "current_price": technical_data.get('current_price'),
            "comprehensive_score": round(comprehensive_score, 2),
            "technical_contribution": round(weights['technical'] * normalized_tech_score, 2),
            "fundamental_contribution": round(weights['fundamental'] * normalized_fund_score, 2) if fundamental_data and 'fundamental_score' in fundamental_data else 0,
            "rs_contribution": round(rs_contribution, 2),
            "trend": trend,
            "suggestion": suggestion,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "analysis_type": analysis_type,
            "analysis_time": datetime.now().isoformat()
        }
        
        return result
    
    def filter_stocks_by_market_cap(self, stocks: List[Dict[str, str]], top_n: int = 100) -> List[Dict[str, str]]:
        """
        根據市值篩選股票
        
        參數:
        - stocks: 股票列表
        - top_n: 篩選前N大市值的股票
        
        返回:
        - 篩選後的股票列表
        """
        # 收集市值數據
        stocks_with_market_cap = []
        
        for stock in stocks:
            code = stock['code']
            if code in self.fundamental_data and 'market_cap' in self.fundamental_data[code]:
                stocks_with_market_cap.append({
                    **stock,
                    'market_cap': self.fundamental_data[code]['market_cap']
                })
            else:
                # 沒有市值數據的股票，使用較小的預設值
                stocks_with_market_cap.append({
                    **stock,
                    'market_cap': 0
                })
        
        # 排序並取前N名
        sorted_stocks = sorted(stocks_with_market_cap, key=lambda x: x['market_cap'], reverse=True)
        
        # 取前N名或全部（如果不足N支）
        return sorted_stocks[:min(top_n, len(sorted_stocks))]
    
    def filter_stocks_by_volume(self, all_stocks: List[Dict[str, Any]], min_volume: int = 1000000) -> List[Dict[str, Any]]:
        """
        根據成交量篩選股票
        
        參數:
        - all_stocks: 所有股票分析結果
        - min_volume: 最小成交量
        
        返回:
        - 篩選後的股票列表
        """
        # 篩選成交量大於閾值的股票
        filtered_stocks = [stock for stock in all_stocks if stock.get('volume', 0) >= min_volume]
        
        return filtered_stocks
    
    def filter_stocks_by_industry(self, stocks: List[Dict[str, str]], industries: List[str] = None) -> List[Dict[str, str]]:
        """
        根據行業篩選股票
        
        參數:
        - stocks: 股票列表
        - industries: 行業列表，如為None則不篩選
        
        返回:
        - 篩選後的股票列表
        """
        if industries is None:
            return stocks
        
        # 篩選指定行業的股票
        filtered_stocks = []
        
        for stock in stocks:
            code = stock['code']
            if code in self.fundamental_data and 'industry' in self.fundamental_data[code]:
                industry = self.fundamental_data[code]['industry']
                if industry in industries:
                    filtered_stocks.append(stock)
        
        return filtered_stocks
    
    def select_stocks_for_analysis(self, total_stocks: List[Dict[str, str]], limit: int = 100) -> List[Dict[str, str]]:
        """
        為分析選擇股票
        
        參數:
        - total_stocks: 完整的股票列表
        - limit: 限制股票數量
        
        返回:
        - 選擇的股票列表
        """
        # 首先根據市值篩選
        stocks_by_market_cap = self.filter_stocks_by_market_cap(total_stocks, top_n=limit)
        
        # 如果還需要更多股票，增加一些成交活躍的中小型股
        if len(stocks_by_market_cap) < limit:
            # TODO: 增加對活躍交易中小型股的篩選
            pass
        
        return stocks_by_market_cap[:limit]

# 如果直接運行此文件，則執行示例代碼
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 創建分析器
    analyzer = AdvancedStockAnalyzer()
    
    # 獲取台股列表
    stocks = analyzer.fetch_taiwan_stocks_list()
    print(f"獲取台股列表: {len(stocks)} 支股票")
    
    # 選擇股票進行分析
    selected_stocks = analyzer.select_stocks_for_analysis(stocks, limit=10)
    print(f"選擇 {len(selected_stocks)} 支股票進行分析:")
    for stock in selected_stocks:
        print(f"  {stock['code']} {stock['name']}")
