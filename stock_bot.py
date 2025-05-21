"""
stock_bot.py - 股市機器人主程序
執行股票分析並通過通知系統發送推薦
"""
import os
import time
import json
import random
import logging
import schedule
import requests
import datetime
import numpy as np
import pandas as pd
from io import StringIO
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

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

def fetch_stock_data(stock_code: str, days: int = 30) -> pd.DataFrame:
    """
    從台灣證券交易所獲取股票數據
    
    參數:
    - stock_code: 股票代碼
    - days: 獲取的天數
    
    返回:
    - pandas DataFrame
    """
    try:
        # 處理股票代碼格式 (例如將2330變成2330.TW)
        tw_stock_code = f"{stock_code}.TW" if '.' not in stock_code else stock_code
        
        # 計算開始日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)  # 多取一些天數來確保有足夠的交易日
        
        # 格式化日期
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 使用備用方法獲取股票數據
        # 方法1: 嘗試從Yahoo Finance獲取數據
        url = f"https://query1.finance.yahoo.com/v7/finance/download/{tw_stock_code}?period1={int(start_date.timestamp())}&period2={int(end_date.timestamp())}&interval=1d&events=history"
        response = requests.get(url)
        
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            # 確保列名標準化
            df.columns = [c.lower() for c in df.columns]
            # 確保日期列是日期類型
            df['date'] = pd.to_datetime(df['date'])
            # 按日期排序
            df = df.sort_values('date')
            # 取最近的指定天數
            df = df.tail(days)
            
            # 添加股票代碼列
            df['code'] = stock_code
            
            return df
        else:
            log_event(f"從Yahoo Finance獲取 {stock_code} 的數據失敗，嘗試其他方法", level='warning')
            
            # 方法2: 直接從台灣證券交易所獲取
            # 這裡為了簡化示例，我們返回隨機生成的數據
            # 實際應用中應替換為真實的台灣證券交易所API調用
            df = generate_mock_stock_data(stock_code, days)
            return df
            
    except Exception as e:
        log_event(f"獲取股票 {stock_code} 數據失敗: {e}", level='error')
        # 返回空的DataFrame
        return pd.DataFrame()

