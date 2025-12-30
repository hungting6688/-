"""
real_data_fetcher.py - 真實歷史數據獲取器
整合多個數據源獲取台股真實歷史數據

數據源：
1. TWSE 台灣證券交易所
2. TPEX 櫃買中心
3. Yahoo Finance (備用)
4. FinMind (備用)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import time
import logging
import json
import os
from io import StringIO

logger = logging.getLogger(__name__)


class RealTimeDataFetcher:
    """
    真實數據獲取器
    支援多數據源、自動重試、數據快取
    """

    def __init__(self, cache_dir: str = './data/cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        # API 設定
        self.request_delay = 0.3  # 請求間隔（秒）
        self.max_retries = 3
        self.timeout = 15

        # 數據源優先順序
        self.data_sources = ['twse', 'yahoo', 'finmind']

        # 快取設定
        self.cache_hours = 4  # 盤中快取4小時

        # 請求頭
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
        }

    # ==================== TWSE 數據源 ====================

    def fetch_twse_daily(self, stock_code: str, date: str = None) -> Optional[pd.DataFrame]:
        """
        從 TWSE 獲取每日交易數據

        Args:
            stock_code: 股票代碼
            date: 日期 YYYYMMDD 格式，預設今天
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
        params = {
            'response': 'json',
            'date': date,
            'stockNo': stock_code
        }

        try:
            response = self._make_request(url, params)
            if response and 'data' in response:
                df = self._parse_twse_daily(response['data'])
                if df is not None and len(df) > 0:
                    logger.info(f"TWSE: 獲取 {stock_code} {len(df)} 筆數據")
                    return df
        except Exception as e:
            logger.warning(f"TWSE 獲取失敗: {stock_code} - {e}")

        return None

    def fetch_twse_history(self, stock_code: str, months: int = 3) -> pd.DataFrame:
        """
        獲取多月歷史數據
        """
        all_data = []
        current_date = datetime.now()

        for i in range(months):
            target_date = current_date - timedelta(days=30 * i)
            date_str = target_date.strftime("%Y%m%d")

            df = self.fetch_twse_daily(stock_code, date_str)
            if df is not None:
                all_data.append(df)

            time.sleep(self.request_delay)

        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            combined = combined.drop_duplicates(subset=['date'])
            combined = combined.sort_values('date').reset_index(drop=True)
            return combined

        return pd.DataFrame()

    def _parse_twse_daily(self, data: List) -> Optional[pd.DataFrame]:
        """解析 TWSE 每日數據"""
        records = []
        for row in data:
            try:
                # 民國年轉西元年
                date_parts = row[0].split('/')
                year = int(date_parts[0]) + 1911
                date_str = f"{year}-{date_parts[1]}-{date_parts[2]}"

                def safe_float(val):
                    if isinstance(val, str):
                        val = val.replace(',', '').replace('--', '0').replace('X', '0').strip()
                    try:
                        return float(val) if val else 0.0
                    except:
                        return 0.0

                def safe_int(val):
                    if isinstance(val, str):
                        val = val.replace(',', '').strip()
                    try:
                        return int(float(val)) if val else 0
                    except:
                        return 0

                records.append({
                    'date': pd.to_datetime(date_str),
                    'volume': safe_int(row[1]),
                    'trade_value': safe_int(row[2]),
                    'open': safe_float(row[3]),
                    'high': safe_float(row[4]),
                    'low': safe_float(row[5]),
                    'close': safe_float(row[6]),
                    'change': safe_float(row[7]),
                    'transactions': safe_int(row[8]) if len(row) > 8 else 0
                })
            except Exception as e:
                continue

        if records:
            return pd.DataFrame(records)
        return None

    # ==================== Yahoo Finance 數據源 ====================

    def fetch_yahoo_history(self, stock_code: str, days: int = 60) -> Optional[pd.DataFrame]:
        """
        從 Yahoo Finance 獲取歷史數據
        台股代碼需加 .TW 或 .TWO
        """
        # 嘗試上市 (.TW) 和上櫃 (.TWO)
        for suffix in ['.TW', '.TWO']:
            yahoo_code = f"{stock_code}{suffix}"
            df = self._fetch_yahoo_data(yahoo_code, days)
            if df is not None and len(df) > 0:
                return df

        return None

    def _fetch_yahoo_data(self, yahoo_code: str, days: int) -> Optional[pd.DataFrame]:
        """Yahoo Finance API 請求"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)

            # Yahoo Finance v8 API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_code}"
            params = {
                'period1': int(start_date.timestamp()),
                'period2': int(end_date.timestamp()),
                'interval': '1d',
                'events': 'history'
            }

            response = self._make_request(url, params)
            if response and 'chart' in response:
                result = response['chart']['result']
                if result:
                    return self._parse_yahoo_data(result[0])
        except Exception as e:
            logger.debug(f"Yahoo 獲取失敗: {yahoo_code} - {e}")

        return None

    def _parse_yahoo_data(self, data: Dict) -> Optional[pd.DataFrame]:
        """解析 Yahoo Finance 數據"""
        try:
            timestamps = data.get('timestamp', [])
            quote = data.get('indicators', {}).get('quote', [{}])[0]

            if not timestamps or not quote:
                return None

            df = pd.DataFrame({
                'date': pd.to_datetime(timestamps, unit='s'),
                'open': quote.get('open', []),
                'high': quote.get('high', []),
                'low': quote.get('low', []),
                'close': quote.get('close', []),
                'volume': quote.get('volume', [])
            })

            # 移除空值
            df = df.dropna()
            df['trade_value'] = df['close'] * df['volume']

            return df
        except Exception as e:
            return None

    # ==================== 法人買賣數據 ====================

    def fetch_institutional_data(self, stock_code: str, date: str = None) -> Dict[str, int]:
        """
        獲取三大法人買賣數據
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        url = "https://www.twse.com.tw/fund/T86"
        params = {
            'response': 'json',
            'date': date,
            'selectType': 'ALLBUT0999'
        }

        try:
            response = self._make_request(url, params)
            if response and 'data' in response:
                for row in response['data']:
                    if row[0].strip() == stock_code:
                        return self._parse_institutional(row)
        except Exception as e:
            logger.warning(f"法人數據獲取失敗: {stock_code} - {e}")

        return {'foreign_net': 0, 'trust_net': 0, 'dealer_net': 0, 'total_net': 0}

    def _parse_institutional(self, row: List) -> Dict[str, int]:
        """解析法人買賣數據"""
        def safe_int(val):
            if isinstance(val, str):
                val = val.replace(',', '').replace(' ', '')
            try:
                return int(val)
            except:
                return 0

        try:
            # TWSE T86 格式
            foreign_buy = safe_int(row[2]) if len(row) > 2 else 0
            foreign_sell = safe_int(row[3]) if len(row) > 3 else 0
            foreign_net = safe_int(row[4]) if len(row) > 4 else (foreign_buy - foreign_sell)

            trust_buy = safe_int(row[8]) if len(row) > 8 else 0
            trust_sell = safe_int(row[9]) if len(row) > 9 else 0
            trust_net = safe_int(row[10]) if len(row) > 10 else (trust_buy - trust_sell)

            dealer_net = safe_int(row[11]) if len(row) > 11 else 0
            total_net = safe_int(row[18]) if len(row) > 18 else (foreign_net + trust_net + dealer_net)

            return {
                'foreign_net': foreign_net,
                'trust_net': trust_net,
                'dealer_net': dealer_net,
                'total_net': total_net,
                'foreign_buy': foreign_buy,
                'foreign_sell': foreign_sell,
                'trust_buy': trust_buy,
                'trust_sell': trust_sell
            }
        except:
            return {'foreign_net': 0, 'trust_net': 0, 'dealer_net': 0, 'total_net': 0}

    # ==================== 融資融券數據 ====================

    def fetch_margin_data(self, stock_code: str, date: str = None) -> Dict[str, int]:
        """
        獲取融資融券數據
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        url = "https://www.twse.com.tw/exchangeReport/MI_MARGN"
        params = {
            'response': 'json',
            'date': date,
            'selectType': 'STOCK'
        }

        try:
            response = self._make_request(url, params)
            if response and 'data' in response:
                for row in response['data']:
                    if row[0].strip() == stock_code:
                        return self._parse_margin(row)
        except Exception as e:
            logger.debug(f"融資融券數據獲取失敗: {stock_code} - {e}")

        return {'margin_buy': 0, 'margin_sell': 0, 'margin_balance': 0,
                'short_buy': 0, 'short_sell': 0, 'short_balance': 0}

    def _parse_margin(self, row: List) -> Dict[str, int]:
        """解析融資融券數據"""
        def safe_int(val):
            if isinstance(val, str):
                val = val.replace(',', '')
            try:
                return int(val)
            except:
                return 0

        try:
            return {
                'margin_buy': safe_int(row[2]) if len(row) > 2 else 0,
                'margin_sell': safe_int(row[3]) if len(row) > 3 else 0,
                'margin_balance': safe_int(row[6]) if len(row) > 6 else 0,
                'short_buy': safe_int(row[8]) if len(row) > 8 else 0,
                'short_sell': safe_int(row[9]) if len(row) > 9 else 0,
                'short_balance': safe_int(row[12]) if len(row) > 12 else 0
            }
        except:
            return {'margin_buy': 0, 'margin_sell': 0, 'margin_balance': 0,
                    'short_buy': 0, 'short_sell': 0, 'short_balance': 0}

    # ==================== 整合獲取函數 ====================

    def get_stock_data(self, stock_code: str, days: int = 60,
                       include_institutional: bool = True) -> Dict[str, Any]:
        """
        整合獲取股票完整數據

        Returns:
            {
                'historical': pd.DataFrame,  # 歷史價格數據
                'institutional': Dict,       # 法人買賣
                'margin': Dict,              # 融資融券
                'success': bool,
                'source': str
            }
        """
        result = {
            'historical': pd.DataFrame(),
            'institutional': {},
            'margin': {},
            'success': False,
            'source': None
        }

        # 嘗試獲取歷史數據
        # 1. 先嘗試 TWSE
        months_needed = (days // 20) + 1
        df = self.fetch_twse_history(stock_code, months_needed)

        if df is not None and len(df) >= min(days, 20):
            result['historical'] = df.tail(days)
            result['source'] = 'TWSE'
            result['success'] = True
        else:
            # 2. 嘗試 Yahoo Finance
            df = self.fetch_yahoo_history(stock_code, days)
            if df is not None and len(df) > 0:
                result['historical'] = df.tail(days)
                result['source'] = 'Yahoo'
                result['success'] = True

        # 獲取法人數據
        if include_institutional:
            result['institutional'] = self.fetch_institutional_data(stock_code)
            result['margin'] = self.fetch_margin_data(stock_code)

        return result

    # ==================== 工具函數 ====================

    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """發送 HTTP 請求，支援重試"""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"請求超時 (嘗試 {attempt + 1}/{self.max_retries})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"請求失敗: {e}")
            except json.JSONDecodeError:
                logger.warning("JSON 解析失敗")

            if attempt < self.max_retries - 1:
                time.sleep(self.request_delay * (attempt + 1))

        return None

    def _load_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """載入快取"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        meta_file = os.path.join(self.cache_dir, f"{cache_key}.meta")

        if not os.path.exists(cache_file) or not os.path.exists(meta_file):
            return None

        try:
            with open(meta_file, 'r') as f:
                meta = json.load(f)

            cache_time = datetime.fromisoformat(meta['timestamp'])
            if datetime.now() - cache_time > timedelta(hours=self.cache_hours):
                return None

            return pd.read_pickle(cache_file)
        except:
            return None

    def _save_cache(self, cache_key: str, data: pd.DataFrame):
        """保存快取"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            meta_file = os.path.join(self.cache_dir, f"{cache_key}.meta")

            data.to_pickle(cache_file)
            with open(meta_file, 'w') as f:
                json.dump({'timestamp': datetime.now().isoformat()}, f)
        except Exception as e:
            logger.warning(f"快取保存失敗: {e}")


# ==================== 市場概況數據 ====================

class MarketOverviewFetcher:
    """市場概況數據獲取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_market_index(self) -> Dict[str, Any]:
        """獲取大盤指數"""
        url = "https://www.twse.com.tw/exchangeReport/FMTQIK"
        params = {'response': 'json'}

        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    latest = data['data'][-1]
                    return {
                        'date': latest[0],
                        'index': float(latest[1].replace(',', '')),
                        'change': float(latest[2].replace(',', '')),
                        'volume': int(latest[3].replace(',', '')),
                        'trade_value': int(latest[4].replace(',', '')),
                        'transactions': int(latest[5].replace(',', ''))
                    }
        except Exception as e:
            logger.warning(f"大盤指數獲取失敗: {e}")

        return {}

    def get_market_breadth(self, date: str = None) -> Dict[str, int]:
        """
        獲取市場寬度（漲跌家數）
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        url = "https://www.twse.com.tw/exchangeReport/MI_INDEX"
        params = {
            'response': 'json',
            'date': date,
            'type': 'MS'
        }

        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # 解析漲跌家數
                if 'data8' in data:
                    for row in data['data8']:
                        if '上漲' in str(row):
                            return {
                                'up': int(str(row[2]).replace(',', '')),
                                'down': int(str(row[3]).replace(',', '')),
                                'unchanged': int(str(row[4]).replace(',', ''))
                            }
        except Exception as e:
            logger.debug(f"市場寬度獲取失敗: {e}")

        return {'up': 0, 'down': 0, 'unchanged': 0}


# ==================== 測試 ====================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    fetcher = RealTimeDataFetcher()

    # 測試獲取歷史數據
    print("測試獲取 2330 台積電歷史數據...")
    result = fetcher.get_stock_data('2330', days=30)

    if result['success']:
        print(f"數據來源: {result['source']}")
        print(f"數據筆數: {len(result['historical'])}")
        print("\n最近 5 筆數據:")
        print(result['historical'].tail())

        print("\n法人買賣:")
        print(result['institutional'])
    else:
        print("獲取失敗")

    # 測試市場概況
    print("\n" + "=" * 50)
    market = MarketOverviewFetcher()
    print("大盤指數:")
    print(market.get_market_index())
