"""
enhanced_stock_bot.py - 改進版每日推播程式
基於緊急分析的成功經驗，改進為更穩定快速的版本
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
    """改進版股市機器人 - 快速穩定版"""
    
    def __init__(self):
        """初始化機器人"""
        self.data_fetcher = TWStockDataFetcher()
        self.cache_dir = os.path.join(DATA_DIR, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 時段配置 - 基於緊急分析的成功經驗調整
        self.time_slot_config = {
            'morning_scan': {
                'name': '早盤掃描',
                'stock_count': 100,
                'analysis_count': 30,  # 實際分析數量
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 2,
                    'weak_stocks': 2
                }
            },
            'mid_morning_scan': {
                'name': '盤中掃描',
                'stock_count': 150,
                'analysis_count': 40,
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 2,
                    'weak_stocks': 1
                }
            },
            'mid_day_scan': {
                'name': '午間掃描',
                'stock_count': 150,
                'analysis_count': 40,
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 2,
                    'weak_stocks': 1
                }
            },
            'afternoon_scan': {
                'name': '盤後掃描',
                'stock_count': 450,
                'analysis_count': 50,  # 盤後分析更多股票
                'recommendation_limits': {
                    'short_term': 4,
                    'long_term': 3,
                    'weak_stocks': 2
                }
            },
            'weekly_summary': {
                'name': '週末總結',
                'stock_count': 200,
                'analysis_count': 50,
                'recommendation_limits': {
                    'short_term': 4,
                    'long_term': 4,
                    'weak_stocks': 3
                }
            }
        }
    
    def get_stocks_for_analysis(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """獲取要分析的股票"""
        log_event(f"🔍 開始獲取 {time_slot} 時段的股票數據")
        
        try:
            stocks = self.data_fetcher.get_stocks_by_time_slot(time_slot, date)
            
            # 過濾掉無效股票
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
    
    def analyze_stock_fast(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """快速分析股票 - 基於緊急分析的成功邏輯"""
        stock_code = stock_info['code']
        stock_name = stock_info['name']
        
        try:
            # 基於當日數據的快速分析
            current_price = stock_info['close']
            change_percent = stock_info['change_percent']
            volume = stock_info['volume']
            trade_value = stock_info['trade_value']
            
            # 快速評分邏輯（經過驗證的算法）
            score = 0
            
            # 價格變動評分 - 主要因子
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
            
            # 成交量評分 - 流動性指標
            if trade_value > 5000000000:  # 50億以上
                score += 2
            elif trade_value > 1000000000:  # 10億以上
                score += 1
            elif trade_value < 10000000:  # 1000萬以下
                score -= 1
            
            # 特殊行業調整
            if any(keyword in stock_name for keyword in ['航運', '海運', '長榮', '陽明', '萬海']):
                # 海運股波動較大，稍微降低門檻
                score += 0.5
            elif any(keyword in stock_name for keyword in ['台積電', '聯發科', '鴻海']):
                # 權值股加分
                score += 0.5
            
            # 根據得分判斷趨勢和建議
            if score >= 4:
                trend = "強烈看漲"
                suggestion = "適合積極買入"
                target_price = round(current_price * 1.08, 1)
                stop_loss = round(current_price * 0.95, 1)
            elif score >= 2:
                trend = "看漲"
                suggestion = "可考慮買入"
                target_price = round(current_price * 1.05, 1)
                stop_loss = round(current_price * 0.97, 1)
            elif score >= 0:
                trend = "中性偏多"
                suggestion = "適合中長期投資"
                target_price = round(current_price * 1.08, 1)
                stop_loss = round(current_price * 0.95, 1)
            elif score > -2:
                trend = "中性"
                suggestion = "觀望為宜"
                target_price = None
                stop_loss = round(current_price * 0.95, 1)
            elif score >= -4:
                trend = "看跌"
                suggestion = "建議減碼"
                target_price = None
                stop_loss = round(current_price * 0.97, 1)
            else:
                trend = "強烈看跌"
                suggestion = "建議賣出"
                target_price = None
                stop_loss = round(current_price * 0.98, 1)
            
            # 生成推薦理由
            reason = self._generate_recommendation_reason(change_percent, trade_value, stock_name)
            
            analysis = {
                "code": stock_code,
                "name": stock_name,
                "current_price": current_price,
                "change_percent": round(change_percent, 1),
                "volume": volume,
                "trade_value": trade_value,
                "weighted_score": round(score, 1),
                "trend": trend,
                "suggestion": suggestion,
                "reason": reason,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "analysis_time": datetime.now().isoformat(),
                "analysis_method": "fast_enhanced",
                "data_quality": "current_day"
            }
            
            return analysis
            
        except Exception as e:
            log_event(f"⚠️ 分析股票 {stock_code} 失敗: {e}", level='warning')
            # 返回基本結果，不中斷整個流程
            return {
                "code": stock_code,
                "name": stock_name,
                "current_price": stock_info.get('close', 0),
                "change_percent": stock_info.get('change_percent', 0),
                "volume": stock_info.get('volume', 0),
                "trade_value": stock_info.get('trade_value', 0),
                "weighted_score": 0,
                "trend": "數據不足",
                "suggestion": "需要更多數據",
                "reason": "分析異常",
                "target_price": None,
                "stop_loss": None,
                "analysis_time": datetime.now().isoformat(),
                "analysis_method": "error",
                "data_quality": "limited"
            }
    
    def _generate_recommendation_reason(self, change_percent: float, trade_value: float, stock_name: str) -> str:
        """生成推薦理由"""
        reasons = []
        
        # 價格變動理由
        if change_percent > 5:
            reasons.append(f"今日大漲 {change_percent:.1f}%，動能強勁")
        elif change_percent > 3:
            reasons.append(f"今日上漲 {change_percent:.1f}%，表現強勢")
        elif change_percent > 1:
            reasons.append(f"今日上漲 {change_percent:.1f}%，走勢良好")
        elif change_percent > 0:
            reasons.append(f"今日微漲 {change_percent:.1f}%，穩健表現")
        elif change_percent < -5:
            reasons.append(f"今日大跌 {abs(change_percent):.1f}%，風險較高")
        elif change_percent < -3:
            reasons.append(f"今日下跌 {abs(change_percent):.1f}%，需注意風險")
        elif change_percent < 0:
            reasons.append(f"今日小跌 {abs(change_percent):.1f}%，短線偏弱")
        
        # 成交量理由
        if trade_value > 5000000000:
            reasons.append("成交金額龐大，市場高度關注")
        elif trade_value > 1000000000:
            reasons.append("成交活躍，資金關注度高")
        elif trade_value > 500000000:
            reasons.append("成交量適中，流動性良好")
        
        # 特殊股票理由
        if any(keyword in stock_name for keyword in ['台積電', '聯發科', '鴻海']):
            reasons.append("權值股表現，指標意義重大")
        elif any(keyword in stock_name for keyword in ['航運', '海運', '長榮', '陽明', '萬海']):
            reasons.append("航運股表現，關注產業動態")
        
        return "、".join(reasons) if reasons else "技術面穩健，適合中長期投資"
    
    def generate_recommendations(self, analyses: List[Dict[str, Any]], time_slot: str) -> Dict[str, List[Dict[str, Any]]]:
        """生成推薦 - 使用驗證過的邏輯"""
        if not analyses:
            return {"short_term": [], "long_term": [], "weak_stocks": []}
        
        # 獲取配置
        config = self.time_slot_config[time_slot]
        limits = config['recommendation_limits']
        
        # 過濾有效分析
        valid_analyses = [a for a in analyses if a.get('data_quality') != 'limited']
        
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
        
        # 長線推薦（得分 0-2 之間）
        long_term_candidates = [a for a in valid_analyses 
                              if 0 <= a.get('weighted_score', 0) < 2 
                              and a.get('trade_value', 0) > 100000000]  # 至少1億成交量
        long_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
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
    
    def run_analysis(self, time_slot: str) -> None:
        """執行分析並發送通知 - 改進版"""
        start_time = time.time()
        log_event(f"🚀 開始執行 {time_slot} 分析")
        
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
            
            # 根據配置決定分析數量
            config = self.time_slot_config[time_slot]
            analysis_count = config['analysis_count']
            
            # 選擇最活躍的股票進行分析
            top_stocks = sorted(stocks, key=lambda x: x.get('trade_value', 0), reverse=True)[:analysis_count]
            
            log_event(f"📊 將分析最活躍的 {len(top_stocks)} 支股票")
            
            # 快速分析
            all_analyses = []
            
            for i, stock in enumerate(top_stocks):
                try:
                    if i % 10 == 0:
                        log_event(f"🔍 分析進度: {i+1}/{len(top_stocks)}")
                    
                    analysis = self.analyze_stock_fast(stock)
                    all_analyses.append(analysis)
                    
                except Exception as e:
                    log_event(f"⚠️ 分析股票 {stock['code']} 失敗: {e}", level='warning')
                    continue
            
            elapsed_time = time.time() - start_time
            log_event(f"✅ 完成 {len(all_analyses)} 支股票分析，耗時 {elapsed_time:.1f} 秒")
            
            # 生成推薦
            recommendations = self.generate_recommendations(all_analyses, time_slot)
            
            # 顯示推薦統計
            short_count = len(recommendations['short_term'])
            long_count = len(recommendations['long_term'])
            weak_count = len(recommendations['weak_stocks'])
            
            log_event(f"📈 推薦結果: 短線 {short_count} 支, 長線 {long_count} 支, 極弱股 {weak_count} 支")
            
            # 發送通知
            display_name = config['name']
            notifier.send_combined_recommendations(recommendations, display_name)
            
            # 保存分析結果
            self.save_analysis_results(all_analyses, recommendations, time_slot)
            
            total_time = time.time() - start_time
            log_event(f"🎉 {time_slot} 分析完成，總耗時 {total_time:.1f} 秒")
            
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
    weekly_summary_time = NOTIFICATION_SCHEDULE['weekly_summary']
    schedule.every().friday.at(weekly_summary_time).do(run_analysis, 'weekly_summary')
    
    # 心跳檢測
    schedule.every().day.at(NOTIFICATION_SCHEDULE['heartbeat']).do(notifier.send_heartbeat)
    
    log_event("✅ 排程任務已設置")

def main() -> None:
    """主函數"""
    log_event("🚀 改進版股市機器人啟動")
    
    # 初始化通知系統
    notifier.init()
    
    # 設置排程任務
    setup_schedule()
    
    # 啟動時發送一次心跳
    notifier.send_heartbeat()
    
    # 運行排程
    log_event("⏰ 開始執行排程任務")
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)  # 每30秒檢查一次
        except KeyboardInterrupt:
            log_event("⚠️ 用戶中斷程序", level='warning')
            break
        except Exception as e:
            log_event(f"❌ 排程執行時發生錯誤: {e}", level='error')
            time.sleep(300)  # 發生錯誤時等待5分鐘
    
    log_event("👋 改進版股市機器人關閉")

if __name__ == "__main__":
    main()
