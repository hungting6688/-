#!/usr/bin/env python3
"""
taiwan_stock_data_fixer.py - 台股真實數據診斷修復工具
診斷並修復台股數據獲取問題，確保使用真實數據而非模擬數據
"""
import os
import sys
import time
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pytz
import subprocess

class TaiwanStockDataFixer:
    """台股真實數據診斷修復工具"""
    
    def __init__(self):
        self.taipei_tz = pytz.timezone('Asia/Taipei')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, */*',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        })
        
        # 最新的台股API端點 (2024-2025年有效)
        self.api_endpoints = {
            # 證交所最新OpenAPI
            'twse_openapi_stocks': 'https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL',
            'twse_openapi_realtime': 'https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX',
            'twse_openapi_institutional': 'https://openapi.twse.com.tw/v1/fund/T86',
            
            # 即時股價API (重要!)
            'twse_realtime_quotes': 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp',
            'twse_realtime_index': 'https://mis.twse.com.tw/stock/api/getStockCategory.jsp',
            
            # 備用API
            'twse_daily_trading': 'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX',
            
            # 櫃買中心API
            'tpex_daily': 'https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes',
            'tpex_institutional': 'https://www.tpex.org.tw/openapi/v1/tpex_mainboard_three_primary_market'
        }
        
        self.diagnosis_results = {}
        self.fix_results = {}
    
    def run_complete_diagnosis(self):
        """執行完整診斷"""
        print("🔍 台股真實數據診斷開始")
        print("=" * 80)
        print(f"診斷時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 檢查網路連接
        print("🌐 步驟1: 檢查網路連接...")
        network_ok = self._check_network_connection()
        self.diagnosis_results['network'] = network_ok
        
        # 2. 測試API端點
        print("\n📡 步驟2: 測試API端點...")
        api_results = self._test_all_apis()
        self.diagnosis_results['apis'] = api_results
        
        # 3. 檢查系統文件
        print("\n📂 步驟3: 檢查系統文件...")
        file_status = self._check_system_files()
        self.diagnosis_results['files'] = file_status
        
        # 4. 測試真實數據獲取
        print("\n📊 步驟4: 測試真實數據獲取...")
        data_test = self._test_real_data_fetching()
        self.diagnosis_results['data_fetch'] = data_test
        
        # 5. 分析問題並提供解決方案
        print("\n🔧 步驟5: 分析問題並提供解決方案...")
        self._analyze_and_fix()
        
        # 6. 顯示診斷結果
        self._show_diagnosis_summary()
    
    def _check_network_connection(self):
        """檢查網路連接"""
        test_urls = [
            'https://www.twse.com.tw',
            'https://openapi.twse.com.tw',
            'https://www.tpex.org.tw'
        ]
        
        results = {}
        for name, url in zip(['證交所官網', 'OpenAPI', '櫃買中心'], test_urls):
            try:
                response = requests.get(url, timeout=10)
                success = response.status_code == 200
                results[name] = success
                status = "✅ 正常" if success else f"❌ 失敗 ({response.status_code})"
                print(f"   {name}: {status}")
            except Exception as e:
                results[name] = False
                print(f"   {name}: ❌ 連接失敗 ({str(e)[:50]})")
        
        all_connected = all(results.values())
        print(f"\n網路連接狀態: {'✅ 正常' if all_connected else '❌ 部分失敗'}")
        return results
    
    def _test_all_apis(self):
        """測試所有API端點"""
        results = {}
        
        for api_name, api_url in self.api_endpoints.items():
            print(f"   測試 {api_name}...")
            try:
                if 'getStockInfo.jsp' in api_url:
                    # 即時股價API需要特定參數
                    params = {
                        'ex_ch': 'tse_2330.tw',
                        'json': '1',
                        'delay': '0',
                        '_': str(int(time.time() * 1000))
                    }
                    response = self.session.get(api_url, params=params, timeout=15)
                else:
                    response = self.session.get(api_url, timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        has_data = len(data) > 0 if isinstance(data, list) else bool(data)
                        results[api_name] = {'status': True, 'has_data': has_data}
                        print(f"      ✅ 成功 (有數據: {'是' if has_data else '否'})")
                    except:
                        results[api_name] = {'status': True, 'has_data': False}
                        print(f"      ⚠️ 連接成功但數據格式異常")
                else:
                    results[api_name] = {'status': False, 'has_data': False}
                    print(f"      ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                results[api_name] = {'status': False, 'has_data': False}
                print(f"      ❌ 失敗: {str(e)[:50]}")
                
            time.sleep(0.5)  # 避免請求過於頻繁
        
        working_apis = sum(1 for r in results.values() if r['status'])
        print(f"\nAPI測試結果: {working_apis}/{len(results)} 個端點正常")
        
        return results
    
    def _check_system_files(self):
        """檢查系統文件"""
        critical_files = [
            'real_taiwan_stock_fetcher.py',
            'unified_stock_analyzer.py',
            'config.py'
        ]
        
        optional_files = [
            'enhanced_stock_bot.py',
            'notifier.py',
            'requirements.txt'
        ]
        
        results = {}
        
        print("   關鍵文件:")
        for file in critical_files:
            exists = os.path.exists(file)
            results[file] = {'exists': exists, 'critical': True}
            status = "✅ 存在" if exists else "❌ 缺失"
            print(f"      {file}: {status}")
        
        print("   可選文件:")
        for file in optional_files:
            exists = os.path.exists(file)
            results[file] = {'exists': exists, 'critical': False}
            status = "✅ 存在" if exists else "⚠️ 缺失"
            print(f"      {file}: {status}")
        
        critical_missing = [f for f in critical_files if not results[f]['exists']]
        if critical_missing:
            print(f"\n❌ 缺失關鍵文件: {', '.join(critical_missing)}")
        else:
            print(f"\n✅ 所有關鍵文件都存在")
        
        return results
    
    def _test_real_data_fetching(self):
        """測試真實數據獲取"""
        print("   嘗試獲取台積電 (2330) 真實數據...")
        
        results = {}
        
        # 測試1: OpenAPI
        try:
            url = self.api_endpoints['twse_openapi_stocks']
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                tsmc_data = None
                for item in data:
                    if item.get('Code') == '2330':
                        tsmc_data = item
                        break
                
                if tsmc_data:
                    results['openapi'] = {
                        'success': True,
                        'price': tsmc_data.get('ClosingPrice', 0),
                        'volume': tsmc_data.get('TradeVolume', 0)
                    }
                    print(f"      ✅ OpenAPI: 價格 {tsmc_data.get('ClosingPrice')} 元")
                else:
                    results['openapi'] = {'success': False, 'reason': '找不到台積電數據'}
                    print(f"      ❌ OpenAPI: 找不到台積電數據")
            else:
                results['openapi'] = {'success': False, 'reason': f'HTTP {response.status_code}'}
                print(f"      ❌ OpenAPI: HTTP {response.status_code}")
        except Exception as e:
            results['openapi'] = {'success': False, 'reason': str(e)}
            print(f"      ❌ OpenAPI: {str(e)[:50]}")
        
        # 測試2: 即時股價API
        try:
            url = self.api_endpoints['twse_realtime_quotes']
            params = {
                'ex_ch': 'tse_2330.tw',
                'json': '1',
                'delay': '0',
                '_': str(int(time.time() * 1000))
            }
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'msgArray' in data and len(data['msgArray']) > 0:
                    tsmc_data = data['msgArray'][0]
                    results['realtime'] = {
                        'success': True,
                        'price': tsmc_data.get('z', 0),
                        'volume': tsmc_data.get('v', 0)
                    }
                    print(f"      ✅ 即時API: 價格 {tsmc_data.get('z')} 元")
                else:
                    results['realtime'] = {'success': False, 'reason': '無數據返回'}
                    print(f"      ❌ 即時API: 無數據返回")
            else:
                results['realtime'] = {'success': False, 'reason': f'HTTP {response.status_code}'}
                print(f"      ❌ 即時API: HTTP {response.status_code}")
        except Exception as e:
            results['realtime'] = {'success': False, 'reason': str(e)}
            print(f"      ❌ 即時API: {str(e)[:50]}")
        
        successful_tests = sum(1 for r in results.values() if r['success'])
        print(f"\n數據獲取測試: {successful_tests}/{len(results)} 項成功")
        
        return results
    
    def _analyze_and_fix(self):
        """分析問題並提供修復方案"""
        print("正在分析診斷結果...")
        
        # 分析網路問題
        network_issues = []
        if not all(self.diagnosis_results['network'].values()):
            network_issues.append("部分網站無法訪問")
        
        # 分析API問題
        api_issues = []
        working_apis = [name for name, result in self.diagnosis_results['apis'].items() 
                       if result['status']]
        if len(working_apis) == 0:
            api_issues.append("所有API都無法連接")
        elif len(working_apis) < len(self.diagnosis_results['apis']) // 2:
            api_issues.append("大部分API無法連接")
        
        # 分析文件問題
        file_issues = []
        for filename, info in self.diagnosis_results['files'].items():
            if info['critical'] and not info['exists']:
                file_issues.append(f"缺失關鍵文件: {filename}")
        
        # 分析數據獲取問題
        data_issues = []
        if not any(result['success'] for result in self.diagnosis_results['data_fetch'].values()):
            data_issues.append("無法獲取任何真實數據")
        
        # 生成修復方案
        all_issues = network_issues + api_issues + file_issues + data_issues
        
        if not all_issues:
            print("✅ 沒有發現問題，系統應該能正常獲取真實數據")
            self._create_working_data_fetcher()
        else:
            print("⚠️ 發現以下問題:")
            for issue in all_issues:
                print(f"   • {issue}")
            
            print("\n🔧 正在生成修復方案...")
            self._create_comprehensive_fix()
    
    def _create_working_data_fetcher(self):
        """創建工作中的數據獲取器"""
        print("創建優化的真實數據獲取器...")
        
        working_apis = [name for name, result in self.diagnosis_results['apis'].items() 
                       if result['status'] and result['has_data']]
        
        fetcher_code = self._generate_working_fetcher_code(working_apis)
        
        with open('working_taiwan_stock_fetcher.py', 'w', encoding='utf-8') as f:
            f.write(fetcher_code)
        
        print("✅ 已創建 working_taiwan_stock_fetcher.py")
        self.fix_results['working_fetcher'] = True
    
    def _create_comprehensive_fix(self):
        """創建綜合修復方案"""
        print("創建綜合修復方案...")
        
        # 1. 創建修復版數據獲取器
        self._create_robust_fetcher()
        
        # 2. 創建系統修復腳本
        self._create_system_fixer()
        
        # 3. 創建強制真實數據配置
        self._create_force_real_data_config()
        
        print("✅ 修復方案已準備完成")
    
    def _create_robust_fetcher(self):
        """創建強健的數據獲取器"""
        robust_code = '''#!/usr/bin/env python3
"""
robust_taiwan_stock_fetcher.py - 強健的台股數據獲取器
自動適應API變化，確保獲取真實數據
"""
import requests
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

class RobustTaiwanStockFetcher:
    """強健的台股數據獲取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, */*',
            'Referer': 'https://www.twse.com.tw/'
        })
        
        # 多重API策略
        self.api_strategies = [
            self._fetch_from_openapi,
            self._fetch_from_realtime_api,
            self._fetch_from_backup_api
        ]
    
    def get_stocks_by_time_slot(self, time_slot: str, force_fresh: bool = True) -> List[Dict[str, Any]]:
        """強健地獲取股票數據"""
        print(f"🔄 強健模式獲取 {time_slot} 數據...")
        
        for i, strategy in enumerate(self.api_strategies, 1):
            try:
                print(f"   嘗試策略 {i}...")
                stocks = strategy()
                if stocks and len(stocks) > 10:
                    print(f"   ✅ 策略 {i} 成功獲取 {len(stocks)} 支股票")
                    return self._process_stocks(stocks, time_slot)
                else:
                    print(f"   ⚠️ 策略 {i} 數據不足")
            except Exception as e:
                print(f"   ❌ 策略 {i} 失敗: {e}")
                continue
        
        # 如果所有策略都失敗，拋出錯誤而不是返回模擬數據
        raise Exception("❌ 所有數據獲取策略都失敗，無法獲取真實數據")
    
    def _fetch_from_openapi(self) -> List[Dict[str, Any]]:
        """策略1: OpenAPI"""
        url = 'https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL'
        response = self.session.get(url, timeout=15)
        
        if response.status_code != 200:
            raise Exception(f"OpenAPI HTTP {response.status_code}")
        
        data = response.json()
        if not isinstance(data, list) or len(data) == 0:
            raise Exception("OpenAPI無有效數據")
        
        stocks = []
        for item in data:
            try:
                stock = self._parse_openapi_stock(item)
                if stock:
                    stocks.append(stock)
            except:
                continue
        
        return stocks
    
    def _fetch_from_realtime_api(self) -> List[Dict[str, Any]]:
        """策略2: 即時API"""
        # 熱門股票代碼
        hot_stocks = ['2330', '2317', '2454', '2412', '2308', '1301', '2002', '2882']
        
        stocks = []
        for i in range(0, len(hot_stocks), 5):
            batch = hot_stocks[i:i+5]
            batch_stocks = self._fetch_realtime_batch(batch)
            stocks.extend(batch_stocks)
            time.sleep(1)  # 避免請求過於頻繁
        
        if len(stocks) < 5:
            raise Exception("即時API數據不足")
        
        return stocks
    
    def _fetch_realtime_batch(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """批次獲取即時數據"""
        ex_ch = '|'.join([f'tse_{code}.tw' for code in stock_codes])
        
        url = 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp'
        params = {
            'ex_ch': ex_ch,
            'json': '1',
            'delay': '0',
            '_': str(int(time.time() * 1000))
        }
        
        response = self.session.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        if 'msgArray' not in data:
            return []
        
        stocks = []
        for item in data['msgArray']:
            try:
                stock = self._parse_realtime_stock(item)
                if stock:
                    stocks.append(stock)
            except:
                continue
        
        return stocks
    
    def _fetch_from_backup_api(self) -> List[Dict[str, Any]]:
        """策略3: 備用API"""
        # 這裡可以實現其他數據源
        # 例如爬蟲、其他金融API等
        raise Exception("備用API暫未實現")
    
    def _parse_openapi_stock(self, data: Dict) -> Optional[Dict[str, Any]]:
        """解析OpenAPI股票數據"""
        code = data.get('Code', '').strip()
        name = data.get('Name', '').strip()
        
        if not code or not code.isdigit() or len(code) != 4:
            return None
        
        close = self._safe_float(data.get('ClosingPrice', '0'))
        volume = self._safe_int(data.get('TradeVolume', '0'))
        trade_value = self._safe_int(data.get('TradeValue', '0'))
        change = self._safe_float(data.get('Change', '0'))
        
        if close <= 0 or volume <= 0:
            return None
        
        return {
            'code': code,
            'name': name,
            'close': close,
            'volume': volume,
            'trade_value': trade_value,
            'change': change,
            'change_percent': (change / (close - change) * 100) if (close - change) > 0 else 0,
            'data_source': 'openapi_real',
            'is_real_data': True
        }
    
    def _parse_realtime_stock(self, data: Dict) -> Optional[Dict[str, Any]]:
        """解析即時API股票數據"""
        code = data.get('c', '').strip()
        name = data.get('n', '').strip()
        
        if not code or not code.isdigit():
            return None
        
        close = self._safe_float(data.get('z', '0'))
        volume = self._safe_int(data.get('v', '0'))
        trade_value = self._safe_int(data.get('tv', '0'))
        yesterday = self._safe_float(data.get('y', '0'))
        
        if close <= 0 or yesterday <= 0:
            return None
        
        change = close - yesterday
        
        return {
            'code': code,
            'name': name,
            'close': close,
            'volume': volume,
            'trade_value': trade_value,
            'change': change,
            'change_percent': (change / yesterday * 100) if yesterday > 0 else 0,
            'data_source': 'realtime_real',
            'is_real_data': True
        }
    
    def _process_stocks(self, stocks: List[Dict], time_slot: str) -> List[Dict[str, Any]]:
        """處理股票數據"""
        # 按成交金額排序
        valid_stocks = [s for s in stocks if s.get('trade_value', 0) > 0]
        sorted_stocks = sorted(valid_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)
        
        # 根據時段限制數量
        limits = {
            'morning_scan': 200,
            'afternoon_scan': 500,
            'weekly_summary': 1000
        }
        
        limit = limits.get(time_slot, 300)
        result = sorted_stocks[:limit]
        
        # 標記為真實數據
        for stock in result:
            stock['fetch_time'] = datetime.now().isoformat()
            stock['is_simulation'] = False
        
        return result
    
    def _safe_float(self, value):
        """安全轉換浮點數"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return float(value) if value else 0.0
        except:
            return 0.0
    
    def _safe_int(self, value):
        """安全轉換整數"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return int(float(value)) if value else 0
        except:
            return 0

# 測試函數
def test_robust_fetcher():
    """測試強健獲取器"""
    print("🧪 測試強健台股數據獲取器")
    
    fetcher = RobustTaiwanStockFetcher()
    
    try:
        stocks = fetcher.get_stocks_by_time_slot('afternoon_scan')
        
        if stocks:
            print(f"✅ 成功獲取 {len(stocks)} 支真實股票數據")
            
            print("\\n📈 前5支股票:")
            for i, stock in enumerate(stocks[:5]):
                real_flag = "🟢 真實" if stock.get('is_real_data') else "🔴 模擬"
                print(f"   {i+1}. {stock['code']} {stock['name']}")
                print(f"      現價: {stock['close']:.2f} 元 ({stock['change_percent']:+.2f}%)")
                print(f"      數據: {real_flag} | 來源: {stock.get('data_source', 'unknown')}")
        else:
            print("❌ 無法獲取股票數據")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    test_robust_fetcher()
'''
        
        with open('robust_taiwan_stock_fetcher.py', 'w', encoding='utf-8') as f:
            f.write(robust_code)
        
        print("✅ 已創建 robust_taiwan_stock_fetcher.py")
        self.fix_results['robust_fetcher'] = True
    
    def _create_system_fixer(self):
        """創建系統修復腳本"""
        fixer_code = '''#!/usr/bin/env python3
"""
force_real_data_mode.py - 強制真實數據模式
修改系統配置，確保只使用真實數據
"""
import os
import sys
import shutil
from datetime import datetime

def force_real_data_mode():
    """強制啟用真實數據模式"""
    print("🔧 強制啟用真實數據模式")
    
    # 1. 備份原始文件
    backup_dir = f"backup_before_real_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = ['unified_stock_analyzer.py', 'enhanced_stock_bot.py']
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_dir, file))
            print(f"   已備份: {file}")
    
    # 2. 修改unified_stock_analyzer.py
    if os.path.exists('unified_stock_analyzer.py'):
        modify_unified_analyzer()
    
    # 3. 創建強制配置文件
    create_force_real_config()
    
    print("✅ 真實數據模式已啟用")
    print(f"📁 備份位置: {backup_dir}")
    print("\\n⚠️ 現在系統將拒絕使用模擬數據，只接受真實數據")

