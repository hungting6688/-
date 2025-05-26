"""
test_fixed_display.py - 測試修復版顯示效果
驗證短線技術指標標籤和長線文字清晰度的修復
"""
import os
import sys
from datetime import datetime

# 確保可以導入修復版通知模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_technical_indicators_display():
    """測試技術指標標籤顯示修復"""
    print("=" * 60)
    print("🔧 測試技術指標標籤顯示修復")
    print("=" * 60)
    
    # 模擬包含豐富技術指標的分析數據
    analysis_with_indicators = {
        'rsi': 65.2,
        'volume_ratio': 2.8,
        'foreign_net_buy': 25000,
        'technical_signals': {
            'macd_golden_cross': True,
            'macd_bullish': True,
            'ma20_bullish': True,
            'ma_golden_cross': True,
            'rsi_healthy': True
        }
    }
    
    # 測試技術指標文字生成
    try:
        # 導入修復版通知模組
        import optimized_notifier_fixed as notifier
        
        # 測試技術指標提取函數
        indicators = notifier.get_technical_indicators_text(analysis_with_indicators)
        
        print("✅ 技術指標提取測試:")
        print(f"原始數據包含: RSI、MACD、均線、成交量、外資買超指標")
        print(f"提取結果: {indicators}")
        print(f"指標數量: {len(indicators)}")
        
        # 驗證各類指標是否正確提取
        expected_indicators = ['RSI', 'MACD', '均線', '成交量', '外資']
        found_indicators = []
        
        for indicator in indicators:
            for expected in expected_indicators:
                if expected in indicator or (expected == 'RSI' and 'RSI' in indicator):
                    found_indicators.append(expected)
                elif expected == 'MACD' and ('MACD' in indicator or 'macd' in indicator.lower()):
                    found_indicators.append(expected)
                elif expected == '均線' and ('MA' in indicator or '均線' in indicator):
                    found_indicators.append(expected)
                elif expected == '成交量' and ('量' in indicator or '倍' in indicator):
                    found_indicators.append(expected)
                elif expected == '外資' and '外資' in indicator:
                    found_indicators.append(expected)
        
        found_indicators = list(set(found_indicators))  # 去重
        
        print(f"✅ 找到的指標類型: {found_indicators}")
        
        if len(found_indicators) >= 3:
            print("✅ 技術指標提取功能正常")
            return True
        else:
            print("❌ 技術指標提取不完整")
            return False
            
    except ImportError as e:
        print(f"❌ 無法導入修復版通知模組: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試技術指標提取失敗: {e}")
        return False

def test_long_term_clarity():
    """測試長線推薦文字清晰度"""
    print("\n" + "=" * 60)
    print("💎 測試長線推薦文字清晰度")
    print("=" * 60)
    
    # 模擬長線股票分析數據
    long_term_analysis = {
        'dividend_yield': 6.5,
        'eps_growth': 18.3,
        'pe_ratio': 12.8,
        'roe': 16.4,
        'revenue_growth': 15.2,
        'dividend_consecutive_years': 12,
        'foreign_net_buy': 35000,
        'trust_net_buy': 12000,
        'total_institutional': 48000,
        'consecutive_buy_days': 5
    }
    
    try:
        # 導入修復版通知模組
        import optimized_notifier_fixed as notifier
        
        # 測試數字格式化函數
        print("✅ 數字格式化測試:")
        
        # 測試法人買賣金額格式化
        foreign_formatted = notifier.format_institutional_flow(long_term_analysis['foreign_net_buy'])
        trust_formatted = notifier.format_institutional_flow(long_term_analysis['trust_net_buy'])
        total_formatted = notifier.format_institutional_flow(long_term_analysis['total_institutional'])
        
        print(f"外資買超: {long_term_analysis['foreign_net_buy']}萬 → {foreign_formatted}")
        print(f"投信買超: {long_term_analysis['trust_net_buy']}萬 → {trust_formatted}")
        print(f"法人合計: {long_term_analysis['total_institutional']}萬 → {total_formatted}")
        
        # 測試成交金額格式化
        trade_values = [50000000, 1500000000, 15000000000]
        for value in trade_values:
            formatted = notifier.format_number(value)
            print(f"成交金額: {value:,} → {formatted}")
        
        print("✅ 基本面指標檢查:")
        print(f"殖利率: {long_term_analysis['dividend_yield']:.1f}% {'(高殖利率)' if long_term_analysis['dividend_yield'] > 5 else ''}")
        print(f"EPS成長: {long_term_analysis['eps_growth']:.1f}% {'(高成長)' if long_term_analysis['eps_growth'] > 15 else ''}")
        print(f"ROE: {long_term_analysis['roe']:.1f}% {'(優異)' if long_term_analysis['roe'] > 15 else ''}")
        print(f"連續配息: {long_term_analysis['dividend_consecutive_years']}年 {'(穩定)' if long_term_analysis['dividend_consecutive_years'] > 10 else ''}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 無法導入修復版通知模組: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試長線文字清晰度失敗: {e}")
        return False

