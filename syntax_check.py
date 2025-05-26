#!/usr/bin/env python3
import os
import py_compile
import sys

def check_syntax(file_path):
    """檢查文件語法"""
    try:
        py_compile.compile(file_path, doraise=True)
        print(f"✅ {file_path} 語法正確")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ {file_path} 語法錯誤:")
        print(f"   {e}")
        return False

def main():
    print("🔍 檢查 Python 語法...")
    
    files = [
        "enhanced_stock_bot.py",
        "notifier.py", 
        "twse_data_fetcher.py",
        "config.py"
    ]
    
    all_passed = True
    
    for file in files:
        if os.path.exists(file):
            if not check_syntax(file):
                all_passed = False
        else:
            print(f"⚠️ 檔案不存在: {file}")
    
    if all_passed:
        print("\n🎉 所有檔案語法檢查通過！")
    else:
        print("\n❌ 發現語法錯誤，請修正後再執行")

if __name__ == "__main__":
    main()
