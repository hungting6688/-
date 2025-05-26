"""
run_optimized_system.py - 啟動優化版股市分析系統
針對長線推薦加強 EPS、法人買超、殖利率等基本面分析
"""
import os
import sys
import time
import schedule
import argparse
from datetime import datetime

# 添加當前目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入優化版模組
try:
    from enhanced_stock_bot_optimized import OptimizedStockBot, run_optimized_analysis
    import optimized_notifier as notifier
    from config import NOTIFICATION_SCHEDULE
    OPTIMIZED_AVAILABLE = True
    print("✅ 已載入優化版股市分析系統")
except ImportError as e:
    print(f"❌ 無法載入優化版系統: {e}")
    print("⚠️ 請確認 enhanced_stock_bot_optimized.py 和 optimized_notifier.py 檔案存在")
    OPTIMIZED_AVAILABLE = False

def setup_optimized_schedule():
    """設置優化版排程任務"""
    if not OPTIMIZED_AVAILABLE:
        print("❌ 優化版系統不可用，無法設置排程")
        return False
    
    print("⏰ 設置優化版排程任務...")
    
    # 工作日排程
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    
    # 早盤掃描 (9:00) - 200支股票，短線為主
    for day in weekdays:
        getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['morning_scan']).do(
            run_optimized_analysis, 'morning_scan'
        )
    
    # 盤中掃描 (10:30) - 300支股票，短線為主
    for day in weekdays:
        getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(
            run_optimized_analysis, 'mid_morning_scan'
        )
    
    # 午間掃描 (12:30) - 300支股票，混合分析
    for day in weekdays:
        getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(
            run_optimized_analysis, 'mid_day_scan'
        )
    
    # 盤後掃描 (15:00) - 1000支股票，混合分析，長線推薦增加
    for day in weekdays:
        getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(
            run_optimized_analysis, 'afternoon_scan'
        )
    
    # 週末總結 (週五17:00) - 1000支股票，長線為主
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['weekly_summary']).do(
        run_optimized_analysis, 'weekly_summary'
    )
    
    # 心跳檢測
    schedule.every().day.at(NOTIFICATION_SCHEDULE['heartbeat']).do(notifier.send_heartbeat)
    
    print("✅ 優化版排程任務設置完成")
    
    # 顯示排程概覽
    print("\n📅 排程概覽:")
    print("  🌅 早盤掃描 (09:00): 200支股票，短線推薦優先")
    print("  ☀️ 盤中掃描 (10:30): 300支股票，短線推薦優先")
    print("  🌞 午間掃描 (12:30): 300支股票，混合分析")
    print("  🌇 盤後掃描 (15:00): 1000支股票，長線推薦增加")
    print("  📈 週末總結 (週五17:00): 1000支股票，長線為主")
    print("  💓 心跳檢測: 每日08:30")
    
    return True

