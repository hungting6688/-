#!/usr/bin/env python3
"""
real_taiwan_stock_fetcher.py - 真實台股數據獲取器
使用官方台灣證交所和櫃買中心API獲取真實股票數據
"""
import os
import json
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import logging
import pytz

class RealTaiwanStockFetcher:
    """真實台股數據獲取器 - 使用官方API"""
    
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
        
        # 官方API URLs
        self.apis = {
            # 證交所 OpenAPI (上市股票)
            'twse_openapi': 'https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL',
            'twse_daily': 'https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL',
            'twse_realtime': 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp',
            
            # 櫃買中心 (上櫃股票)
            'tpex_daily': 'https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php',
            
            # 法人買賣
            'twse_institutional': 'https://www.twse.com.tw/fund/T86',
            'tpex_institutional': 'https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php',
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
        self.max_retries = 3
        self.retry_delay = 2
        
        self.logger.info("真實台股數據獲取器初始化完成")
    
    def get_current_taiwan_time(self) -> datetime:
        """獲取當前台灣時間"""
        return datetime.now(self.taipei_tz)
    
    def get_trading_date(self, offset_days: int = 0) -> str:
        """獲取交易日期（跳過週末）"""
        now = self.get_current_taiwan_time()
        target_date = now + timedelta(days=offset_days)
        
        # 如果是週六或週日，回到最近的週五
        while target_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            target_date -= timedelta(days=1)
        
        return target_date.strftime('%Y%m%d')
    
    def _safe_float(self, value: Any) -> float:
        """安全轉換為浮點數"""
        if not value or value in ["--", "N/A", "除權息", "", "X", "-"]:
            return 0.0
        try:
            # 移除千分位逗號和空格
            cleaned = str(value).replace(",", "").replace(" ", "").strip()
            if cleaned == "" or cleaned == "--":
                return 0.0
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0
    
    def _safe_int(self, value: Any) -> int:
        """安全轉換為整數"""
        try:
            return int(self._safe_float(value))
        except:
            return 0
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """發出HTTP請求，帶重試機制"""
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"請求: {url} (嘗試 {attempt + 1}/{self.max_retries})")
                
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
                self.logger.warning(f"請求失敗 (嘗試 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def fetch_twse_stocks(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取證交所上市股票數據"""
        if date is None:
            date = self.get_trading_date()
        
        self.logger.info(f"獲取證交所上市股票數據 (日期: {date})")
        
        # 優先使用 OpenAPI
        stocks = self._fetch_twse_openapi()
        if stocks:
            self.logger.info(f"OpenAPI成功獲取 {len(stocks)} 支上市股票")
            return stocks
        
        # 回退到傳統API
        stocks = self._fetch_twse_traditional(date)
        if stocks:
            self.logger.info(f"傳統API成功獲取 {len(stocks)} 支上市股票")
            return stocks
        
        self.logger.error("所有上市股票API都無法獲取數據")
        return []
    
    def _fetch_twse_openapi(self) -> List[Dict[str, Any]]:
        """使用證交所OpenAPI獲取數據"""
        url = self.apis['twse_openapi']
        
        response = self._make_request(url)
        if not response:
            return []
        
        try:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                return self._parse_twse_openapi_data(data)
            else:
                self.logger.warning("OpenAPI返回數據格式異常")
                return []
                
        except Exception as e:
            self.logger.warning(f"解析OpenAPI數據失敗: {e}")
            return []
    
    def _parse_twse_openapi_data(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """解析證交所OpenAPI數據"""
        stocks = []
        
        for item in data:
            try:
                code = item.get('Code', '').strip()
                name = item.get('Name', '').strip()
                
                # 驗證股票代號
                if not code or not code.isdigit() or len(code) != 4:
                    continue
                
                # 獲取價格數據
                close_price = self._safe_float(item.get('ClosingPrice'))
                open_price = self._safe_float(item.get('OpeningPrice'))
                high_price = self._safe_float(item.get('HighestPrice'))
                low_price = self._safe_float(item.get('LowestPrice'))
                change = self._safe_float(item.get('Change'))
                
                # 獲取成交量數據
                volume = self._safe_int(item.get('TradeVolume'))
                trade_value = self._safe_int(item.get('TradeValue'))
                
                # 基本驗證
                if close_price <= 0 or volume <= 0:
                    continue
                
                # 計算漲跌幅
                if close_price > 0 and change != 0:
                    change_percent = (change / (close_price - change)) * 100
                else:
                    change_percent = 0
                
                stock_data = {
                    'code': code,
                    'name': name,
                    'market': 'TWSE',
                    'close': close_price,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'change': change,
                    'change_percent': round(change_percent, 2),
                    'volume': volume,
                    'trade_value': trade_value,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'data_source': 'TWSE_OpenAPI',
                    'is_real_data': True,
                    'fetch_time': self.get_current_taiwan_time().isoformat()
                }
                
                stocks.append(stock_data)
                
            except Exception as e:
                self.logger.debug(f"解析股票數據失敗: {e}")
                continue
        
        return stocks
    
    def _fetch_twse_traditional(self, date: str) -> List[Dict[str, Any]]:
        """使用證交所傳統API獲取數據"""
        url = self.apis['twse_daily']
        params = {
            'response': 'json',
            'date': date,
            'type': 'ALLBUT0999'
        }
        
        response = self._make_request(url, params=params)
        if not response:
            return []
        
        try:
            data = response.json()
            
            if data.get("stat") == "OK":
                return self._parse_twse_traditional_data(data, date)
            else:
                self.logger.warning(f"證交所API返回錯誤: {data.get('stat')}")
                return []
                
        except Exception as e:
            self.logger.warning(f"解析傳統API數據失敗: {e}")
            return []
    
    def _parse_twse_traditional_data(self, data: Dict, date: str) -> List[Dict[str, Any]]:
        """解析證交所傳統API數據"""
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
                    
                    # 獲取價格數據
                    close_price = self._safe_float(stock_dict.get("收盤價"))
                    open_price = self._safe_float(stock_dict.get("開盤價"))
                    high_price = self._safe_float(stock_dict.get("最高價"))
                    low_price = self._safe_float(stock_dict.get("最低價"))
                    change = self._safe_float(stock_dict.get("漲跌價差"))
                    
                    # 獲取成交量數據
                    volume = self._safe_int(stock_dict.get("成交股數"))
                    trade_value = self._safe_int(stock_dict.get("成交金額"))
                    
                    if close_price <= 0 or volume <= 0:
                        continue
                    
                    # 計算漲跌幅
                    change_percent = (change / close_price * 100) if close_price > 0 else 0
                    
                    stock_data = {
                        'code': code,
                        'name': name,
                        'market': 'TWSE',
                        'close': close_price,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'change': change,
                        'change_percent': round(change_percent, 2),
                        'volume': volume,
                        'trade_value': trade_value,
                        'date': datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'data_source': 'TWSE_Traditional_API',
                        'is_real_data': True,
                        'fetch_time': self.get_current_taiwan_time().isoformat()
                    }
                    
                    stocks.append(stock_data)
                    
                except Exception as e:
                    self.logger.debug(f"解析股票數據失敗: {e}")
                    continue
        
        return stocks
    
    def fetch_tpex_stocks(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取櫃買中心上櫃股票數據"""
        if date is None:
            date = self.get_trading_date()
        
        self.logger.info(f"獲取櫃買中心上櫃股票數據 (日期: {date})")
        
        try:
            # 轉換為民國年格式
            date_obj = datetime.strptime(date, '%Y%m%d')
            minguo_year = date_obj.year - 1911
            minguo_date = f"{minguo_year}/{date_obj.month:02d}/{date_obj.day:02d}"
            
            url = self.apis['tpex_daily']
            params = {
                'l': 'zh-tw',
                'd': minguo_date,
                'se': 'EW',
                'o': 'json'
            }
            
            response = self._make_request(url, params=params)
            if not response:
                return []
            
            data = response.json()
            
            if data.get("stat") == "OK":
                stocks = self._parse_tpex_data(data, date)
                self.logger.info(f"成功獲取 {len(stocks)} 支上櫃股票")
                return stocks
            else:
                self.logger.warning(f"櫃買中心API返回錯誤: {data.get('stat')}")
                return []
                
        except Exception as e:
            self.logger.error(f"獲取上櫃數據失敗: {e}")
            return []
    
    def _parse_tpex_data(self, data: Dict, date: str) -> List[Dict[str, Any]]:
        """解析櫃買中心數據"""
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
                    
                    # 獲取價格數據
                    close_price = self._safe_float(stock_dict.get("收盤"))
                    open_price = self._safe_float(stock_dict.get("開盤"))
                    high_price = self._safe_float(stock_dict.get("最高"))
                    low_price = self._safe_float(stock_dict.get("最低"))
                    change = self._safe_float(stock_dict.get("漲跌"))
                    
                    # 獲取成交量數據（櫃買中心單位可能不同）
                    volume = self._safe_int(stock_dict.get("成交量"))
                    
                    if close_price <= 0 or volume <= 0:
                        continue
                    
                    # 計算成交金額和漲跌幅
                    trade_value = volume * close_price
                    change_percent = (change / close_price * 100) if close_price > 0 else 0
                    
                    stock_data = {
                        'code': code,
                        'name': name,
                        'market': 'TPEX',
                        'close': close_price,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'change': change,
                        'change_percent': round(change_percent, 2),
                        'volume': volume,
                        'trade_value': int(trade_value),
                        'date': datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'data_source': 'TPEX_API',
                        'is_real_data': True,
                        'fetch_time': self.get_current_taiwan_time().isoformat()
                    }
                    
                    stocks.append(stock_data)
                    
                except Exception as e:
                    self.logger.debug(f"解析上櫃股票數據失敗: {e}")
                    continue
        
        return stocks
    
    def fetch_institutional_data(self, date: str = None) -> Dict[str, Dict[str, Any]]:
        """獲取法人買賣數據"""
        if date is None:
            date = self.get_trading_date()
        
        self.logger.info(f"獲取法人買賣數據 (日期: {date})")
        
        institutional_data = {}
        
        # 獲取證交所法人數據
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
                    self.logger.info(f"獲取到 {len(institutional_data)} 支股票的法人數據")
                    
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
                    
                    # 法人買賣數據（單位：千股）
                    foreign_buy = self._safe_int(row_dict.get("外陸資買進股數(不含外資自營商)", "0"))
                    foreign_sell = self._safe_int(row_dict.get("外陸資賣出股數(不含外資自營商)", "0"))
                    trust_buy = self._safe_int(row_dict.get("投信買進股數", "0"))
                    trust_sell = self._safe_int(row_dict.get("投信賣出股數", "0"))
                    dealer_buy = self._safe_int(row_dict.get("自營商買進股數(自行買賣)", "0"))
                    dealer_sell = self._safe_int(row_dict.get("自營商賣出股數(自行買賣)", "0"))
                    
                    # 計算淨買超（單位：千股）
                    foreign_net = foreign_buy - foreign_sell
                    trust_net = trust_buy - trust_sell
                    dealer_net = dealer_buy - dealer_sell
                    total_net = foreign_net + trust_net + dealer_net
                    
                    institutional_data[code] = {
                        'foreign_net_buy': foreign_net,
                        'trust_net_buy': trust_net,
                        'dealer_net_buy': dealer_net,
                        'total_net_buy': total_net,
                        'foreign_buy': foreign_buy,
                        'foreign_sell': foreign_sell,
                        'trust_buy': trust_buy,
                        'trust_sell': trust_sell,
                        'dealer_buy': dealer_buy,
                        'dealer_sell': dealer_sell,
                        'institutional_data_available': True
                    }
                    
                except Exception as e:
                    self.logger.debug(f"解析法人數據失敗: {e}")
                    continue
        
        return institutional_data
    
    def get_all_stocks_by_volume(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取所有股票並按成交金額排序"""
        self.logger.info("開始獲取所有台股數據")
        
        all_stocks = []
        
        # 獲取上市股票
        twse_stocks = self.fetch_twse_stocks(date)
        if twse_stocks:
            all_stocks.extend(twse_stocks)
            self.logger.info(f"獲取 {len(twse_stocks)} 支上市股票")
            time.sleep(1)  # 避免請求過於頻繁
        
        # 獲取上櫃股票
        tpex_stocks = self.fetch_tpex_stocks(date)
        if tpex_stocks:
            all_stocks.extend(tpex_stocks)
            self.logger.info(f"獲取 {len(tpex_stocks)} 支上櫃股票")
        
        if not all_stocks:
            self.logger.error("無法獲取任何股票數據")
            return []
        
        # 過濾有效數據
        valid_stocks = [
            stock for stock in all_stocks 
            if stock.get('trade_value', 0) > 0 and stock.get('close', 0) > 0
        ]
        
        # 按成交金額排序
        sorted_stocks = sorted(valid_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)
        
        # 獲取法人數據並整合
        institutional_data = self.fetch_institutional_data(date)
        
        for stock in sorted_stocks:
            code = stock['code']
            if code in institutional_data:
                stock.update(institutional_data[code])
            else:
                # 添加空的法人數據
                stock.update({
                    'foreign_net_buy': 0,
                    'trust_net_buy': 0,
                    'dealer_net_buy': 0,
                    'total_net_buy': 0,
                    'institutional_data_available': False
                })
        
        self.logger.info(f"成功獲取並排序 {len(sorted_stocks)} 支股票")
        
        return sorted_stocks
    
    def get_stocks_by_time_slot(self, time_slot: str, date: str = None, force_fresh: bool = False) -> List[Dict[str, Any]]:
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
                raise Exception("無法獲取任何真實股票數據")
            
            # 返回前N支股票
            selected_stocks = all_stocks[:limit]
            
            # 添加時段資訊和數據品質標記
            for stock in selected_stocks:
                stock['time_slot'] = time_slot
                stock['data_quality'] = 'real_verified'
                stock['is_simulation'] = False
                stock['data_freshness'] = 'current_day'
            
            self.logger.info(f"為 {time_slot} 時段成功選擇了 {len(selected_stocks)} 支真實股票")
            
            # 顯示數據品質統計
            real_data_count = sum(1 for stock in selected_stocks if stock.get('is_real_data', False))
            institutional_data_count = sum(1 for stock in selected_stocks if stock.get('institutional_data_available', False))
            
            self.logger.info(f"數據品質統計: 真實數據 {real_data_count}/{len(selected_stocks)}, 法人數據 {institutional_data_count}/{len(selected_stocks)}")
            
            return selected_stocks
            
        except Exception as e:
            self.logger.error(f"獲取 {time_slot} 真實數據失敗: {e}")
            raise Exception(f"無法獲取 {time_slot} 的真實股票數據: {e}")
    
    def test_all_apis(self) -> Dict[str, bool]:
        """測試所有API連接"""
        self.logger.info("測試所有API連接...")
        
        results = {}
        
        # 測試證交所OpenAPI
        try:
            response = self._make_request(self.apis['twse_openapi'])
            results['twse_openapi'] = response is not None and response.status_code == 200
            if results['twse_openapi']:
                self.logger.info("✅ 證交所OpenAPI連接正常")
            else:
                self.logger.warning("❌ 證交所OpenAPI連接失敗")
        except Exception as e:
            results['twse_openapi'] = False
            self.logger.warning(f"❌ 證交所OpenAPI測試異常: {e}")
        
        # 測試證交所傳統API
        try:
            date = self.get_trading_date()
            params = {'response': 'json', 'date': date, 'type': 'ALLBUT0999'}
            response = self._make_request(self.apis['twse_daily'], params=params)
            results['twse_traditional'] = response is not None and response.status_code == 200
            if results['twse_traditional']:
                self.logger.info("✅ 證交所傳統API連接正常")
            else:
                self.logger.warning("❌ 證交所傳統API連接失敗")
        except Exception as e:
            results['twse_traditional'] = False
            self.logger.warning(f"❌ 證交所傳統API測試異常: {e}")
        
        # 測試櫃買中心API
        try:
            now = self.get_current_taiwan_time()
            minguo_year = now.year - 1911
            minguo_date = f"{minguo_year}/{now.month:02d}/{now.day:02d}"
            params = {'l': 'zh-tw', 'd': minguo_date, 'se': 'EW', 'o': 'json'}
            response = self._make_request(self.apis['tpex_daily'], params=params)
            results['tpex'] = response is not None and response.status_code == 200
            if results['tpex']:
                self.logger.info("✅ 櫃買中心API連接正常")
            else:
                self.logger.warning("❌ 櫃買中心API連接失敗")
        except Exception as e:
            results['tpex'] = False
            self.logger.warning(f"❌ 櫃買中心API測試異常: {e}")
        
        # 顯示總結
        working_apis = sum(1 for status in results.values() if status)
        total_apis = len(results)
        
        if working_apis > 0:
            self.logger.info(f"🎉 API連接測試完成: {working_apis}/{total_apis} 個API可用")
        else:
            self.logger.error("❌ 所有API都無法連接，請檢查網路連接")
        
        return results
    
    def get_market_summary(self) -> Dict[str, Any]:
        """獲取市場總體狀況"""
        try:
            all_stocks = self.get_all_stocks_by_volume()
            
            if not all_stocks:
                return {}
            
            # 計算市場統計
            total_stocks = len(all_stocks)
            up_stocks = sum(1 for stock in all_stocks if stock.get('change_percent', 0) > 0)
            down_stocks = sum(1 for stock in all_stocks if stock.get('change_percent', 0) < 0)
            unchanged_stocks = total_stocks - up_stocks - down_stocks
            
            # 成交金額統計
            total_value = sum(stock.get('trade_value', 0) for stock in all_stocks)
            
            # 找出表現最好和最差的股票
            top_gainers = sorted(all_stocks, key=lambda x: x.get('change_percent', 0), reverse=True)[:5]
            top_losers = sorted(all_stocks, key=lambda x: x.get('change_percent', 0))[:5]
            most_active = sorted(all_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)[:5]
            
            return {
                'total_stocks': total_stocks,
                'up_stocks': up_stocks,
                'down_stocks': down_stocks,
                'unchanged_stocks': unchanged_stocks,
                'total_value': total_value,
                'top_gainers': top_gainers,
                'top_losers': top_losers,
                'most_active': most_active,
                'update_time': self.get_current_taiwan_time().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"獲取市場總體狀況失敗: {e}")
            return {}


def test_real_fetcher():
    """測試真實數據獲取器"""
    print("🧪 測試真實台股數據獲取器")
    print("=" * 60)
    
    # 創建獲取器
    fetcher = RealTaiwanStockFetcher()
    
    # 1. 測試API連接
    print("\n1. 測試API連接:")
    api_results = fetcher.test_all_apis()
    
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
                print(f"     市場: {stock['market']}")
                
                if stock.get('institutional_data_available'):
                    foreign_net = stock['foreign_net_buy']
                    print(f"     外資淨買: {foreign_net:+,} 千股")
                
                print(f"     真實數據: {'✅' if stock.get('is_real_data') else '❌'}")
                print()
            
            # 3. 測試市場總體狀況
            print("\n3. 測試市場總體狀況:")
            market_summary = fetcher.get_market_summary()
            if market_summary:
                print(f"📊 市場統計:")
                print(f"   總股票數: {market_summary['total_stocks']:,}")
                print(f"   上漲: {market_summary['up_stocks']:,}")
                print(f"   下跌: {market_summary['down_stocks']:,}")
                print(f"   平盤: {market_summary['unchanged_stocks']:,}")
                print(f"   總成交值: {market_summary['total_value']:,.0f} 元")
            
            return True
            
        else:
            print("❌ 沒有獲取到股票數據")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def main():
    """主函數"""
    print("🎯 真實台股數據獲取器")
    print("使用官方台灣證交所和櫃買中心API")
    print("確保獲取真實、可靠的台股數據")
    print()
    
    # 執行測試
    success = test_real_fetcher()
    
    if success:
        print("\n🎉 真實數據獲取器測試成功！")
        print("\n📋 使用方法:")
        print("```python")
        print("from real_taiwan_stock_fetcher import RealTaiwanStockFetcher")
        print("")
        print("fetcher = RealTaiwanStockFetcher()")
        print("stocks = fetcher.get_stocks_by_time_slot('afternoon_scan')")
        print("```")
        print("\n💡 特色功能:")
        print("✅ 使用官方API獲取真實數據")
        print("✅ 同時支援上市和上櫃股票")
        print("✅ 包含法人買賣數據")
        print("✅ 自動重試和錯誤處理")
        print("✅ 數據品質驗證和標記")
        print("✅ 完整的市場統計功能")
    else:
        print("\n❌ 測試失敗，請檢查網路連接")


if __name__ == "__main__":
    # 設置日誌級別
    logging.basicConfig(level=logging.INFO)
    
    # 執行主函數
    main()
