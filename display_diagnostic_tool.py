#!/usr/bin/env python3
"""
display_diagnostic_tool.py - 診斷技術指標、基本面、法人動向顯示問題
"""
import json
import sys
from typing import Dict, Any

def diagnose_analysis_data(analysis_data: Dict[str, Any], stock_code: str = "TEST"):
    """診斷分析數據結構"""
    
    print(f"🔍 診斷股票 {stock_code} 的數據結構")
    print("=" * 60)
    
    # 1. 檢查基本結構
    print("📋 1. 基本數據結構檢查:")
    essential_fields = ['code', 'name', 'current_price', 'change_percent', 'trade_value']
    
    for field in essential_fields:
        if field in analysis_data:
            value = analysis_data[field]
            print(f"  ✅ {field}: {value} ({type(value).__name__})")
        else:
            print(f"  ❌ 缺少 {field}")
    
    # 2. 檢查技術指標數據
    print(f"\n📊 2. 技術指標數據檢查:")
    
    # 檢查 technical_signals
    technical_signals = analysis_data.get('technical_signals', {})
    if technical_signals:
        print(f"  ✅ 找到 technical_signals:")
        for signal, value in technical_signals.items():
            print(f"    📈 {signal}: {value}")
    else:
        print(f"  ❌ 未找到 technical_signals")
    
    # 檢查具體技術指標數值
    indicators = ['rsi', 'volume_ratio', 'macd', 'ma20', 'ma5']
    for indicator in indicators:
        if indicator in analysis_data:
            value = analysis_data[indicator]
            print(f"  ✅ {indicator}: {value}")
        else:
            print(f"  ⚠️ 未找到 {indicator}")
    
    # 3. 檢查基本面數據
    print(f"\n💎 3. 基本面數據檢查:")
    
    fundamental_fields = ['dividend_yield', 'eps_growth', 'pe_ratio', 'roe', 'revenue_growth', 'dividend_consecutive_years']
    found_fundamental = False
    
    # 檢查頂層基本面數據
    for field in fundamental_fields:
        if field in analysis_data and analysis_data[field] > 0:
            value = analysis_data[field]
            print(f"  ✅ {field}: {value}")
            found_fundamental = True
    
    # 檢查 enhanced_analysis 中的基本面數據
    enhanced_analysis = analysis_data.get('enhanced_analysis', {})
    if enhanced_analysis:
        print(f"  📊 enhanced_analysis 中的基本面數據:")
        for field in fundamental_fields:
            if field in enhanced_analysis and enhanced_analysis[field] > 0:
                value = enhanced_analysis[field]
                print(f"    ✅ {field}: {value}")
                found_fundamental = True
    
    if not found_fundamental:
        print(f"  ❌ 未找到任何基本面數據")
    
    # 4. 檢查法人動向數據
    print(f"\n🏦 4. 法人動向數據檢查:")
    
    institutional_fields = ['foreign_net_buy', 'trust_net_buy', 'dealer_net_buy', 'total_institutional', 'consecutive_buy_days']
    found_institutional = False
    
    # 檢查頂層法人數據
    for field in institutional_fields:
        if field in analysis_data:
            value = analysis_data[field]
            if abs(value) > 100:  # 只顯示有意義的數值
                print(f"  ✅ {field}: {value}")
                found_institutional = True
    
    # 檢查 enhanced_analysis 中的法人數據
    if enhanced_analysis:
        print(f"  📊 enhanced_analysis 中的法人數據:")
        for field in institutional_fields:
            if field in enhanced_analysis:
                value = enhanced_analysis[field]
                if abs(value) > 100:
                    print(f"    ✅ {field}: {value}")
                    found_institutional = True
    
    if not found_institutional:
        print(f"  ❌ 未找到任何法人動向數據")
    
    # 5. 檢查 analysis 嵌套結構
    print(f"\n🔧 5. 嵌套結構檢查:")
    
    nested_analysis = analysis_data.get('analysis', {})
    if nested_analysis:
        print(f"  ✅ 找到嵌套的 'analysis' 結構")
        print(f"  📊 嵌套 analysis 包含的字段: {list(nested_analysis.keys())}")
        
        # 檢查嵌套結構中的關鍵數據
        if 'enhanced_analysis' in nested_analysis:
            print(f"  📈 嵌套結構中有 enhanced_analysis")
        if 'technical_signals' in nested_analysis:
            print(f"  📊 嵌套結構中有 technical_signals")
    else:
        print(f"  ⚠️ 未找到嵌套的 'analysis' 結構")
    
    # 6. 生成修復建議
    print(f"\n🛠️ 6. 修復建議:")
    
    suggestions = []
    
    if not technical_signals and not any(ind in analysis_data for ind in indicators):
        suggestions.append("需要確保技術指標數據正確生成和傳遞")
    
    if not found_fundamental:
        suggestions.append("需要檢查基本面數據獲取邏輯，確保 enhanced_analysis 正確填充")
    
    if not found_institutional:
        suggestions.append("需要檢查法人數據獲取邏輯，確保 institutional 分析正確執行")
    
    if nested_analysis:
        suggestions.append("數據可能在嵌套結構中，需要更新提取邏輯")
    
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print(f"  ✅ 數據結構看起來正常，問題可能在顯示邏輯中")
    
    return {
        'has_technical': bool(technical_signals) or any(ind in analysis_data for ind in indicators),
        'has_fundamental': found_fundamental,
        'has_institutional': found_institutional,
        'has_nested': bool(nested_analysis),
        'suggestions': suggestions
    }

