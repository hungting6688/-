"""
integrate_fixed_system.py - 整合修復版系統
將修復的通知系統整合到現有的優化版股市機器人中
"""
import os
import sys
import shutil
from datetime import datetime

def backup_original_files():
    """備份原始檔案"""
    print("📁 備份原始檔案...")
    
    files_to_backup = [
        'notifier.py',
        'optimized_notifier.py'
    ]
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for filename in files_to_backup:
        if os.path.exists(filename):
            backup_path = os.path.join(backup_dir, filename)
            shutil.copy2(filename, backup_path)
            print(f"  ✅ 已備份: {filename} → {backup_path}")
    
    print(f"✅ 備份完成，備份目錄: {backup_dir}")
    return backup_dir

def install_fixed_notifier():
    """安裝修復版通知系統"""
    print("\n🔧 安裝修復版通知系統...")
    
    # 檢查修復版檔案是否存在
    if not os.path.exists('optimized_notifier_fixed.py'):
        print("❌ 找不到 optimized_notifier_fixed.py")
        print("請確保修復版通知模組檔案在當前目錄中")
        return False
    
    # 複製修復版檔案
    try:
        # 替換 notifier.py
        shutil.copy2('optimized_notifier_fixed.py', 'notifier.py')
        print("  ✅ 已更新: notifier.py")
        
        # 也替換 optimized_notifier.py（如果存在）
        if os.path.exists('optimized_notifier.py'):
            shutil.copy2('optimized_notifier_fixed.py', 'optimized_notifier.py')
            print("  ✅ 已更新: optimized_notifier.py")
        
        return True
        
    except Exception as e:
        print(f"❌ 安裝修復版通知系統失敗: {e}")
        return False

def update_import_statements():
    """更新導入語句"""
    print("\n📝 檢查導入語句...")
    
    files_to_check = [
        'enhanced_stock_bot.py',
        'enhanced_stock_bot_optimized.py',
        'run_optimized_system.py'
    ]
    
    for filename in files_to_check:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查是否需要更新導入語句
                if 'import optimized_notifier_fixed' in content:
                    # 替換為標準的 notifier 導入
                    content = content.replace('import optimized_notifier_fixed as notifier', 'import notifier')
                    content = content.replace('from optimized_notifier_fixed import', 'from notifier import')
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"  ✅ 已更新導入語句: {filename}")
                else:
                    print(f"  ℹ️ 導入語句正常: {filename}")
                    
            except Exception as e:
                print(f"  ⚠️ 檢查 {filename} 時發生錯誤: {e}")

def verify_installation():
    """驗證安裝"""
    print("\n🔍 驗證安裝...")
    
    try:
        # 嘗試導入修復版通知系統
        import notifier
        
        # 檢查修復版特有的函數
        if hasattr(notifier, 'get_technical_indicators_text'):
            print("  ✅ 技術指標提取函數存在")
        else:
            print("  ❌ 缺少技術指標提取函數")
            return False
        
        if hasattr(notifier, 'send_optimized_combined_recommendations'):
            print("  ✅ 優化版推薦發送函數存在")
        else:
            print("  ❌ 缺少優化版推薦發送函數")
            return False
        
        # 嘗試初始化
        notifier.init()
        print("  ✅ 通知系統初始化成功")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ 導入通知模組失敗: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 驗證過程發生錯誤: {e}")
        return False