def run_daemon():
    """運行優化版後台服務"""
    print("🚀 啟動優化版股市分析系統")
    print("=" * 60)
    print("💎 主要優化特色:")
    print("  • 長線推薦權重優化: 基本面 1.2倍, 法人 0.8倍")
    print("  • 重視高殖利率股票 (>2.5% 優先推薦)")
    print("  • 重視EPS高成長股票 (>8% 優先推薦)")
    print("  • 重視法人買超股票 (>5000萬優先推薦)")
    print("  • 強化通知顯示: 詳細基本面資訊")
    print("  • 連續配息年數納入評分")
    print("=" * 60)
    
    if not OPTIMIZED_AVAILABLE:
        print("❌ 優化版系統不可用，程序退出")
        return
    
    # 初始化通知系統
    notifier.init()
    
    # 設置排程
    if not setup_optimized_schedule():
        print("❌ 排程設置失敗，程序退出")
        return
    
    # 啟動時發送心跳
    print("💓 發送啟動心跳...")
    notifier.send_heartbeat()
    
    print("\n🎯 系統已啟動，開始執行排程任務...")
    print("📝 按 Ctrl+C 停止系統")
    
    # 運行排程循環
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # 每30秒檢查一次
    except KeyboardInterrupt:
        print("\n\n⚠️ 收到用戶中斷信號")
        print("🛑 正在優雅關閉系統...")
        
        # 發送關閉通知
        try:
            close_message = f"""📴 優化版股市分析系統關閉通知

⏰ 關閉時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 系統已安全關閉
💎 感謝使用優化版長線基本面分析系統

下次啟動時將繼續為您提供：
• 高殖利率股票推薦
• EPS高成長股票推薦  
• 法人大額買超股票推薦
• 詳細基本面分析報告

祝您投資順利！💰"""
            
            notifier.send_notification(close_message, "📴 優化版系統關閉通知")
        except:
            pass
        
        print("👋 系統已關閉")
    except Exception as e:
        print(f"\n❌ 系統運行出現錯誤: {e}")
        
        # 發送錯誤通知
        try:
            error_message = f"""⚠️ 優化版股市分析系統錯誤通知

⏰ 錯誤時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ 錯誤內容: {str(e)}

請檢查系統狀態並重新啟動。"""
            
            notifier.send_notification(error_message, "⚠️ 優化版系統錯誤通知", urgent=True)
        except:
            pass
        
        print("🔄 請檢查錯誤並重新啟動系統")

def run_single_analysis(time_slot):
    """執行單次分析"""
    if not OPTIMIZED_AVAILABLE:
        print("❌ 優化版系統不可用")
        return
    
    print(f"🔍 執行優化版 {time_slot} 分析...")
    
    # 顯示該時段的特色
    time_slot_info = {
        'morning_scan': {
            'name': '早盤掃描',
            'stocks': 200,
            'focus': '短線技術面',
            'feature': '快速捕捉開盤機會'
        },
        'mid_morning_scan': {
            'name': '盤中掃描', 
            'stocks': 300,
            'focus': '短線動能',
            'feature': '追蹤盤中強勢股'
        },
        'mid_day_scan': {
            'name': '午間掃描',
            'stocks': 300, 
            'focus': '混合分析',
            'feature': '平衡技術面與基本面'
        },
        'afternoon_scan': {
            'name': '盤後掃描',
            'stocks': 1000,
            'focus': '混合分析',
            'feature': '全面分析，長線推薦增加'
        },
        'weekly_summary': {
            'name': '週末總結',
            'stocks': 1000,
            'focus': '長線基本面',
            'feature': '重點挖掘基本面優質股'
        }
    }
    
    info = time_slot_info.get(time_slot, {'name': time_slot, 'stocks': 100, 'focus': '混合', 'feature': '綜合分析'})
    
    print(f"📊 {info['name']}")
    print(f"🔢 分析股票數: {info['stocks']} 支")
    print(f"🎯 分析重點: {info['focus']}")
    print(f"✨ 特色: {info['feature']}")
    
    if time_slot in ['afternoon_scan', 'weekly_summary']:
        print("💎 長線推薦將重點關注:")
        print("  • 殖利率 > 2.5% 的高息股")
        print("  • EPS成長 > 8% 的成長股")
        print("  • 法人買超 > 5000萬的法人愛股")
        print("  • ROE > 12% 的獲利能力優秀股")
        print("  • 連續配息 > 5年的穩定股")
    
    print("\n" + "="*50)
    
    try:
        # 初始化通知系統
        notifier.init()
        
        # 執行分析
        run_optimized_analysis(time_slot)
        
        print(f"✅ {info['name']} 分析完成！")
        print("📧 分析報告已發送，請檢查您的郵箱")
        
    except Exception as e:
        print(f"❌ 分析執行失敗: {e}")
        import traceback
        print(traceback.format_exc())

