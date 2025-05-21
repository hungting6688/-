"""
test_notification.py - 測試通知系統
用於檢測通知系統的各種功能是否正常
"""
import os
import sys
import json
import argparse
from datetime import datetime

# 確保可以引入主要模塊
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import notifier
from config import EMAIL_CONFIG, FILE_BACKUP

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
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
            .header {{ color: #0066cc; font-size: 24px; margin-bottom: 20px; }}
            .content {{ margin-bottom: 20px; }}
            .timestamp {{ color: #666; font-size: 14px; }}
            .footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }}
            .success {{ color: green; font-weight: bold; }}
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
                </ul>
                
                <p class="success">測試成功！</p>
            </div>
            
            <div class="footer">
                此郵件由測試程序自動發送，請勿回覆。
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

def test_stock_notification():
    """測試股票推薦通知"""
    print("測試股票推薦通知...")
    
    # 模擬股票數據
    mock_stocks = [
        {
            "code": "2330",
            "name": "台積電",
            "reason": "5日均線上穿20日均線、MACD金叉",
            "target_price": 650.0,
            "stop_loss": 620.0
        },
        {
            "code": "2317",
            "name": "鴻海",
            "reason": "放量上漲、RSI顯示超賣回升",
            "target_price": 120.0,
            "stop_loss": 110.0
        },
        {
            "code": "2454",
            "name": "聯發科",
            "reason": "價格觸及布林帶下軌後反彈、成交量逐漸增加",
            "target_price": 850.0,
            "stop_loss": 800.0
        }
    ]
    
    # 發送股票推薦通知
    success = notifier.send_stock_recommendations(mock_stocks, "測試")
    
    if success:
        print("✅ 股票推薦通知測試成功！")
    else:
        print("❌ 股票推薦通知測試失敗！")
    
    return success

def test_combined_notification():
    """測試股票綜合分析通知"""
    print("測試股票綜合分析通知...")
    
    # 模擬股票分析數據
    mock_data = {
        "short_term": [
            {
                "code": "2330",
                "name": "台積電",
                "current_price": 638.0,
                "reason": "5日均線上穿20日均線、MACD金叉",
                "target_price": 670.0,
                "stop_loss": 620.0
            },
            {
                "code": "2454",
                "name": "聯發科",
                "current_price": 830.0,
                "reason": "放量上漲、RSI顯示超賣回升",
                "target_price": 880.0,
                "stop_loss": 800.0
            }
        ],
        "long_term": [
            {
                "code": "2317",
                "name": "鴻海",
                "current_price": 115.5,
                "reason": "均線多頭排列、RSI處於健康區間",
                "target_price": 140.0,
                "stop_loss": 105.0
            },
            {
                "code": "2412",
                "name": "中華電",
                "current_price": 120.0,
                "reason": "價格位於20日均線上方、成交量逐漸增加",
                "target_price": 130.0,
                "stop_loss": 115.0
            }
        ],
        "weak_stocks": [
            {
                "code": "2002",
                "name": "中鋼",
                "current_price": 25.8,
                "alert_reason": "5日均線下穿20日均線、放量下跌"
            },
            {
                "code": "1301",
                "name": "台塑",
                "current_price": 58.3,
                "alert_reason": "MACD死叉、RSI顯示超買回落"
            }
        ]
    }
    
    # 發送綜合分析通知
    success = notifier.send_combined_recommendations(mock_data, "測試綜合分析")
    
    if success:
        print("✅ 股票綜合分析通知測試成功！")
    else:
        print("❌ 股票綜合分析通知測試失敗！")
    
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
    
    return True

def main():
    """主程序"""
    parser = argparse.ArgumentParser(description='測試通知系統')
    parser.add_argument('--test', '-t', choices=['all', 'simple', 'html', 'urgent', 'stock', 'combined', 'heartbeat'], 
                      default='all', help='指定要運行的測試')
    args = parser.parse_args()
    
    print("=" * 50)
    print("通知系統測試工具")
    print("=" * 50)
    
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
        
    if args.test in ['all', 'urgent']:
        results['urgent'] = test_urgent_notification()
        print()
        
    if args.test in ['all', 'stock']:
        results['stock'] = test_stock_notification()
        print()
        
    if args.test in ['all', 'combined']:
        results['combined'] = test_combined_notification()
        print()
        
    if args.test in ['all', 'heartbeat']:
        results['heartbeat'] = test_heartbeat()
        print()
    
    # 顯示測試結果摘要
    print("=" * 50)
    print("測試結果摘要")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name.ljust(10)}: {status}")
    
    print("-" * 50)
    print(f"總計: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print("\n🎉 所有測試都已通過，通知系統運作正常！")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} 項測試失敗，請檢查日誌以獲取詳細信息。")

if __name__ == "__main__":
    main()