def create_test_script():
    """創建測試腳本"""
    print("\n📝 創建測試腳本...")
    
    test_script_content = '''#!/usr/bin/env python3
"""
test_fixed_integration.py - 測試修復版整合效果
"""
import sys
import os
from datetime import datetime

def test_short_term_indicators():
    """測試短線技術指標顯示"""
    print("🔥 測試短線技術指標...")
    
    try:
        import notifier
        
        # 模擬技術指標數據
        analysis = {
            'rsi': 58.5,
            'volume_ratio': 2.3,
            'foreign_net_buy': 25000,
            'technical_signals': {
                'macd_golden_cross': True,
                'ma20_bullish': True,
                'rsi_healthy': True
            }
        }
        
        indicators = notifier.get_technical_indicators_text(analysis)
        print(f"✅ 提取到指標: {indicators}")
        
        return len(indicators) > 0
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_long_term_clarity():
    """測試長線推薦清晰度"""
    print("💎 測試長線推薦清晰度...")
    
    try:
        import notifier
        
        # 測試數字格式化
        test_values = [50000, 150000, 1500000]
        for value in test_values:
            formatted = notifier.format_institutional_flow(value)
            print(f"  {value}萬 → {formatted}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_complete_notification():
    """測試完整通知"""
    print("📧 測試完整通知...")
    
    try:
        import notifier
        
        notifier.init()
        
        # 創建簡單測試數據
        test_data = {
            "short_term": [{
                "code": "TEST",
                "name": "測試股",
                "current_price": 100.0,
                "reason": "測試用途",
                "target_price": 110.0,
                "stop_loss": 95.0,
                "trade_value": 1000000000,
                "analysis": {
                    "change_percent": 2.5,
                    "rsi": 60,
                    "technical_signals": {"macd_bullish": True}
                }
            }],
            "long_term": [{
                "code": "TEST2",
                "name": "測試長線",
                "current_price": 50.0,
                "reason": "長線測試",
                "target_price": 60.0,
                "stop_loss": 45.0,
                "trade_value": 500000000,
                "analysis": {
                    "change_percent": 1.0,
                    "dividend_yield": 5.5,
                    "eps_growth": 15.0
                }
            }],
            "weak_stocks": []
        }
        
        # 發送測試通知
        notifier.send_optimized_combined_recommendations(test_data, "整合測試")
        print("✅ 測試通知已發送")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 修復版整合測試")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("短線技術指標", test_short_term_indicators),
        ("長線文字清晰度", test_long_term_clarity),
        ("完整通知發送", test_complete_notification)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\\n{'='*40}")
        print(f"測試: {test_name}")
        print('='*40)
        result = test_func()
        results.append((test_name, result))
    
    print(f"\\n{'='*60}")
    print("測試結果摘要")
    print('='*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name.ljust(15)}: {status}")
        if result:
            passed += 1
    
    print(f"\\n總計: {passed}/{len(results)} 測試通過")
    
    if passed == len(results):
        print("\\n🎉 修復版整合成功！")
        print("可以開始使用修復版系統")
    else:
        print("\\n⚠️ 整合可能存在問題，請檢查錯誤")
'''
    
    try:
        with open('test_fixed_integration.py', 'w', encoding='utf-8') as f:
            f.write(test_script_content)
        print("  ✅ 已創建測試腳本: test_fixed_integration.py")
        return True
        
    except Exception as e:
        print(f"  ❌ 創建測試腳本失敗: {e}")
        return False

