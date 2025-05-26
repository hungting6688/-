#!/bin/bash

echo "🔍 檢查 Python 語法..."

# 檢查主要檔案並修正已知問題
files=(
    "enhanced_stock_bot.py"
    "notifier.py"
    "twse_data_fetcher.py"
    "config.py"
)

all_passed=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "檢查 $file..."
        
        # 嘗試編譯檢查語法
        if python -m py_compile "$file" 2>/dev/null; then
            echo "✅ $file 語法正確"
        else
            echo "❌ $file 語法錯誤"
            all_passed=false
            
            # 嘗試顯示具體錯誤
            python -c "
import sys
try:
    with open('$file', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查常見問題
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if line.strip().endswith('} ^'):
            print(f'第 {i} 行可能有語法錯誤: {line.strip()}')
        elif line.count('(') != line.count(')'):
            print(f'第 {i} 行括號不匹配: {line.strip()}')
        elif line.count('{') != line.count('}'):
            print(f'第 {i} 行花括號不匹配: {line.strip()}')
            
except Exception as e:
    print(f'檢查 $file 時發生錯誤: {e}')
"
        fi
    else
        echo "⚠️ 檔案不存在: $file"
    fi
done

# 檢查其他重要檔案（如果存在）
optional_files=(
    "report_generator.py"
    "text_formatter.py"
    "stock_analyzers.py"
    "run_enhanced.py"
    "run.py"
)

for file in "${optional_files[@]}"; do
    if [ -f "$file" ]; then
        echo "檢查可選檔案 $file..."
        if python -m py_compile "$file" 2>/dev/null; then
            echo "✅ $file 語法正確"
        else
            echo "⚠️ $file 語法有問題"
        fi
    fi
done

if [ "$all_passed" = true ]; then
    echo ""
    echo "🎉 所有主要檔案語法檢查通過！"
    echo ""
    echo "📝 下一步："
    echo "1. 設定環境變數（.env 檔案）"
    echo "2. 安裝必要套件：pip install -r requirements.txt"
    echo "3. 測試通知系統：python test_notification.py"
    echo "4. 執行股票分析：python enhanced_stock_bot.py morning_scan"
    echo ""
else
    echo ""
    echo "❌ 發現語法錯誤，請修正後再執行"
    echo ""
    echo "💡 常見修正方法："
    echo "1. 檢查是否有不匹配的括號 () [] {}"
    echo "2. 檢查是否有未完成的函數定義"
    echo "3. 檢查是否有缺少的冒號 :"
    echo "4. 檢查縮進是否正確"
    echo ""
fi

echo "語法檢查完成"
