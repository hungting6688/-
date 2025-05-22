"""
improved_stock_bot.py - 改進版股票分析機器人
增加超時處理、錯誤處理和進度追蹤
"""
import os
import time
import json
import logging
import signal
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# 引入必要模組
from config import (
    STOCK_ANALYSIS, 
    NOTIFICATION_SCHEDULE, 
    LOG_CONFIG, 
    DATA_DIR,
    LOG_DIR
)
import notifier
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

class TimeoutError(Exception):
    """超時異常"""
    pass

@contextmanager
def timeout(seconds):
    """超時上下文管理器"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"操作超時 ({seconds}秒)")
    
    # 設置信號處理器
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

class FastStockBot:
    """快速股票分析機器人"""
    
    def __init__(self):
        """初始化機器人"""
        self.data_fetcher = TWStockDataFetcher()
        self.cache_dir = os.path.join(DATA_DIR, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 分析配置
        self.max_analysis_time = 300  # 5分鐘總超時
        self.per_stock_timeout = 10   # 每支股票10秒超時
        self.batch_size = 10          # 批次處理大小
        
    def analyze_stock_fast(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """快速分析單支股票（帶超時）"""
        stock_code = stock_info['code']
        
        try:
            with timeout(self.per_stock_timeout):
                # 基於當日數據的簡化分析
                current_price = stock_info['close']
                change_percent = stock_info['change_percent']
                volume = stock_info['volume']
                trade_value = stock_info['trade_value']
                
                # 簡化的技術分析評分
                score = 0
                
                # 價格變動評分
                if change_percent > 3:
                    score += 3
                elif change_percent > 1:
                    score += 2
                elif change_percent > 0:
                    score += 1
                elif change_percent < -3:
                    score -= 3
                elif change_percent < -1:
                    score -= 2
                elif change_percent < 0:
                    score -= 1
                
                # 成交量評分 (簡化)
                if trade_value > 1000000000:  # 10億以上
                    score += 2
                elif trade_value > 100000000:  # 1億以上
                    score += 1
                
                # 根據得分判斷趨勢
                if score >= 4:
                    trend = "強烈看漲"
                    suggestion = "適合積極買入"
                    target_price = round(current_price * 1.08, 2)
                    stop_loss = round(current_price * 0.95, 2)
                elif score >= 2:
                    trend = "看漲"
                    suggestion = "可考慮買入"
                    target_price = round(current_price * 1.05, 2)
                    stop_loss = round(current_price * 0.97, 2)
                elif score > -2:
                    trend = "中性"
                    suggestion = "觀望為宜"
                    target_price = None
                    stop_loss = round(current_price * 0.95, 2)
                elif score >= -4:
                    trend = "看跌"
                    suggestion = "建議減碼"
                    target_price = None
                    stop_loss = round(current_price * 0.97, 2)
                else:
                    trend = "強烈看跌"
                    suggestion = "建議賣出"
                    target_price = None
                    stop_loss = round(current_price * 0.98, 2)
                
                # 生成分析結果
                analysis = {
                    "code": stock_code,
                    "name": stock_info['name'],
                    "current_price": current_price,
                    "change_percent": change_percent,
                    "volume": volume,
                    "trade_value": trade_value,
                    "weighted_score": score,
                    "trend": trend,
                    "suggestion": suggestion,
                    "target_price": target_price,
                    "stop_loss": stop_loss,
                    "analysis_time": datetime.now().isoformat(),
                    "analysis_method": "fast",
                    "data_quality": "current_day"
                }
                
                return analysis
                
        except TimeoutError:
            log_event(f"分析股票 {stock_code} 超時，使用簡化結果", level='warning')
            # 返回基本結果
            return {
                "code": stock_code,
                "name": stock_info['name'],
                "current_price": stock_info['close'],
                "change_percent": stock_info['change_percent'],
                "volume": stock_info['volume'],
                "trade_value": stock_info['trade_value'],
                "weighted_score": 0,
                "trend": "數據不足",
                "suggestion": "分析超時",
                "target_price": None,
                "stop_loss": None,
                "analysis_time": datetime.now().isoformat(),
                "analysis_method": "timeout",
                "data_quality": "limited"
            }
            
        except Exception as e:
            log_event(f"分析股票 {stock_code} 失敗: {e}", level='error')
            return {
                "code": stock_code,
                "name": stock_info['name'],
                "current_price": stock_info.get('close', 0),
                "change_percent": stock_info.get('change_percent', 0),
                "volume": stock_info.get('volume', 0),
                "trade_value": stock_info.get('trade_value', 0),
                "weighted_score": 0,
                "trend": "分析失敗",
                "suggestion": "需要手動檢查",
                "target_price": None,
                "stop_loss": None,
                "analysis_time": datetime.now().isoformat(),
                "analysis_method": "error",
                "data_quality": "error"
            }
    
    def generate_recommendations_fast(self, analyses: List[Dict[str, Any]], time_slot: str) -> Dict[str, List[Dict[str, Any]]]:
        """快速生成推薦"""
        if not analyses:
            return {"short_term": [], "long_term": [], "weak_stocks": []}
        
        # 過濾有效分析
        valid_analyses = [a for a in analyses if a.get('data_quality') not in ['limited', 'error']]
        
        # 如果有效分析不足，使用所有分析
        if len(valid_analyses) < len(analyses) * 0.5:
            valid_analyses = analyses
        
        # 短線推薦（得分 >= 2）
        short_term_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) >= 2]
        short_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        short_term = []
        for analysis in short_term_candidates[:3]:  # 最多3支
            reason = self._generate_simple_reason(analysis, "short_term")
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
        
        # 長線推薦（得分 0-1）
        long_term_candidates = [a for a in valid_analyses if 0 <= a.get('weighted_score', 0) < 2]
        long_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        long_term = []
        for analysis in long_term_candidates[:2]:  # 最多2支
            reason = self._generate_simple_reason(analysis, "long_term")
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
        
        # 極弱股（得分 <= -3）
        weak_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) <= -3]
        weak_candidates.sort(key=lambda x: x.get('weighted_score', 0))
        
        weak_stocks = []
        for analysis in weak_candidates[:2]:  # 最多2支
            alert_reason = self._generate_simple_reason(analysis, "weak")
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
    
    def _generate_simple_reason(self, analysis: Dict[str, Any], category: str) -> str:
        """生成簡化的推薦理由"""
        change_percent = analysis.get('change_percent', 0)
        trade_value = analysis.get('trade_value', 0)
        
        if category == "short_term":
            if change_percent > 3:
                return f"今日上漲 {change_percent:.1f}%，動能強勁"
            elif change_percent > 1:
                return f"今日上漲 {change_percent:.1f}%，表現良好"
            elif trade_value > 1000000000:
                return "成交金額龐大，市場關注度高"
            else:
                return "技術指標轉強"
                
        elif category == "long_term":
            if trade_value > 500000000:
                return "成交活躍，具長期投資價值"
            elif change_percent > 0:
                return f"今日微幅上漲 {change_percent:.1f}%，穩健表現"
            else:
                return "基本面穩健，適合長期持有"
                
        else:  # weak
            if change_percent < -3:
                return f"今日下跌 {abs(change_percent):.1f}%，跌幅較大"
            elif change_percent < 0:
                return f"今日下跌 {abs(change_percent):.1f}%，需注意風險"
            else:
                return "技術指標轉弱，建議觀望"
    
    def run_fast_analysis(self, time_slot: str) -> None:
        """執行快速分析"""
        start_time = time.time()
        log_event(f"🚀 開始執行快速 {time_slot} 分析")
        
        try:
            # 確保通知系統可用
            if not notifier.is_notification_available():
                log_event("通知系統不可用，嘗試初始化", level='warning')
                notifier.init()
            
            # 獲取股票數據（快速版）
            log_event("📊 獲取股票數據...")
            stocks = self.data_fetcher.get_stocks_by_time_slot(time_slot)
            
            if not stocks:
                log_event("❌ 無法獲取股票數據", level='error')
                return
            
            log_event(f"✅ 獲取了 {len(stocks)} 支股票")
            
            # 快速分析（批次處理）
            all_analyses = []
            total_stocks = len(stocks)
            
            for i in range(0, total_stocks, self.batch_size):
                batch = stocks[i:i + self.batch_size]
                batch_end = min(i + self.batch_size, total_stocks)
                
                log_event(f"🔍 分析股票 {i+1}-{batch_end}/{total_stocks}")
                
                for j, stock in enumerate(batch):
                    try:
                        analysis = self.analyze_stock_fast(stock)
                        all_analyses.append(analysis)
                        
                        # 每10支股票顯示進度
                        if (i + j + 1) % 10 == 0:
                            elapsed = time.time() - start_time
                            log_event(f"⏱️ 已分析 {i+j+1}/{total_stocks} 支股票，耗時 {elapsed:.1f}秒")
                        
                    except Exception as e:
                        log_event(f"⚠️ 分析股票 {stock['code']} 失敗: {e}", level='warning')
                        continue
                
                # 批次間短暫休息
                time.sleep(0.5)
            
            elapsed_time = time.time() - start_time
            log_event(f"✅ 完成 {len(all_analyses)} 支股票分析，總耗時 {elapsed_time:.1f} 秒")
            
            # 生成推薦
            log_event("📈 生成投資推薦...")
            recommendations = self.generate_recommendations_fast(all_analyses, time_slot)
            
            # 顯示推薦統計
            short_count = len(recommendations['short_term'])
            long_count = len(recommendations['long_term'])
            weak_count = len(recommendations['weak_stocks'])
            
            log_event(f"📊 推薦結果: 短線 {short_count} 支, 長線 {long_count} 支, 極弱股 {weak_count} 支")
            
            # 發送通知
            time_slot_names = {
                'morning_scan': "早盤掃描",
                'mid_morning_scan': "盤中掃描",
                'mid_day_scan': "午間掃描",
                'afternoon_scan': "盤後掃描",
                'weekly_summary': "週末總結"
            }
            
            display_name = time_slot_names.get(time_slot, time_slot)
            
            log_event(f"📧 發送 {display_name} 通知...")
            notifier.send_combined_recommendations(recommendations, display_name)
            
            total_time = time.time() - start_time
            log_event(f"🎉 {time_slot} 快速分析完成，總耗時 {total_time:.1f} 秒")
            
        except Exception as e:
            log_event(f"❌ 執行 {time_slot} 快速分析時發生錯誤: {e}", level='error')
            import traceback
            log_event(traceback.format_exc(), level='error')

# 全域快速機器人實例
fast_bot = FastStockBot()

def run_analysis_fast(time_slot: str) -> None:
    """執行快速分析的包裝函數"""
    fast_bot.run_fast_analysis(time_slot)

if __name__ == "__main__":
    import sys
    time_slot = sys.argv[1] if len(sys.argv) > 1 else 'morning_scan'
    run_analysis_fast(time_slot)
