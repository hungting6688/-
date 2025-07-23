#!/usr/bin/env python3
"""
integrated_twse_data_fetcher.py - 整合版台股數據獲取器
結合多個數據源和功能的完整台股數據抓取系統
"""
import os
import json
import time
import requests
import pandas as pd
import pytz
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from urllib.parse import quote
import hashlib
import re

# 可選的異步支援檢測
try:
    import aiohttp
    import asyncio
    ASYNC_SUPPORT = True
    print("✅ 異步支援已啟用")
except ImportError:
    ASYNC_SUPPORT = False
    print("⚠️ 異步支援未啟用，將使用同步模式")
    
    # 模擬類別以避免導入錯誤
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

class IntegratedTWSEDataFetcher:
    """整合版台股數據獲取器"""
    
    def __init__(self, cache_dir: str = 'cache/stock_data'):
        """初始化數據獲取器"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 台灣時區
        self.taipei_tz = pytz.timezone('Asia/Taipei')
        
        # 設置日誌
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 請求會話設置
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.twse.com.tw/',
        })
        
        # 數據源配置
        self.apis = {
            'twse_daily': 'https://www.twse.com.tw/exchangeReport/MI_INDEX',
            'twse_all': 'https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL',
            'tpex_daily': 'https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php',
            'institutional': 'https://www.twse.com.tw/fund/T86',
        }
        
        # 快取設定
        self.cache_expire_hours = 1  # 1小時過期
        
        # 請求限制
        self.request_delay = 0.5  # 每次請求間隔0.5秒
        self.last_request_time = 0
        self.timeout = 30
        self.max_fallback_days = 5
    
    def get_current_taiwan_time(self) -> datetime:
        """獲取當前台灣時間"""
        return datetime.now(self.taipei_tz)
    
    def get_optimal_data_date(self) -> str:
        """獲取最佳的數據日期"""
        now = self.get_current_taiwan_time()
        
        # 判斷最佳的數據日期
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
    
    def _rate_limit(self):
        """請求頻率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_path(self, cache_key: str, date: str = None) -> str:
        """獲取快取文件路徑"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        return os.path.join(self.cache_dir, f"{cache_key}_{date}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """檢查快取是否有效"""
        if not os.path.exists(cache_path):
            return False
        
        file_time = os.path.getmtime(cache_path)
        current_time = time.time()
        
        return (current_time - file_time) < (self.cache_expire_hours * 3600)
    
    def _load_cache(self, cache_path: str) -> Optional[Any]:
        """載入快取數據"""
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"載入快取失敗: {e}")
            return None
    
    def _save_cache(self, cache_path: str, data: Any):
        """保存快取數據"""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"快取已保存: {cache_path}")
        except Exception as e:
            self.logger.warning(f"保存快取失敗: {e}")
    
    def _safe_float(self, value: Any) -> float:
        """安全轉換為浮點數"""
        if not value or value in ["--", "N/A", "除權息", "", "X"]:
            return 0.0
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # 處理逗號分隔的數字和特殊符號
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
            
            # 移除HTML標籤和特殊字符
            cleaned = re.sub(r'<[^>]+>', '', str(change_str))
            cleaned = cleaned.replace(',', '').strip()
            
            # 處理特殊符號
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
    
    def fetch_twse_data(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取證交所數據（多種方式嘗試）"""
        if date is None:
            date = self.get_optimal_data_date()
        
        # 檢查快取
        cache_path = self._get_cache_path('twse_market', date)
        if self._is_cache_valid(cache_path):
            cached_data = self._load_cache(cache_path)
            if cached_data:
                self.logger.info(f"使用快取的TWSE數據: {len(cached_data)} 支股票")
                return cached_data
        
        self.logger.info(f"從TWSE獲取 {date} 的市場數據...")
        
        # 嘗試多個日期和API
        for attempt in range(self.max_fallback_days):
            try:
                attempt_date = datetime.strptime(date, '%Y%m%d') - timedelta(days=attempt)
                if attempt_date.weekday() >= 5:  # 跳過週末
                    continue
                    
                date_str = attempt_date.strftime('%Y%m%d')
                
                # 方法1: 使用MI_INDEX API
                stocks = self._fetch_twse_mi_index(date_str)
                if stocks:
                    self.logger.info(f"成功獲取 {len(stocks)} 支TWSE股票 (MI_INDEX)")
                    self._save_cache(cache_path, stocks)
                    return stocks
                
                # 方法2: 使用STOCK_DAY_ALL API
                stocks = self._fetch_twse_stock_day_all(date_str)
                if stocks:
                    self.logger.info(f"成功獲取 {len(stocks)} 支TWSE股票 (STOCK_DAY_ALL)")
                    self._save_cache(cache_path, stocks)
                    return stocks
                    
            except Exception as e:
                self.logger.warning(f"獲取 {date_str} TWSE數據失敗: {e}")
                continue
        
        self.logger.error("所有嘗試都無法獲取TWSE數據")
        return []
    
    def _fetch_twse_mi_index(self, date: str) -> List[Dict[str, Any]]:
        """使用MI_INDEX API獲取TWSE數據"""
        try:
            url = self.apis['twse_daily']
            params = {
                'response': 'json',
                'date': date,
                'type': 'ALL'
            }
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('stat') != 'OK':
                raise Exception(f"API狀態異常: {data.get('stat')}")
            
            return self._parse_twse_mi_data(data, date)
            
        except Exception as e:
            self.logger.warning(f"MI_INDEX API失敗: {e}")
            return []
    
    def _fetch_twse_stock_day_all(self, date: str) -> List[Dict[str, Any]]:
        """使用STOCK_DAY_ALL API獲取TWSE數據"""
        try:
            url = self.apis['twse_all']
            params = {
                'response': 'json',
                'date': date,
                'type': 'ALLBUT0999'
            }
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('stat') != 'OK':
                raise Exception(f"API狀態異常: {data.get('stat')}")
            
            return self._parse_twse_stock_day_data(data, date)
            
        except Exception as e:
            self.logger.warning(f"STOCK_DAY_ALL API失敗: {e}")
            return []
    
    def _parse_twse_mi_data(self, data: Dict, date: str) -> List[Dict[str, Any]]:
        """解析MI_INDEX數據"""
        stocks = []
        fields = data.get('fields', [])
        data_list = data.get('data9', [])  # 一般股票數據
        
        if not fields or not data_list:
            return []
        
        for row in data_list:
            try:
                if len(row) < len(fields):
                    continue
                
                stock_code = row[0].strip()
                stock_name = row[1].strip()
                
                # 過濾非股票代碼
                if not stock_code.isdigit() or len(stock_code) != 4:
                    continue
                
                # 解析數據
                trade_volume = self._safe_int(row[2])
                trade_value = self._safe_int(row[3])
                open_price = self._safe_float(row[4])
                high_price = self._safe_float(row[5])
                low_price = self._safe_float(row[6])
                close_price = self._safe_float(row[7])
                
                # 漲跌信息
                change_str = row[8].strip() if len(row) > 8 else ""
                change = self._parse_change(change_str)
                change_percent = (change / close_price * 100) if close_price > 0 else 0
                
                # 只保留有交易的股票
                if close_price <= 0 or trade_volume <= 0:
                    continue
                
                stock = {
                    'code': stock_code,
                    'name': stock_name,
                    'market': 'TWSE',
                    'close': close_price,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'volume': trade_volume,
                    'trade_value': trade_value,
                    'change': change,
                    'change_percent': round(change_percent, 2),
                    'date': datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                    'data_source': 'TWSE_MI_INDEX'
                }
                
                stocks.append(stock)
                
            except Exception as e:
                self.logger.debug(f"解析股票數據失敗: {row[:2] if len(row) >= 2 else row}")
                continue
        
        return stocks
    
    def _parse_twse_stock_day_data(self, data: Dict, date: str) -> List[Dict[str, Any]]:
        """解析STOCK_DAY_ALL數據"""
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
                    
                    stock = {
                        "code": code,
                        "name": name,
                        "market": "TWSE",
                        "close": close_price,
                        "open": self._safe_float(stock_dict.get("開盤價", close_price)),
                        "high": self._safe_float(stock_dict.get("最高價", close_price)),
                        "low": self._safe_float(stock_dict.get("最低價", close_price)),
                        "volume": int(volume),
                        "trade_value": trade_value,
                        "change": change,
                        "change_percent": round(change_percent, 2),
                        "date": datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                        "data_source": "TWSE_STOCK_DAY_ALL"
                    }
                    
                    stocks.append(stock)
                    
                except Exception as e:
                    continue
        
        return stocks
    
    def fetch_tpex_data(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取櫃買中心數據"""
        if date is None:
            date = self.get_optimal_data_date()
        
        # 檢查快取
        cache_path = self._get_cache_path('tpex_market', date)
        if self._is_cache_valid(cache_path):
            cached_data = self._load_cache(cache_path)
            if cached_data:
                self.logger.info(f"使用快取的TPEX數據: {len(cached_data)} 支股票")
                return cached_data
        
        self.logger.info(f"從TPEX獲取 {date} 的上櫃數據...")
        
        # 嘗試多個日期
        for attempt in range(self.max_fallback_days):
            try:
                attempt_date = datetime.strptime(date, '%Y%m%d') - timedelta(days=attempt)
                if attempt_date.weekday() >= 5:  # 跳過週末
                    continue
                
                # 轉換為民國年格式
                minguo_year = attempt_date.year - 1911
                minguo_date = f"{minguo_year}/{attempt_date.month:02d}/{attempt_date.day:02d}"
                date_str = attempt_date.strftime('%Y%m%d')
                
                url = self.apis['tpex_daily']
                params = {
                    'l': 'zh-tw',
                    'd': minguo_date,
                    'se': 'EW',
                    'o': 'json'
                }
                
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('stat') == 'OK' and data.get('iTotalRecords', 0) > 0:
                    stocks = self._parse_tpex_data(data, date_str)
                    if stocks:
                        self.logger.info(f"成功獲取 {len(stocks)} 支TPEX股票")
                        self._save_cache(cache_path, stocks)
                        return stocks
                        
            except Exception as e:
                self.logger.warning(f"獲取TPEX數據失敗: {e}")
                continue
        
        self.logger.error("所有嘗試都無法獲取TPEX數據")
        return []
    
    def _parse_tpex_data(self, data: Dict, date: str) -> List[Dict[str, Any]]:
        """解析TPEX數據"""
        stocks = []
        data_list = data.get('aaData', [])
        
        for row in data_list:
            try:
                if len(row) < 10:
                    continue
                
                stock_code = row[0].strip()
                stock_name = row[1].strip()
                
                # 過濾非股票代碼
                if not stock_code.isdigit():
                    continue
                
                close_price = self._safe_float(row[2])
                change = self._safe_float(row[3])
                open_price = self._safe_float(row[4])
                high_price = self._safe_float(row[5])
                low_price = self._safe_float(row[6])
                trade_volume = self._safe_int(row[7]) * 1000  # 轉換為股數
                trade_value = self._safe_int(row[8]) * 1000  # 轉換為元
                
                change_percent = (change / close_price * 100) if close_price > 0 else 0
                
                # 只保留有交易的股票
                if close_price <= 0 or trade_volume <= 0:
                    continue
                
                stock = {
                    'code': stock_code,
                    'name': stock_name,
                    'market': 'TPEX',
                    'close': close_price,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'volume': trade_volume,
                    'trade_value': trade_value,
                    'change': change,
                    'change_percent': round(change_percent, 2),
                    'date': datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                    'data_source': 'TPEX_API'
                }
                
                stocks.append(stock)
                
            except Exception as e:
                self.logger.debug(f"解析TPEX股票數據失敗: {row[:2] if len(row) >= 2 else row}")
                continue
        
        return stocks
    
    def fetch_institutional_data(self, date: str = None) -> Dict[str, Dict[str, int]]:
        """獲取三大法人買賣超數據"""
        if date is None:
            date = self.get_optimal_data_date()
        
        # 檢查快取
        cache_path = self._get_cache_path('institutional', date)
        if self._is_cache_valid(cache_path):
            cached_data = self._load_cache(cache_path)
            if cached_data:
                self.logger.info(f"使用快取的法人數據: {len(cached_data)} 支股票")
                return cached_data
        
        try:
            self.logger.info(f"獲取 {date} 的三大法人數據...")
            
            url = self.apis['institutional']
            params = {
                'response': 'json',
                'date': date,
                'selectType': 'ALL'
            }
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('stat') != 'OK':
                raise Exception(f"法人數據API狀態異常: {data.get('stat')}")
            
            # 解析法人數據
            institutional_data = {}
            data_list = data.get('data', [])
            
            for row in data_list:
                try:
                    if len(row) < 4:
                        continue
                    
                    stock_code = row[0].strip()
                    
                    # 過濾非股票代碼
                    if not stock_code.isdigit() or len(stock_code) != 4:
                        continue
                    
                    # 外資、投信、自營商買賣超（單位：千股）
                    foreign_net = self._safe_int(row[1]) * 1000  # 轉換為股數
                    trust_net = self._safe_int(row[2]) * 1000
                    dealer_net = self._safe_int(row[3]) * 1000
                    
                    institutional_data[stock_code] = {
                        'foreign_net_buy': foreign_net,
                        'trust_net_buy': trust_net,
                        'dealer_net_buy': dealer_net,
                        'total_net_buy': foreign_net + trust_net + dealer_net
                    }
                    
                except Exception as e:
                    continue
            
            self.logger.info(f"成功獲取 {len(institutional_data)} 支股票的法人數據")
            
            # 保存快取
            self._save_cache(cache_path, institutional_data)
            
            return institutional_data
            
        except Exception as e:
            self.logger.error(f"獲取法人數據失敗: {e}")
            return {}
    
    def get_financial_data(self, stock_codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """獲取基本面財務數據（模擬版本）"""
        cache_path = self._get_cache_path('financial', datetime.now().strftime('%Y%m'))
        
        # 基本面數據更新頻率較低，使用月度快取
        if self._is_cache_valid(cache_path):
            cached_data = self._load_cache(cache_path)
            if cached_data:
                self.logger.info(f"使用快取的財務數據: {len(cached_data)} 支股票")
                return {code: cached_data.get(code, {}) for code in stock_codes}
        
        try:
            self.logger.info(f"生成 {len(stock_codes)} 支股票的財務數據...")
            
            financial_data = {}
            
            # 限制處理數量避免過長時間
            for i, stock_code in enumerate(stock_codes[:100]):
                try:
                    # 使用股票代碼生成一致性的模擬數據
                    seed = int(hashlib.md5(stock_code.encode()).hexdigest()[:8], 16)
                    np.random.seed(seed)
                    
                    # 根據不同股票類型設定不同的財務特徵
                    if stock_code.startswith('23'):  # 科技股
                        base_roe = np.random.normal(15, 5)
                        base_pe = np.random.normal(20, 8)
                        base_eps_growth = np.random.normal(12, 15)
                        base_dividend_yield = np.random.normal(2.5, 1.5)
                    elif stock_code.startswith('28'):  # 金融股
                        base_roe = np.random.normal(10, 3)
                        base_pe = np.random.normal(12, 4)
                        base_eps_growth = np.random.normal(5, 8)
                        base_dividend_yield = np.random.normal(4.5, 1.5)
                    elif stock_code.startswith('26'):  # 航運股
                        base_roe = np.random.normal(20, 10)
                        base_pe = np.random.normal(8, 5)
                        base_eps_growth = np.random.normal(25, 20)
                        base_dividend_yield = np.random.normal(6, 2)
                    else:  # 其他股票
                        base_roe = np.random.normal(12, 6)
                        base_pe = np.random.normal(15, 6)
                        base_eps_growth = np.random.normal(8, 12)
                        base_dividend_yield = np.random.normal(3.5, 2)
                    
                    financial_data[stock_code] = {
                        'roe': max(0, round(base_roe, 1)),
                        'pe_ratio': max(3, round(base_pe, 1)),
                        'eps_growth': round(base_eps_growth, 1),
                        'dividend_yield': max(0, round(base_dividend_yield, 1)),
                        'revenue_growth': round(np.random.normal(base_eps_growth * 0.8, 8), 1),
                        'debt_ratio': round(np.random.uniform(0.2, 0.6), 2),
                        'current_ratio': round(np.random.uniform(1.0, 3.0), 2)
                    }
                    
                except Exception as e:
                    continue
            
            self.logger.info(f"成功生成 {len(financial_data)} 支股票的財務數據")
            
            # 保存快取
            self._save_cache(cache_path, financial_data)
            
            return financial_data
            
        except Exception as e:
            self.logger.error(f"生成財務數據失敗: {e}")
            return {}
    
    def get_all_stocks_by_volume(self, date: str = None) -> List[Dict[str, Any]]:
        """獲取所有股票並按成交金額排序"""
        self.logger.info("開始獲取所有股票數據")
        
        # 獲取上市股票
        twse_stocks = self.fetch_twse_data(date)
        time.sleep(1)  # 避免請求過於頻繁
        
        # 獲取上櫃股票
        tpex_stocks = self.fetch_tpex_data(date)
        
        # 合併股票數據
        all_stocks = twse_stocks + tpex_stocks
        
        if not all_stocks:
            self.logger.error("無法獲取任何股票數據")
            return []
        
        # 獲取法人數據
        institutional_data = self.fetch_institutional_data(date)
        
        # 獲取財務數據（僅對前100支活躍股票）
        top_stocks = sorted(all_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)[:100]
        stock_codes = [s['code'] for s in top_stocks]
        financial_data = self.get_financial_data(stock_codes)
        
        # 整合數據
        for stock in all_stocks:
            stock_code = stock['code']
            
            # 添加法人數據
            if stock_code in institutional_data:
                inst_data = institutional_data[stock_code]
                stock.update(inst_data)
            else:
                stock.update({
                    'foreign_net_buy': 0,
                    'trust_net_buy': 0,
                    'dealer_net_buy': 0,
                    'total_net_buy': 0
                })
            
            # 添加財務數據
            if stock_code in financial_data:
                stock.update(financial_data[stock_code])
        
        # 過濾有效數據
        valid_stocks = [
            stock for stock in all_stocks 
            if stock.get('trade_value', 0) > 0 and stock.get('close', 0) > 0
        ]
        
        # 按成交金額排序
        sorted_stocks = sorted(valid_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)
        
        self.logger.info(f"成功整合並排序 {len(sorted_stocks)} 支股票")
        
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
        
        self.logger.info(f"獲取 {time_slot} 時段的前 {limit} 支股票")
        
        # 獲取所有股票
        all_stocks = self.get_all_stocks_by_volume(date)
        
        # 根據時段篩選和排序
        filtered_stocks = self._filter_stocks_by_time_slot(all_stocks, time_slot)
        
        # 添加時段資訊
        for stock in filtered_stocks:
            stock['time_slot'] = time_slot
        
        self.logger.info(f"為 {time_slot} 時段選擇了 {len(filtered_stocks)} 支股票")
        
        return filtered_stocks
    
    def _filter_stocks_by_time_slot(self, stocks: List[Dict[str, Any]], time_slot: str) -> List[Dict[str, Any]]:
        """根據時段篩選股票"""
        
        # 基本篩選條件
        valid_stocks = [
            stock for stock in stocks
            if stock.get('close', 0) > 0 
            and stock.get('trade_value', 0) > 100000  # 至少10萬成交金額
            and stock.get('volume', 0) > 1000  # 至少1000股成交量
        ]
        
        # 根據時段設定不同的篩選和排序策略
        if time_slot == 'morning_scan':
            # 早盤關注活躍股票
            valid_stocks.sort(key=lambda x: x.get('trade_value', 0), reverse=True)
            return valid_stocks[:200]
            
        elif time_slot == 'afternoon_scan':
            # 盤後綜合分析，包含更多股票
            valid_stocks.sort(key=lambda x: (
                x.get('trade_value', 0) * 0.7 + 
                abs(x.get('change_percent', 0)) * x.get('close', 0) * x.get('volume', 0) * 0.3
            ), reverse=True)
            return valid_stocks[:1000]
            
        elif time_slot == 'weekly_summary':
            # 週末總結，全面分析
            valid_stocks.sort(key=lambda x: x.get('trade_value', 0), reverse=True)
            return valid_stocks[:500]
            
        else:
            # 其他時段
            valid_stocks.sort(key=lambda x: x.get('trade_value', 0), reverse=True)
            return valid_stocks[:300]
    
    def test_connection(self) -> Dict[str, bool]:
        """測試所有數據源連接"""
        results = {}
        test_date = self.get_optimal_data_date()
        
        # 測試TWSE連接
        try:
            twse_data = self.fetch_twse_data(test_date)
            results['twse'] = len(twse_data) > 0
            print(f"✅ TWSE連接測試: 獲取 {len(twse_data)} 支股票")
        except Exception as e:
            results['twse'] = False
            print(f"❌ TWSE連接測試失敗: {e}")
        
        # 測試TPEX連接
        try:
            tpex_data = self.fetch_tpex_data(test_date)
            results['tpex'] = len(tpex_data) > 0
            print(f"✅ TPEX連接測試: 獲取 {len(tpex_data)} 支股票")
        except Exception as e:
            results['tpex'] = False
            print(f"❌ TPEX連接測試失敗: {e}")
        
        # 測試法人數據
        try:
            inst_data = self.fetch_institutional_data(test_date)
            results['institutional'] = len(inst_data) > 0
            print(f"✅ 法人數據測試: 獲取 {len(inst_data)} 支股票")
        except Exception as e:
            results['institutional'] = False
            print(f"❌ 法人數據測試失敗: {e}")
        
        return results

# 測試和使用示例
def test_integrated_fetcher():
    """測試整合版數據抓取器"""
    print("🧪 測試 IntegratedTWSEDataFetcher...")
    
    try:
        # 設置日誌級別
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # 創建數據獲取器
        fetcher = IntegratedTWSEDataFetcher()
        print("✅ IntegratedTWSEDataFetcher 初始化成功")
        
        # 測試數據源連接
        print("\n🔍 測試數據源連接...")
        test_results = fetcher.test_connection()
        
        # 測試獲取股票數據
        print("\n📊 測試獲取股票數據...")
        stocks = fetcher.get_stocks_by_time_slot('morning_scan')
        
        if stocks:
            print(f"✅ 成功獲取 {len(stocks)} 支股票數據")
            print(f"\n📈 前5支最活躍股票:")
            for i, stock in enumerate(stocks[:5]):
                print(f"  {i+1}. {stock['code']} {stock['name']} ({stock['market']})")
                print(f"     價格: {stock['close']:.2f} ({stock['change_percent']:+.2f}%)")
                print(f"     成交值: {stock['trade_value']:,.0f} 元")
                if 'foreign_net_buy' in stock:
                    print(f"     外資: {stock['foreign_net_buy']:,} 股")
                print()
        else:
            print("⚠️ 沒有獲取到股票數據")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integrated_fetcher()
    if success:
        print("🎉 整合版台股數據獲取器測試完成！")
    else:
        print("💥 測試失敗，請檢查錯誤信息")