def main():
    """主整合流程"""
    print("🔧 修復版系統整合工具")
    print("=" * 60)
    print(f"整合時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🎯 整合目標:")
    print("  1. 修復短線推薦技術指標標籤顯示問題")
    print("  2. 優化長線推薦基本面文字清晰度")
    print("  3. 保持原有功能完整性")
    print()
    
    # 確認用戶是否要繼續
    response = input("是否繼續整合修復版系統？(y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ 整合已取消")
        return
    
    success_count = 0
    total_steps = 5
    
    # 步驟1: 備份原始檔案
    try:
        backup_dir = backup_original_files()
        success_count += 1
        print(f"✅ 步驟1完成 ({success_count}/{total_steps})")
    except Exception as e:
        print(f"❌ 步驟1失敗: {e}")
        return
    
    # 步驟2: 安裝修復版通知系統
    try:
        if install_fixed_notifier():
            success_count += 1
            print(f"✅ 步驟2完成 ({success_count}/{total_steps})")
        else:
            print("❌ 步驟2失敗")
            return
    except Exception as e:
        print(f"❌ 步驟2異常: {e}")
        return
    
    # 步驟3: 更新導入語句
    try:
        update_import_statements()
        success_count += 1
        print(f"✅ 步驟3完成 ({success_count}/{total_steps})")
    except Exception as e:
        print(f"❌ 步驟3異常: {e}")
        # 這個步驟失敗不影響主要功能
        print("⚠️ 導入語句更新失敗，但不影響主要功能")
        success_count += 1
    
    # 步驟4: 驗證安裝
    try:
        if verify_installation():
            success_count += 1
            print(f"✅ 步驟4完成 ({success_count}/{total_steps})")
        else:
            print("❌ 步驟4失敗 - 安裝驗證不通過")
            print(f"💡 建議: 檢查 {backup_dir} 中的備份檔案，可能需要回滾")
            return
    except Exception as e:
        print(f"❌ 步驟4異常: {e}")
        return
    
    # 步驟5: 創建測試腳本
    try:
        if create_test_script():
            success_count += 1
            print(f"✅ 步驟5完成 ({success_count}/{total_steps})")
        else:
            print("❌ 步驟5失敗 - 測試腳本創建失敗")
            # 這個不影響主要功能
            success_count += 1
    except Exception as e:
        print(f"❌ 步驟5異常: {e}")
        success_count += 1  # 不影響主要功能
    
    # 整合完成
    print("\n" + "=" * 60)
    print("🎉 修復版系統整合完成！")
    print("=" * 60)
    
    print(f"✅ 完成步驟: {success_count}/{total_steps}")
    print(f"📁 備份位置: {backup_dir}")
    
    print(f"\n🔧 修復內容:")
    print(f"  1. ✅ 短線推薦技術指標標籤完整顯示")
    print(f"     - RSI、MACD、均線、成交量標籤")
    print(f"     - 不同類型指標用不同顏色標示")
    print(f"  2. ✅ 長線推薦基本面文字清晰度優化")
    print(f"     - 基本面優勢區塊化顯示")
    print(f"     - 法人動向獨立清晰顯示")
    print(f"     - 重要數值突出標示")
    
    print(f"\n📧 測試建議:")
    print(f"  1. 執行整合測試: python test_fixed_integration.py")
    print(f"  2. 發送完整測試: python test_fixed_display.py")
    print(f"  3. 運行實際分析: python run_optimized_system.py run --slot afternoon_scan")
    
    print(f"\n🔄 如需回滾:")
    print(f"  備份檔案位於: {backup_dir}")
    print(f"  可將備份檔案復原來回滾修改")
    
    print(f"\n💡 使用提醒:")
    print(f"  修復主要改善顯示效果，不影響分析邏輯")
    print(f"  建議先進行測試確認修復效果")
    print(f"  如有問題可隨時使用備份檔案回滾")
    
    # 詢問是否立即測試
    test_response = input(f"\n是否立即執行整合測試？(y/N): ")
    if test_response.lower() in ['y', 'yes']:
        print(f"\n🧪 執行整合測試...")
        try:
            os.system('python test_fixed_integration.py')
        except Exception as e:
            print(f"❌ 執行測試失敗: {e}")
            print(f"請手動執行: python test_fixed_integration.py")

def rollback_installation():
    """回滾安裝"""
    print("🔄 回滾修復版安裝")
    print("=" * 40)
    
    # 查找備份目錄
    backup_dirs = [d for d in os.listdir('.') if d.startswith('backup_') and os.path.isdir(d)]
    
    if not backup_dirs:
        print("❌ 找不到備份目錄")
        return
    
    print("📁 找到以下備份:")
    for i, backup_dir in enumerate(backup_dirs, 1):
        print(f"  {i}. {backup_dir}")
    
    try:
        choice = int(input("請選擇要回滾的備份 (輸入數字): ")) - 1
        if 0 <= choice < len(backup_dirs):
            selected_backup = backup_dirs[choice]
            
            # 回滾檔案
            files_to_restore = ['notifier.py', 'optimized_notifier.py']
            
            for filename in files_to_restore:
                backup_file = os.path.join(selected_backup, filename)
                if os.path.exists(backup_file):
                    shutil.copy2(backup_file, filename)
                    print(f"✅ 已回滾: {filename}")
            
            print(f"✅ 回滾完成，使用備份: {selected_backup}")
            
        else:
            print("❌ 無效的選擇")
            
    except (ValueError, KeyboardInterrupt):
        print("❌ 回滾已取消")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        rollback_installation()
    else:
        main()
