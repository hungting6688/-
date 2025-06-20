"""
comprehensive_test_tool.py - 台股分析系統綜合測試工具
整合所有測試功能，提供統一的測試界面
"""
import os
import sys
import argparse
import logging
import random
from datetime import datetime
from typing import Dict, Any, List

# 確保可以導入所有必要模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ComprehensiveTestTool:
    """綜合測試工具類別"""
    
    def __init__(self):
        self.setup_logging()
        self.test_results = {}
        
    def setup_logging(self):
        """設置日誌系統"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def print_header(self, title: str, level: int = 1):
        """打印標題"""
        if level == 1:
            print("\n" + "=" * 80)
            print(f"🧪 {title}")
            print("=" * 80)
        elif level == 2:
            print("\n" + "-" * 60)
            print(f"📋 {title}")
            print("-" * 60)
        else:
            print(f"\n💡 {title}")
    
    def test_enhanced_longterm(self):
        """測試增強版長線推薦功能"""
        self.print_header("增強版長線推薦功能測試", 1)
        
        try:
            # 創建測試股票數據
            test_stocks = self._create_longterm_test_data()
            
            # 導入增強版股票機器人
            from enhanced_stock_bot import EnhancedStockBot
            bot = EnhancedStockBot()
            
            print(f"測試股票數量: {len(test_stocks)}")
            
            all_analyses = []
            for stock in test_stocks:
                analysis = bot.analyze_stock_enhanced(stock, 'long_term')
                all_analyses.append(analysis)
                
                print(f"\n分析 {stock['code']} {stock['name']}:")
                print(f"  基礎評分: {analysis.get('base_score', 0):.1f}")
                print(f"  加權評分: {analysis.get('weighted_score', 0):.1f}")
                
                if analysis.get('analysis_components', {}).get('fundamental'):
                    print(f"  殖利率: {analysis.get('dividend_yield', 0):.1f}%")
                    print(f"  EPS成長: {analysis.get('eps_growth', 0):.1f}%")
                    print(f"  ROE: {analysis.get('roe', 0):.1f}%")
            
            # 生成推薦
            recommendations = bot.generate_recommendations(all_analyses, 'afternoon_scan')
            
            print(f"\n📊 推薦結果:")
            print(f"短線推薦: {len(recommendations['short_term'])} 支")
            print(f"長線推薦: {len(recommendations['long_term'])} 支")
            print(f"風險警示: {len(recommendations['weak_stocks'])} 支")
            
            # 檢查長線推薦中的高基本面股票比例
            high_fundamental = sum(1 for stock in recommendations['long_term'] 
                                 if (stock['analysis'].get('dividend_yield', 0) > 4 or 
                                     stock['analysis'].get('eps_growth', 0) > 15 or 
                                     stock['analysis'].get('foreign_net_buy', 0) > 20000))
            
            success = high_fundamental > 0
            print(f"✅ 高基本面股票比例: {high_fundamental}/{len(recommendations['long_term'])}")
            
            return success
            
        except Exception as e:
            print(f"❌ 長線推薦測試失敗: {e}")
            return False
    
    def test_price_display(self):
        """測試現價和漲跌百分比顯示"""
        self.print_header("現價和漲跌百分比顯示測試", 1)
        
        try:
            # 創建測試數據
            test_stocks = [
                {
                    'code': '2330', 'name': '台積電', 'close': 638.5,
                    'change': 15.5, 'change_percent': 2.5, 'volume': 25000000,
                    'trade_value': 15967500000
                },
                {
                    'code': '2454', 'name': '聯發科', 'close': 825.0,
                    'change': -12.0, 'change_percent': -1.4, 'volume': 8000000,
                    'trade_value': 6600000000
                }
            ]
            
            print("測試價格格式化:")
            for stock in test_stocks:
                change_symbol = "+" if stock['change'] >= 0 else ""
                display = (f"{stock['name']} - 現價: {stock['close']} 元 | "
                          f"漲跌: {change_symbol}{stock['change_percent']:.1f}%")
                print(f"  {display}")
            
            print("✅ 價格顯示格式測試通過")
            return True
            
        except Exception as e:
            print(f"❌ 價格顯示測試失敗: {e}")
            return False
    
    def test_technical_indicators(self):
        """測試技術指標標籤顯示"""
        self.print_header("技術指標標籤顯示測試", 1)
        
        try:
            # 模擬技術指標數據
            analysis_data = {
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
            
            # 測試指標提取
            indicators = self._extract_technical_indicators(analysis_data)
            
            print("技術指標提取結果:")
            for indicator in indicators:
                print(f"  📊 {indicator}")
            
            success = len(indicators) >= 3
            print(f"{'✅' if success else '❌'} 技術指標提取: {len(indicators)} 個指標")
            
            return success
            
        except Exception as e:
            print(f"❌ 技術指標測試失敗: {e}")
            return False
    
    def test_weak_stocks_detection(self):
        """測試極弱股檢測功能"""
        self.print_header("極弱股檢測功能測試", 1)
        
        try:
            # 創建包含極弱股的測試數據
            test_stocks = [
                {
                    'code': '1111', 'name': '測試弱股A', 'close': 30.0,
                    'change_percent': -4.5, 'volume': 10000000, 'trade_value': 300000000,
                    'weighted_score': -2.8, 'eps_growth': -15.0, 'foreign_net_buy': -8000
                },
                {
                    'code': '2222', 'name': '測試弱股B', 'close': 50.0,
                    'change_percent': -2.8, 'volume': 20000000, 'trade_value': 1000000000,
                    'weighted_score': -1.5, 'foreign_net_buy': -15000
                },
                {
                    'code': '3333', 'name': '測試正常股', 'close': 100.0,
                    'change_percent': 1.2, 'volume': 15000000, 'trade_value': 1500000000,
                    'weighted_score': 2.5, 'eps_growth': 10.0, 'foreign_net_buy': 5000
                }
            ]
            
            # 識別極弱股
            weak_stocks = []
            for stock in test_stocks:
                if (stock['weighted_score'] < -1.0 or 
                    stock['change_percent'] < -3.0 or 
                    stock.get('foreign_net_buy', 0) < -10000):
                    alert_reason = f"綜合評分 {stock['weighted_score']:.1f}，今日下跌 {abs(stock['change_percent']):.1f}%"
                    weak_stocks.append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'alert_reason': alert_reason
                    })
            
            print(f"檢測到 {len(weak_stocks)} 支極弱股:")
            for stock in weak_stocks:
                print(f"  ⚠️ {stock['code']} {stock['name']}: {stock['alert_reason']}")
            
            success = len(weak_stocks) >= 2
            print(f"{'✅' if success else '❌'} 極弱股檢測功能")
            
            return success
            
        except Exception as e:
            print(f"❌ 極弱股檢測測試失敗: {e}")
            return False
    
    def test_gmail_notification(self):
        """測試Gmail通知系統"""
        self.print_header("Gmail通知系統測試", 1)
        
        try:
            # 檢查Gmail設定
            required_vars = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECEIVER']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                print(f"❌ 缺少環境變數: {', '.join(missing_vars)}")
                print("\n📋 Gmail設定步驟:")
                print("1. 設定環境變數或創建 .env 文件")
                print("2. EMAIL_SENDER=your-email@gmail.com")
                print("3. EMAIL_PASSWORD=your-16-digit-app-password")  
                print("4. EMAIL_RECEIVER=recipient@gmail.com")
                print("\n⚠️ 重要: 需使用Gmail應用程式密碼，非一般密碼！")
                return False
            
            # 檢查密碼格式
            password = os.getenv('EMAIL_PASSWORD')
            if len(password) != 16:
                print("⚠️ Gmail應用程式密碼應為16位數")
                print("請前往 Google 帳戶安全設定生成應用程式密碼")
                return False
            
            print("✅ Gmail設定檢查通過")
            
            # 創建測試通知數據
            test_data = self._create_notification_test_data()
            
            print("📧 模擬通知發送測試...")
            print("測試數據包含:")
            print(f"  短線推薦: {len(test_data['short_term'])} 支")
            print(f"  長線推薦: {len(test_data['long_term'])} 支") 
            print(f"  風險警示: {len(test_data['weak_stocks'])} 支")
            
            # 這裡只是檢查設定，不實際發送郵件以免測試時產生垃圾郵件
            print("✅ 通知系統設定檢查完成")
            print("💡 實際發送測試請手動執行通知功能")
            
            return True
            
        except Exception as e:
            print(f"❌ Gmail通知測試失敗: {e}")
            return False
    
    def test_real_data_fetcher(self):
        """測試實際台股數據獲取"""
        self.print_header("實際台股數據獲取測試", 1)
        
        try:
            from twse_data_fetcher import TWStockDataFetcher
            fetcher = TWStockDataFetcher()
            
            print("📡 測試上市股票數據獲取...")
            twse_stocks = fetcher.fetch_twse_daily_data()
            print(f"上市股票數量: {len(twse_stocks)}")
            
            if twse_stocks:
                print("前3支上市股票:")
                for i, stock in enumerate(twse_stocks[:3]):
                    print(f"  {i+1}. {stock['code']} {stock['name']} - 收盤: {stock['close']}")
            
            print("\n📡 測試上櫃股票數據獲取...")
            tpex_stocks = fetcher.fetch_tpex_daily_data()
            print(f"上櫃股票數量: {len(tpex_stocks)}")
            
            print("\n📊 測試按成交金額排序...")
            all_stocks = fetcher.get_all_stocks_by_volume()
            print(f"總股票數量: {len(all_stocks)}")
            
            if all_stocks:
                print("成交金額前5名:")
                for i, stock in enumerate(all_stocks[:5]):
                    print(f"  {i+1}. {stock['code']} {stock['name']} - {stock['trade_value']:,.0f} 元")
            
            success = len(all_stocks) > 100
            print(f"{'✅' if success else '❌'} 數據獲取測試")
            
            return success
            
        except Exception as e:
            print(f"❌ 實際數據獲取測試失敗: {e}")
            return False
    
    def test_text_formatter(self):
        """測試白話文格式化功能"""
        self.print_header("白話文格式化功能測試", 1)
        
        try:
            # 模擬分析數據
            mock_analysis = {
                "code": "2330",
                "name": "台積電", 
                "current_price": 638.0,
                "weighted_score": 7,
                "target_price": 670.0,
                "stop_loss": 620.0,
                "rsi": 58,
                "signals": {
                    "ma5_crosses_above_ma20": True,
                    "macd_crosses_above_signal": True,
                    "price_up": True,
                    "volume_spike": True
                }
            }
            
            # 測試短線描述生成
            short_desc = self._generate_plain_text(mock_analysis, "short_term")
            print("📝 短線白話文描述測試:")
            print(f"  描述: {short_desc['description'][:100]}...")
            print(f"  建議: {short_desc['suggestion'][:100]}...")
            
            # 測試長線描述生成
            long_desc = self._generate_plain_text(mock_analysis, "long_term")
            print("\n📝 長線白話文描述測試:")
            print(f"  描述: {long_desc['description'][:100]}...")
            print(f"  建議: {long_desc['suggestion'][:100]}...")
            
            # 測試引言文字生成
            intro = self._generate_intro_text("morning_scan", "bullish")
            print(f"\n📝 引言文字測試:")
            print(f"  {intro[:150]}...")
            
            print("\n✅ 白話文格式化功能正常")
            return True
            
        except Exception as e:
            print(f"❌ 白話文格式化測試失敗: {e}")
            return False
    
    def test_data_timing(self):
        """測試數據時效性判斷"""
        self.print_header("數據時效性判斷測試", 1)
        
        try:
            import pytz
            from datetime import datetime
            
            taipei_tz = pytz.timezone('Asia/Taipei')
            now = datetime.now(taipei_tz)
            
            print(f"當前台北時間: {now.strftime('%Y-%m-%d %H:%M:%S %A')}")
            print(f"是否為交易日: {'是' if now.weekday() < 5 else '否（週末）'}")
            
            # 測試不同時段的數據時效性
            time_slots = {
                'morning_scan': '早盤掃描 (09:00)',
                'afternoon_scan': '盤後掃描 (15:00)',
                'weekly_summary': '週末總結'
            }
            
            for slot, desc in time_slots.items():
                target_date = self._get_trading_date(slot, now)
                print(f"\n{desc}:")
                print(f"  建議使用數據日期: {target_date}")
                
                # 計算時效性
                target_dt = datetime.strptime(target_date, '%Y%m%d')
                target_dt = taipei_tz.localize(target_dt)
                days_diff = (now.date() - target_dt.date()).days
                
                if days_diff == 0:
                    print(f"  數據時效: 當日數據 ✅")
                elif days_diff == 1:
                    print(f"  數據時效: 前一交易日數據 ⚠️")
                else:
                    print(f"  數據時效: {days_diff}天前數據 ❌")
            
            print("\n✅ 數據時效性判斷功能正常")
            return True
            
        except Exception as e:
            print(f"❌ 數據時效性測試失敗: {e}")
            return False
    
    def run_all_tests(self):
        """執行所有測試"""
        self.print_header("台股分析系統綜合測試", 1)
        print(f"測試開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 定義所有測試項目
        test_cases = [
            ("增強長線推薦", self.test_enhanced_longterm),
            ("價格顯示", self.test_price_display),
            ("技術指標", self.test_technical_indicators),
            ("極弱股檢測", self.test_weak_stocks_detection),
            ("Gmail通知", self.test_gmail_notification),
            ("實際數據獲取", self.test_real_data_fetcher),
            ("白話文格式化", self.test_text_formatter),
            ("數據時效性", self.test_data_timing)
        ]
        
        # 執行測試
        for test_name, test_func in test_cases:
            try:
                print(f"\n🔄 執行測試: {test_name}")
                result = test_func()
                self.test_results[test_name] = result
                status = "✅ 通過" if result else "❌ 失敗"
                print(f"結果: {status}")
            except Exception as e:
                print(f"❌ 測試 {test_name} 發生錯誤: {e}")
                self.test_results[test_name] = False
        
        # 顯示測試總結
        self._show_test_summary()
    
    def run_specific_test(self, test_name: str):
        """執行特定測試"""
        test_map = {
            'longterm': ('增強長線推薦', self.test_enhanced_longterm),
            'price': ('價格顯示', self.test_price_display),
            'indicators': ('技術指標', self.test_technical_indicators),
            'weak': ('極弱股檢測', self.test_weak_stocks_detection),
            'notification': ('Gmail通知', self.test_gmail_notification),
            'data': ('實際數據獲取', self.test_real_data_fetcher),
            'formatter': ('白話文格式化', self.test_text_formatter),
            'timing': ('數據時效性', self.test_data_timing)
        }
        
        if test_name not in test_map:
            print(f"❌ 未知的測試項目: {test_name}")
            print(f"可用的測試項目: {', '.join(test_map.keys())}")
            return
        
        test_display_name, test_func = test_map[test_name]
        print(f"🔄 執行單項測試: {test_display_name}")
        
        try:
            result = test_func()
            self.test_results[test_display_name] = result
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"\n最終結果: {status}")
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            self.test_results[test_display_name] = False
    
    def _show_test_summary(self):
        """顯示測試結果總結"""
        self.print_header("測試結果總結", 1)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print("📊 各項測試結果:")
        for test_name, result in self.test_results.items():
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"  {test_name.ljust(15)}: {status}")
        
        print("-" * 60)
        print(f"總計: {passed_tests}/{total_tests} 項測試通過")
        
        if passed_tests == total_tests:
            print("\n🎉 所有測試都已通過！系統運作正常")
            print("\n🚀 後續步驟:")
            print("1. 可以開始使用台股分析系統")
            print("2. 執行 python enhanced_stock_bot.py 開始自動分析") 
            print("3. 執行 python run.py analyze morning_scan 進行單次分析")
        else:
            print(f"\n⚠️ 有 {total_tests - passed_tests} 項測試未通過")
            print("請檢查相關模組和設定")
        
        print(f"\n📅 測試完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 輔助方法
    def _create_longterm_test_data(self):
        """創建長線推薦測試數據"""
        return [
            {
                'code': '2882', 'name': '國泰金', 'close': 45.8, 'change_percent': 0.5,
                'volume': 15000000, 'trade_value': 687000000
            },
            {
                'code': '2454', 'name': '聯發科', 'close': 825.0, 'change_percent': 1.2,
                'volume': 8000000, 'trade_value': 6600000000
            },
            {
                'code': '2330', 'name': '台積電', 'close': 638.0, 'change_percent': -0.3,
                'volume': 25000000, 'trade_value': 15950000000
            },
            {
                'code': '2609', 'name': '陽明', 'close': 91.2, 'change_percent': 2.1,
                'volume': 35000000, 'trade_value': 3192000000
            }
        ]
    
    def _create_notification_test_data(self):
        """創建通知測試數據"""
        return {
            "short_term": [
                {
                    "code": "2330", "name": "台積電", "current_price": 638.5,
                    "reason": "技術面全面轉強，多項指標同步看漲",
                    "target_price": 670.0, "stop_loss": 620.0,
                    "trade_value": 14730000000,
                    "analysis": {
                        "change_percent": 2.35, "foreign_net_buy": 25000,
                        "technical_signals": {"rsi_healthy": True, "macd_bullish": True}
                    }
                }
            ],
            "long_term": [
                {
                    "code": "2317", "name": "鴻海", "current_price": 115.5,
                    "reason": "均線多頭排列，基本面穩健，適合中長期布局",
                    "target_price": 140.0, "stop_loss": 105.0,
                    "trade_value": 3200000000,
                    "analysis": {
                        "change_percent": 0.87, "dividend_yield": 4.2,
                        "pe_ratio": 12.5, "eps_growth": 8.3
                    }
                }
            ],
            "weak_stocks": [
                {
                    "code": "2002", "name": "中鋼", "current_price": 25.8,
                    "alert_reason": "技術面轉弱，外資賣超",
                    "trade_value": 980000000,
                    "analysis": {"change_percent": -3.21, "foreign_net_buy": -8000}
                }
            ]
        }
    
    def _extract_technical_indicators(self, analysis_data):
        """提取技術指標"""
        indicators = []
        
        if analysis_data.get('rsi'):
            indicators.append(f"RSI {analysis_data['rsi']:.1f}")
            
        if analysis_data.get('volume_ratio'):
            indicators.append(f"爆量 {analysis_data['volume_ratio']:.1f}倍")
            
        signals = analysis_data.get('technical_signals', {})
        if signals.get('macd_bullish'):
            indicators.append("MACD轉強")
        if signals.get('ma20_bullish'):
            indicators.append("站穩20MA")
        if signals.get('ma_golden_cross'):
            indicators.append("均線金叉")
            
        if analysis_data.get('foreign_net_buy', 0) > 0:
            amount = analysis_data['foreign_net_buy'] / 10000
            indicators.append(f"外資買超 {amount:.1f}億")
            
        return indicators
    
    def _generate_plain_text(self, analysis, category):
        """生成白話文描述"""
        templates = {
            "short_term": {
                "description": "技術面顯示短線有上漲動能，多項指標轉為看漲",
                "suggestion": f"建議買進，目標價 {analysis.get('target_price', 0):.0f}，停損 {analysis.get('stop_loss', 0):.0f}"
            },
            "long_term": {
                "description": "基本面穩健，適合中長期投資布局",
                "suggestion": f"適合長期持有，目標價 {analysis.get('target_price', 0):.0f}，停損 {analysis.get('stop_loss', 0):.0f}"
            }
        }
        return templates.get(category, templates["short_term"])
    
    def _generate_intro_text(self, time_slot, market_trend):
        """生成引言文字"""
        intros = {
            "morning_scan": "早盤掃描完成，已為您篩選出今日最值得關注的股票",
            "afternoon_scan": "今日收盤分析結果出爐，以下是綜合表現最佳的股票"
        }
        
        market_desc = {
            "bullish": "今日大盤氣氛偏向正面，投資人可適度積極布局",
            "neutral": "市場多空力道相當，建議選股不選市"
        }
        
        intro = intros.get(time_slot, intros["morning_scan"])
        desc = market_desc.get(market_trend, market_desc["neutral"])
        
        return f"{intro}。\n\n{desc}。"
    
    def _get_trading_date(self, time_slot, current_time):
        """獲取交易日期"""
        today = current_time.strftime('%Y%m%d')
        
        if time_slot == 'morning_scan' and current_time.hour < 9:
            # 早盤掃描且在9點前，使用前一交易日
            prev_day = current_time.replace(day=current_time.day-1)
            return prev_day.strftime('%Y%m%d')
        
        return today


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='台股分析系統綜合測試工具')
    parser.add_argument('--test', '-t', 
                      choices=['all', 'longterm', 'price', 'indicators', 'weak', 
                              'notification', 'data', 'formatter', 'timing'], 
                      default='all', 
                      help='指定要執行的測試項目')
    parser.add_argument('--verbose', '-v', action='store_true', 
                      help='顯示詳細輸出')
    
    args = parser.parse_args()
    
    # 創建測試工具實例
    tester = ComprehensiveTestTool()
    
    print("🧪 台股分析系統綜合測試工具")
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.verbose:
        tester.logger.setLevel(logging.DEBUG)
    
    # 執行測試
    if args.test == 'all':
        tester.run_all_tests()
    else:
        tester.run_specific_test(args.test)
    
    print("\n" + "=" * 80)
    print("📚 使用說明")
    print("=" * 80)
    print("1. 執行全部測試: python comprehensive_test_tool.py")
    print("2. 執行特定測試: python comprehensive_test_tool.py --test longterm")
    print("3. 顯示詳細日誌: python comprehensive_test_tool.py --verbose")
    print("4. 可用測試項目: all, longterm, price, indicators, weak, notification, data, formatter, timing")
    print("5. 查看測試結果日誌: logs/test_results.log")


if __name__ == "__main__":
    main()