def modify_unified_analyzer():
    """修改統一分析器"""
    print("   修改 unified_stock_analyzer.py...")
    
    with open('unified_stock_analyzer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加強制真實數據代碼
    force_real_code = '''
# === 強制真實數據模式 ===
FORCE_REAL_DATA_ONLY = True
REJECT_SIMULATION_DATA = True

def validate_real_data(stocks):
    """驗證數據是否為真實數據"""
    if not stocks:
        raise Exception("❌ 數據為空，拒絕使用")
    
    # 檢查是否有真實數據標記
    real_data_count = sum(1 for stock in stocks if stock.get('is_real_data', False))
    simulation_count = len(stocks) - real_data_count
    
    if FORCE_REAL_DATA_ONLY and simulation_count > 0:
        raise Exception(f"❌ 檢測到 {simulation_count} 筆模擬數據，強制真實數據模式拒絕使用")
    
    if real_data_count == 0:
        raise Exception("❌ 沒有檢測到真實數據標記，拒絕使用")
    
    print(f"✅ 數據驗證通過: {real_data_count} 筆真實數據")
    return True
'''
    
    # 在DataFetcher類的開頭添加
    if 'class DataFetcher:' in content:
        content = content.replace(
            'class DataFetcher:',
            force_real_code + '\\nclass DataFetcher:'
        )
    
    # 修改get_stocks_by_time_slot方法
    old_method = '''    def get_stocks_by_time_slot(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """根據時段獲取股票數據（統一入口）"""'''
    
    new_method = '''    def get_stocks_by_time_slot(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """根據時段獲取股票數據（強制真實數據模式）"""
        
        # 強制使用強健獲取器
        try:
            from robust_taiwan_stock_fetcher import RobustTaiwanStockFetcher
            robust_fetcher = RobustTaiwanStockFetcher()
            stocks = robust_fetcher.get_stocks_by_time_slot(time_slot, force_fresh=True)
            
            # 驗證數據真實性
            validate_real_data(stocks)
            
            log_event(f"✅ 強制真實數據模式: 獲取 {len(stocks)} 支真實股票", level='success')
            return stocks
            
        except ImportError:
            log_event("❌ 強健獲取器不可用", level='error')
            raise Exception("強制真實數據模式: 必需的獲取器不可用")
        except Exception as e:
            log_event(f"❌ 強制真實數據模式失敗: {e}", level='error')
            raise Exception(f"強制真實數據模式: {e}")'''
    
    content = content.replace(old_method, new_method)
    
    with open('unified_stock_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("   ✅ unified_stock_analyzer.py 已修改")

def create_force_real_config():
    """創建強制配置"""
    config_content = '''# force_real_data_config.py - 強制真實數據配置
FORCE_REAL_DATA_ONLY = True
DISABLE_SIMULATION_FALLBACK = True
REQUIRE_DATA_VALIDATION = True

# 數據驗證規則
DATA_VALIDATION_RULES = {
    'min_stocks_count': 10,
    'require_real_data_flag': True,
    'require_recent_timestamp': True,
    'max_simulation_ratio': 0.0  # 0% 模擬數據
}

print("⚠️ 強制真實數據配置已加載")
print("🚫 模擬數據回退已禁用")
'''
    
    with open('force_real_data_config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("   ✅ 已創建強制配置文件")

if __name__ == "__main__":
    force_real_data_mode()
'''
        
        with open('force_real_data_mode.py', 'w', encoding='utf-8') as f:
            f.write(fixer_code)
        
        print("✅ 已創建 force_real_data_mode.py")
        self.fix_results['system_fixer'] = True
    
    def _create_force_real_data_config(self):
        """創建強制真實數據配置"""
        config_content = '''# real_data_config.py - 真實數據配置
"""
這個文件確保系統只使用真實的台股數據
"""

# 強制設定
FORCE_REAL_DATA = True
DISABLE_MOCK_DATA = True
STRICT_VALIDATION = True

# 數據來源優先級
DATA_SOURCE_PRIORITY = [
    'openapi_real',
    'realtime_real', 
    'backup_real'
]

# 拒絕的數據來源
REJECTED_SOURCES = [
    'mock',
    'simulation',
    'test_data'
]

# 驗證規則
VALIDATION_RULES = {
    'require_is_real_data_flag': True,
    'require_current_day_timestamp': True,
    'min_data_count': 50,
    'max_simulation_ratio': 0.0
}

def is_real_data(stock_data):
    """檢查數據是否為真實數據"""
    # 檢查真實數據標記
    if not stock_data.get('is_real_data', False):
        return False
    
    # 檢查數據來源
    source = stock_data.get('data_source', '')
    if source in REJECTED_SOURCES:
        return False
    
    # 檢查基本數據完整性
    required_fields = ['code', 'name', 'close', 'volume', 'trade_value']
    for field in required_fields:
        if field not in stock_data or stock_data[field] is None:
            return False
    
    return True

def validate_stock_list(stocks):
    """驗證股票列表"""
    if not stocks:
        raise ValueError("股票數據為空")
    
    real_count = sum(1 for stock in stocks if is_real_data(stock))
    total_count = len(stocks)
    
    if STRICT_VALIDATION and real_count < total_count:
        fake_count = total_count - real_count
        raise ValueError(f"發現 {fake_count} 筆非真實數據，嚴格模式拒絕使用")
    
    if real_count < VALIDATION_RULES['min_data_count']:
        raise ValueError(f"真實數據不足: {real_count} < {VALIDATION_RULES['min_data_count']}")
    
    return True
'''
        
        with open('real_data_config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print("✅ 已創建 real_data_config.py")
        self.fix_results['real_data_config'] = True
    
    def _generate_working_fetcher_code(self, working_apis):
        """生成工作中的獲取器代碼"""
        # 這裡可以根據working_apis生成優化的代碼
        # 簡化版本，直接返回robust fetcher的代碼
        return '''# 這是基於診斷結果生成的獲取器
# 請參考 robust_taiwan_stock_fetcher.py
from robust_taiwan_stock_fetcher import RobustTaiwanStockFetcher
'''
    
    def _show_diagnosis_summary(self):
        """顯示診斷總結"""
        print("\n" + "=" * 80)
        print("🎯 診斷總結報告")
        print("=" * 80)
        
        # 網路狀態
        network_ok = all(self.diagnosis_results['network'].values())
        print(f"🌐 網路連接: {'✅ 正常' if network_ok else '❌ 異常'}")
        
        # API狀態
        working_apis = sum(1 for r in self.diagnosis_results['apis'].values() if r['status'])
        total_apis = len(self.diagnosis_results['apis'])
        print(f"📡 API端點: {working_apis}/{total_apis} 可用")
        
        # 文件狀態
        critical_files_ok = all(
            info['exists'] for info in self.diagnosis_results['files'].values() 
            if info['critical']
        )
        print(f"📂 關鍵文件: {'✅ 完整' if critical_files_ok else '❌ 缺失'}")
        
        # 數據獲取狀態
        data_fetch_ok = any(r['success'] for r in self.diagnosis_results['data_fetch'].values())
        print(f"📊 數據獲取: {'✅ 成功' if data_fetch_ok else '❌ 失敗'}")
        
        # 修復方案
        print(f"\n🔧 已創建的修復工具:")
        for tool, created in self.fix_results.items():
            if created:
                print(f"   ✅ {tool}")
        
        # 使用指南
        print(f"\n📋 使用指南:")
        print(f"1. 測試強健獲取器: python robust_taiwan_stock_fetcher.py")
        print(f"2. 啟用強制真實數據模式: python force_real_data_mode.py")
        print(f"3. 運行系統: python unified_stock_analyzer.py run --slot afternoon_scan")
        
        if data_fetch_ok and working_apis > 0:
            print(f"\n🎉 好消息: 系統能夠獲取真實數據!")
            print(f"💡 建議: 執行 'python force_real_data_mode.py' 來禁用模擬數據回退")
        else:
            print(f"\n⚠️ 需要修復: 真實數據獲取有問題")
            print(f"💡 建議: 檢查網路連接和API可用性")

def main():
    """主函數"""
    print("🔍 台股真實數據診斷修復工具")
    print("幫助您診斷並修復數據獲取問題，確保使用真實數據")
    print()
    
    fixer = TaiwanStockDataFixer()
    fixer.run_complete_diagnosis()
    
    print(f"\n🎯 下一步:")
    print(f"1. 如果診斷顯示數據獲取成功，執行: python force_real_data_mode.py")
    print(f"2. 測試真實數據: python robust_taiwan_stock_fetcher.py")
    print(f"3. 重新運行股票分析系統")

if __name__ == "__main__":
    main()
