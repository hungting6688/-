"""
test_real_data.py - 測試實際台股數據獲取與分析
"""
import os
import sys
import argparse
import logging
from datetime import datetime

# 確保可以引入模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from twse_data_fetcher import TWStockDataFetcher
from enhanced_stock_bot import EnhancedStockBot

def setup_logging():
    """設置日誌"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_data_fetcher():
    """測試數據獲取器"""
    print("=" * 60)
    print("測試台股數據獲取器")
    print("=" * 60)
    
    fetcher = TWStockDataFetcher()
    
    # 測試獲取上市股票數據
    print("\n1. 測試獲取上市股票數據...")
    twse_stocks = fetcher.fetch_twse_daily_data()
    print(f"獲取上市股票數量: {len(twse_stocks)}")
    
    if twse_stocks:
        print("前5支上市股票:")
        for i, stock in enumerate(twse_stocks[:5]):
            print(f"  {i+1}. {stock['code']} {stock['name']} - 收盤價: {stock['close']}, 成交金額: {stock['trade_value']:,.0f}")
    
    # 測試獲取上櫃股票數據
    print("\n2. 測試獲取上櫃股票數據...")
    tpex_stocks = fetcher.fetch_tpex_daily_data()
    print(f"獲取上櫃股票數量: {len(tpex_stocks)}")
    
    if tpex_stocks:
        print("前5支上櫃股票:")
        for i, stock in enumerate(tpex_stocks[:5]):
            print(f"  {i+1}. {stock['code']} {stock['name']} - 收盤價: {stock['close']}, 成交金額: {stock['trade_value']:,.0f}")
    
    # 測試按成交金額排序
    print("\n3. 測試按成交金額排序...")
    all_stocks = fetcher.get_all_stocks_by_volume()
    print(f"總股票數量（按成交金額排序）: {len(all_stocks)}")
    
    if all_stocks:
        print("成交金額前10名:")
        for i, stock in enumerate(all_stocks[:10]):
            print(f"  {i+1}. {stock['code']} {stock['name']} ({stock['market']}) - 成交金額: {stock['trade_value']:,.0f}")
    
    return len(all_stocks) > 0

def test_time_slot_selection():
    """測試不同時段的股票選擇"""
    print("\n" + "=" * 60)
    print("測試不同時段股票選擇")
    print("=" * 60)
    
    fetcher = TWStockDataFetcher()
    
    time_slots = ['morning_scan', 'mid_morning_scan', 'mid_day_scan', 'afternoon_scan']
    expected_counts = [100, 150, 150, 450]
    
    for i, slot in enumerate(time_slots):
        print(f"\n{i+1}. 測試 {slot}...")
        stocks = fetcher.get_stocks_by_time_slot(slot)
        expected = expected_counts[i]
        actual = len(stocks)
        
        print(f"預期股票數量: {expected}")
        print(f"實際股票數量: {actual}")
        
        if stocks:
            print(f"前3支股票:")
            for j, stock in enumerate(stocks[:3]):
                print(f"  {j+1}. {stock['code']} {stock['name']} - 成交金額: {stock['trade_value']:,.0f}")
        
        # 檢查是否符合預期
        status = "✅ 通過" if actual > 0 else "❌ 失敗"
        print(f"測試結果: {status}")

def test_stock_analysis():
    """測試股票分析功能"""
    print("\n" + "=" * 60)
    print("測試股票分析功能")
    print("=" * 60)
    
    bot = EnhancedStockBot()
    
    # 獲取一些股票進行測試
    print("\n1. 獲取測試股票...")
    stocks = bot.get_stocks_for_analysis('morning_scan')
    
    if not stocks:
        print("❌ 無法獲取股票數據進行測試")
        return False
    
    print(f"獲取了 {len(stocks)} 支股票進行測試")
    
    # 選擇前3支股票進行分析
    test_stocks = stocks[:3]
    
    print("\n2. 進行股票分析...")
    analyses = []
    
    for i, stock in enumerate(test_stocks):
        print(f"\n分析股票 {i+1}: {stock['code']} {stock['name']}")
        
        try:
            analysis = bot.analyze_stock_with_real_data(stock, 'mixed')
            analyses.append(analysis)
            
            print(f"  當前價格: {analysis['current_price']}")
            print(f"  加權得分: {analysis['weighted_score']}")
            print(f"  趨勢判斷: {analysis['trend']}")
            print(f"  建議: {analysis['suggestion']}")
            print(f"  數據品質: {analysis['data_quality']}")
            
        except Exception as e:
            print(f"  ❌ 分析失敗: {e}")
    
    # 測試推薦生成
    print("\n3. 生成股票推薦...")
    if analyses:
        recommendations = bot.generate_recommendations(analyses, 'morning_scan')
        
        print(f"短線推薦: {len(recommendations['short_term'])} 支")
        for stock in recommendations['short_term']:
            print(f"  - {stock['code']} {stock['name']}: {stock['reason']}")
        
        print(f"長線推薦: {len(recommendations['long_term'])} 支")
        for stock in recommendations['long_term']:
            print(f"  - {stock['code']} {stock['name']}: {stock['reason']}")
        
        print(f"極弱股警示: {len(recommendations['weak_stocks'])} 支")
        for stock in recommendations['weak_stocks']:
            print(f"  - {stock['code']} {stock['name']}: {stock['alert_reason']}")
        
        return True
    else:
        print("❌ 無分析結果可生成推薦")
        return False

def test_single_stock_analysis():
    """測試單支股票深度分析"""
    print("\n" + "=" * 60)
    print("測試單支股票深度分析")
    print("=" * 60)
    
    # 測試台積電
    stock_code = "2330"
    print(f"測試股票: {stock_code} (台積電)")
    
    fetcher = TWStockDataFetcher()
    
    try:
        # 獲取歷史數據
        print(f"\n1. 獲取 {stock_code} 歷史數據...")
        df = fetcher.get_stock_historical_data(stock_code, days=30)
        
        if df.empty:
            print(f"❌ 無法獲取 {stock_code} 的歷史數據")
            return False
        
        print(f"成功獲取 {len(df)} 天的歷史數據")
        print("最近5天數據:")
        print(df[['date', 'close', 'volume']].tail().to_string(index=False))
        
        # 獲取當日數據
        print(f"\n2. 獲取 {stock_code} 當日數據...")
        all_stocks = fetcher.get_all_stocks_by_volume()
        target_stock = None
        
        for stock in all_stocks:
            if stock['code'] == stock_code:
                target_stock = stock
                break
        
        if target_stock:
            print(f"找到 {stock_code}:")
            print(f"  名稱: {target_stock['name']}")
            print(f"  收盤價: {target_stock['close']}")
            print(f"  漲跌幅: {target_stock['change_percent']:.2f}%")
            print(f"  成交量: {target_stock['volume']:,}")
            print(f"  成交金額: {target_stock['trade_value']:,.0f}")
            
            # 進行完整分析
            print(f"\n3. 進行完整技術分析...")
            bot = EnhancedStockBot()
            analysis = bot.analyze_stock_with_real_data(target_stock, 'comprehensive')
            
            print(f"分析結果:")
            print(f"  加權得分: {analysis['weighted_score']}")
            print(f"  趨勢判斷: {analysis['trend']}")
            print(f"  操作建議: {analysis['suggestion']}")
            print(f"  目標價: {analysis['target_price']}")
            print(f"  止損價: {analysis['stop_loss']}")
            print(f"  RSI: {analysis['rsi']}")
            print(f"  MACD: {analysis['macd']}")
            
            return True
        else:
            print(f"❌ 在今日股票列表中未找到 {stock_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='實際台股數據測試工具')
    parser.add_argument('--test', '-t', 
                      choices=['all', 'data', 'timeslot', 'analysis', 'single'], 
                      default='all', help='指定要運行的測試')
    args = parser.parse_args()
    
    setup_logging()
    
    print("實際台股數據測試工具")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    try:
        if args.test in ['all', 'data']:
            results['data'] = test_data_fetcher()
        
        if args.test in ['all', 'timeslot']:
            test_time_slot_selection()
            results['timeslot'] = True
        
        if args.test in ['all', 'analysis']:
            results['analysis'] = test_stock_analysis()
        
        if args.test in ['all', 'single']:
            results['single'] = test_single_stock_analysis()
        
        # 顯示測試結果摘要
        print("\n" + "=" * 60)
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
            print("\n🎉 所有測試都已通過，實際數據系統運作正常！")
            print("\n後續步驟:")
            print("1. 可以開始使用 enhanced_stock_bot.py 進行實際分析")
            print("2. 執行 'python enhanced_stock_bot.py' 啟動自動化分析")
            print("3. 或使用 'python run.py analyze morning_scan' 進行單次分析")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} 項測試失敗")
            print("請檢查網路連線和台灣證券交易所API的可用性")
            
    except Exception as e:
        print(f"\n❌ 測試過程中發生未預期的錯誤: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
