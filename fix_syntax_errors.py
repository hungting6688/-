#!/usr/bin/env python3
"""修正語法錯誤的腳本"""
import os
import re

def fix_enhanced_stock_bot():
    """修正 enhanced_stock_bot.py 的語法錯誤"""
    file_path = 'enhanced_stock_bot.py'
    
    if not os.path.exists(file_path):
        print(f"檔案 {file_path} 不存在")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修正不完整的 elif 語句
    content = re.sub(
        r'elif trust_\s*\n',
        'elif trust_net < -1000:\n                inst_score -= 1\n',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修正 {file_path}")

def fix_notifier():
    """修正 notifier.py 的語法錯誤"""
    file_path = 'notifier.py'
    
    if not os.path.exists(file_path):
        print(f"檔案 {file_path} 不存在")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 檢查第 962 行附近
    if len(lines) > 961:
        # 如果第 962 行是單獨的 return，刪除它
        if lines[961].strip() == 'return':
            lines.pop(961)
            print("已移除第 962 行的獨立 return")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ 已修正 {file_path}")

if __name__ == "__main__":
    print("開始修正語法錯誤...")
    fix_enhanced_stock_bot()
    fix_notifier()
    print("修正完成！")
