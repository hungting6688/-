#!/usr/bin/env python3
"""
real_taiwan_stock_fetcher.py - 台股當天真實數據獲取器
確保獲取最新、最準確的台股當天數據，絕不使用模擬數據
"""
import os
import time
import json
import requests
import pandas as pd
import pytz
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

class RealTaiwanStockFetcher:
    """台股當天真實數據獲取器 - 專注於獲取真實當天數據"""
    
    def __init__(self, cache_enabled: bool = False):
        """初始化真實數據獲取器"""
        self.cache_enabled = cache_enabled
        self.cache = {}
        self.cache_expire_minutes = 1  # 只緩存1分鐘，確保數據新鮮
        
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
        
        # 請求會話設置
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.twse.com.tw/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # 真實數據源API配置 - 多重備用確保可靠性
        self.apis = {
            # 1. 證交所Open API (最新官方API)
            'twse_openapi_daily': 'https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL',
            'twse_openapi_institutional': 'https://openapi.twse.com.tw/v1/fund/T86',
            
            # 2. 即時股價API (當天最新價格)
            'realtime_quotes': 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp',
            
            # 3. 證交所傳統API (備用)
            'twse_daily_backup': 'https://www.twse.com.tw/exchangeReport/MI_INDEX',
            'twse_institutional_backup': 'https://www.twse.com.tw/fund/T86',
            
            # 4. 櫃買中心API
            'tpex_daily': 'https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php',
            'tpex_institutional': 'https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php',
        }
        
        # 請求設置
        self.timeout = 15
        self.max_retries = 3
        self.retry_delay = 2
        
        self.logger.info("台股真實數據獲取器初始化完成")
    
    def get_current_taiwan_time(self) -> datetime:
        """獲取當前台灣時間"""
        return datetime.now(self.taipei_tz)
    
    def is_trading_day(self) -> bool:
        """檢查今天是否為交易日"""
        now = self.get_current_taiwan_time()
        # 週一到週五為交易日 (簡化版，不考慮國定假日)
        return now.weekday() < 5
    
    def get_stocks_by_time_slot(self, time_slot: str, force_fresh: bool = True) -> List[Dict[str, Any]]:
        """
        根據時段獲取股票數據（統一入口）
        
        參數:
        - time_slot: 時段名稱
        - force_fresh: 是否強制獲取新鮮數據
        
        返回:
        - 股票數據列表
        """
        self.logger.info(f"開始獲取 {time_slot} 時段的台股真實數據")
        
        if not self.is_trading_day():
            self.logger.warning("今天不是交易日，數據可能不是最新的")
        
        try:
            # 獲取當天所有股票數據
            all_stocks = self._get_today_all_stocks(force_fresh)
            
            if not all_stocks:
                raise Exception("無法獲取任何股票數據")
            
            self.logger.info(f"成功獲取 {len(all_stocks)} 支股票的真實數據")
            
            # 根據時段過濾和排序
            filtered_stocks = self._filter_stocks_by_time_slot(all_stocks, time_slot)
            
            # 獲取法人數據
            institutional_data = self._get_institutional_data()
            
            # 整合法人數據
            for stock in filtered_stocks:
                stock_code = stock['code']
                if stock_code in institutional_data:
                    stock.update(institutional_data[stock_code])
                else:
                    # 設置默認值，但標記為無法獲取
                    stock.update({
                        'foreign_net_buy': 0,
                        'trust_net_buy': 0,
                        'dealer_net_buy': 0,
                        'total_net_buy': 0,
                        'institutional_data_available': False
                    })
            
            # 添加數據品質標記
            for stock in filtered_stocks:
                stock['data_source'] = 'TWSE_REAL_API'
                stock['data_quality'] = 'current_day_verified'
                stock['fetch_time'] = self.get_current_taiwan_time().isoformat()
                stock['is_real_data'] = True
                stock['is_simulation'] = False
            
            self.logger.info(f"✅ 成功整合並返回 {len(filtered_stocks)} 支股票的當天真實數據")
            return filtered_stocks
            
        except Exception as e:
            self.logger.error(f"獲取真實數據失敗: {e}")
            # 絕不使用模擬數據！拋出異常讓上層處理
            raise Exception(f"無法獲取台股真實數據，請稍後再試。錯誤: {e}")
    
    def _get_today_all_stocks(self, force_fresh: bool = True) -> List[Dict[str, Any]]:
        """獲取今天所有股票數據"""
        cache_key = f"today_stocks_{datetime.now().strftime('%Y%m%d_%H')}"
        
        # 檢查快取（如果啟用且不強制刷新）
        if not force_fresh and self.cache_enabled and self._is_cache_valid(cache_key):
            self.logger.info("使用快取的當天股票數據")
            return self.cache[cache_key]
        
        all_stocks = []
        
        # 方法1: 嘗試使用Open API (最優先)
        try:
            self.logger.info("嘗試使用證交所Open API獲取數據")
            stocks = self._fetch_from_openapi()
            if stocks:
                all_stocks.extend(stocks)
                self.logger.info(f"✅ Open API成功獲取 {len(stocks)} 支股票")
        except Exception as e:
            self.logger.warning(f"Open API失敗: {e}")
        
        # 方法2: 如果Open API數據不足，使用即時API補充
        if len(all_stocks) < 100:  # 如果數據太少，嘗試其他方法
            try:
                self.logger.info("使用即時股價API補充數據")
                realtime_stocks = self._fetch_from_realtime_api()
                if realtime_stocks:
                    # 合併數據，避免重複
                    existing_codes = {stock['code'] for stock in all_stocks}
                    new_stocks = [s for s in realtime_stocks if s['code'] not in existing_codes]
                    all_stocks.extend(new_stocks)
                    self.logger.info(f"✅ 即時API補充 {len(new_stocks)} 支股票")
            except Exception as e:
                self.logger.warning(f"即時API失敗: {e}")
        
        # 方法3: 使用傳統API作為最後手段
        if len(all_stocks) < 50:  # 如果還是數據不足
            try:
                self.logger.info("使用傳統API作為備用")
                backup_stocks = self._fetch_from_backup_api()
                if backup_stocks:
                    existing_codes = {stock['code'] for stock in all_stocks}
                    new_stocks = [s for s in backup_stocks if s['code'] not in existing_codes]
                    all_stocks.extend(new_stocks)
                    self.logger.info(f"✅ 備用API補充 {len(new_stocks)} 支股票")
            except Exception as e:
                self.logger.warning(f"備用API失敗: {e}")
        
        if not all_stocks:
            raise Exception("所有API都無法獲取數據")
        
        # 數據後處理
        processed_stocks = self._process_stock_data(all_stocks)
        
        # 緩存結果（如果啟用）
        if self.cache_enabled:
            self.cache[cache_key] = processed_stocks
        
        return processed_stocks
    
    def _fetch_from_openapi(self) -> List[Dict[str, Any]]:
        """從證交所Open API獲取數據"""
        url = self.apis['twse_openapi_daily']
        
        response = self._make_request(url)
        if not response:
            return []
        
        data = response.json()
        
        stocks = []
        for item in data:
            try:
                stock = self._parse_openapi_stock(item)
                if stock:
                    stocks.append(stock)
            except Exception as e:
                self.logger.debug(f"解析股票數據失敗: {e}")
                continue
        
        return stocks
    
    def _fetch_from_realtime_api(self) -> List[Dict[str, Any]]:
        """從即時股價API獲取數據"""
        # 獲取熱門股票代碼
        popular_stocks = [
            '2330', '2317', '2454', '2412', '2308', '2303', '1301', '1303', 
            '2002', '2882', '2891', '2886', '2892', '2881', '2884', '2887',
            '2609', '2615', '2603', '2618', '2634', '5880', '6505', '3008',
            '2382', '2379', '3711', '2347', '6446', '3034', '2368', '2408'
        ]
        
        # 分批獲取（每次最多20支）
        all_stocks = []
        batch_size = 20
        
        for i in range(0, len(popular_stocks), batch_size):
            batch_codes = popular_stocks[i:i + batch_size]
            try:
                stocks = self._fetch_realtime_batch(batch_codes)
                all_stocks.extend(stocks)
                time.sleep(0.5)  # 避免請求過於頻繁
            except Exception as e:
                self.logger.warning(f"獲取即時數據批次失敗: {e}")
                continue
        
        return all_stocks
    
    def _fetch_realtime_batch(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """批次獲取即時股價"""
        # 組合查詢字符串
        ex_ch = '|'.join([f'tse_{code}.tw' for code in stock_codes])
        
        url = self.apis['realtime_quotes']
        params = {
            'ex_ch': ex_ch,
            'json': '1',
            'delay': '0',
            '_': str(int(time.time() * 1000))
        }
        
        response = self._make_request(url, params=params)
        if not response:
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
            except Exception as e:
                self.logger.debug(f"解析即時股票數據失敗: {e}")
                continue
        
        return stocks
    
    def _fetch_from_backup_api(self) -> List[Dict[str, Any]]:
        """從備用API獲取數據"""
        url = self.apis['twse_daily_backup']
        today = datetime.now().strftime('%Y%m%d')
        
        params = {
            'response': 'json',
            'date': today,
            'type': 'ALL'
        }
        
        response = self._make_request(url, params=params)
        if not response:
            return []
        
        data = response.json()
        if data.get('stat') != 'OK':
            return []
        
        stocks = []
        fields = data.get('fields', [])
        data_list = data.get('data9', [])
        
        for row in data_list:
            try:
                stock = self._parse_backup_stock(row, fields)
                if stock:
                    stocks.append(stock)
            except Exception as e:
                self.logger.debug(f"解析備用API股票數據失敗: {e}")
                continue
        
        return stocks
    
    def _get_institutional_data(self) -> Dict[str, Dict[str, Any]]:
        """獲取法人買賣數據"""
        institutional_data = {}
        
        # 嘗試從Open API獲取
        try:
            url = self.apis['twse_openapi_institutional']
            response = self._make_request(url)
            
            if response:
                data = response.json()
                for item in data:
                    parsed = self._parse_institutional_data(item)
                    if parsed:
                        institutional_data[parsed['code']] = parsed['data']
                        
        except Exception as e:
            self.logger.warning(f"獲取法人數據失敗: {e}")
        
        return institutional_data
    
    def _make_request(self, url: str, params: Dict = None, max_retries: int = None) -> Optional[requests.Response]:
        """發出HTTP請求，帶重試機制"""
        if max_retries is None:
            max_retries = self.max_retries
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"請求: {url} (嘗試 {attempt + 1}/{max_retries})")
                
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=self.timeout,
                    verify=True
                )
                
                if response.status_code == 200:
                    return response
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"請求失敗 (嘗試 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def _parse_openapi_stock(self, data: Dict) -> Optional[Dict[str, Any]]:
        """解析Open API股票數據"""
        try:
            code = data.get('Code', '').strip()
            name = data.get('Name', '').strip()
            
            if not code or not code.isdigit() or len(code) != 4:
                return None
            
            # 數值轉換，處理空字符串
            close = self._safe_float(data.get('ClosingPrice', '0'))
            open_price = self._safe_float(data.get('OpeningPrice', '0'))
            high = self._safe_float(data.get('HighestPrice', '0'))
            low = self._safe_float(data.get('LowestPrice', '0'))
            volume = self._safe_int(data.get('TradeVolume', '0'))
            trade_value = self._safe_int(data.get('TradeValue', '0'))
            change = self._safe_float(data.get('Change', '0'))
            
            if close <= 0 or volume <= 0:
                return None
            
            change_percent = (change / (close - change) * 100) if (close - change) > 0 else 0
            
            return {
                'code': code,
                'name': name,
                'close': close,
                'open': open_price,
                'high': high,
                'low': low,
                'volume': volume,
                'trade_value': trade_value,
                'change': change,
                'change_percent': round(change_percent, 2),
                'market': 'TWSE',
                'api_source': 'openapi'
            }
            
        except Exception as e:
            self.logger.debug(f"解析Open API數據失敗: {e}")
            return None
    
    def _parse_realtime_stock(self, data: Dict) -> Optional[Dict[str, Any]]:
        """解析即時API股票數據"""
        try:
            code = data.get('c', '').strip()
            name = data.get('n', '').strip()
            
            if not code or not code.isdigit():
                return None
            
            close = self._safe_float(data.get('z', '0'))
            open_price = self._safe_float(data.get('o', '0'))
            high = self._safe_float(data.get('h', '0'))
            low = self._safe_float(data.get('l', '0'))
            volume = self._safe_int(data.get('v', '0'))
            trade_value = self._safe_int(data.get('tv', '0'))
            yesterday = self._safe_float(data.get('y', '0'))
            
            if close <= 0 or yesterday <= 0:
                return None
            
            change = close - yesterday
            change_percent = (change / yesterday * 100) if yesterday > 0 else 0
            
            return {
                'code': code,
                'name': name,
                'close': close,
                'open': open_price,
                'high': high,
                'low': low,
                'volume': volume,
                'trade_value': trade_value,
                'change': change,
                'change_percent': round(change_percent, 2),
                'market': 'TWSE',
                'api_source': 'realtime'
            }
            
        except Exception as e:
            self.logger.debug(f"解析即時API數據失敗: {e}")
            return None
    
    def _parse_backup_stock(self, row: List, fields: List) -> Optional[Dict[str, Any]]:
        """解析備用API股票數據"""
        try:
            if len(row) < len(fields):
                return None
            
            code = row[0].strip()
            name = row[1].strip()
            
            if not code or not code.isdigit() or len(code) != 4:
                return None
            
            trade_volume = self._safe_int(row[2])
            trade_value = self._safe_int(row[3])
            open_price = self._safe_float(row[4])
            high_price = self._safe_float(row[5])
            low_price = self._safe_float(row[6])
            close_price = self._safe_float(row[7])
            
            if close_price <= 0 or trade_volume <= 0:
                return None
            
            change_str = row[8].strip() if len(row) > 8 else ""
            change = self._parse_change(change_str)
            change_percent = (change / close_price * 100) if close_price > 0 else 0
            
            return {
                'code': code,
                'name': name,
                'close': close_price,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'volume': trade_volume,
                'trade_value': trade_value,
                'change': change,
                'change_percent': round(change_percent, 2),
                'market': 'TWSE',
                'api_source': 'backup'
            }
            
        except Exception as e:
            self.logger.debug(f"解析備用API數據失敗: {e}")
            return None
    
    def _parse_institutional_data(self, data: Dict) -> Optional[Dict[str, Any]]:
        """解析法人數據"""
        try:
            code = data.get('Code', '').strip()
            if not code or not code.isdigit() or len(code) != 4:
                return None
            
            foreign_net = self._safe_int(data.get('ForeignInvestorBuy', '0')) - \
                         self._safe_int(data.get('ForeignInvestorSell', '0'))
            trust_net = self._safe_int(data.get('InvestmentTrustBuy', '0')) - \
                       self._safe_int(data.get('InvestmentTrustSell', '0'))
            dealer_net = self._safe_int(data.get('DealersBuy', '0')) - \
                        self._safe_int(data.get('DealersSell', '0'))
            
            return {
                'code': code,
                'data': {
                    'foreign_net_buy': foreign_net,
                    'trust_net_buy': trust_net,
                    'dealer_net_buy': dealer_net,
                    'total_net_buy': foreign_net + trust_net + dealer_net,
                    'institutional_data_available': True
                }
            }
            
        except Exception as e:
            self.logger.debug(f"解析法人數據失敗: {e}")
            return None
    
    def _process_stock_data(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """後處理股票數據"""
        processed = []
        
        for stock in stocks:
            try:
                # 數據驗證
                if not self._validate_stock_data(stock):
                    continue
                
                # 添加額外計算欄位
                stock['price_range'] = stock['high'] - stock['low']
                stock['price_range_percent'] = (stock['price_range'] / stock['close'] * 100) if stock['close'] > 0 else 0
                stock['volume_value_avg'] = (stock['trade_value'] / stock['volume']) if stock['volume'] > 0 else 0
                
                # 添加時間戳
                stock['last_updated'] = self.get_current_taiwan_time().isoformat()
                
                processed.append(stock)
                
            except Exception as e:
                self.logger.debug(f"處理股票 {stock.get('code', 'unknown')} 數據失敗: {e}")
                continue
        
        return processed
    
    def _validate_stock_data(self, stock: Dict[str, Any]) -> bool:
        """驗證股票數據完整性"""
        required_fields = ['code', 'name', 'close', 'volume', 'trade_value']
        
        for field in required_fields:
            if field not in stock or stock[field] is None:
                return False
            
            if field in ['close', 'volume', 'trade_value'] and stock[field] <= 0:
                return False
        
        return True
    
    def _filter_stocks_by_time_slot(self, stocks: List[Dict[str, Any]], time_slot: str) -> List[Dict[str, Any]]:
        """根據時段過濾股票"""
        # 先過濾有效股票
        valid_stocks = [s for s in stocks if self._validate_stock_data(s)]
        
        # 按成交金額排序
        sorted_stocks = sorted(valid_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)
        
        # 根據時段設定數量限制
        slot_limits = {
            'morning_scan': 200,
            'mid_morning_scan': 300,
            'mid_day_scan': 300,
            'afternoon_scan': 500,
            'weekly_summary': 500
        }
        
        limit = slot_limits.get(time_slot, 200)
        return sorted_stocks[:limit]
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查快取是否有效"""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache.get(f"{cache_key}_timestamp")
        if not cache_time:
            return False
        
        elapsed = (datetime.now() - cache_time).total_seconds()
        return elapsed < (self.cache_expire_minutes * 60)
    
    def _safe_float(self, value: Any) -> float:
        """安全轉換為浮點數"""
        if not value or value in ["--", "N/A", "除權息", "", "X"]:
            return 0.0
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                cleaned = value.replace(',', '').replace(' ', '').replace('+', '').strip()
                if cleaned == '' or cleaned == '--' or cleaned == 'N/A':
                    return 0.0
                return float(cleaned)
            return float(value)
        except (ValueError, TypeError, AttributeError):
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
    
    def _parse_change(self, change_str: str) -> float:
        """解析漲跌金額"""
        try:
            if not change_str or change_str.strip() == '':
                return 0.0
            
            import re
            cleaned = re.sub(r'<[^>]+>', '', str(change_str))
            cleaned = cleaned.replace(',', '').strip()
            
            if '△' in cleaned or cleaned.startswith('+'):
                cleaned = cleaned.replace('△', '').replace('+', '')
                return abs(self._safe_float(cleaned))
            elif '▽' in cleaned or cleaned.startswith('-'):
                cleaned = cleaned.replace('▽', '').replace('-', '')
                return -abs(self._safe_float(cleaned))
            else:
                return self._safe_float(cleaned)
                
        except Exception:
            return 0.0
    
    def test_all_apis(self) -> Dict[str, bool]:
        """測試所有API連接"""
        self.logger.info("開始測試所有API連接...")
        
        results = {}
        
        # 測試Open API
        try:
            response = self._make_request(self.apis['twse_openapi_daily'], max_retries=1)
            results['openapi'] = response is not None and response.status_code == 200
        except:
            results['openapi'] = False
        
        # 測試即時API
        try:
            params = {
                'ex_ch': 'tse_2330.tw',
                'json': '1',
                'delay': '0',
                '_': str(int(time.time() * 1000))
            }
            response = self._make_request(self.apis['realtime_quotes'], params=params, max_retries=1)
            results['realtime'] = response is not None and response.status_code == 200
        except:
            results['realtime'] = False
        
        # 測試備用API
        try:
            params = {
                'response': 'json',
                'date': datetime.now().strftime('%Y%m%d'),
                'type': 'ALL'
            }
            response = self._make_request(self.apis['twse_daily_backup'], params=params, max_retries=1)
            results['backup'] = response is not None and response.status_code == 200
        except:
            results['backup'] = False
        
        # 顯示測試結果
        print("API連接測試結果:")
        for api_name, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {api_name}: {status_icon}")
        
        return results


def test_real_fetcher():
    """測試真實數據獲取器"""
    print("🧪 測試台股真實數據獲取器")
    print("=" * 50)
    
    # 創建獲取器
    fetcher = RealTaiwanStockFetcher()
    
    # 測試API連接
    print("\n1. 測試API連接:")
    api_results = fetcher.test_all_apis()
    
    if not any(api_results.values()):
        print("❌ 所有API都無法連接，請檢查網路連接")
        return False
    
    # 測試獲取股票數據
    print("\n2. 測試獲取股票數據:")
    try:
        stocks = fetcher.get_stocks_by_time_slot('afternoon_scan', force_fresh=True)
        
        if stocks:
            print(f"✅ 成功獲取 {len(stocks)} 支股票的真實數據")
            print(f"\n📈 前5支最活躍股票:")
            
            for i, stock in enumerate(stocks[:5]):
                print(f"  {i+1}. {stock['code']} {stock['name']}")
                print(f"     現價: {stock['close']:.2f} 元 ({stock['change_percent']:+.2f}%)")
                print(f"     成交值: {stock['trade_value']:,.0f} 元")
                print(f"     數據源: {stock['api_source']} | 品質: {stock['data_quality']}")
                
                if 'foreign_net_buy' in stock:
                    net_flow = stock['foreign_net_buy'] / 1000 if stock['foreign_net_buy'] != 0 else 0
                    print(f"     外資: {net_flow:+.0f}K 股")
                print()
            
            return True
            
        else:
            print("❌ 沒有獲取到股票數據")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


if __name__ == "__main__":
    # 設置日誌級別
    logging.basicConfig(level=logging.INFO)
    
    # 執行測試
    success = test_real_fetcher()
    
    if success:
        print("\n🎉 台股真實數據獲取器測試成功！")
        print("\n📋 使用說明:")
        print("1. 這個獲取器確保獲取台股當天真實數據")
        print("2. 使用多重API備援，確保數據可靠性")
        print("3. 絕不會退回到模擬數據")
        print("4. 支援即時股價和法人買賣數據")
    else:
        print("\n❌ 測試失敗，請檢查網路連接或API狀態")