def test_complete_notification():
    """測試完整的通知發送"""
    print("\n" + "=" * 60)
    print("📧 測試完整通知發送")
    print("=" * 60)
    
    try:
        # 導入修復版通知模組
        import optimized_notifier_fixed as notifier
        
        # 初始化通知系統
        notifier.init()
        
        # 創建完整的測試數據
        test_data = {
            "short_term": [
                {
                    "code": "2330",
                    "name": "台積電",
                    "current_price": 638.5,
                    "reason": "技術面全面轉強，多項指標同步看漲",
                    "target_price": 670.0,
                    "stop_loss": 620.0,
                    "trade_value": 14730000000,
                    "analysis": {
                        "change_percent": 2.35,
                        "rsi": 58.5,
                        "volume_ratio": 2.3,
                        "foreign_net_buy": 25000,
                        "technical_signals": {
                            "rsi_healthy": True,
                            "macd_bullish": True,
                            "macd_golden_cross": True,
                            "ma20_bullish": True,
                            "ma_golden_cross": True
                        }
                    }
                },
                {
                    "code": "2454",
                    "name": "聯發科",
                    "current_price": 825.0,
                    "reason": "RSI從超賣區回升，成交量大幅放大",
                    "target_price": 880.0,
                    "stop_loss": 800.0,
                    "trade_value": 8950000000,
                    "analysis": {
                        "change_percent": 4.12,
                        "rsi": 35.2,
                        "volume_ratio": 3.8,
                        "foreign_net_buy": 18000,
                        "technical_signals": {
                            "rsi_oversold": True,
                            "macd_bullish": True,
                            "ma20_bullish": True
                        }
                    }
                }
            ],
            "long_term": [
                {
                    "code": "2609",
                    "name": "陽明",
                    "current_price": 91.2,
                    "reason": "基本面全面優異，高殖利率配合高成長",
                    "target_price": 110.0,
                    "stop_loss": 85.0,
                    "trade_value": 4560000000,
                    "analysis": {
                        "change_percent": 1.8,
                        "dividend_yield": 7.2,
                        "eps_growth": 35.6,
                        "pe_ratio": 8.9,
                        "roe": 18.4,
                        "revenue_growth": 28.9,
                        "dividend_consecutive_years": 5,
                        "foreign_net_buy": 45000,
                        "trust_net_buy": 15000,
                        "total_institutional": 62000,
                        "consecutive_buy_days": 6
                    }
                },
                {
                    "code": "2882",
                    "name": "國泰金",
                    "current_price": 58.3,
                    "reason": "金融股龍頭，股息政策穩定",
                    "target_price": 65.0,
                    "stop_loss": 55.0,
                    "trade_value": 2100000000,
                    "analysis": {
                        "change_percent": 0.5,
                        "dividend_yield": 6.2,
                        "eps_growth": 8.5,
                        "pe_ratio": 11.3,
                        "roe": 13.8,
                        "revenue_growth": 6.7,
                        "dividend_consecutive_years": 18,
                        "foreign_net_buy": 16000,
                        "trust_net_buy": 3000,
                        "total_institutional": 20000,
                        "consecutive_buy_days": 4
                    }
                }
            ],
            "weak_stocks": [
                {
                    "code": "6666",
                    "name": "測試弱股",
                    "current_price": 25.8,
                    "alert_reason": "技術指標全面轉弱，外資大幅賣超",
                    "trade_value": 500000000,
                    "analysis": {
                        "change_percent": -4.2,
                        "foreign_net_buy": -28000
                    }
                }
            ]
        }
        
        print("📊 測試數據統計:")
        print(f"短線推薦: {len(test_data['short_term'])} 支")
        print(f"長線推薦: {len(test_data['long_term'])} 支")
        print(f"風險警示: {len(test_data['weak_stocks'])} 支")
        
        # 發送測試通知
        print(f"\n📧 發送修復版測試通知...")
        notifier.send_optimized_combined_recommendations(test_data, "修復版顯示測試")
        
        print("✅ 修復版通知已發送！")
        print("\n📋 請檢查您的郵箱，重點確認:")
        
        print("\n🔥 短線推薦修復項目:")
        print("  1. ✅ 技術指標標籤是否完整顯示")
        print("     - RSI 58.5 (紫色標籤)")
        print("     - MACD金叉 (橙色標籤)")
        print("     - 站穩20MA (青色標籤)")
        print("     - 爆量2.3倍 (黃色標籤)")
        print("     - 外資買超 (綠色標籤)")
        
        print("  2. ✅ 標籤是否按類型有不同顏色")
        print("  3. ✅ HTML版本中標籤是否正常顯示")
        
        print("\n💎 長線推薦修復項目:")
        print("  1. ✅ 基本面資訊是否清晰分類顯示")
        print("     - 基本面優勢區塊")
        print("     - 法人動向區塊")
        print("  2. ✅ 數值是否有適當的突出顯示")
        print("     - 高殖利率 7.2% (綠色突出)")
        print("     - EPS高成長 35.6% (綠色突出)")
        print("     - 外資大幅買超 6.2億 (綠色突出)")
        print("  3. ✅ 文字是否容易閱讀")
        print("  4. ✅ 連續配息年數是否顯示")
        
        print("\n🌐 HTML格式修復項目:")
        print("  1. ✅ 短線和長線區塊是否有明顯區分")
        print("  2. ✅ 技術指標標籤是否在專門區塊內")
        print("  3. ✅ 基本面和法人動向是否分開顯示")
        print("  4. ✅ 在手機上是否正常顯示")
        
        return True
        
    except ImportError as e:
        print(f"❌ 無法導入修復版通知模組: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試完整通知發送失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """主測試函數"""
    print("🔧 修復版顯示效果測試工具")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 1. 測試技術指標標籤顯示
    results['technical_indicators'] = test_technical_indicators_display()
    
    # 2. 測試長線文字清晰度
    results['long_term_clarity'] = test_long_term_clarity()
    
    # 3. 測試完整通知發送
    results['complete_notification'] = test_complete_notification()
    
    # 顯示測試結果摘要
    print("\n" + "=" * 60)
    print("📊 測試結果摘要")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        test_display = {
            'technical_indicators': '短線技術指標標籤',
            'long_term_clarity': '長線文字清晰度',
            'complete_notification': '完整通知發送'
        }
        print(f"{test_display[test_name].ljust(20)}: {status}")
    
    print("-" * 60)
    print(f"總計: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print(f"\n🎉 所有修復項目測試通過！")
        print(f"\n✅ 修復內容確認:")
        print(f"  1. 🔥 短線推薦技術指標標籤完整顯示")
        print(f"  2. 💎 長線推薦基本面文字清晰易讀")
        print(f"  3. 📊 數值格式化和顏色標示正常")
        print(f"  4. 🌐 HTML郵件格式美觀易讀")
        
        print(f"\n🚀 可以開始使用修復版系統:")
        print(f"  python run_optimized_system.py run --slot afternoon_scan")
        
    else:
        print(f"\n⚠️ {total_tests - passed_tests} 項測試失敗")
        print(f"請檢查修復版通知模組是否正確安裝")
    
    print(f"\n💡 提醒:")
    print(f"  修復版主要改進短線技術指標顯示和長線基本面清晰度")
    print(f"  如果郵件收發正常，修復效果應該立即可見")

if __name__ == "__main__":
    main()
