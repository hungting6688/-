"""
enhanced_stock_bot.py - 增強版股市機器人主程序
使用實際台股數據執行股票分析並通過通知系統發送推薦
"""
import os
import time
import json
import logging
import schedule
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
    """記錄事件"""
    if level == 'error':
        logging.error(message)
        print(f"❌ {message}")
    elif level == 'warning':
        logging.warning(message)
        print(f"⚠️ {message}")
    else:
        logging.info(message)
        print(f"ℹ️ {message}")

class EnhancedStockBot:
    """增強版股市機器人"""
    
    def __init__(self):
        """初始化機器人"""
        self.data_fetcher = TWStockDataFetcher()
        self.cache_dir = os.path.join(DATA_DIR, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 時段配置
        self.time_slot_config = {
            'morning_scan': {
                'name': '早盤掃描',
                'stock_count': 100,
                'analysis_focus': 'short_term',
                'recommendation_limits': {
                    'long_term': 2,
                    'short_term': 3,
                    'weak_stocks': 2
                }
            },
            'mid_morning_scan': {
                'name': '盤中掃描',
                'stock_count': 150,
                'analysis_focus': 'short_term',
                'recommendation_limits': {
                    'long_term': 3,
                    'short_term': 2,
                    'weak_stocks': 0
                }
            },
            'mid_day_scan': {
                'name': '午間掃描',
                'stock_count': 150,
                'analysis_focus': 'mixed',
                'recommendation_limits': {
                    'long_term': 3,
                    'short_term': 2,
                    'weak_stocks': 0
                }
            },
            'afternoon_scan': {
                'name': '盤後掃描',
                'stock_count': 450,
                'analysis_focus': 'comprehensive',
                'recommendation_limits': {
                    'long_term': 3,
                    'short_term': 3,
                    'weak_stocks': 0
                }
            },
            'weekly_summary': {
                'name': '週末總結',
                'stock_count': 200,
                'analysis_focus': 'long_term',
                'recommendation_limits': {
                    'long_term': 5,
                    'short_term': 3,
                    'weak_stocks': 3
                }
            }
        }
    
    def get_stocks_for_analysis(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """
        根據時段獲取要分析的股票
        
        參數:
        - time_slot: 時段名稱
        - date: 日期 (可選)
        
        返回:
        - 股票列表
        """
        log_event(f"開始獲取 {time_slot} 時段的股票數據")
        
        try:
            # 使用數據獲取器獲取股票
            stocks = self.data_fetcher.get_stocks_by_time_slot(time_slot, date)
            
            # 過濾掉無效股票
            valid_stocks = []
            for stock in stocks:
                # 基本過濾條件
                if (stock.get('close', 0) > 0 and 
                    stock.get('volume', 0) > 1000 and  # 最小成交量
                    stock.get('trade_value', 0) > 100000):  # 最小成交金額
                    valid_stocks.append(stock)
            
            log_event(f"獲取了 {len(valid_stocks)} 支有效股票進行分析")
            return valid_stocks
            
        except Exception as e:
            log_event(f"獲取股票數據失敗: {e}", level='error')
            return []
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算技術指標
        
        參數:
        - df: 股票價格DataFrame
        
        返回:
        - DataFrame with indicators
        """
        if df.empty:
            return df
            
        # 確保列名標準化
        df.columns = [c.lower() for c in df.columns]
        
        # 復制一個DataFrame以避免修改原始數據
        result = df.copy()
        
        # 確保數據按日期排序
        if 'date' in result.columns:
            result = result.sort_values('date')
        
        # 計算移動平均線
        result['ma5'] = result['close'].rolling(window=5, min_periods=1).mean()
        result['ma10'] = result['close'].rolling(window=10, min_periods=1).mean()
        result['ma20'] = result['close'].rolling(window=20, min_periods=1).mean()
        result['ma60'] = result['close'].rolling(window=60, min_periods=1).mean()
        
        # 計算相對強弱指標 (RSI)
        delta = result['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=14, min_periods=1).mean()
        avg_loss = loss.rolling(window=14, min_periods=1).mean()
        
        rs = avg_gain / (avg_loss + 1e-10)  # 避免除以零
        result['rsi'] = 100 - (100 / (1 + rs))
        
        # 計算MACD
        result['ema12'] = result['close'].ewm(span=12, adjust=False).mean()
        result['ema26'] = result['close'].ewm(span=26, adjust=False).mean()
        result['macd'] = result['ema12'] - result['ema26']
        result['signal'] = result['macd'].ewm(span=9, adjust=False).mean()
        result['macd_hist'] = result['macd'] - result['signal']
        
        # 計算布林帶
        result['sma20'] = result['close'].rolling(window=20, min_periods=1).mean()
        result['stddev'] = result['close'].rolling(window=20, min_periods=1).std()
        result['upper_band'] = result['sma20'] + (result['stddev'] * 2)
        result['lower_band'] = result['sma20'] - (result['stddev'] * 2)
        
        # 計算成交量變化
        result['volume_change'] = result['volume'].pct_change() * 100
        
        # 計算價格變化百分比
        result['price_change'] = result['close'].pct_change() * 100
        
        # 過濾掉NaN值
        result = result.fillna(method='bfill').fillna(0)
        
        return result
    
    def analyze_stock_with_real_data(self, stock_info: Dict[str, Any], analysis_focus: str = 'mixed') -> Dict[str, Any]:
        """
        使用實際數據分析股票
        
        參數:
        - stock_info: 股票基本資訊
        - analysis_focus: 分析重點
        
        返回:
        - 分析結果字典
        """
        stock_code = stock_info['code']
        
        try:
            # 獲取歷史數據
            historical_data = self.data_fetcher.get_stock_historical_data(
                stock_code, 
                days=30 if analysis_focus == 'short_term' else 60
            )
            
            if historical_data.empty:
                log_event(f"無法獲取股票 {stock_code} 的歷史數據", level='warning')
                return self._create_basic_analysis(stock_info)
            
            # 計算技術指標
            data_with_indicators = self.calculate_technical_indicators(historical_data)
            
            # 執行技術分析
            analysis = self._perform_technical_analysis(data_with_indicators, stock_info, analysis_focus)
            
            return analysis
            
        except Exception as e:
            log_event(f"分析股票 {stock_code} 時發生錯誤: {e}", level='error')
            return self._create_basic_analysis(stock_info)
    
    def _create_basic_analysis(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """創建基本分析結果（當無法獲取歷史數據時使用）"""
        return {
            "code": stock_info['code'],
            "name": stock_info['name'],
            "current_price": stock_info['close'],
            "change_percent": stock_info['change_percent'],
            "volume": stock_info['volume'],
            "trade_value": stock_info['trade_value'],
            "weighted_score": 0,
            "trend": "數據不足",
            "suggestion": "需要更多數據進行分析",
            "target_price": None,
            "stop_loss": None,
            "signals": {},
            "analysis_time": datetime.now().isoformat(),
            "data_quality": "limited"
        }
    
    def _perform_technical_analysis(self, df: pd.DataFrame, stock_info: Dict[str, Any], focus: str) -> Dict[str, Any]:
        """執行技術分析"""
        if df.empty:
            return self._create_basic_analysis(stock_info)
        
        # 獲取最新和前一日數據
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
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
        
        # 成交量信號
        avg_volume = df['volume'].mean()
        signals['volume_spike'] = latest['volume'] > 2 * avg_volume
        signals['volume_increasing'] = latest['volume'] > prev['volume'] * 1.2
        
        # 價格變動信號
        signals['price_up'] = latest['close'] > prev['close']
        signals['price_down'] = latest['close'] < prev['close']
        
        # 根據分析重點調整權重
        if focus == 'short_term':
            weights = {
                'ma_signals': 2.0,
                'macd_signals': 3.0,
                'rsi_signals': 2.0,
                'volume_signals': 2.0,
                'price_signals': 1.0
            }
        elif focus == 'long_term':
            weights = {
                'ma_signals': 3.0,
                'macd_signals': 2.0,
                'rsi_signals': 1.0,
                'volume_signals': 1.0,
                'price_signals': 2.0
            }
        else:  # mixed or comprehensive
            weights = {
                'ma_signals': 2.5,
                'macd_signals': 2.5,
                'rsi_signals': 1.5,
                'volume_signals': 1.5,
                'price_signals': 1.5
            }
        
        # 計算加權得分
        weighted_score = 0
        
        # 均線信號得分
        ma_score = 0
        if signals['price_above_ma20']: ma_score += 2
        if signals['ma5_above_ma20']: ma_score += 2
        if signals['ma5_crosses_above_ma20']: ma_score += 3
        if signals['ma5_crosses_below_ma20']: ma_score -= 3
        weighted_score += ma_score * weights['ma_signals']
        
        # MACD信號得分
        macd_score = 0
        if signals['macd_above_signal']: macd_score += 2
        if signals['macd_crosses_above_signal']: macd_score += 3
        if signals['macd_crosses_below_signal']: macd_score -= 3
        weighted_score += macd_score * weights['macd_signals']
        
        # RSI信號得分
        rsi_score = 0
        if signals['rsi_oversold']: rsi_score += 2
        if signals['rsi_overbought']: rsi_score -= 2
        if signals['rsi_bullish']: rsi_score += 2
        if signals['rsi_bearish']: rsi_score -= 2
        weighted_score += rsi_score * weights['rsi_signals']
        
        # 成交量信號得分
        vol_score = 0
        if signals['volume_spike'] and signals['price_up']: vol_score += 2
        if signals['volume_spike'] and signals['price_down']: vol_score -= 1
        if signals['volume_increasing']: vol_score += 1
        weighted_score += vol_score * weights['volume_signals']
        
        # 價格信號得分
        price_score = 0
        if signals['price_up']: price_score += 1
        if signals['price_down']: price_score -= 1
        weighted_score += price_score * weights['price_signals']
        
        # 正規化得分
        weighted_score = weighted_score / sum(weights.values())
        
        # 根據得分確定趨勢和建議
        if weighted_score >= 5:
            trend = "強烈看漲"
            suggestion = "適合積極買入"
            target_price = round(latest['close'] * 1.08, 2)
            stop_loss = round(latest['close'] * 0.95, 2)
        elif weighted_score >= 3:
            trend = "看漲"
            suggestion = "適合短線買入"
            target_price = round(latest['close'] * 1.05, 2)
            stop_loss = round(latest['close'] * 0.97, 2)
        elif weighted_score >= 1:
            trend = "輕度看漲"
            suggestion = "可考慮買入持有"
            target_price = round(latest['close'] * 1.10, 2)
            stop_loss = round(latest['close'] * 0.95, 2)
        elif weighted_score > -1:
            trend = "中性"
            suggestion = "觀望為宜"
            target_price = None
            stop_loss = round(latest['close'] * 0.95, 2)
        elif weighted_score > -3:
            trend = "輕度看跌"
            suggestion = "持有者保持警覺"
            target_price = None
            stop_loss = round(latest['close'] * 0.97, 2)
        elif weighted_score > -5:
            trend = "看跌"
            suggestion = "建議減碼"
            target_price = None
            stop_loss = round(latest['close'] * 0.98, 2)
        else:
            trend = "強烈看跌"
            suggestion = "建議賣出"
            target_price = None
            stop_loss = round(latest['close'] * 0.98, 2)
        
        # 整合分析結果
        result = {
            "code": stock_info['code'],
            "name": stock_info['name'],
            "current_price": round(latest['close'], 2),
            "change_percent": round(stock_info['change_percent'], 2),
            "volume": stock_info['volume'],
            "trade_value": stock_info['trade_value'],
            "volume_change": round(latest['volume_change'], 2),
            "ma5": round(latest['ma5'], 2),
            "ma20": round(latest['ma20'], 2),
            "rsi": round(latest['rsi'], 2),
            "macd": round(latest['macd'], 4),
            "signals": signals,
            "weighted_score": round(weighted_score, 2),
            "trend": trend,
            "suggestion": suggestion,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "analysis_time": datetime.now().isoformat(),
            "analysis_focus": focus,
            "data_quality": "complete"
        }
        
        return result
    
    def generate_recommendations(self, analyses: List[Dict[str, Any]], time_slot: str) -> Dict[str, List[Dict[str, Any]]]:
        """生成股票推薦"""
        if not analyses:
            return {"short_term": [], "long_term": [], "weak_stocks": []}
        
        # 獲取推薦限制
        limits = self.time_slot_config[time_slot]['recommendation_limits']
        
        # 過濾掉數據不足的分析
        valid_analyses = [a for a in analyses if a.get('data_quality') != 'limited']
        
        # 短線推薦（加權得分 >= 3）
        short_term_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) >= 3]
        short_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        short_term = []
        for analysis in short_term_candidates[:limits['short_term']]:
            reason = self._generate_reason(analysis, "short_term")
            short_term.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "reason": reason,
                "target_price": analysis["target_price"],
                "stop_loss": analysis["stop_loss"],
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        # 長線推薦（加權得分 1-3之間）
        long_term_candidates = [a for a in valid_analyses if 1 <= a.get('weighted_score', 0) < 3]
        long_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        long_term = []
        for analysis in long_term_candidates[:limits['long_term']]:
            reason = self._generate_reason(analysis, "long_term")
            long_term.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "reason": reason,
                "target_price": analysis["target_price"],
                "stop_loss": analysis["stop_loss"],
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        # 極弱股（加權得分 <= -3）
        weak_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) <= -3]
        weak_candidates.sort(key=lambda x: x.get('weighted_score', 0))
        
        weak_stocks = []
        for analysis in weak_candidates[:limits['weak_stocks']]:
            alert_reason = self._generate_reason(analysis, "weak")
            weak_stocks.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "alert_reason": alert_reason,
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        return {
            "short_term": short_term,
            "long_term": long_term,
            "weak_stocks": weak_stocks
        }
    
    def _generate_reason(self, analysis: Dict[str, Any], category: str) -> str:
        """生成推薦理由"""
        signals = analysis.get("signals", {})
        
        if category == "short_term":
            reasons = []
            if signals.get("ma5_crosses_above_ma20"):
                reasons.append("5日均線上穿20日均線")
            if signals.get("macd_crosses_above_signal"):
                reasons.append("MACD金叉")
            if signals.get("rsi_bullish"):
                reasons.append("RSI顯示回升")
            if signals.get("volume_spike") and signals.get("price_up"):
                reasons.append("放量上漲")
            
            if not reasons:
                reasons.append("多項技術指標轉強")
            
        elif category == "long_term":
            reasons = []
            if signals.get("price_above_ma20"):
                reasons.append("站穩20日均線")
            if signals.get("ma5_above_ma20") and signals.get("ma10_above_ma20"):
                reasons.append("均線多頭排列")
            if 40 <= analysis.get("rsi", 0) <= 60:
                reasons.append("RSI健康區間")
            
            if not reasons:
                reasons.append("技術面穩健向上")
            
        else:  # weak
            reasons = []
            if signals.get("ma5_crosses_below_ma20"):
                reasons.append("均線死叉")
            if signals.get("macd_crosses_below_signal"):
                reasons.append("MACD轉弱")
            if signals.get("volume_spike") and signals.get("price_down"):
                reasons.append("放量下跌")
            
            if not reasons:
                reasons.append("技術指標轉弱")
        
        return "、".join(reasons)
    
    def run_analysis(self, time_slot: str) -> None:
        """執行分析並發送通知"""
        log_event(f"開始執行 {time_slot} 分析")
        
        try:
            # 確保通知系統可用
            if not notifier.is_notification_available():
                log_event("通知系統不可用，嘗試初始化", level='warning')
                notifier.init()
            
            # 獲取股票數據
            stocks = self.get_stocks_for_analysis(time_slot)
            
            if not stocks:
                log_event(f"無法獲取 {time_slot} 的股票數據", level='error')
                return
            
            # 獲取時段配置
            config = self.time_slot_config[time_slot]
            analysis_focus = config['analysis_focus']
            
            # 分析股票
            all_analyses = []
            
            for i, stock in enumerate(stocks):
                try:
                    log_event(f"分析股票 {i+1}/{len(stocks)}: {stock['code']} {stock['name']}")
                    
                    analysis = self.analyze_stock_with_real_data(stock, analysis_focus)
                    all_analyses.append(analysis)
                    
                    # 避免請求過於頻繁
                    if i % 10 == 9:  # 每10支股票休息一下
                        time.sleep(1)
                    
                except Exception as e:
                    log_event(f"分析股票 {stock['code']} 時發生錯誤: {e}", level='error')
                    continue
            
            log_event(f"完成 {len(all_analyses)} 支股票分析")
            
            # 生成推薦
            recommendations = self.generate_recommendations(all_analyses, time_slot)
            
            # 發送通知
            display_name = config['name']
            notifier.send_combined_recommendations(recommendations, display_name)
            
            # 保存分析結果
            self.save_analysis_results(all_analyses, recommendations, time_slot)
            
            log_event(f"{time_slot} 分析完成，推薦股票數：短線{len(recommendations['short_term'])}、長線{len(recommendations['long_term'])}、極弱{len(recommendations['weak_stocks'])}")
            
        except Exception as e:
            log_event(f"執行 {time_slot} 分析時發生錯誤: {e}", level='error')
    
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
            
            log_event(f"分析結果已保存到 {results_dir}")
            
        except Exception as e:
            log_event(f"保存分析結果時發生錯誤: {e}", level='error')

# 全域機器人實例
bot = EnhancedStockBot()

def run_analysis(time_slot: str) -> None:
    """執行分析的包裝函數"""
    bot.run_analysis(time_slot)

def setup_schedule() -> None:
    """設置排程任務"""
    # 早盤掃描 (9:00)
    schedule.every().monday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_analysis, 'morning_scan')
    schedule.every().tuesday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_analysis, 'morning_scan')
    schedule.every().wednesday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_analysis, 'morning_scan')
    schedule.every().thursday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_analysis, 'morning_scan')
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['morning_scan']).do(run_analysis, 'morning_scan')
    
    # 盤中掃描 (10:30)
    schedule.every().monday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_analysis, 'mid_morning_scan')
    schedule.every().tuesday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_analysis, 'mid_morning_scan')
    schedule.every().wednesday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_analysis, 'mid_morning_scan')
    schedule.every().thursday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_analysis, 'mid_morning_scan')
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(run_analysis, 'mid_morning_scan')
    
    # 午間掃描 (12:30)
    schedule.every().monday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_analysis, 'mid_day_scan')
    schedule.every().tuesday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_analysis, 'mid_day_scan')
    schedule.every().wednesday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_analysis, 'mid_day_scan')
    schedule.every().thursday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_analysis, 'mid_day_scan')
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(run_analysis, 'mid_day_scan')
    
    # 盤後掃描 (15:00)
    schedule.every().monday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_analysis, 'afternoon_scan')
    schedule.every().tuesday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_analysis, 'afternoon_scan')
    schedule.every().wednesday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_analysis, 'afternoon_scan')
    schedule.every().thursday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_analysis, 'afternoon_scan')
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(run_analysis, 'afternoon_scan')
    
    # 週末總結
    weekly_summary_time = NOTIFICATION_SCHEDULE['weekly_summary'].split()[-1]
    schedule.every().friday.at(weekly_summary_time).do(run_analysis, 'weekly_summary')
    
    # 心跳檢測
    schedule.every().day.at(NOTIFICATION_SCHEDULE['heartbeat']).do(notifier.send_heartbeat)
    
    log_event("排程任務已設置")
    for slot, config in bot.time_slot_config.items():
        if slot in NOTIFICATION_SCHEDULE:
            time_str = NOTIFICATION_SCHEDULE[slot] if slot != 'weekly_summary' else weekly_summary_time
            log_event(f"{config['name']}: 每個工作日 {time_str} (掃描{config['stock_count']}支股票)")

def main() -> None:
    """主函數"""
    log_event("增強版股市機器人啟動")
    
    # 初始化通知系統
    notifier.init()
    
    # 設置排程任務
    setup_schedule()
    
    # 啟動時發送一次心跳
    notifier.send_heartbeat()
    
    # 運行排程
    log_event("開始執行排程任務")
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)  # 每30秒檢查一次
        except KeyboardInterrupt:
            log_event("用戶中斷程序", level='warning')
            break
        except Exception as e:
            log_event(f"排程執行時發生錯誤: {e}", level='error')
            time.sleep(300)  # 發生錯誤時等待5分鐘
    
    log_event("增強版股市機器人關閉")

if __name__ == "__main__":
    main()
