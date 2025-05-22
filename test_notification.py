"""
enhanced_test_notification.py - 增強版通知系統測試腳本
測試多維度分析和白話文轉換功能
"""
import os
import sys
import json
import argparse
from datetime import datetime

# 確保可以引入主要模塊
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入通知系統
try:
    import enhanced_notifier as notifier
    ENHANCED_NOTIFIER_AVAILABLE = True
except ImportError:
    import notifier
    ENHANCED_NOTIFIER_AVAILABLE = False

# 導入配置
try:
    from enhanced_config import EMAIL_CONFIG, FILE_BACKUP
except ImportError:
    from config import EMAIL_CONFIG, FILE_BACKUP

# 導入白話文轉換
try:
    import text_formatter
    WHITE_TEXT_AVAILABLE = True
except ImportError:
    WHITE_TEXT_AVAILABLE = False

def test_simple_notification():
    """測試簡單文字通知"""
    print("測試簡單文字通知...")
    
    # 組裝測試訊息
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = "測試通知"
    message = f"""這是一條測試通知
    
時間: {current_time}
    
這是一個簡單的文字訊息，用於測試通知系統是否正常運作。
如果您收到此訊息，表示通知系統運作正常。

---
此訊息由測試程序自動發送
"""
    
    # 發送通知
    success = notifier.send_notification(
        message=message,
        subject=subject
    )
    
    if success:
        print("✅ 簡單文字通知測試成功！")
    else:
        print("❌ 簡單文字通知測試失敗！")
    
    return success

