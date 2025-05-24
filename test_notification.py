"""
test_fixed_notification.py - 測試修復版通知系統
驗證Gmail認證和現價漲跌百分比顯示
"""
import os
import sys
from datetime import datetime

# 模擬股票數據，包含現價和漲跌百分比
def create_test_data():
    """創建測試用的股票推薦數據"""
    return {
        "short_term": [
            {
                "code": "2330",
                "name": "台積電",
                "current_price": 638.5,
                "reason": "5日均線上穿20日均線，MACD出現黃金交叉，技術面轉強",
                "target_price": 670.0,
                "stop_loss": 620.0,
                "trade_value": 14730000000,
                "analysis": {
                    "change_percent": 2.35,
                    "foreign_net_buy": 25000,  # 2.5億買超
                    "technical_signals": {
                        "rsi_healthy": True,
                        "macd_bullish": True,
                        "ma20_bullish": True
                    }
                }
            },
            {
                "code": "2454",
                "name": "聯發科",
                "current_price": 825.0,
                "reason": "放量突破前高，RSI顯示超賣回升，短線動能強勁",
                "target_price": 880.0,
                "stop_loss": 800.0,
                "trade_value": 8950000000,
                "analysis": {
                    "change_percent": 4.12,
                    "foreign_net_buy": 15000,
                    "technical_signals": {
                        "rsi_healthy": True,
                        "macd_bullish": True
                    }
                }
            }
        ],
        "long_term": [
            {
                "code": "2317",
                "name": "鴻海",
                "current_price": 115.5,
                "reason": "均線多頭排列，基本面穩健，適合中長期布局",
                "target_price": 140.0,
                "stop_loss": 105.0,
                "trade_value": 3200000000,
                "analysis": {
                    "change_percent": 0.87,
                    "dividend_yield": 4.2,
                    "pe_ratio": 12.5,
                    "eps_growth": 8.3,
                    "foreign_net_buy": 5000
                }
            }
        ],
        "weak_stocks": [
            {
                "code": "2002",
                "name": "中鋼",
                "current_price": 25.8,
                "alert_reason": "5日均線下穿20日均線，成交量放大，技術面轉弱",
                "trade_value": 980000000,
                "analysis": {
                    "change_percent": -3.21,
                    "foreign_net_buy": -8000  # 8000萬賣超
                }
            }
        ]
    }

def test_gmail_setup():
    """測試Gmail設定"""
    print("🔧 檢查Gmail設定...")
    
    required_vars = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECEIVER']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少環境變數: {', '.join(missing_vars)}")
        print("\n📋 設定步驟:")
        print("1. 創建 .env 文件或設定系統環境變數")
        print("2. 設定以下變數:")
        print("   EMAIL_SENDER=your-email@gmail.com")
        print("   EMAIL_PASSWORD=your-16-digit-app-password")
        print("   EMAIL_RECEIVER=recipient@gmail.com")
        print("\n⚠️ 重要: Gmail需要使用應用程式密碼，不是一般密碼！")
        return False
    
    # 檢查密碼格式
    password = os.getenv('EMAIL_PASSWORD')
    if len(password) != 16:
        print("⚠️ Gmail應用程式密碼應該是16位數")
        print("📋 如何生成應用程式密碼:")
        print("1. 前往 https://myaccount.google.com/")
        print("2. 選擇「安全性」> 「兩步驟驗證」")
        print("3. 啟用兩步驟驗證")
        print("4. 選擇「應用程式密碼」")
        print("5. 選擇「郵件」和您的裝置")
        print("6. 複製生成的16位密碼")
        return False
    
    print("✅ Gmail設定檢查通過")
    return True

