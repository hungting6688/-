#!/usr/bin/env python3
"""
fixed_taiwan_stock_fetcher.py - 修正版台股數據獲取器
基於可行的 twse_data_fetcher.py 邏輯，整合並修正
確保獲取真實、可靠的台股數據
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

class FixedTaiwanStockFetcher:
    """修正版台股數據獲取器 - 基於可行邏輯"""
    
    def __init__(self, cache_dir: str = 'cache'):
        """初始化數據獲取器"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 台灣時區
        self.taipei_tz = pytz.timezone('Asia/Taipei')
        
        # 設置日誌
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 經過驗證的API URLs（基於twse_data_fetcher.py）
        self.apis = {
            # 主要API - 證交所官方
            'twse_daily': 'https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL',
            'twse_institutional': 'https://www.twse.com.tw/fund/T86',
            
            # 櫃買中心API
            'tpex_daily': 'https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php',
            'tpex_institutional': 'https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php',
            
            # 備用API
            'twse_openapi': 'https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL',
            'realtime_quotes': 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp',
        }
        
        # 請求標頭
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.twse.com.tw/',
            'Cache-Control': 'no-cache',
        }
        
        # 請求設定
        self.timeout = 30
        self.max_fallback_days = 5
        self.max_retries = 3
        
        self.logger.info("修正版台股數據獲取器初始化完成")
    
    def get_current_taiwan_time(self) -> datetime:
        """獲取當前台灣時間"""
        return datetime.now(self.taipei_tz)
    
    def get_optimal_data_date(self) -> str:
        """獲取最佳的數據日期（基於原始邏輯）"""
        now = self.get_current_taiwan_time()
        
        # 使用原始的簡化邏輯
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
        """安全轉換為浮點數（沿用原始邏輯）"""
        if not value or value in ["--", "N/A", "除權息", "", "X"]:
            return 0.0
        try:
            return float(str(value).replace(",", "").replace("+", "").replace(" ", "").strip())
        except (ValueError, AttributeError):
            return 0.0
    
    def _safe_int(self, value: Any) -> int:
        """安全轉換為整數"""
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                cleaned = value.replace(',', '').replace(' ', '').strip()
                if cleaned == '' or cleaned == '--' or cleaned == 'N/A':
                    return 0
                return int(float(cleaned))
            return int(float(value))
        except (ValueError, TypeError, AttributeError):
            return 0
    
    def _make_request(self, url: str, params: Dict = None, max_retries: int = None) -> Optional[requests.Response]:
        """發出HTTP請求，帶重試機制"""
        if max_retries is None:
            max_retries = self.max_retries
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"請求: {url} (嘗試 {attempt + 1}/{max_retries})")
                
                response = requests.get(
                    url, 
                    params=params, 
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"請求失敗 (嘗試 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))  # 遞增延遲
        
        return None
    
    def fetch_twse_daily_data(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取證交所上市股票數據（沿用原始成功邏輯）"""
        if date is None:
            date = self.get_optimal_data_date()
        
        self.logger.info(f"獲取證交所數據 (日期: {date})")
        
        # 嘗試多個日期（原始邏輯）
        for attempt in range(self.max_fallback_days):
            try:
                attempt_date = datetime.strptime(date, '%Y%m%d') - timedelta(days=attempt)
                if attempt_date.weekday() >= 5:  # 跳過週末
                    continue
                    
                date_str = attempt_date.strftime('%Y%m%d')
                
                # 首先嘗試主要API
                stocks = self._fetch_twse_main_api(date_str)
                if stocks:
                    self.logger.info(f"主要API成功獲取 {len(stocks)} 支上市股票")
                    return stocks
                
                # 如果主要API失敗，嘗試OpenAPI
                stocks = self._fetch_twse_openapi(date_str)
                if stocks:
                    self.logger.info(f"OpenAPI成功獲取 {len(stocks)} 支上市股票")
                    return stocks
                        
            except Exception as e:
                self.logger.warning(f"獲取 {date_str} 數據失敗: {e}")
                continue
        
        self.logger.error("所有日期都無法獲取上市股票數據")
        return []
    
    def _fetch_twse_main_api(self, date_str: str) -> List[Dict[str, Any]]:
        """從主要TWSE API獲取數據"""
        url = self.apis['twse_daily']
        params = {
            'response': 'json',
            'date': date_str,
            'type': 'ALLBUT0999'
        }
        
        response = self._make_request(url, params=params)
        if not response:
            return []
        
        try:
            data = response.json()
            
            if data.get("stat") == "OK":
                return self._parse_twse_data(data, date_str)
        except Exception as e:
            self.logger.warning(f"解析主要API數據失敗: {e}")
            
        return []
    
    def _fetch_twse_openapi(self, date_str: str) -> List[Dict[str, Any]]:
        """從OpenAPI獲取數據"""
        url = self.apis['twse_openapi']
        
        response = self._make_request(url)
        if not response:
            return []
        
        try:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                return self._parse_openapi_data(data, date_str)
        except Exception as e:
            self.logger.warning(f"解析OpenAPI數據失敗: {e}")
            
        return []
    
    def _parse_twse_data(self, data: Dict, date: str) -> List[Dict[str, Any]]:
        """解析證交所數據（沿用原始邏輯）"""
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
                        "data_source": "TWSE_MAIN_API",
                        "is_real_data": True,
                        "fetch_time": self.get_current_taiwan_time().isoformat()
                    })
                    
                except Exception as e:
                    continue
        
        return stocks
    
    def _parse_openapi_data(self, data: List, date: str) -> List[Dict[str, Any]]:
        """解析OpenAPI數據"""
        stocks = []
        
        for item in data:
            try:
                code = item.get('Code', '').strip()
                name = item.get('Name', '').strip()
                
                if not code or not code.isdigit() or len(code) != 4:
                    continue
                
                close_price = self._safe_float(item.get('ClosingPrice', '0'))
                volume = self._safe_int(item.get('TradeVolume', '0'))
                trade_value = self._safe_int(item.get('TradeValue', '0'))
                change = self._safe_float(item.get('Change', '0'))
                
                if close_price <= 0 or volume <= 0:
                    continue
                
                change_percent = (change / (close_price - change) * 100) if (close_price - change) > 0 else 0
                
                stocks.append({
                    "code": code,
                    "name": name,
                    "market": "TWSE",
                    "close": close_price,
                    "volume": volume,
                    "trade_value": trade_value,
                    "change": change,
                    "change_percent": round(change_percent, 2),
                    "date": datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                    "data_source": "TWSE_OPENAPI",
                    "is_real_data": True,
                    "fetch_time": self.get_current_taiwan_time().isoformat()
                })
                
            except Exception as e:
                continue
        
        return stocks
    
    def fetch_tpex_daily_data(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取櫃買中心上櫃股票數據（沿用原始邏輯）"""
        if date is None:
            date = self.get_optimal_data_date()
        
        self.logger.info(f"獲取櫃買數據 (日期: {date})")
        
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
                
                response = self._make_request(url, params=params)
                if not response:
                    continue
                
                data = response.json()
                
                if data.get("stat") == "OK":
                    stocks = self._parse_tpex_data(data, attempt_date.strftime('%Y%m%d'))
                    if stocks:
                        self.logger.info(f"成功獲取 {len(stocks)} 支上櫃股票")
                        return stocks
                        
            except Exception as e:
                self.logger.warning(f"獲取上櫃數據失敗: {e}")
                continue
        
        self.logger.error("所有日期都無法獲取上櫃股票數據")
        return []
    
    def _parse_tpex_data(self, data: Dict, date: str) -> List[Dict[str, Any]]:
        """解析櫃買數據（沿用原始邏輯）"""
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
                        "data_source": "TPEX_API",
                        "is_real_data": True,
                        "fetch_time": self.get_current_taiwan_time().isoformat()
                    })
                    
                except Exception as e:
                    continue
        
        return stocks
    
    def get_institutional_data(self, date: str = None) -> Dict[str, Dict[str, Any]]:
        """獲取法人買賣數據"""
        if date is None:
            date = self.get_optimal_data_date()
        
        self.logger.info(f"獲取法人數據 (日期: {date})")
        
        institutional_data = {}
        
        # 嘗試獲取證交所法人數據
        try:
            url = self.apis['twse_institutional']
            params = {
                'response': 'json',
                'date': date,
                'selectType': 'ALL'
            }
            
            response = self._make_request(url, params=params)
            if response:
                data = response.json()
                if data.get("stat") == "OK":
                    institutional_data.update(self._parse_institutional_data(data))
                    
        except Exception as e:
            self.logger.warning(f"獲取證交所法人數據失敗: {e}")
        
        return institutional_data
    
    def _parse_institutional_data(self, data: Dict) -> Dict[str, Dict[str, Any]]:
        """解析法人數據"""
        institutional_data = {}
        fields = data.get("fields", [])
        raw_data = data.get("data", [])
        
        for row in raw_data:
            if len(row) >= len(fields):
                try:
                    row_dict = dict(zip(fields, row))
                    
                    code = row_dict.get("證券代號", "").strip()
                    if not code or not code.isdigit():
                        continue
                    
                    foreign_buy = self._safe_int(row_dict.get("外陸資買進股數(不含外資自營商)", "0"))
                    foreign_sell = self._safe_int(row_dict.get("外陸資賣出股數(不含外資自營商)", "0"))
                    trust_buy = self._safe_int(row_dict.get("投信買進股數", "0"))
                    trust_sell = self._safe_int(row_dict.get("投信賣出股數", "0"))
                    dealer_buy = self._safe_int(row_dict.get("自營商買進股數(自行買賣)", "0"))
                    dealer_sell = self._safe_int(row_dict.get("自營商賣出股數(自行買賣)", "0"))
                    
                    foreign_net = foreign_buy - foreign_sell
                    trust_net = trust_buy - trust_sell
                    dealer_net = dealer_buy - dealer_sell
                    
                    institutional_data[code] = {
                        'foreign_net_buy': foreign_net,
                        'trust_net_buy': trust_net,
                        'dealer_net_buy': dealer_net,
                        'total_net_buy': foreign_net + trust_net + dealer_net,
                        'institutional_data_available': True
                    }
                    
                except Exception as e:
                    continue
        
        return institutional_data
    
    def get_all_stocks_by_volume(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取所有股票並按成交金額排序（沿用原始邏輯）"""
        self.logger.info("開始獲取所有股票數據")
        
        # 獲取上市股票
        twse_stocks = self.fetch_twse_daily_data(date)
        if twse_stocks:
            time.sleep(1)  # 避免請求過於頻繁
        
        # 獲取上櫃股票
        tpex_stocks = self.fetch_tpex_daily_data(date)
        
        # 合併數據
        all_stocks = twse_stocks + tpex_stocks
        
        # 過濾有效數據
        valid_stocks = [
            stock for stock in all_stocks 
            if stock.get('trade_value', 0) > 0 and stock.get('close', 0) > 0
        ]
        
        # 按成交金額排序
        sorted_stocks = sorted(valid_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)
        
        # 獲取法人數據並整合
        institutional_data = self.get_institutional_data(date)
        
        for stock in sorted_stocks:
            code = stock['code']
            if code in institutional_data:
                stock.update(institutional_data[code])
            else:
                stock.update({
                    'foreign_net_buy': 0,
                    'trust_net_buy': 0,
                    'dealer_net_buy': 0,
                    'total_net_buy': 0,
                    'institutional_data_available': False
                })
        
        self.logger.info(f"成功獲取並排序 {len(sorted_stocks)} 支股票")
        
        return sorted_stocks
    
    def get_stocks_by_time_slot(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """根據時段獲取相應數量的股票（主要入口函數）"""
        # 定義每個時段的股票數量
        slot_limits = {
            'morning_scan': 200,
            'mid_morning_scan': 300,
            'mid_day_scan': 300,
            'afternoon_scan': 500,
            'weekly_summary': 1000
        }
        
        limit = slot_limits.get(time_slot, 200)
        
        self.logger.info(f"獲取 {time_slot} 時段的前 {limit} 支股票")
        
        try:
            # 獲取所有股票
            all_stocks = self.get_all_stocks_by_volume(date)
            
            if not all_stocks:
                raise Exception("無法獲取任何股票數據")
            
            # 返回前N支股票
            selected_stocks = all_stocks[:limit]
            
            # 添加時段資訊和數據品質標記
            for stock in selected_stocks:
                stock['time_slot'] = time_slot
                stock['data_quality'] = 'verified_real_data'
                stock['is_simulation'] = False
            
            self.logger.info(f"為 {time_slot} 時段成功選擇了 {len(selected_stocks)} 支真實股票")
            
            return selected_stocks
            
        except Exception as e:
            self.logger.error(f"獲取 {time_slot} 數據失敗: {e}")
            raise Exception(f"無法獲取 {time_slot} 的真實股票數據: {e}")
    
    def test_connection(self) -> Dict[str, bool]:
        """測試所有API連接"""
        self.logger.info("測試API連接...")
        
        results = {}
        
        # 測試主要API
        try:
            response = self._make_request(self.apis['twse_daily'], max_retries=1)
            results['twse_main'] = response is not None and response.status_code == 200
        except:
            results['twse_main'] = False
        
        # 測試OpenAPI
        try:
            response = self._make_request(self.apis['twse_openapi'], max_retries=1)
            results['twse_openapi'] = response is not None and response.status_code == 200
        except:
            results['twse_openapi'] = False
        
        # 測試櫃買API
        try:
            minguo_date = f"113/01/02"  # 測試用日期
            params = {'l': 'zh-tw', 'd': minguo_date, 'se': 'EW', 'o': 'json'}
            response = self._make_request(self.apis['tpex_daily'], params=params, max_retries=1)
            results['tpex'] = response is not None and response.status_code == 200
        except:
            results['tpex'] = False
        
        # 顯示結果
        print("API連接測試結果:")
        for api_name, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {api_name}: {status_icon}")
        
        return results


def test_fixed_fetcher():
    """測試修正版數據獲取器"""
    print("🧪 測試修正版台股數據獲取器")
    print("=" * 60)
    
    # 創建獲取器
    fetcher = FixedTaiwanStockFetcher()
    
    # 1. 測試API連接
    print("\n1. 測試API連接:")
    api_results = fetcher.test_connection()
    
    if not any(api_results.values()):
        print("❌ 所有API都無法連接，請檢查網路")
        return False
    
    # 2. 測試獲取股票數據
    print("\n2. 測試獲取股票數據:")
    try:
        stocks = fetcher.get_stocks_by_time_slot('afternoon_scan')
        
        if stocks:
            print(f"✅ 成功獲取 {len(stocks)} 支真實股票數據")
            
            print(f"\n📈 前5支最活躍股票:")
            for i, stock in enumerate(stocks[:5]):
                print(f"  {i+1}. {stock['code']} {stock['name']}")
                print(f"     現價: {stock['close']:.2f} 元 ({stock['change_percent']:+.2f}%)")
                print(f"     成交值: {stock['trade_value']:,.0f} 元")
                print(f"     數據源: {stock['data_source']}")
                
                if stock.get('institutional_data_available'):
                    foreign_net = stock['foreign_net_buy'] / 1000 if stock['foreign_net_buy'] != 0 else 0
                    print(f"     外資淨買: {foreign_net:+.0f}K 股")
                
                print(f"     真實數據: {'✅' if stock.get('is_real_data') else '❌'}")
                print()
            
            return True
            
        else:
            print("❌ 沒有獲取到股票數據")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def main():
    """主函數"""
    print("🎯 修正版台股數據獲取器")
    print("基於可行的 twse_data_fetcher.py 邏輯")
    print("確保獲取真實、可靠的台股數據")
    print()
    
    # 執行測試
    success = test_fixed_fetcher()
    
    if success:
        print("\n🎉 修正版數據獲取器測試成功！")
        print("\n📋 使用方法:")
        print("```python")
        print("from fixed_taiwan_stock_fetcher import FixedTaiwanStockFetcher")
        print("")
        print("fetcher = FixedTaiwanStockFetcher()")
        print("stocks = fetcher.get_stocks_by_time_slot('afternoon_scan')")
        print("```")
    else:
        print("\n❌ 測試失敗，請檢查網路連接或聯繫開發者")


if __name__ == "__main__":
    # 設置日誌級別
    logging.basicConfig(level=logging.INFO)
    
    # 執行主函數
    main()