def test_html_notification():
    """測試HTML格式通知"""
    print("測試HTML格式通知...")
    
    # 組裝測試訊息
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = "HTML格式測試通知"
    
    # 純文字內容
    message = f"""這是一條HTML格式測試通知
    
時間: {current_time}
    
這是測試HTML格式的通知。如果您的郵件客戶端支持HTML格式，您應該能看到格式化的內容。
    
此訊息由測試程序自動發送
"""
    
    # HTML格式內容
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Microsoft JhengHei', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
            .header {{ color: #0066cc; font-size: 24px; margin-bottom: 20px; }}
            .content {{ margin-bottom: 20px; }}
            .timestamp {{ color: #666; font-size: 14px; }}
            .footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }}
            .success {{ color: green; font-weight: bold; }}
            .badge {{ display: inline-block; padding: 4px 8px; background: #e3f2fd; color: #1976d2; border-radius: 12px; font-size: 12px; margin: 2px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">HTML格式測試通知</div>
            
            <div class="content">
                <p>這是一條<strong>HTML格式</strong>的測試通知。</p>
                
                <p class="timestamp">時間: {current_time}</p>
                
                <p>如果您看到這段格式化的文字，表示您的郵件客戶端支持HTML格式，且通知系統可正常發送HTML內容。</p>
                
                <p>測試項目：</p>
                <ul>
                    <li>格式化文字</li>
                    <li>顏色顯示</li>
                    <li>排版布局</li>
                    <li>徽章顯示: <span class="badge">HTML支援</span></li>
                </ul>
                
                <p class="success">測試成功！</p>
            </div>
            
            <div class="footer">
                此郵件由增強版測試程序自動發送，請勿回復。
            </div>
        </div>
    </body>
    </html>
    """
    
    # 發送通知
    success = notifier.send_notification(
        message=message,
        subject=subject,
        html_body=html_body
    )
    
    if success:
        print("✅ HTML格式通知測試成功！")
    else:
        print("❌ HTML格式通知測試失敗！")
    
    return success

def test_white_text_conversion():
    """測試白話文轉換功能"""
    print("測試白話文轉換功能...")
    
    if not WHITE_TEXT_AVAILABLE:
        print("⚠️ 白話文轉換模組不可用，跳過測試")
        return False
    
    # 模擬股票分析結果
    mock_analysis = {
        "code": "2330",
        "name": "台積電",
        "current_price": 638.0,
        "weighted_score": 7.5,
        "target_price": 670.0,
        "stop_loss": 620.0,
        "rsi": 58,
        "signals": {
            "ma5_crosses_above_ma20": True,
            "macd_crosses_above_signal": True,
            "price_up": True,
            "volume_spike": True,
            "rsi_bullish": True
        }
    }
    
    try:
        # 測試短線白話文轉換
        short_term_text = text_formatter.generate_plain_text(mock_analysis, "short_term")
        print(f"短線描述: {short_term_text['description']}")
        print(f"短線建議: {short_term_text['suggestion']}")
        
        # 測試長線白話文轉換
        long_term_text = text_formatter.generate_plain_text(mock_analysis, "long_term")
        print(f"長線描述: {long_term_text['description']}")
        print(f"長線建議: {long_term_text['suggestion']}")
        
        # 測試引言生成
        intro_text = text_formatter.generate_intro_text("morning_scan", "bullish")
        print(f"引言範例: {intro_text}")
        
        print("✅ 白話文轉換功能測試成功！")
        return True
        
    except Exception as e:
        print(f"❌ 白話文轉換功能測試失敗: {e}")
        return False

def test_urgent_notification():
    """測試緊急通知"""
    print("測試緊急通知...")
    
    # 組裝測試訊息
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = "緊急測試通知"
    message = f"""⚠️ 這是一條緊急測試通知 ⚠️
    
時間: {current_time}
    
這是模擬緊急情況的測試訊息。在實際應用中，此類通知將用於重要警報。
    
此訊息由測試程序自動發送，請忽略此緊急提示。
"""
    
    # 發送通知
    success = notifier.send_notification(
        message=message,
        subject=subject,
        urgent=True
    )
    
    if success:
        print("✅ 緊急通知測試成功！")
    else:
        print("❌ 緊急通知測試失敗！")
    
    return success

def test_enhanced_stock_notification():
    """測試增強版股票推薦通知"""
    print("測試增強版股票推薦通知...")
    
    # 模擬增強版股票數據
    mock_stocks = [
        {
            "code": "2330",
            "name": "台積電",
            "current_price": 638.0,
            "reason": "5日均線上穿20日均線、MACD金叉",
            "target_price": 670.0,
            "stop_loss": 620.0,
            "analysis": {
                "code": "2330",
                "current_price": 638.0,
                "weighted_score": 7.5,
                "comprehensive_score": 7.5,
                "technical_contribution": 5.2,
                "fundamental_contribution": 1.8,
                "rs_contribution": 0.5,
                "signals": {
                    "ma5_crosses_above_ma20": True,
                    "macd_crosses_above_signal": True,
                    "price_up": True,
                    "volume_spike": True
                },
                "pe_ratio": 23.5,
                "dividend_yield": 2.8,
                "eps_growth": 15.2
            }
        },
        {
            "code": "2454",
            "name": "聯發科",
            "current_price": 830.0,
            "reason": "放量上漲、RSI顯示超賣回升",
            "target_price": 880.0,
            "stop_loss": 800.0,
            "analysis": {
                "code": "2454",
                "current_price": 830.0,
                "weighted_score": 8.2,
                "comprehensive_score": 8.2,
                "technical_contribution": 6.1,
                "fundamental_contribution": 1.6,
                "rs_contribution": 0.5,
                "signals": {
                    "macd_crosses_above_signal": True,
                    "rsi_bullish": True,
                    "volume_increasing": True
                },
                "eps_growth": 18.5
            }
        }
    ]
    
    # 發送股票推薦通知
    success = notifier.send_stock_recommendations(mock_stocks, "測試")
    
    if success:
        print("✅ 增強版股票推薦通知測試成功！")
    else:
        print("❌ 增強版股票推薦通知測試失敗！")
    
    return success

def test_combined_analysis_notification():
    """測試綜合分析通知"""
    print("測試綜合分析通知...")
    
    # 模擬完整的綜合分析數據
    mock_data = {
        "short_term": [
            {
                "code": "2330",
                "name": "台積電",
                "current_price": 638.0,
                "reason": "5日均線上穿20日均線、MACD金叉",
                "target_price": 670.0,
                "stop_loss": 620.0,
                "analysis": {
                    "code": "2330",
                    "current_price": 638.0,
                    "weighted_score": 7.5,
                    "comprehensive_score": 7.5,
                    "technical_contribution": 5.2,
                    "fundamental_contribution": 1.8,
                    "rs_contribution": 0.5,
                    "signals": {
                        "ma5_crosses_above_ma20": True,
                        "macd_crosses_above_signal": True,
                        "price_up": True,
                        "volume_spike": True
                    },
                    "pe_ratio": 23.5,
                    "dividend_yield": 2.8,
                    "eps_growth": 15.2
                }
            }
        ],
        "long_term": [
            {
                "code": "2317",
                "name": "鴻海",
                "current_price": 115.5,
                "reason": "均線多頭排列、RSI處於健康區間",
                "target_price": 140.0,
                "stop_loss": 105.0,
                "analysis": {
                    "code": "2317",
                    "current_price": 115.5,
                    "weighted_score": 6.3,
                    "comprehensive_score": 6.3,
                    "technical_contribution": 1.5,
                    "fundamental_contribution": 4.2,
                    "rs_contribution": 0.6,
                    "signals": {
                        "ma5_above_ma20": True,
                        "ma10_above_ma20": True,
                        "price_above_ma20": True
                    },
                    "dividend_yield": 4.5,
                    "roe": 18.2
                }
            }
        ],
        "weak_stocks": [
            {
                "code": "2002",
                "name": "中鋼",
                "current_price": 25.8,
                "alert_reason": "5日均線下穿20日均線、放量下跌",
                "analysis": {
                    "code": "2002",
                    "current_price": 25.8,
                    "weighted_score": -8.2,
                    "comprehensive_score": -8.2,
                    "technical_contribution": -6.5,
                    "fundamental_contribution": -1.2,
                    "rs_contribution": -0.5,
                    "signals": {
                        "ma5_crosses_below_ma20": True,
                        "volume_spike": True,
                        "price_down": True
                    }
                }
            }
        ]
    }
    
    # 發送綜合分析通知
    success = notifier.send_combined_recommendations(mock_data, "測試綜合分析")
    
    if success:
        print("✅ 綜合分析通知測試成功！")
    else:
        print("❌ 綜合分析通知測試失敗！")
    
    return success

def test_heartbeat():
    """測試心跳通知"""
    print("測試心跳通知...")
    
    # 發送心跳通知
    success = notifier.send_heartbeat()
    
    if success:
        print("✅ 心跳通知測試成功！")
    else:
        print("❌ 心跳通知測試失敗！")
    
    return success

def test_multi_dimensional_analysis():
    """測試多維度分析功能"""
    print("測試多維度分析功能...")
    
    try:
        from stock_analyzer_integrator import StockAnalyzerIntegrator
        
        # 創建分析整合器
        integrator = StockAnalyzerIntegrator()
        
        # 測試股票列表獲取
        stocks = integrator.fetch_taiwan_stocks()
        print(f"成功獲取 {len(stocks)} 支股票")
        
        # 測試時段配置
        morning_stocks = integrator.get_stock_list_for_time_slot('morning_scan', stocks)
        print(f"早盤掃描將分析 {len(morning_stocks)} 支股票")
        
        # 測試推薦限制
        limits = integrator.get_recommendation_limits('morning_scan')
        print(f"早盤推薦限制: {limits}")
        
        print("✅ 多維度分析功能測試成功！")
        return True
        
    except ImportError:
        print("⚠️ 股票分析整合器不可用，跳過測試")
        return False
    except Exception as e:
        print(f"❌ 多維度分析功能測試失敗: {e}")
        return False

def check_config():
    """檢查基本配置"""
    print("檢查基本配置...")
    
    # 檢查電子郵件配置
    if EMAIL_CONFIG['enabled']:
        missing = []
        for key in ['sender', 'password', 'receiver']:
            if not EMAIL_CONFIG[key]:
                missing.append(key)
        
        if missing:
            print(f"❌ 電子郵件配置不完整，缺少以下項目: {', '.join(missing)}")
            print(f"   請在.env文件中設置 EMAIL_{', EMAIL_'.join([m.upper() for m in missing])}")
            return False
        else:
            print(f"✅ 電子郵件配置完整")
            print(f"   發件人: {EMAIL_CONFIG['sender']}")
            print(f"   收件人: {EMAIL_CONFIG['receiver']}")
            print(f"   SMTP服務器: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
    else:
        print("⚠️ 電子郵件通知已禁用")
    
    # 檢查文件備份配置
    if FILE_BACKUP['enabled']:
        if not os.path.exists(FILE_BACKUP['directory']):
            try:
                os.makedirs(FILE_BACKUP['directory'], exist_ok=True)
                print(f"✅ 已創建文件備份目錄: {FILE_BACKUP['directory']}")
            except Exception as e:
                print(f"❌ 無法創建文件備份目錄: {e}")
                return False
        else:
            print(f"✅ 文件備份目錄已存在: {FILE_BACKUP['directory']}")
    else:
        print("⚠️ 文件備份已禁用")
    
    # 檢查白話文轉換模組
    if WHITE_TEXT_AVAILABLE:
        print("✅ 白話文轉換模組可用")
    else:
        print("⚠️ 白話文轉換模組不可用")
    
    # 檢查增強版通知模組
    if ENHANCED_NOTIFIER_AVAILABLE:
        print("✅ 增強版通知模組可用")
    else:
        print("⚠️ 使用標準通知模組")
    
    return True

def main():
    """主程序"""
    parser = argparse.ArgumentParser(description='增強版通知系統測試工具')
    parser.add_argument('--test', '-t', 
                      choices=['all', 'simple', 'html', 'white-text', 'urgent', 'stock', 'combined', 'heartbeat', 'analysis'], 
                      default='all', help='指定要運行的測試')
    args = parser.parse_args()
    
    print("=" * 60)
    print("增強版通知系統測試工具")
    print("=" * 60)
    
    # 檢查配置
    if not check_config():
        print("\n❌ 配置檢查失敗，測試中止！")
        return
    
    print("\n配置檢查通過，開始測試...\n")
    
    # 初始化通知系統
    notifier.init()
    
    # 根據參數選擇測試
    results = {}
    
    if args.test in ['all', 'simple']:
        results['simple'] = test_simple_notification()
        print()
        
    if args.test in ['all', 'html']:
        results['html'] = test_html_notification()
        print()
        
    if args.test in ['all', 'white-text']:
        results['white-text'] = test_white_text_conversion()
        print()
        
    if args.test in ['all', 'urgent']:
        results['urgent'] = test_urgent_notification()
        print()
        
    if args.test in ['all', 'stock']:
        results['stock'] = test_enhanced_stock_notification()
        print()
        
    if args.test in ['all', 'combined']:
        results['combined'] = test_combined_analysis_notification()
        print()
        
    if args.test in ['all', 'heartbeat']:
        results['heartbeat'] = test_heartbeat()
        print()
        
    if args.test in ['all', 'analysis']:
        results['analysis'] = test_multi_dimensional_analysis()
        print()
    
    # 顯示測試結果摘要
    print("=" * 60)
    print("測試結果摘要")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name.ljust(15)}: {status}")
    
    print("-" * 60)
    print(f"總計: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print("\n🎉 所有測試都已通過，增強版通知系統運作正常！")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} 項測試失敗，請檢查日誌以獲取詳細信息。")
        
    # 提供後續步驟建議
    print("\n" + "=" * 60)
    print("後續步驟建議")
    print("=" * 60)
    print("1. 如果所有測試通過，您可以開始使用增強版台股分析機器人")
    print("2. 使用 'python run_enhanced.py --time-slot morning_scan' 進行實際分析")
    print("3. 查看 logs/ 目錄下的日誌文件以獲取詳細運行信息")
    print("4. 根據需要調整 enhanced_config.py 中的配置參數")

if __name__ == "__main__":
    main()
