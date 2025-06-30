#!/usr/bin/env python3
"""
quick_fix.py - GitHub Actions aiohttp 問題一鍵修復腳本
自動備份原檔案並應用修復方案
"""

import os
import shutil
import sys
from datetime import datetime

def create_backup_dir():
    """創建備份目錄"""
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def backup_file(file_path, backup_dir):
    """備份單個檔案"""
    if os.path.exists(file_path):
        backup_path = os.path.join(backup_dir, os.path.basename(file_path))
        shutil.copy2(file_path, backup_path)
        print(f"✅ 備份: {file_path} -> {backup_path}")
        return True
    else:
        print(f"⚠️ 檔案不存在，跳過備份: {file_path}")
        return False

def write_fixed_requirements():
    """寫入修復版 requirements.txt"""
    content = """# 台股分析機器人依賴套件 - GitHub Actions 兼容版
# 完全移除 aiohttp 依賴，使用純同步模式

# ==================== 核心數據處理 ====================
pandas>=1.5.3,<2.1.0
numpy>=1.24.2,<1.26.0

# ==================== HTTP 請求套件 ====================
requests>=2.28.2,<2.32.0
urllib3>=1.26.0,<2.1.0

# ==================== 排程和基礎工具 ====================
schedule>=1.1.0,<1.3.0
python-dotenv>=1.0.0,<1.1.0
pytz>=2023.3,<2024.0

# ==================== 郵件和通知 ====================
email-validator>=2.0.0,<2.2.0

# ==================== 網頁解析 ====================
beautifulsoup4>=4.12.0,<4.13.0
lxml>=4.9.0,<5.0.0

# ==================== 資料視覺化（可選）====================
matplotlib>=3.7.1,<3.9.0

# ==================== 基本工具 ====================
setuptools>=65.6.3
python-dateutil>=2.8.2

# ==================== 測試套件（開發用）====================
pytest>=7.3.0
pytest-mock>=3.10.0

# ==================== 注意事項 ====================
# 1. 完全移除 aiohttp 相關依賴
# 2. 使用純同步 requests 進行網路請求
# 3. 所有功能保持完整，僅性能略微降低
# 4. GitHub Actions 環境完全兼容
# 5. 版本鎖定確保穩定性"""
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 已寫入修復版 requirements.txt")

