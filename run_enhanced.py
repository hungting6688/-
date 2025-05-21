"""
 - 增強版台股分析機器人執行腳本
整合多維度分析與白話文轉換功能
"""
import os
import sys
import argparse
import logging
from datetime import datetime

# 導入配置和分析器
from config import LOG_DIR, LOG_CONFIG, STOCK_ANALYSIS, NOTIFICATION_SCHEDULE
import notifier
from stock_analyzer_integrator import StockAnalyzerIntegrator
import stock_bot

def setup_logging():
    """設置日誌"""
    # 確保日誌目錄存在
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 配置日誌
    logging.basicConfig(
        filename=LOG_CONFIG['filename'],
        level=getattr(logging, LOG_CONFIG['level']),
        format=LOG_CONFIG['format']
    )
    
    # 同時輸出到控制台
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, LOG_CONFIG['level']))
    console.setFormatter(logging.Formatter(LOG_CONFIG['format']))
    logging.getLogger().addHandler(console)

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

def run_enhanced_analysis(time_slot, use_white_text=True, market_trend="neutral"):
    """
    執行增強的股市分析並發送通知
    
    參數:
    - time_slot: 時段名稱
    - use_white_text: 是否使用白話文轉換
    - market_trend: 市場趨勢 (bullish, bearish, neutral)
    """
    log_event(f"開始執行增強的 {time_slot} 分析")
    
    try:
        # 確保通知系統可用
        if not notifier.is_notification_available():
            log_event("通知系統不可用，嘗試初始化", level='warning')
            notifier.init()
            
            # 再次檢查
            if not notifier.is_notification_available():
                log_event("通知系統不可用，分析將執行但不發送通知", level='error')
                return
        
        # 創建分析整合器
        integrator = StockAnalyzerIntegrator()
        
        # 獲取股票列表
        all_stocks = integrator.fetch_taiwan_stocks()
        log_event(f"已加載 {len(all_stocks)} 支股票")
        
        # 根據時段選擇要分析的股票
        stocks_to_analyze = integrator.get_stock_list_for_time_slot(time_slot, all_stocks)
        log_event(f"將分析 {len(stocks_to_analyze)} 支股票（時段：{time_slot}）")
        
        # 獲取推薦數量限制
        rec_limits = integrator.get_recommendation_limits(time_slot)
        
        # 設置分析的天數
        if time_slot == 'weekly_summary':
            analysis_days = 60  # 週末總結使用更長的數據
        else:
            analysis_days = 30  # 日常分析使用30天數據
        
        # 分析結果列表
        all_analyses = []
        
        # 對每支股票進行分析
        for stock in stocks_to_analyze:
            stock_code = stock['code']
            try:
                # 獲取股票數據
                log_event(f"獲取股票 {stock_code} 數據")
                stock_data = stock_bot.fetch_stock_data(stock_code, days=analysis_days)
                
                if stock_data.empty:
                    log_event(f"獲取股票 {stock_code} 數據失敗，跳過分析", level='warning')
                    continue
                
                # 計算技術指標
                stock_data_with_indicators = stock_bot.calculate_technical_indicators(stock_data)
                
                # 首先進行基本的技術分析
                technical_analysis = stock_bot.analyze_stock(stock_data_with_indicators)
                
                # 使用整合器增強分析結果
                analysis_type = 'short_term' if 'short' in time_slot or 'morning' in time_slot else 'long_term'
                analysis = integrator.enhance_stock_analysis(
                    stock_data=stock_data_with_indicators,
                    technical_analysis=technical_analysis,
                    analysis_type=analysis_type
                )
                
                # 添加股票名稱
                analysis['name'] = stock['name']
                
                # 添加到分析結果列表
                all_analyses.append(analysis)
                
                log_event(f"股票 {stock_code} 分析完成，趨勢: {analysis.get('trend', '未知')}")
                
            except Exception as e:
                log_event(f"分析股票 {stock_code} 時發生錯誤: {e}", level='error')
                continue
        
        # 生成推薦
        recommendations = stock_bot.generate_stock_recommendations(all_analyses, rec_limits)
        
        # 傳遞完整分析結果給推薦
        for category in ['short_term', 'long_term', 'weak_stocks']:
            for stock in recommendations.get(category, []):
                # 查找對應的完整分析
                for analysis in all_analyses:
                    if analysis['code'] == stock['code']:
                        # 將完整分析數據添加到推薦中
                        stock['analysis'] = analysis
                        break
        
        # 根據時段發送不同的通知
        time_slot_names = {
            'morning_scan': "早盤掃描",
            'mid_morning_scan': "盤中掃描",
            'mid_day_scan': "午間掃描",
            'afternoon_scan': "盤後掃描",
            'weekly_summary': "週末總結"
        }
        
        display_name = time_slot_names.get(time_slot, time_slot)
        
        # 白話文引言生成（如果啟用）
        try:
            if use_white_text:
                import text_formatter
                # 設置引言中的市場環境描述
                intro_text = text_formatter.generate_intro_text(time_slot, market_trend)
                log_event(f"已生成白話文引言: {intro_text[:50]}...")
        except ImportError:
            log_event("白話文轉換模組不可用，使用標準描述", level='warning')
        
        # 發送通知
        notifier.send_combined_recommendations(recommendations, display_name)
        
        # 保存分析結果
        stock_bot.save_analysis_results(all_analyses, recommendations, time_slot)
        
        log_event(f"增強的 {time_slot} 分析完成")
        
    except Exception as e:
        log_event(f"執行 {time_slot} 分析時發生錯誤: {e}", level='error')
        import traceback
        log_event(traceback.format_exc(), level='error')

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='增強版台股分析機器人')
    parser.add_argument('--time-slot', '-t', 
                      choices=['morning_scan', 'mid_morning_scan', 'mid_day_scan', 'afternoon_scan', 'weekly_summary'],
                      default='morning_scan',
                      help='分析時段')
    parser.add_argument('--no-white-text', action='store_true', help='不使用白話文轉換')
    parser.add_argument('--market', '-m', 
                      choices=['bullish', 'bearish', 'neutral'],
                      default='neutral',
                      help='市場趨勢描述')
    
    args = parser.parse_args()
    
    # 設置日誌
    setup_logging()
    
    # 初始化通知系統
    notifier.init()
    
    # 執行增強分析
    run_enhanced_analysis(
        time_slot=args.time_slot,
        use_white_text=not args.no_white_text,
        market_trend=args.market
    )

if __name__ == "__main__":
    main()
