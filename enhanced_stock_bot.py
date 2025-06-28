#!/usr/bin/env python3
"""
enhanced_stock_bot.py - 兼容性包裝腳本
將舊的調用方式重定向到新的統一分析器

這個腳本確保舊的GitHub Actions工作流程仍然可以正常運行
"""

import sys
import os
from datetime import datetime

def log_event(message: str, level: str = 'info'):
    """記錄事件"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    emoji_map = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌',
        'success': '✅'
    }
    
    emoji = emoji_map.get(level, 'ℹ️')
    print(f"[{timestamp}] {emoji} {message}")

def main():
    """主函數 - 重定向到統一分析器"""
    
    log_event("🔄 enhanced_stock_bot.py 兼容性包裝腳本啟動", "info")
    log_event("📍 重定向到統一股票分析器 (unified_stock_analyzer.py)", "info")
    
    # 檢查統一分析器是否存在
    if not os.path.exists('unified_stock_analyzer.py'):
        log_event("❌ 找不到 unified_stock_analyzer.py", "error")
        log_event("請確保 unified_stock_analyzer.py 文件存在", "error")
        sys.exit(1)
    
    # 獲取命令行參數
    if len(sys.argv) < 2:
        log_event("❌ 缺少時段參數", "error")
        log_event("使用方式: python enhanced_stock_bot.py <time_slot>", "error")
        log_event("可用時段: morning_scan, mid_morning_scan, mid_day_scan, afternoon_scan, weekly_summary", "info")
        sys.exit(1)
    
    time_slot = sys.argv[1]
    log_event(f"🎯 分析時段: {time_slot}", "info")
    
    # 映射到統一分析器的參數
    valid_slots = [
        'morning_scan', 'mid_morning_scan', 'mid_day_scan', 
        'afternoon_scan', 'weekly_summary'
    ]
    
    if time_slot not in valid_slots:
        log_event(f"❌ 無效的時段參數: {time_slot}", "error")
        log_event(f"可用時段: {', '.join(valid_slots)}", "info")
        sys.exit(1)
    
    # 構建統一分析器的命令
    unified_cmd = [
        sys.executable,  # 使用當前的Python解釋器
        'unified_stock_analyzer.py',
        'run',
        '--slot', time_slot,
        '--mode', 'optimized',  # 使用優化模式（對應原enhanced_stock_bot的功能）
        '--data-dir', 'data',
        '--log-level', 'INFO'
    ]
    
    log_event(f"🚀 執行命令: {' '.join(unified_cmd)}", "info")
    
    # 導入統一分析器模組並執行
    try:
        # 添加當前目錄到Python路徑
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        
        # 導入統一分析器
        from unified_stock_analyzer import UnifiedStockAnalyzer
        
        log_event("✅ 統一分析器模組載入成功", "success")
        
        # 創建分析器實例（使用優化模式）
        analyzer = UnifiedStockAnalyzer(mode='optimized')
        
        log_event("✅ 分析器初始化成功", "success")
        log_event(f"🔧 分析模式: OPTIMIZED (增強版功能)", "info")
        
        # 執行分析
        analyzer.run_analysis(time_slot)
        
        log_event("🎉 分析執行完成", "success")
        log_event("📧 分析結果已發送通知", "info")
        
    except ImportError as e:
        log_event(f"❌ 無法導入統一分析器: {e}", "error")
        log_event("請確保 unified_stock_analyzer.py 語法正確", "error")
        sys.exit(1)
        
    except Exception as e:
        log_event(f"❌ 執行分析時發生錯誤: {e}", "error")
        
        # 嘗試發送錯誤通知
        try:
            import notifier
            notifier.init()
            error_msg = f"""🚨 增強版股票分析執行失敗

⏰ 失敗時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 分析時段: {time_slot}
❌ 錯誤訊息: {str(e)}

📋 系統已自動重定向到統一分析器，但執行過程中發生錯誤。
請檢查日誌了解詳細資訊。"""
            
            notifier.send_notification(error_msg, "🚨 分析系統錯誤通知", urgent=True)
            log_event("📧 錯誤通知已發送", "info")
            
        except Exception as notify_error:
            log_event(f"⚠️ 無法發送錯誤通知: {notify_error}", "warning")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