def write_enhanced_stock_bot_wrapper():
    """寫入 enhanced_stock_bot.py 包裝器"""
    content = '''#!/usr/bin/env python3
"""
enhanced_stock_bot.py - 兼容包裝器
重定向所有調用到 GitHub Actions 兼容版分析器
"""

import sys
import os
from datetime import datetime

def main():
    """主函數 - 重定向到兼容版分析器"""
    
    print("🔄 enhanced_stock_bot.py 兼容包裝器啟動")
    print("📍 重定向到 GitHub Actions 兼容版分析器")
    print(f"⚡ 特色：無 aiohttp 依賴，純同步，100% 穩定")
    print()
    
    # 檢查兼容版分析器是否存在
    if not os.path.exists('github_actions_compatible_bot.py'):
        print("❌ 找不到 github_actions_compatible_bot.py")
        print("請確保 github_actions_compatible_bot.py 文件存在")
        sys.exit(1)
    
    # 獲取命令行參數
    if len(sys.argv) < 2:
        print("❌ 缺少時段參數")
        print("使用方式: python enhanced_stock_bot.py <time_slot>")
        sys.exit(1)
    
    time_slot = sys.argv[1]
    print(f"🎯 分析時段: {time_slot}")
    
    # 執行兼容版分析器
    try:
        import subprocess
        cmd = [sys.executable, 'github_actions_compatible_bot.py', time_slot]
        if len(sys.argv) > 2:
            cmd.extend(sys.argv[2:])
        
        result = subprocess.run(cmd, check=True)
        print(f"✅ 分析執行完成")
        sys.exit(result.returncode)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 兼容版分析器執行失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open('enhanced_stock_bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 已寫入 enhanced_stock_bot.py 包裝器")

def check_github_actions_compatible_bot():
    """檢查是否有兼容版分析器"""
    if not os.path.exists('github_actions_compatible_bot.py'):
        print("❌ 缺少 github_actions_compatible_bot.py")
        print("請手動創建此檔案，內容請參考修復說明文檔")
        return False
    else:
        print("✅ github_actions_compatible_bot.py 存在")
        return True

def create_directories():
    """創建必要目錄"""
    dirs = ['logs', 'data', 'data/analysis_results', 'data/cache']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ 創建目錄: {dir_path}")

def main():
    """主修復流程"""
    print("🔧 GitHub Actions aiohttp 問題一鍵修復腳本")
    print("=" * 60)
    print("本腳本將：")
    print("1. 備份現有檔案")
    print("2. 應用修復版 requirements.txt")
    print("3. 更新 enhanced_stock_bot.py 為兼容包裝器")
    print("4. 檢查必要檔案")
    print("5. 創建必要目錄")
    print()
    
    # 確認執行
    confirm = input("確定要執行修復嗎？(y/N): ")
    if confirm.lower() not in ['y', 'yes']:
        print("❌ 修復已取消")
        return
    
    print("\n🚀 開始執行修復...")
    
    # 1. 創建備份
    print("\n📦 步驟 1: 創建備份")
    backup_dir = create_backup_dir()
    
    # 備份重要檔案
    files_to_backup = [
        'requirements.txt',
        'enhanced_stock_bot.py',
        '.github/workflows/stock-bot.yml'
    ]
    
    backup_count = 0
    for file_path in files_to_backup:
        if backup_file(file_path, backup_dir):
            backup_count += 1
    
    print(f"📦 備份完成: {backup_count} 個檔案已備份到 {backup_dir}")
    
    # 2. 應用修復
    print("\n🔧 步驟 2: 應用修復")
    
    # 修復 requirements.txt
    write_fixed_requirements()
    
    # 修復 enhanced_stock_bot.py
    write_enhanced_stock_bot_wrapper()
    
    # 3. 檢查必要檔案
    print("\n🔍 步驟 3: 檢查必要檔案")
    
    # 檢查兼容版分析器
    has_compatible_bot = check_github_actions_compatible_bot()
    
    # 檢查通知系統
    if os.path.exists('notifier.py'):
        print("✅ notifier.py 存在")
    else:
        print("⚠️ notifier.py 不存在，通知功能可能受限")
    
    # 4. 創建目錄
    print("\n📁 步驟 4: 創建必要目錄")
    create_directories()
    
    # 5. 生成摘要
    print("\n📋 修復摘要")
    print("=" * 40)
    print(f"✅ 備份目錄: {backup_dir}")
    print("✅ requirements.txt: 已修復（移除 aiohttp）")
    print("✅ enhanced_stock_bot.py: 已更新為兼容包裝器")
    
    if has_compatible_bot:
        print("✅ github_actions_compatible_bot.py: 存在")
    else:
        print("❌ github_actions_compatible_bot.py: 缺少（需手動創建）")
    
    print("✅ 必要目錄: 已創建")
    
    # 6. 後續步驟提示
    print("\n🚀 後續步驟")
    print("=" * 40)
    
    if not has_compatible_bot:
        print("1. ❗ 手動創建 github_actions_compatible_bot.py")
        print("   （請參考修復說明文檔中的完整內容）")
    
    print("2. 📝 檢查並更新 .github/workflows/stock-bot.yml")
    print("   （使用修復說明文檔中的修復版內容）")
    
    print("3. 🧪 本地測試修復效果：")
    print("   python enhanced_stock_bot.py afternoon_scan")
    
    print("4. 📤 提交變更到 Git：")
    print("   git add .")
    print("   git commit -m '🔧 修復 GitHub Actions aiohttp 依賴問題'")
    print("   git push")
    
    print("5. ✅ 在 GitHub Actions 中測試：")
    print("   手動觸發工作流程並選擇 test_notification")
    
    print("\n🎉 修復腳本執行完成！")
    print("💡 完整修復說明請參考 GITHUB_ACTIONS_FIX_README.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 修復已被用戶中斷")
    except Exception as e:
        print(f"\n❌ 修復過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
