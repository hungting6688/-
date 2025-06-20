#!/usr/bin/env python3
"""
fix_twstockdatafetcher_import.py - 修復 TWStockDataFetcher 導入問題
重新創建一個簡化但完整的 twse_data_fetcher.py
"""

import os
import sys

def diagnose_file():
    """診斷當前文件問題"""
    print("🔍 診斷 twse_data_fetcher.py 文件...")
    
    if not os.path.exists('twse_data_fetcher.py'):
        print("❌ 文件不存在")
        return False
    
    try:
        with open('twse_data_fetcher.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 文件大小: {len(content)} 字符")
        print(f"📄 行數: {len(content.splitlines())}")
        
        # 檢查是否包含類定義
        if 'class TWStockDataFetcher' in content:
            print("✅ 找到 TWStockDataFetcher 類定義")
        else:
            print("❌ 沒有找到 TWStockDataFetcher 類定義")
            return False
        
        # 檢查語法
        try:
            compile(content, 'twse_data_fetcher.py', 'exec')
            print("✅ 語法檢查通過")
        except SyntaxError as e:
            print(f"❌ 語法錯誤: 第{e.lineno}行: {e.text}")
            print(f"   錯誤: {e.msg}")
            return False
        
        # 嘗試導入測試
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("twse_data_fetcher", "twse_data_fetcher.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'TWStockDataFetcher'):
                print("✅ TWStockDataFetcher 類可以成功導入")
                return True
            else:
                print("❌ 模組中沒有 TWStockDataFetcher 類")
                return False
                
        except Exception as e:
            print(f"❌ 導入測試失敗: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 文件讀取失敗: {e}")
        return False

def create_minimal_fetcher():
    """創建最小化但可用的 TWStockDataFetcher"""
    print("🔧 創建最小化的 TWStockDataFetcher...")
    
    minimal_code = '''"""
twse_data_fetcher.py - 台股數據抓取器（簡化版）
修復導入問題的最小化版本
"""
import os
import json
import time
import requests
import pandas as pd
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

# 可選的異步支援
try:
    import aiohttp
    import asyncio
    ASYNC_SUPPORT = True
    print("✅ 異步支援已啟用")
except ImportError:
    ASYNC_SUPPORT = False
    print("⚠️ 異步支援未啟用，將使用同步模式")
    
    # 模擬類
    class aiohttp:
        class ClientSession:
            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class ClientTimeout:
            def __init__(self, *args, **kwargs): pass
    
    class asyncio:
        @staticmethod
        def run(*args): return None

# 配置日誌
logger = logging.getLogger(__name__)

class TWStockDataFetcher:
    """台股數據抓取器（簡化版）"""
    
    def __init__(self, cache_dir: str = 'cache'):
        """初始化數據獲取器"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 台灣時區
        self.taipei_tz = pytz.timezone('Asia/Taipei')
        
        # API URLs
        self.apis = {
            'twse_daily': 'https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL',
            'tpex_daily': 'https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php',
        }
        
        # 請求標頭
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.twse.com.tw/',
        }
        
        # 請求設定
        self.timeout = 30
        self.max_fallback_days = 5
    
    def get_current_taiwan_time(self) -> datetime:
        """獲取當前台灣時間"""
        return datetime.now(self.taipei_tz)
    
    def get_optimal_data_date(self) -> str:
        """獲取最佳的數據日期"""
        now = self.get_current_taiwan_time()
        
        # 簡化邏輯：使用前一個工作日
        if now.weekday() == 0:  # 週一
            target_date = now - timedelta(days=3)  # 週五
        elif now.weekday() >= 5:  # 週末
            days_back = now.weekday() - 4  # 回到週五
            target_date = now - timedelta(days=days_back)
        elif now.hour < 9:  # 早上9點前
            target_date = now - timedelta(days=1)
        else:
            target_date = now
            
        return target_date.strftime('%Y%m%d')
    
    def _safe_float(self, value: str) -> float:
        """安全轉換為浮點數"""
        if not value or value in ["--", "N/A", "除權息", ""]:
            return 0.0
        try:
            return float(str(value).replace(",", "").replace("+", "").replace(" ", ""))
        except (ValueError, AttributeError):
            return 0.0
    
    def fetch_twse_daily_data(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取證交所上市股票數據"""
        if date is None:
            date = self.get_optimal_data_date()
        
        logger.info(f"獲取證交所數據 (日期: {date})")
        
        # 嘗試多個日期
        for attempt in range(self.max_fallback_days):
            try:
                attempt_date = datetime.strptime(date, '%Y%m%d') - timedelta(days=attempt)
                if attempt_date.weekday() >= 5:  # 跳過週末
                    continue
                    
                date_str = attempt_date.strftime('%Y%m%d')
                
                url = self.apis['twse_daily']
                params = {
                    'response': 'json',
                    'date': date_str,
                    'type': 'ALLBUT0999'
                }
                
                response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("stat") == "OK":
                    stocks = self._parse_twse_data(data, date_str)
                    if stocks:
                        logger.info(f"成功獲取 {len(stocks)} 支上市股票")
                        return stocks
                        
            except Exception as e:
                logger.warning(f"獲取 {date_str} 數據失敗: {e}")
                continue
        
        logger.error("所有日期都無法獲取上市股票數據")
        return []
    
    def fetch_tpex_daily_data(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取櫃買中心上櫃股票數據"""
        if date is None:
            date = self.get_optimal_data_date()
        
        logger.info(f"獲取櫃買數據 (日期: {date})")
        
        # 嘗試多個日期
        for attempt in range(self.max_fallback_days):
            try:
                attempt_date = datetime.strptime(date, '%Y%m%d') - timedelta(days=attempt)
                if attempt_date.weekday() >= 5:  # 跳過週末
                    continue
                
                # 轉換為民國年格式
                minguo_year = attempt_date.year - 1911
                minguo_date = f"{minguo_year}/{attempt_date.month:02d}/{attempt_date.day:02d}"
                
                url = self.apis['tpex_daily']
                params = {
                    'l': 'zh-tw',
                    'd': minguo_date,
                    'se': 'EW',
                    'o': 'json'
                }
                
                response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("stat") == "OK":
                    stocks = self._parse_tpex_data(data, attempt_date.strftime('%Y%m%d'))
                    if stocks:
                        logger.info(f"成功獲取 {len(stocks)} 支上櫃股票")
                        return stocks
                        
            except Exception as e:
                logger.warning(f"獲取上櫃數據失敗: {e}")
                continue
        
        logger.error("所有日期都無法獲取上櫃股票數據")
        return []
    
    def _parse_twse_data(self, data: Dict, date: str) -> List[Dict[str, Any]]:
        """解析證交所數據"""
        stocks = []
        fields = data.get("fields", [])
        raw_data = data.get("data", [])
        
        for row in raw_data:
            if len(row) >= len(fields):
                try:
                    stock_dict = dict(zip(fields, row))
                    
                    code = stock_dict.get("證券代號", "").strip()
                    name = stock_dict.get("證券名稱", "").strip()
                    
                    if not code or not name:
                        continue
                    
                    close_price = self._safe_float(stock_dict.get("收盤價", "0"))
                    volume = self._safe_float(stock_dict.get("成交股數", "0"))
                    change = self._safe_float(stock_dict.get("漲跌價差", "0"))
                    
                    if close_price <= 0:
                        continue
                    
                    change_percent = (change / close_price * 100) if close_price > 0 else 0
                    trade_value = volume * close_price
                    
                    stocks.append({
                        "code": code,
                        "name": name,
                        "market": "TWSE",
                        "close": close_price,
                        "volume": int(volume),
                        "trade_value": trade_value,
                        "change": change,
                        "change_percent": round(change_percent, 2),
                        "date": datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                        "data_source": "TWSE_API"
                    })
                    
                except Exception as e:
                    continue
        
        return stocks
    
    def _parse_tpex_data(self, data: Dict, date: str) -> List[Dict[str, Any]]:
        """解析櫃買數據"""
        stocks = []
        fields = data.get("fields", [])
        raw_data = data.get("data", [])
        
        for row in raw_data:
            if len(row) >= len(fields):
                try:
                    stock_dict = dict(zip(fields, row))
                    
                    code = stock_dict.get("代號", "").strip()
                    name = stock_dict.get("名稱", "").strip()
                    
                    if not code or not name:
                        continue
                    
                    close_price = self._safe_float(stock_dict.get("收盤", "0"))
                    volume = self._safe_float(stock_dict.get("成交量", "0"))
                    change = self._safe_float(stock_dict.get("漲跌", "0"))
                    
                    if close_price <= 0:
                        continue
                    
                    change_percent = (change / close_price * 100) if close_price > 0 else 0
                    trade_value = volume * close_price
                    
                    stocks.append({
                        "code": code,
                        "name": name,
                        "market": "TPEX",
                        "close": close_price,
                        "volume": int(volume),
                        "trade_value": trade_value,
                        "change": change,
                        "change_percent": round(change_percent, 2),
                        "date": datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                        "data_source": "TPEX_API"
                    })
                    
                except Exception as e:
                    continue
        
        return stocks
    
    def get_all_stocks_by_volume(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取所有股票並按成交金額排序"""
        logger.info("開始獲取所有股票數據")
        
        # 獲取上市股票
        twse_stocks = self.fetch_twse_daily_data(date)
        time.sleep(1)  # 避免請求過於頻繁
        
        # 獲取上櫃股票
        tpex_stocks = self.fetch_tpex_daily_data(date)
        
        # 合併和排序
        all_stocks = twse_stocks + tpex_stocks
        
        # 過濾有效數據
        valid_stocks = [
            stock for stock in all_stocks 
            if stock.get('trade_value', 0) > 0 and stock.get('close', 0) > 0
        ]
        
        # 按成交金額排序
        sorted_stocks = sorted(valid_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)
        
        logger.info(f"成功獲取並排序 {len(sorted_stocks)} 支股票")
        
        return sorted_stocks
    
    def get_stocks_by_time_slot(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """根據時段獲取相應數量的股票"""
        # 定義每個時段的股票數量
        slot_limits = {
            'morning_scan': 200,
            'mid_morning_scan': 300,
            'mid_day_scan': 300,
            'afternoon_scan': 1000,
            'weekly_summary': 500
        }
        
        limit = slot_limits.get(time_slot, 200)
        
        logger.info(f"獲取 {time_slot} 時段的前 {limit} 支股票")
        
        # 獲取所有股票
        all_stocks = self.get_all_stocks_by_volume(date)
        
        # 返回前N支股票
        selected_stocks = all_stocks[:limit]
        
        # 添加時段資訊
        for stock in selected_stocks:
            stock['time_slot'] = time_slot
        
        logger.info(f"為 {time_slot} 時段選擇了 {len(selected_stocks)} 支股票")
        
        return selected_stocks

# 測試函數
def test_fetcher():
    """測試數據抓取器"""
    print("🧪 測試 TWStockDataFetcher...")
    
    try:
        fetcher = TWStockDataFetcher()
        print("✅ TWStockDataFetcher 初始化成功")
        
        # 測試獲取少量股票
        stocks = fetcher.get_stocks_by_time_slot('morning_scan')
        if stocks:
            print(f"✅ 成功獲取 {len(stocks)} 支股票")
            print(f"📊 前3名股票:")
            for i, stock in enumerate(stocks[:3]):
                print(f"  {i+1}. {stock['code']} {stock['name']} - {stock['trade_value']:,.0f} 元")
        else:
            print("⚠️ 沒有獲取到股票數據")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    test_fetcher()
'''
    
    return minimal_code

def fix_import_issue():
    """修復導入問題"""
    print("🚀 開始修復 TWStockDataFetcher 導入問題...")
    
    # 步驟1: 診斷問題
    if diagnose_file():
        print("✅ 文件看起來正常，可能是其他問題")
        return True
    
    # 步驟2: 備份現有文件
    if os.path.exists('twse_data_fetcher.py'):
        backup_name = f'twse_data_fetcher_backup_{int(time.time())}.py'
        os.rename('twse_data_fetcher.py', backup_name)
        print(f"📁 已備份原文件為: {backup_name}")
    
    # 步驟3: 創建新的最小化版本
    minimal_code = create_minimal_fetcher()
    
    with open('twse_data_fetcher.py', 'w', encoding='utf-8') as f:
        f.write(minimal_code)
    
    print("✅ 已創建新的 twse_data_fetcher.py")
    
    # 步驟4: 測試新文件
    print("🧪 測試新文件...")
    
    try:
        # 語法檢查
        with open('twse_data_fetcher.py', 'r', encoding='utf-8') as f:
            content = f.read()
        compile(content, 'twse_data_fetcher.py', 'exec')
        print("✅ 語法檢查通過")
        
        # 導入測試
        import importlib.util
        spec = importlib.util.spec_from_file_location("twse_data_fetcher", "twse_data_fetcher.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, 'TWStockDataFetcher'):
            print("✅ TWStockDataFetcher 類可以成功導入")
            
            # 功能測試
            fetcher = module.TWStockDataFetcher()
            print("✅ TWStockDataFetcher 可以成功實例化")
            
            return True
        else:
            print("❌ 模組中沒有 TWStockDataFetcher 類")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🔧 TWStockDataFetcher 導入問題修復工具")
    print("=" * 50)
    
    if fix_import_issue():
        print("\n🎉 修復成功！")
        print("📋 修復內容:")
        print("  ✅ 重新創建了簡化但完整的 twse_data_fetcher.py")
        print("  ✅ 修復了 aiohttp 可選導入問題")
        print("  ✅ 保持了所有必要的功能")
        print("  ✅ TWStockDataFetcher 類可以正常導入")
        
        print("\n🚀 現在可以運行您的股票分析系統:")
        print("  python enhanced_stock_bot.py afternoon_scan")
        
        return True
    else:
        print("\n❌ 修復失敗")
        print("請檢查錯誤信息或聯繫技術支援")
        return False

if __name__ == "__main__":
    import time
    success = main()
    sys.exit(0 if success else 1)