def test_notifier_display_logic():
    """測試通知系統的顯示邏輯"""
    
    print(f"\n🧪 測試通知系統顯示邏輯")
    print("=" * 60)
    
    # 創建完整的測試數據
    test_stock = {
        "code": "2330",
        "name": "台積電",
        "current_price": 638.5,
        "change_percent": 2.35,
        "trade_value": 14730000000,
        "rsi": 58.5,
        "volume_ratio": 2.3,
        "foreign_net_buy": 25000,
        "trust_net_buy": 8000,
        "technical_signals": {
            "macd_golden_cross": True,
            "ma20_bullish": True,
            "rsi_healthy": True
        },
        "enhanced_analysis": {
            "dividend_yield": 2.3,
            "eps_growth": 12.8,
            "pe_ratio": 18.2,
            "roe": 23.5,
            "foreign_net_buy": 25000,
            "trust_net_buy": 8000,
            "tech_score": 7.2,
            "fund_score": 6.8,
            "inst_score": 7.5
        }
    }
    
    print(f"📊 測試數據創建完成")
    
    # 測試原版提取函數（如果存在）
    try:
        # 這裡可以測試原本的函數
        print(f"\n🔧 測試顯示邏輯...")
        
        # 模擬技術指標提取
        technical_indicators = []
        
        # 從 technical_signals 提取
        signals = test_stock.get('technical_signals', {})
        if signals.get('macd_golden_cross'):
            technical_indicators.append('MACD金叉')
        if signals.get('ma20_bullish'):
            technical_indicators.append('站穩20MA')
        if signals.get('rsi_healthy'):
            technical_indicators.append('RSI健康')
        
        # 從數值提取
        rsi = test_stock.get('rsi', 0)
        if rsi > 0:
            technical_indicators.append(f'RSI{rsi:.0f}')
        
        volume_ratio = test_stock.get('volume_ratio', 0)
        if volume_ratio > 2:
            technical_indicators.append(f'爆量{volume_ratio:.1f}倍')
        
        print(f"  📈 技術指標提取結果: {technical_indicators}")
        
        # 模擬基本面提取
        enhanced = test_stock.get('enhanced_analysis', {})
        fundamental_info = []
        
        if enhanced.get('dividend_yield', 0) > 0:
            fundamental_info.append(f"殖利率{enhanced['dividend_yield']:.1f}%")
        if enhanced.get('eps_growth', 0) > 0:
            fundamental_info.append(f"EPS成長{enhanced['eps_growth']:.1f}%")
        if enhanced.get('roe', 0) > 0:
            fundamental_info.append(f"ROE{enhanced['roe']:.1f}%")
        
        print(f"  💎 基本面提取結果: {fundamental_info}")
        
        # 模擬法人動向提取
        institutional_info = []
        
        foreign_net = enhanced.get('foreign_net_buy', 0)
        if foreign_net > 10000:
            institutional_info.append(f"外資買超{foreign_net//10000:.1f}億")
        
        trust_net = enhanced.get('trust_net_buy', 0)
        if trust_net > 5000:
            institutional_info.append(f"投信買超{trust_net//10000:.1f}億")
        
        print(f"  🏦 法人動向提取結果: {institutional_info}")
        
        if technical_indicators and fundamental_info and institutional_info:
            print(f"  ✅ 所有數據提取正常")
        else:
            print(f"  ⚠️ 部分數據提取可能有問題")
            
    except Exception as e:
        print(f"  ❌ 顯示邏輯測試失敗: {e}")