def generate_mock_stock_data(stock_code: str, days: int) -> pd.DataFrame:
    """生成模擬股票數據用於測試"""
    end_date = datetime.now()
    dates = [end_date - timedelta(days=i) for i in range(days)]
    dates = [d for d in dates if d.weekday() < 5]  # 僅工作日
    dates = sorted(dates)
    
    # 生成隨機價格（確保有一定的趨勢）
    base_price = 100 + random.randint(0, 900)  # 基礎價格
    daily_change = np.random.normal(0, 1, len(dates))  # 每日變化
    trend = np.cumsum(daily_change) * 2  # 添加趨勢
    
    prices = base_price + trend
    prices = [max(10, p) for p in prices]  # 確保價格至少為10
    
    # 生成成交量
    volumes = [int(random.randint(10000, 1000000)) for _ in range(len(dates))]
    
    # 創建DataFrame
    data = {
        'date': dates,
        'open': prices,
        'high': [p * (1 + random.uniform(0, 0.03)) for p in prices],
        'low': [p * (1 - random.uniform(0, 0.03)) for p in prices],
        'close': [p * (1 + random.uniform(-0.02, 0.02)) for p in prices],
        'adj close': [p * (1 + random.uniform(-0.02, 0.02)) for p in prices],
        'volume': volumes,
        'code': [stock_code] * len(dates)
    }
    
    return pd.DataFrame(data)

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
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
    
    # 計算移動平均線
    result['ma5'] = result['close'].rolling(window=5).mean()
    result['ma10'] = result['close'].rolling(window=10).mean()
    result['ma20'] = result['close'].rolling(window=20).mean()
    result['ma60'] = result['close'].rolling(window=60).mean()
    
    # 計算相對強弱指標 (RSI)
    delta = result['close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    
    rs = avg_gain / avg_loss
    result['rsi'] = 100 - (100 / (1 + rs))
    
    # 計算MACD
    result['ema12'] = result['close'].ewm(span=12, adjust=False).mean()
    result['ema26'] = result['close'].ewm(span=26, adjust=False).mean()
    result['macd'] = result['ema12'] - result['ema26']
    result['signal'] = result['macd'].ewm(span=9, adjust=False).mean()
    result['macd_hist'] = result['macd'] - result['signal']
    
    # 計算布林帶
    result['sma20'] = result['close'].rolling(window=20).mean()
    result['stddev'] = result['close'].rolling(window=20).std()
    result['upper_band'] = result['sma20'] + (result['stddev'] * 2)
    result['lower_band'] = result['sma20'] - (result['stddev'] * 2)
    
    # 計算成交量變化
    result['volume_change'] = result['volume'].pct_change() * 100
    
    # 計算價格變化百分比
    result['price_change'] = result['close'].pct_change() * 100
    
    # 過濾掉NaN值
    result = result.fillna(0)
    
    return result

def load_stock_list() -> List[Dict[str, str]]:
    """
    加載股票清單
    
    返回:
    - 股票列表，每個股票是包含code和name的字典
    """
    # 首先嘗試從文件加載
    stock_list_path = os.path.join(DATA_DIR, 'stock_list.json')
    
    if os.path.exists(stock_list_path):
        try:
            with open(stock_list_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_event(f"讀取股票列表文件失敗: {e}", level='error')
    
    # 如果文件不存在或讀取失敗，使用模擬數據
    mock_stocks = [
        {"code": "2330", "name": "台積電"},
        {"code": "2317", "name": "鴻海"},
        {"code": "2454", "name": "聯發科"},
        {"code": "2412", "name": "中華電"},
        {"code": "2308", "name": "台達電"},
        {"code": "2303", "name": "聯電"},
        {"code": "1301", "name": "台塑"},
        {"code": "1303", "name": "南亞"},
        {"code": "2002", "name": "中鋼"},
        {"code": "2882", "name": "國泰金"}
    ]
    
    # 保存模擬數據到文件
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(stock_list_path, 'w', encoding='utf-8') as f:
            json.dump(mock_stocks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_event(f"保存股票列表文件失敗: {e}", level='error')
    
    return mock_stocks

def analyze_stock(stock_data: pd.DataFrame) -> Dict[str, Any]:
    """
    分析股票數據，生成技術分析報告
    
    參數:
    - stock_data: 包含技術指標的股票數據DataFrame
    
    返回:
    - 包含分析結果的字典
    """
    if stock_data.empty:
        return {
            "status": "error",
            "message": "沒有數據可供分析"
        }
    
    # 獲取最新數據
    latest = stock_data.iloc[-1]
    prev = stock_data.iloc[-2] if len(stock_data) > 1 else latest
    
    # 獲取股票代碼和名稱
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
    signals['volume_spike'] = latest['volume'] > 2 * stock_data['volume'].mean()
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
    
    # 生成建議
    if weighted_score >= 5:
        suggestion = "適合短線買入"
        target_price = round(latest['close'] * 1.05, 2)  # 目標5%收益
        stop_loss = round(latest['close'] * 0.97, 2)    # 止損3%
    elif weighted_score >= 2:
        suggestion = "可考慮買入持有"
        target_price = round(latest['close'] * 1.10, 2)  # 目標10%收益
        stop_loss = round(latest['close'] * 0.95, 2)    # 止損5%
    elif weighted_score > -2:
        suggestion = "觀望為宜"
        target_price = None
        stop_loss = None
    elif weighted_score > -5:
        suggestion = "持有者應保持警覺"
        target_price = None
        stop_loss = round(latest['close'] * 0.97, 2)  # 止損3%
    else:
        suggestion = "建議賣出"
        target_price = None
        stop_loss = round(latest['close'] * 0.98, 2)  # 止損2%
    
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
        "suggestion": suggestion,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "analysis_time": datetime.now().isoformat()
    }
    
    return result

def generate_stock_recommendations(all_analyses: List[Dict[str, Any]], rec_limits: Dict[str, int] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    從多只股票的分析中生成推薦
    
    參數:
    - all_analyses: 所有股票分析的列表
    - rec_limits: 各類別推薦數量限制
    
    返回:
    - 按類別分組的股票推薦
    """
    if not all_analyses:
        return {"short_term": [], "long_term": [], "weak_stocks": []}
    
    # 如果沒有指定限制，使用默認值
    if rec_limits is None:
        rec_limits = {
            'long_term': 3,
            'short_term': 3,
            'weak_stocks': 2
        }
    
    # 加載股票名稱對應
    stock_names = {stock["code"]: stock["name"] for stock in load_stock_list()}
    
    # 短線推薦（高於特定分數，建議買入的股票）
    short_term = []
    for analysis in all_analyses:
        if analysis.get("weighted_score", 0) >= 5 and analysis.get("suggestion", "").startswith("適合短線"):
            reason = generate_reason(analysis, "short_term")
            short_term.append({
                "code": analysis["code"],
                "name": stock_names.get(analysis["code"], "未知"),
                "current_price": analysis["current_price"],
                "reason": reason,
                "target_price": analysis["target_price"],
                "stop_loss": analysis["stop_loss"]
            })
    
    # 長線推薦（相對強勢但不夠短線的股票）
    long_term = []
    for analysis in all_analyses:
        if 2 <= analysis.get("weighted_score", 0) < 5 and "可考慮買入持有" in analysis.get("suggestion", ""):
            reason = generate_reason(analysis, "long_term")
            long_term.append({
                "code": analysis["code"],
                "name": stock_names.get(analysis["code"], "未知"),
                "current_price": analysis["current_price"],
                "reason": reason,
                "target_price": analysis["target_price"],
                "stop_loss": analysis["stop_loss"]
            })
    
    # 極弱股（分數極低的股票）
    weak_stocks = []
    for analysis in all_analyses:
        if analysis.get("weighted_score", 0) <= -8:
            alert_reason = generate_reason(analysis, "weak")
            weak_stocks.append({
                "code": analysis["code"],
                "name": stock_names.get(analysis["code"], "未知"),
                "current_price": analysis["current_price"],
                "alert_reason": alert_reason
            })
    
    # 按得分排序
    short_term = sorted(short_term, key=lambda x: -float(getattr(x, "weighted_score", 0) if hasattr(x, "weighted_score") else 0))
    long_term = sorted(long_term, key=lambda x: -float(getattr(x, "weighted_score", 0) if hasattr(x, "weighted_score") else 0))
    weak_stocks = sorted(weak_stocks, key=lambda x: float(getattr(x, "weighted_score", 0) if hasattr(x, "weighted_score") else 0))
    
    # 按推薦限制截取
    short_term_limit = rec_limits.get('short_term', 3)
    long_term_limit = rec_limits.get('long_term', 3)
    weak_stocks_limit = rec_limits.get('weak_stocks', 2)
    
    short_term = short_term[:short_term_limit]
    long_term = long_term[:long_term_limit]
    weak_stocks = weak_stocks[:weak_stocks_limit]
    
    return {
        "short_term": short_term,
        "long_term": long_term,
        "weak_stocks": weak_stocks
    }

def generate_reason(analysis: Dict[str, Any], category: str) -> str:
    """
    根據分析生成推薦/警示理由
    
    參數:
    - analysis: 股票分析結果
    - category: 股票類別 (short_term, long_term, weak)
    
    返回:
    - 推薦理由字符串
    """
    try:
        # 如果導入成功，使用白話文轉換
        import text_formatter
        plain_text = text_formatter.generate_plain_text(analysis, category)
        return plain_text["description"]
    except ImportError:
        # 如果無法導入白話文模組，使用原始邏輯生成技術型描述
        signals = analysis.get("signals", {})
        
        if category == "short_term":
            reasons = []
            
            # 主要技術指標信號
            if signals.get("ma5_crosses_above_ma20"):
                reasons.append("5日均線上穿20日均線")
            if signals.get("macd_crosses_above_signal"):
                reasons.append("MACD金叉")
            if signals.get("rsi_bullish"):
                reasons.append("RSI顯示超賣回升")
            if signals.get("volume_spike") and signals.get("price_up"):
                reasons.append("放量上漲")
            if signals.get("price_below_lower_band"):
                reasons.append("價格觸及布林帶下軌後反彈")
                
            # 如果沒有特別明顯的信號
            if not reasons:
                if analysis.get("weighted_score", 0) > 8:
                    reasons.append("多項技術指標顯示強勢")
                else:
                    reasons.append("短期技術指標轉為正面")
            
            return "、".join(reasons)
            
        elif category == "long_term":
            reasons = []
            
            # 長線相關信號
            if signals.get("price_above_ma20"):
                reasons.append("價格位於20日均線上方")
            if signals.get("ma5_above_ma20") and signals.get("ma10_above_ma20"):
                reasons.append("均線多頭排列")
            if 40 <= analysis.get("rsi", 0) <= 60:
                reasons.append("RSI處於健康區間")
            if signals.get("volume_increasing"):
                reasons.append("成交量逐漸增加")
                
            # 如果沒有特別明顯的信號
            if not reasons:
                reasons.append("整體技術面趨於穩健")
            
            return "、".join(reasons)
            
        elif category == "weak":
            reasons = []
            
            # 弱勢股相關信號
            if signals.get("ma5_crosses_below_ma20"):
                reasons.append("5日均線下穿20日均線")
            if signals.get("macd_crosses_below_signal"):
                reasons.append("MACD死叉")
            if signals.get("rsi_bearish") or signals.get("rsi_overbought"):
                reasons.append("RSI顯示超買回落")
            if signals.get("volume_spike") and signals.get("price_down"):
                reasons.append("放量下跌")
            if signals.get("price_above_upper_band"):
                reasons.append("價格突破布林帶上軌後回落")
                
            # 如果沒有特別明顯的信號
            if not reasons:
                if analysis.get("weighted_score", 0) < -10:
                    reasons.append("多項技術指標顯示弱勢")
                else:
                    reasons.append("短期技術指標轉為負面")
            
            return "、".join(reasons)
        
        # 默認
        return "綜合技術分析結果"

def run_analysis(time_slot: str) -> None:
    """
    執行股市分析並發送通知
    
    參數:
    - time_slot: 時段名稱 ('morning_scan', 'mid_morning_scan', 'mid_day_scan', 'afternoon_scan', 'weekly_summary')
    """
    log_event(f"開始執行 {time_slot} 分析")
    
    try:
        # 確保通知系統可用
        if not notifier.is_notification_available():
            log_event("通知系統不可用，嘗試初始化", level='warning')
            notifier.init()
            
            # 再次檢查
            if not notifier.is_notification_available():
                log_event("通知系統不可用，分析將執行但不發送通知", level='error')
                return
        
        # 加載股票列表
        all_stocks = load_stock_list()
        log_event(f"已加載 {len(all_stocks)} 支股票")
        
        # 確定掃描股票數量
        scan_limit = STOCK_ANALYSIS['scan_limits'].get(time_slot, 100)
        stocks = all_stocks[:scan_limit]  # 取前N支股票
        log_event(f"將掃描 {len(stocks)} 支股票（時段：{time_slot}）")
        
        # 確定推薦數量限制
        rec_limits = STOCK_ANALYSIS['recommendation_limits'].get(time_slot, {
            'long_term': 3,
            'short_term': 3,
            'weak_stocks': 0
        })
        
        # 分析結果列表
        all_analyses = []
        
        # 設置分析的天數
        if time_slot == 'weekly_summary':
            analysis_days = 60  # 週末總結使用更長的數據
        else:
            analysis_days = 30  # 日常分析使用30天數據
        
        # 對每支股票進行分析
        for stock in stocks:
            stock_code = stock['code']
            try:
                # 獲取股票數據
                log_event(f"獲取股票 {stock_code} 數據")
                stock_data = fetch_stock_data(stock_code, days=analysis_days)
                
                if stock_data.empty:
                    log_event(f"獲取股票 {stock_code} 數據失敗，跳過分析", level='warning')
                    continue
                
                # 計算技術指標
                stock_data_with_indicators = calculate_technical_indicators(stock_data)
                
                # 分析股票
                analysis = analyze_stock(stock_data_with_indicators)
                
                # 添加股票名稱
                analysis['name'] = stock['name']
                
                # 添加到分析結果列表
                all_analyses.append(analysis)
                
                log_event(f"股票 {stock_code} 分析完成，趨勢: {analysis.get('trend', '未知')}")
                
            except Exception as e:
                log_event(f"分析股票 {stock_code} 時發生錯誤: {e}", level='error')
                continue
        
        # 生成推薦
        recommendations = generate_stock_recommendations(all_analyses, rec_limits)
        
        # 根據時段發送不同的通知
        time_slot_names = {
            'morning_scan': "早盤掃描",
            'mid_morning_scan': "盤中掃描",
            'mid_day_scan': "午間掃描",
            'afternoon_scan': "盤後掃描",
            'weekly_summary': "週末總結"
        }
        
        display_name = time_slot_names.get(time_slot, time_slot)
        notifier.send_combined_recommendations(recommendations, display_name)
        
        # 保存分析結果
        save_analysis_results(all_analyses, recommendations, time_slot)
        
        log_event(f"{time_slot} 分析完成")
        
    except Exception as e:
        log_event(f"執行 {time_slot} 分析時發生錯誤: {e}", level='error')

def save_analysis_results(analyses: List[Dict[str, Any]], recommendations: Dict[str, List], time_slot: str) -> None:
    """保存分析結果到文件"""
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
    
    # 週末總結 - 從配置字符串中提取時間部分
    weekly_summary_time = NOTIFICATION_SCHEDULE['weekly_summary'].split()[-1]  # 提取 '17:00' 部分
    schedule.every().friday.at(weekly_summary_time).do(run_analysis, 'weekly_summary')
    
    # 心跳檢測
    schedule.every().day.at(NOTIFICATION_SCHEDULE['heartbeat']).do(notifier.send_heartbeat)
    
    log_event("排程任務已設置")
    log_event(f"早盤掃描: 每個工作日 {NOTIFICATION_SCHEDULE['morning_scan']} (掃描{STOCK_ANALYSIS['scan_limits']['morning_scan']}支股票)")
    log_event(f"盤中掃描: 每個工作日 {NOTIFICATION_SCHEDULE['mid_morning_scan']} (掃描{STOCK_ANALYSIS['scan_limits']['mid_morning_scan']}支股票)")
    log_event(f"午間掃描: 每個工作日 {NOTIFICATION_SCHEDULE['mid_day_scan']} (掃描{STOCK_ANALYSIS['scan_limits']['mid_day_scan']}支股票)")
    log_event(f"盤後掃描: 每個工作日 {NOTIFICATION_SCHEDULE['afternoon_scan']} (掃描{STOCK_ANALYSIS['scan_limits']['afternoon_scan']}支股票)")
    log_event(f"週末總結: 每週五 {weekly_summary_time}")
    log_event(f"系統心跳: 每天 {NOTIFICATION_SCHEDULE['heartbeat']}")

def main() -> None:
    """主函數"""
    log_event("股市機器人啟動")
    
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
    
    log_event("股市機器人關閉")

if __name__ == "__main__":
    main()
