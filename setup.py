"""
setup.py - 股市機器人安裝腳本
用於建立安裝環境、依賴套件及目錄結構
"""
import os
import sys
import json
import shutil
from setuptools import setup, find_packages

# 基本資訊
VERSION = '0.1.0'
DESCRIPTION = '台股分析機器人 - 自動化股市分析與通知'
LONG_DESCRIPTION = '自動化股票技術分析系統，提供短線、長線推薦及弱勢股票警示，並通過電子郵件發送分析報告'

# 建立必要目錄
def create_directories():
    """建立必要的目錄結構"""
    print("建立目錄結構...")
    
    # 基本目錄
    directories = [
        'logs',
        'logs/notifications',
        'logs/undelivered',
        'cache',
        'data',
        'data/analysis_results'
    ]
    
    # 建立目錄
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 已建立目錄: {directory}")
    
    return True

# 建立樣本股票列表
def create_sample_stock_list():
    """建立樣本股票列表"""
    print("建立樣本股票列表...")
    
    # 樣本資料
    sample_stocks = [
        {"code": "2330", "name": "台積電"},
        {"code": "2317", "name": "鴻海"},
        {"code": "2454", "name": "聯發科"},
        {"code": "2412", "name": "中華電"},
        {"code": "2308", "name": "台達電"},
        {"code": "2303", "name": "聯電"},
        {"code": "1301", "name": "台塑"},
        {"code": "1303", "name": "南亞"},
        {"code": "2002", "name": "中鋼"},
        {"code": "2882", "name": "國泰金"}
    ]
    
    # 建立檔案
    filepath = os.path.join('data', 'stock_list.json')
    
    # 如果已存在則不覆蓋
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sample_stocks, f, ensure_ascii=False, indent=2)
        print(f"✓ 已建立樣本股票列表: {filepath}")
    else:
        print(f"✓ 股票列表已存在，保留現有檔案: {filepath}")
    
    return True

# 建立環境變數檔案
def create_env_file():
    """建立環境變數檔案"""
    print("建立環境變數檔案...")
    
    # 檢查是否已有.env檔案
    if os.path.exists('.env'):
        print("✓ .env檔案已存在，保留現有設定")
        return True
    
    # 確認是否有.env.sample檔案
    if not os.path.exists('.env.sample'):
        print("⚠ 找不到.env.sample範例檔")
        return False
    
    # 複製樣本檔案
    shutil.copy('.env.sample', '.env')
    print("✓ 已建立.env檔案，請編輯此檔案設定您的環境變數")
    
    return True

# 安裝前準備
def prepare_installation():
    """執行安裝前準備工作"""
    print("=" * 60)
    print(" 台股分析機器人 - 安裝程序 ")
    print("=" * 60)
    print()
    
    # 建立目錄
    success_dirs = create_directories()
    
    # 建立樣本檔案
    success_stocks = create_sample_stock_list()
    
    # 建立環境變數檔案
    success_env = create_env_file()
    
    if success_dirs and success_stocks and success_env:
        print("\n✓ 安裝前準備工作完成!\n")
    else:
        print("\n⚠ 安裝前準備工作部分失敗，請檢查上方訊息\n")
    
    print("=" * 60)
    print(" 接下來將安裝必要的Python套件 ")
    print("=" * 60)
    print()

# 主要安裝設定
if 'install' in sys.argv or 'develop' in sys.argv:
    prepare_installation()

setup(
    name="taiwan_stock_bot",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author="Your Name",
    author_email="your.email@example.com",
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'requests>=2.28.0',
        'pandas>=1.5.0',
        'numpy>=1.24.0',
        'schedule>=1.1.0',
        'python-dotenv>=1.0.0',
        'pytz>=2023.3',
        'matplotlib>=3.7.0',
    ],
    keywords=['stock', 'analysis', 'notification', 'taiwan', 'investment'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)

# 安裝後指引
if 'install' in sys.argv or 'develop' in sys.argv:
    print("\n" + "=" * 60)
    print(" 安裝完成 - 接下來您需要: ")
    print("=" * 60)
    print("""
1. 編輯 .env 檔案，設定您的郵件系統：
   - 開啟 .env 檔案
   - 填入您的電子郵件地址與密碼
   - 如使用Gmail，請使用應用程式密碼

2. 測試通知系統是否正常：
   - 執行: python test_notification.py

3. 啟動股市機器人：
   - 執行: python stock_bot.py

4. 有任何問題，請參考 README.md 文件

祝您投資順利！
""")