def analyze_real_recommendation_data(recommendations_file: str = None):
    """分析實際的推薦數據文件"""
    
    if not recommendations_file:
        print(f"💡 使用方式: analyze_real_recommendation_data('path/to/recommendations.json')")
        return
    
    try:
        with open(recommendations_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📁 分析文件: {recommendations_file}")
        print("=" * 60)
        
        # 分析短線推薦
        short_term = data.get('short_term', [])
        if short_term:
            print(f"🔥 短線推薦數據分析 ({len(short_term)} 支):")
            for i, stock in enumerate(short_term[:2]):  # 只分析前2支
                print(f"\n  📊 股票 {i+1}: {stock.get('code', 'N/A')} {stock.get('name', 'N/A')}")
                analysis = stock.get('analysis', {})
                diagnose_analysis_data(analysis, stock.get('code', f'SHORT_{i+1}'))
        
        # 分析長線推薦
        long_term = data.get('long_term', [])
        if long_term:
            print(f"\n💎 長線推薦數據分析 ({len(long_term)} 支):")
            for i, stock in enumerate(long_term[:2]):  # 只分析前2支
                print(f"\n  📊 股票 {i+1}: {stock.get('code', 'N/A')} {stock.get('name', 'N/A')}")
                analysis = stock.get('analysis', {})
                diagnose_analysis_data(analysis, stock.get('code', f'LONG_{i+1}'))
        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {recommendations_file}")
    except json.JSONDecodeError:
        print(f"❌ JSON文件格式錯誤")
    except Exception as e:
        print(f"❌ 分析失敗: {e}")

def check_system_integration():
    """檢查系統整合狀況"""
    
    print(f"🔧 檢查系統整合狀況")
    print("=" * 60)
    
    # 檢查模組導入
    modules_to_check = [
        'enhanced_stock_bot',
        'notifier', 
        'twse_data_fetcher',
        'unified_stock_analyzer',
        'config'
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"  ✅ {module}: 可正常導入")
        except ImportError as e:
            print(f"  ❌ {module}: 導入失敗 - {e}")
        except Exception as e:
            print(f"  ⚠️ {module}: 導入時出現警告 - {e}")
    
    # 檢查資料目錄
    directories = ['data', 'logs', 'cache', 'data/results']
    for directory in directories:
        import os
        if os.path.exists(directory):
            print(f"  ✅ 目錄 {directory}: 存在")
        else:
            print(f"  ❌ 目錄 {directory}: 不存在")
    
    # 檢查環境變數
    env_vars = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECEIVER']
    for var in env_vars:
        import os
        if os.getenv(var):
            print(f"  ✅ 環境變數 {var}: 已設置")
        else:
            print(f"  ❌ 環境變數 {var}: 未設置")

def main():
    """主函數"""
    
    print("🔍 台股分析系統顯示問題診斷工具")
    print("=" * 60)
    print("本工具用於診斷技術指標、基本面、法人動向顯示問題")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'test':
            # 測試顯示邏輯
            test_notifier_display_logic()
            
        elif command == 'analyze' and len(sys.argv) > 2:
            # 分析實際數據文件
            file_path = sys.argv[2]
            analyze_real_recommendation_data(file_path)
            
        elif command == 'check':
            # 檢查系統整合
            check_system_integration()
            
        else:
            print("❌ 無效的命令")
            show_usage()
    else:
        # 預設執行完整診斷
        print("🚀 執行完整系統診斷...")
        
        # 1. 測試標準數據結構
        test_notifier_display_logic()
        
        # 2. 檢查系統整合
        print(f"\n" + "="*60)
        check_system_integration()
        
        # 3. 提供解決方案
        print(f"\n" + "="*60)
        print("💡 常見問題解決方案:")
        print("  1. 如果技術指標不顯示:")
        print("     - 檢查 enhanced_stock_bot.py 中的 technical_signals 生成邏輯")
        print("     - 確保 analyze_stock_enhanced 函數正確填充技術指標")
        print("  2. 如果基本面數據不顯示:")
        print("     - 檢查 _get_enhanced_fundamental_analysis 函數")
        print("     - 確保 enhanced_analysis 結構正確填充基本面數據")
        print("  3. 如果法人動向不顯示:")
        print("     - 檢查 _get_enhanced_institutional_analysis 函數")
        print("     - 確保法人買賣數據正確計算")
        print("  4. 使用修復版 notifier.py 替換原版")

def show_usage():
    """顯示使用說明"""
    print("使用方式:")
    print("  python display_diagnostic_tool.py              # 執行完整診斷")
    print("  python display_diagnostic_tool.py test         # 測試顯示邏輯")
    print("  python display_diagnostic_tool.py check        # 檢查系統整合")
    print("  python display_diagnostic_tool.py analyze <file>  # 分析數據文件")

if __name__ == "__main__":
    main()