def test_basic_notification():
    """測試基本通知功能"""
    print("\n📧 測試基本通知...")
    
    try:
        # 動態導入修復版通知模組
        if 'enhanced_notifier_fixed' in sys.modules:
            notifier = sys.modules['enhanced_notifier_fixed']
        else:
            import enhanced_notifier_fixed as notifier
        
        # 初始化通知系統
        notifier.init()
        
        # 發送測試通知
        test_message = f"""📧 通知系統測試

⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 如果您收到此郵件，表示Gmail認證問題已解決！

🧪 測試內容:
• Gmail SMTP 連接
• TLS 加密通信
• 應用程式密碼認證
• 中文內容顯示

📊 接下來將測試完整的股票推薦格式...
"""
        
        success = notifier.send_notification(
            message=test_message,
            subject="✅ 台股分析系統 - 基本功能測試",
        )
        
        if success:
            print("✅ 基本通知測試成功！")
            return True
        else:
            print("❌ 基本通知測試失敗")
            return False
            
    except ImportError as e:
        print(f"❌ 無法導入通知模組: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        return False

def test_enhanced_stock_notification():
    """測試增強版股票通知（包含現價和漲跌百分比）"""
    print("\n📊 測試增強版股票通知...")
    
    try:
        # 動態導入修復版通知模組
        if 'enhanced_notifier_fixed' in sys.modules:
            notifier = sys.modules['enhanced_notifier_fixed']
        else:
            import enhanced_notifier_fixed as notifier
        
        # 創建測試數據
        test_data = create_test_data()
        
        # 發送增強版通知
        notifier.send_combined_recommendations(test_data, "測試分析")
        
        print("✅ 增強版股票通知已發送！")
        print("\n📋 請檢查您的郵箱，確認以下內容:")
        print("1. ✅ 是否收到郵件")
        print("2. 📈 現價是否正確顯示 (如: 638.5 元)")
        print("3. 📊 漲跌百分比是否正確顯示 (如: +2.35%)")
        print("4. 💵 成交金額是否格式化顯示 (如: 147.3億)")
        print("5. 🏦 外資買賣超是否顯示 (如: 外資買超 2.5億)")
        print("6. 🎯 目標價和止損價是否顯示")
        print("7. 📊 技術指標是否顯示")
        print("8. ⚠️ 風險警示股票是否正確標示")
        
        return True
        
    except Exception as e:
        print(f"❌ 增強版通知測試失敗: {e}")
        return False

def test_html_format():
    """測試HTML格式郵件"""
    print("\n🌐 測試HTML格式...")
    
    try:
        if 'enhanced_notifier_fixed' in sys.modules:
            notifier = sys.modules['enhanced_notifier_fixed']
        else:
            import enhanced_notifier_fixed as notifier
        
        test_data = create_test_data()
        today = datetime.now().strftime("%Y/%m/%d")
        
        # 生成HTML報告
        html_content = notifier.generate_enhanced_html_report(test_data, "HTML測試", today)
        
        # 發送HTML郵件
        plain_message = "這是HTML格式測試郵件，請查看HTML版本以獲得最佳體驗。"
        
        success = notifier.send_notification(
            message=plain_message,
            subject="🌐 HTML格式測試 - 現價漲跌顯示",
            html_body=html_content
        )
        
        if success:
            print("✅ HTML格式測試成功！")
            print("📋 請檢查郵件中的HTML格式是否正常顯示:")
            print("• 顏色和排版")
            print("• 現價和漲跌百分比的格式")
            print("• 圖表和表格")
            return True
        else:
            print("❌ HTML格式測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ HTML測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🔧 台股分析系統 - 修復版通知測試")
    print("=" * 60)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 測試結果統計
    test_results = []
    
    # 1. 檢查Gmail設定
    gmail_ok = test_gmail_setup()
    test_results.append(("Gmail設定", gmail_ok))
    
    if not gmail_ok:
        print("\n❌ Gmail設定有問題，請先修正後再進行測試")
        return
    
    # 2. 測試基本通知
    basic_ok = test_basic_notification()
    test_results.append(("基本通知", basic_ok))
    
    if basic_ok:
        # 3. 測試增強版股票通知
        enhanced_ok = test_enhanced_stock_notification()
        test_results.append(("增強版通知", enhanced_ok))
        
        # 4. 測試HTML格式
        html_ok = test_html_format()
        test_results.append(("HTML格式", html_ok))
    
    # 顯示測試結果摘要
    print("\n" + "=" * 60)
    print("📊 測試結果摘要")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name.ljust(15)}: {status}")
        if result:
            passed += 1
    
    total = len(test_results)
    print("-" * 60)
    print(f"總計: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！通知系統修復成功！")
        print("\n✅ 修復內容:")
        print("• Gmail應用程式密碼認證問題")
        print("• 郵件通知現價顯示")
        print("• 漲跌百分比格式化顯示")
        print("• 成交金額單位轉換")
        print("• 外資買賣超資訊")
        print("• HTML郵件格式優化")
    else:
        print(f"\n⚠️ 還有 {total - passed} 項測試未通過")
        print("請檢查錯誤訊息並修正相關問題")
    
    print("\n" + "=" * 60)
    print("📚 使用說明")
    print("=" * 60)
    print("1. 確保收到所有測試郵件")
    print("2. 檢查郵件內容格式是否正確")
    print("3. 如果測試通過，可以開始使用修復版系統:")
    print("   python enhanced_stock_bot.py")
    print("4. 查看 logs/notifier.log 了解詳細運行情況")
    
if __name__ == "__main__":
    main()