def show_status():
    """顯示系統狀態"""
    print("📊 優化版股市分析系統狀態")
    print("=" * 50)
    
    if not OPTIMIZED_AVAILABLE:
        print("❌ 系統狀態: 不可用")
        print("⚠️ 請檢查相關模組是否正確安裝")
        return
    
    print("✅ 系統狀態: 可用")
    print("💎 系統版本: 長線基本面優化版")
    
    # 檢查通知狀態
    try:
        notifier.init()
        if notifier.is_notification_available():
            print("📧 通知系統: 可用")
        else:
            print("⚠️ 通知系統: 不可用")
    except Exception as e:
        print(f"❌ 通知系統: 錯誤 - {e}")
    
    # 顯示優化特色
    print("\n💎 優化特色:")
    print("  📈 長線推薦基本面權重: 1.2倍 (提高20%)")
    print("  🏦 法人買賣權重: 0.8倍 (提高60%)")
    print("  💸 殖利率 > 2.5% 優先推薦")
    print("  📊 EPS成長 > 8% 優先推薦")
    print("  💰 法人買超 > 5000萬優先推薦")
    print("  🏆 ROE > 12% 加分評估")
    print("  ⏰ 連續配息 > 5年 穩定性加分")
    
    print("\n📅 排程時段:")
    print("  🌅 早盤掃描 (09:00): 200支股票")
    print("  ☀️ 盤中掃描 (10:30): 300支股票") 
    print("  🌞 午間掃描 (12:30): 300支股票")
    print("  🌇 盤後掃描 (15:00): 1000支股票 ⭐長線推薦增加")
    print("  📈 週末總結 (週五17:00): 1000支股票 ⭐長線為主")
    
    print("\n📧 通知優化:")
    print("  💎 長線推薦區塊獨立顯示")
    print("  📊 基本面指標詳細標示")
    print("  🏦 法人買賣金額清楚顯示")
    print("  🎨 HTML格式美化呈現")

