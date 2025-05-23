"""
test_enhanced_system.py - 測試增強版股票分析系統
確認現價和漲跌百分比正確顯示在報告中
"""
import logging
from datetime import datetime
from report_generator import ReportGenerator
from stock_analyzer import StockAnalyzer

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_report_with_price_info():
    """測試報告是否正確顯示現價和漲跌幅"""
    
    # 創建分析器和報告生成器
    analyzer = StockAnalyzer()
    generator = ReportGenerator()
    
    # 模擬實際股票數據（包含現價和漲跌資訊）
    test_stocks = [
        {
            'code': '2609',
            'name': '陽明',
            'close': 91.2,  # 現價
            'change': 3.5,   # 漲跌金額
            'change_percent': 4.1,  # 漲跌百分比
            'volume': 50000000,
            'trade_value': 4560000000,
            'open': 87.5,
            'high': 92.0,
            'low': 87.0
        },
        {
            'code': '2615',
            'name': '萬海',
            'close': 132.8,  # 現價
            'change': 11.2,   # 漲跌金額
            'change_percent': 9.1,  # 漲跌百分比
            'volume': 30000000,
            'trade_value': 3984000000,
            'open': 122.0,
            'high': 135.0,
            'low': 121.5
        },
        {
            'code': '2368',
            'name': '金像電',
            'close': 262.5,  # 現價
            'change': 6.0,    # 漲跌金額
            'change_percent': 2.4,  # 漲跌百分比
            'volume': 15000000,
            'trade_value': 3937500000,
            'open': 257.0,
            'high': 265.0,
            'low': 256.5
        },
        {
            'code': '6191',
            'name': '精成科',
            'close': 82.5,   # 現價
            'change': -1.5,   # 漲跌金額（負值）
            'change_percent': -1.8,  # 漲跌百分比（負值）
            'volume': 8000000,
            'trade_value': 660000000,
            'open': 84.0,
            'high': 84.5,
            'low': 82.0
        },
        {
            'code': '1618',
            'name': '合機',
            'close': 47.3,   # 現價
            'change': 0,      # 平盤
            'change_percent': 0,  # 平盤
            'volume': 5000000,
            'trade_value': 236500000,
            'open': 47.3,
            'high': 47.8,
            'low': 47.0
        }
    ]
    
    # 分析股票（不使用歷史數據，僅用當日數據）
    analysis_results = []
    for stock in test_stocks:
        # 簡單分析，主要關注價格顯示
        result = {
            'code': stock['code'],
            'name': stock['name'],
            'close': stock['close'],
            'change': stock['change'],
            'change_percent': stock['change_percent'],
            'volume': stock['volume'],
            'trade_value': stock['trade_value'],
            'signals': [],
            'patterns': [],
            'indicators': {'volume_ratio': 2.0},  # 模擬成交量比率
            'score': 70
        }
        
        # 根據漲跌幅添加一些模擬的信號和形態
        if stock['change_percent'] > 5:
            result['signals'].append('強勢上漲信號')
            result['patterns'].append('成交量突破')
            result['score'] = 85
        elif stock['change_percent'] > 2:
            result['patterns'].append('突破20日均線')
            result['score'] = 75
        elif stock['change_percent'] < -2:
            result['signals'].append('弱勢信號')
            result['score'] = 40
        
        analysis_results.append(result)
    
    # 測試不同時段的報告生成
    time_slots = ['morning_scan', 'afternoon_scan']
    
    for time_slot in time_slots:
        logger.info(f"\n=== 生成 {time_slot} 報告 ===")
        
        # 生成電子郵件格式報告
        email_report = generator.generate_email_report(
            time_slot=time_slot,
            analysis_results=analysis_results,
            max_stocks=3
        )
        
        # 打印報告內容
        print(f"\n{'='*60}")
        print(f"{time_slot.upper()} 報告內容：")
        print('='*60)
        print(email_report)
        
        # 檢查報告是否包含現價和漲跌幅
        logger.info("檢查報告內容...")
        
        # 檢查是否包含現價
        for stock in test_stocks[:3]:  # 檢查前3支股票
            if f"現價: {stock['close']}" in email_report:
                logger.info(f"✓ 找到 {stock['name']} 的現價顯示")
            else:
                logger.error(f"✗ 未找到 {stock['name']} 的現價顯示")
        
        # 檢查是否包含漲跌幅
        for stock in test_stocks[:3]:
            if f"{stock['change_percent']:.1f}%" in email_report:
                logger.info(f"✓ 找到 {stock['name']} 的漲跌幅顯示")
            else:
                logger.error(f"✗ 未找到 {stock['name']} 的漲跌幅顯示")
        
        # 保存報告
        filepath = generator.save_report(email_report, time_slot)
        logger.info(f"報告已保存至: {filepath}")

def test_single_stock_display():
    """測試單支股票的顯示格式"""
    logger.info("\n=== 測試單支股票顯示格式 ===")
    
    # 測試不同漲跌情況的顯示
    test_cases = [
        {'name': '上漲股', 'close': 100.5, 'change': 5.5, 'change_percent': 5.8},
        {'name': '下跌股', 'close': 50.2, 'change': -2.3, 'change_percent': -4.4},
        {'name': '平盤股', 'close': 75.0, 'change': 0, 'change_percent': 0},
    ]
    
    for case in test_cases:
        # 格式化顯示
        change_symbol = "+" if case['change'] >= 0 else ""
        display = f"{case['name']} - 現價: {case['close']} | 漲跌: {change_symbol}{case['change_percent']}%"
        print(display)

if __name__ == "__main__":
    # 執行測試
    test_report_with_price_info()
    test_single_stock_display()
    
    print("\n測試完成！請檢查生成的報告是否包含現價和漲跌幅資訊。")