def test_optimized_notification():
    """測試優化版通知"""
    if not OPTIMIZED_AVAILABLE:
        print("❌ 優化版系統不可用，無法測試")
        return
    
    print("📧 測試優化版通知系統...")
    
    try:
        # 初始化
        notifier.init()
        
        # 創建測試數據 - 展示長線基本面優勢
        test_data = {
            "short_term": [
                {
                    "code": "2330",
                    "name": "台積電", 
                    "current_price": 638.5,
                    "reason": "技術面轉強，MACD金叉",
                    "target_price": 670.0,
                    "stop_loss": 620.0,
                    "trade_value": 14730000000,
                    "analysis": {
                        "change_percent": 2.35,
                        "foreign_net_buy": 25000
                    }
                }
            ],
            "long_term": [
                {
                    "code": "2609",
                    "name": "陽明",
                    "current_price": 91.2,
                    "reason": "高殖利率7.2%，EPS高成長35.6%，三大法人大幅買超62億，連續配息5年穩定",
                    "target_price": 110.0,
                    "stop_loss": 85.0,
                    "trade_value": 4560000000,
                    "analysis": {
                        "change_percent": 1.8,
                        "dividend_yield": 7.2,       # 高殖利率
                        "eps_growth": 35.6,          # 高EPS成長
                        "pe_ratio": 8.9,             # 低本益比
                        "roe": 18.4,                 # 優秀ROE
                        "revenue_growth": 28.9,      # 營收成長
                        "dividend_consecutive_years": 5,  # 連續配息
                        "foreign_net_buy": 45000,    # 外資大幅買超
                        "trust_net_buy": 15000,      # 投信買超
                        "total_institutional": 62000, # 三大法人合計
                        "consecutive_buy_days": 6     # 持續買超天數
                    }
                },
                {
                    "code": "2882", 
                    "name": "國泰金",
                    "current_price": 58.3,
                    "reason": "穩定殖利率6.2%，連續配息18年，外資持續買超1.6億",
                    "target_price": 65.0,
                    "stop_loss": 55.0,
                    "trade_value": 2100000000,
                    "analysis": {
                        "change_percent": 0.5,
                        "dividend_yield": 6.2,        # 高殖利率
                        "eps_growth": 8.5,           # 穩定EPS成長
                        "pe_ratio": 11.3,            # 合理本益比
                        "roe": 13.8,                 # 良好ROE
                        "revenue_growth": 6.7,       # 營收成長
                        "dividend_consecutive_years": 18,  # 長期穩定配息
                        "foreign_net_buy": 16000,    # 外資買超
                        "trust_net_buy": 3000,       # 投信買超
                        "total_institutional": 20000, # 法人合計
                        "consecutive_buy_days": 4     # 持續買超
                    }
                },
                {
                    "code": "1301",
                    "name": "台塑",
                    "current_price": 115.8,
                    "reason": "殖利率5.1%，連續20年配息，EPS成長12.7%，傳產龍頭地位穩固",
                    "target_price": 125.0,
                    "stop_loss": 108.0,
                    "trade_value": 1800000000,
                    "analysis": {
                        "change_percent": -0.3,
                        "dividend_yield": 5.1,        # 穩定殖利率
                        "eps_growth": 12.7,          # 雙位數EPS成長
                        "pe_ratio": 12.8,            # 合理估值
                        "roe": 14.2,                 # 良好獲利能力
                        "revenue_growth": 9.3,       # 營收成長
                        "dividend_consecutive_years": 20,  # 超長期穩定配息
                        "foreign_net_buy": 8000,     # 外資買超
                        "trust_net_buy": 2000,       # 投信買超
                        "total_institutional": 11000, # 法人合計
                        "consecutive_buy_days": 3     # 持續買超
                    }
                }
            ],
            "weak_stocks": [
                {
                    "code": "6666",
                    "name": "測試弱股",
                    "current_price": 25.8,
                    "alert_reason": "技術面轉弱，法人大幅賣超",
                    "trade_value": 500000000,
                    "analysis": {
                        "change_percent": -5.2
                    }
                }
            ]
        }
        
        # 發送測試通知
        notifier.send_optimized_combined_recommendations(test_data, "優化版功能測試")
        
        print("✅ 測試通知已發送！")
        print("\n📋 請檢查郵箱確認以下優化內容:")
        print("🎯 長線推薦部分:")
        print("  📊 基本面指標是否清楚顯示（殖利率、EPS成長、ROE等）")
        print("  🏦 法人買賣金額是否詳細標示")
        print("  ⏰ 連續配息年數是否顯示")
        print("  💎 長線推薦區塊是否突出顯示")
        print("  🎨 HTML格式是否美觀（基本面和法人動向分區顯示）")
        print("  🔢 數字格式化是否正確（億、萬單位轉換）")
        
        print("\n💡 優化亮點:")
        print("  • 陽明: 殖利率7.2% + EPS成長35.6% + 法人買超6.2億")
        print("  • 國泰金: 殖利率6.2% + 連續配息18年 + 外資買超1.6億")
        print("  • 台塑: 殖利率5.1% + 連續配息20年 + EPS成長12.7%")
        
    except Exception as e:
        print(f"❌ 測試通知失敗: {e}")
        import traceback
        print(traceback.format_exc())

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='優化版台股分析系統 - 強化長線基本面分析')
    parser.add_argument('command', 
                       choices=['start', 'run', 'status', 'test'],
                       help='執行命令')
    parser.add_argument('--slot', '-s',
                       choices=['morning_scan', 'mid_morning_scan', 'mid_day_scan', 
                               'afternoon_scan', 'weekly_summary'],
                       help='分析時段 (配合 run 命令使用)')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        # 啟動後台服務
        run_daemon()
        
    elif args.command == 'run':
        # 執行單次分析
        if not args.slot:
            print("❌ 使用 run 命令時必須指定 --slot 參數")
            print("📝 範例: python run_optimized_system.py run --slot afternoon_scan")
            return
        
        run_single_analysis(args.slot)
        
    elif args.command == 'status':
        # 顯示系統狀態
        show_status()
        
    elif args.command == 'test':
        # 測試通知
        test_optimized_notification()

if __name__ == "__main__":
    main()
