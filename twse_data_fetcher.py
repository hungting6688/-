"""
twse_data_fetcher.py - 台灣證券交易所數據獲取模組
從台灣證券交易所API獲取實際股票數據
"""
import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

# 配置日誌
logger = logging.getLogger(__name__)

class TWStockDataFetcher:
    """台股數據獲取器"""
    
    def __init__(self, cache_dir: str = 'cache'):
        """
        初始化數據獲取器
        
        參數:
        - cache_dir: 快取目錄
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 台灣證券交易所API基礎URL
        self.twse_base_url = "https://www.twse.com.tw/exchangeReport"
        self.tpex_base_url = "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430"
        
        # 快取期限（秒）
        self.cache_expire_time = 3600  # 1小時
        
        # 請求間隔（秒）
        self.request_delay = 2
        
    def _get_cache_path(self, cache_key: str) -> str:
        """獲取快取檔案路徑"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """檢查快取是否有效"""
        if not os.path.exists(cache_path):
            return False
        
        # 檢查檔案修改時間
        file_time = os.path.getmtime(cache_path)
        current_time = time.time()
        
        return (current_time - file_time) < self.cache_expire_time
    
    def _load_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """載入快取數據"""
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"載入快取失敗: {e}")
        
        return None
    
    def _save_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """保存快取數據"""
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存快取失敗: {e}")
    
    def fetch_twse_daily_data(self, date: str = None) -> List[Dict[str, Any]]:
        """
        獲取台灣證券交易所上市股票日交易資料
        
        參數:
        - date: 日期 (格式: YYYYMMDD)，默認為今日
        
        返回:
        - 股票交易數據列表
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"twse_daily_{date}"
        
        # 檢查快取
        cached_data = self._load_cache(cache_key)
        if cached_data:
            logger.info(f"從快取載入TWSE日交易資料: {date}")
            return cached_data
        
        # 從API獲取數據
        url = f"{self.twse_base_url}/STOCK_DAY_ALL"
        params = {
            'response': 'json',
            'date': date
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("stat") != "OK":
                logger.error(f"TWSE API返回錯誤: {data.get('stat')}")
                return []
            
            # 解析數據
            fields = data.get("fields", [])
            raw_data = data.get("data", [])
            
            stocks = []
            for row in raw_data:
                if len(row) >= len(fields):
                    stock_data = {}
                    for i, field in enumerate(fields):
                        stock_data[field] = row[i]
                    
                    # 處理數據格式
                    processed_stock = self._process_twse_stock_data(stock_data)
                    if processed_stock:
                        stocks.append(processed_stock)
            
            # 保存快取
            self._save_cache(cache_key, stocks)
            
            logger.info(f"成功獲取TWSE {len(stocks)} 支股票資料")
            return stocks
            
        except Exception as e:
            logger.error(f"獲取TWSE日交易資料失敗: {e}")
            return []
    
    def fetch_tpex_daily_data(self, date: str = None) -> List[Dict[str, Any]]:
        """
        獲取台灣證券櫃檯買賣中心上櫃股票日交易資料
        
        參數:
        - date: 日期 (格式: YYYYMMDD)，默認為今日
        
        返回:
        - 股票交易數據列表
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"tpex_daily_{date}"
        
        # 檢查快取
        cached_data = self._load_cache(cache_key)
        if cached_data:
            logger.info(f"從快取載入TPEX日交易資料: {date}")
            return cached_data
        
        # 轉換日期格式為民國年
        try:
            date_obj = datetime.strptime(date, '%Y%m%d')
            minguo_date = f"{date_obj.year - 1911}/{date_obj.month:02d}/{date_obj.day:02d}"
        except ValueError:
            logger.error(f"日期格式錯誤: {date}")
            return []
        
        # 從API獲取數據
        url = f"{self.tpex_base_url}/stk_wn1430_result.php"
        params = {
            'l': 'zh-tw',
            'd': minguo_date,
            'se': 'EW',
            'o': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("stat") != "OK":
                logger.error(f"TPEX API返回錯誤: {data.get('stat')}")
                return []
            
            # 解析數據
            fields = data.get("fields", [])
            raw_data = data.get("data", [])
            
            stocks = []
            for row in raw_data:
                if len(row) >= len(fields):
                    stock_data = {}
                    for i, field in enumerate(fields):
                        stock_data[field] = row[i]
                    
                    # 處理數據格式
                    processed_stock = self._process_tpex_stock_data(stock_data)
                    if processed_stock:
                        stocks.append(processed_stock)
            
            # 保存快取
            self._save_cache(cache_key, stocks)
            
            logger.info(f"成功獲取TPEX {len(stocks)} 支股票資料")
            return stocks
            
        except Exception as e:
            logger.error(f"獲取TPEX日交易資料失敗: {e}")
            return []
    
    def _process_twse_stock_data(self, raw_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """處理TWSE股票數據"""
        try:
            # 獲取基本資訊
            code = raw_data.get("證券代號", "").strip()
            name = raw_data.get("證券名稱", "").strip()
            
            if not code or not name:
                return None
            
            # 處理數值數據
            def parse_number(value: str) -> float:
                if not value or value == "--" or value == "N/A":
                    return 0.0
                # 移除千分位逗號
                value = value.replace(",", "")
                try:
                    return float(value)
                except ValueError:
                    return 0.0
            
            # 處理價格數據
            open_price = parse_number(raw_data.get("開盤價", "0"))
            high_price = parse_number(raw_data.get("最高價", "0"))
            low_price = parse_number(raw_data.get("最低價", "0"))
            close_price = parse_number(raw_data.get("收盤價", "0"))
            volume = parse_number(raw_data.get("成交股數", "0"))
            
            # 計算成交金額（成交股數 * 收盤價）
            trade_value = volume * close_price
            
            # 計算漲跌幅
            change = parse_number(raw_data.get("漲跌價差", "0"))
            change_percent = (change / close_price * 100) if close_price > 0 else 0
            
            processed_data = {
                "code": code,
                "name": name,
                "market": "TWSE",
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": int(volume),
                "trade_value": trade_value,
                "change": change,
                "change_percent": round(change_percent, 2),
                "date": datetime.now().strftime('%Y-%m-%d')
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"處理TWSE股票數據失敗: {e}")
            return None
    
    def _process_tpex_stock_data(self, raw_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """處理TPEX股票數據"""
        try:
            # 獲取基本資訊
            code = raw_data.get("代號", "").strip()
            name = raw_data.get("名稱", "").strip()
            
            if not code or not name:
                return None
            
            # 處理數值數據
            def parse_number(value: str) -> float:
                if not value or value == "--" or value == "N/A":
                    return 0.0
                # 移除千分位逗號
                value = value.replace(",", "")
                try:
                    return float(value)
                except ValueError:
                    return 0.0
            
            # 處理價格數據
            open_price = parse_number(raw_data.get("開盤", "0"))
            high_price = parse_number(raw_data.get("最高", "0"))
            low_price = parse_number(raw_data.get("最低", "0"))
            close_price = parse_number(raw_data.get("收盤", "0"))
            volume = parse_number(raw_data.get("成交量", "0"))
            
            # 計算成交金額
            trade_value = volume * close_price
            
            # 計算漲跌幅
            change = parse_number(raw_data.get("漲跌", "0"))
            change_percent = (change / close_price * 100) if close_price > 0 else 0
            
            processed_data = {
                "code": code,
                "name": name,
                "market": "TPEX",
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": int(volume),
                "trade_value": trade_value,
                "change": change,
                "change_percent": round(change_percent, 2),
                "date": datetime.now().strftime('%Y-%m-%d')
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"處理TPEX股票數據失敗: {e}")
            return None
    
    def get_all_stocks_by_volume(self, date: str = None) -> List[Dict[str, Any]]:
        """
        獲取所有股票並按成交金額排序
        
        參數:
        - date: 日期 (格式: YYYYMMDD)，默認為今日
        
        返回:
        - 按成交金額排序的股票列表
        """
        logger.info("開始獲取所有股票數據...")
        
        # 獲取上市股票數據
        twse_stocks = self.fetch_twse_daily_data(date)
        time.sleep(self.request_delay)  # 避免請求過於頻繁
        
        # 獲取上櫃股票數據
        tpex_stocks = self.fetch_tpex_daily_data(date)
        
        # 合併數據
        all_stocks = twse_stocks + tpex_stocks
        
        # 過濾掉成交金額為0的股票
        active_stocks = [stock for stock in all_stocks if stock.get('trade_value', 0) > 0]
        
        # 按成交金額排序（由大到小）
        sorted_stocks = sorted(active_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)
        
        logger.info(f"成功獲取並排序 {len(sorted_stocks)} 支活躍股票")
        
        return sorted_stocks
    
    def get_stocks_by_time_slot(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """
        根據時段獲取相應數量的股票
        
        參數:
        - time_slot: 時段名稱
        - date: 日期 (格式: YYYYMMDD)，默認為今日
        
        返回:
        - 選定的股票列表
        """
        # 定義每個時段的股票數量（已更新為新的數量）
        slot_limits = {
            'morning_scan': 200,        # 早盤掃描（原100，現200）
            'mid_morning_scan': 300,    # 盤中掃描（原150，現300）
            'mid_day_scan': 300,        # 午間掃描（原150，現300）
            'afternoon_scan': 1000,     # 盤後掃描（原450，現1000）
            'weekly_summary': 500       # 週末總結（原200，現500）
        }
        
        limit = slot_limits.get(time_slot, 100)
        
        logger.info(f"獲取 {time_slot} 時段的前 {limit} 支股票")
        
        # 獲取所有股票
        all_stocks = self.get_all_stocks_by_volume(date)
        
        # 返回前N支股票
        selected_stocks = all_stocks[:limit]
        
        logger.info(f"為 {time_slot} 時段選擇了 {len(selected_stocks)} 支股票")
        
        return selected_stocks
    
    def get_stock_historical_data(self, stock_code: str, days: int = 30) -> pd.DataFrame:
        """
        獲取單支股票的歷史數據
        
        參數:
        - stock_code: 股票代碼
        - days: 獲取天數
        
        返回:
        - 股票歷史數據DataFrame
        """
        cache_key = f"stock_history_{stock_code}_{days}d"
        
        # 檢查快取
        cached_data = self._load_cache(cache_key)
        if cached_data:
            logger.info(f"從快取載入股票 {stock_code} 歷史數據")
            return pd.DataFrame(cached_data)
        
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)  # 多取幾天確保有足夠交易日
        
        data_list = []
        current_date = start_date
        
        while current_date <= end_date:
            # 跳過週末
            if current_date.weekday() < 5:
                date_str = current_date.strftime('%Y%m%d')
                
                # 獲取當日所有股票數據
                all_stocks = self.get_all_stocks_by_volume(date_str)
                
                # 找到目標股票
                target_stock = None
                for stock in all_stocks:
                    if stock['code'] == stock_code:
                        target_stock = stock
                        break
                
                if target_stock:
                    # 轉換為DataFrame格式
                    row_data = {
                        'date': pd.to_datetime(target_stock['date']),
                        'open': target_stock['open'],
                        'high': target_stock['high'],
                        'low': target_stock['low'],
                        'close': target_stock['close'],
                        'volume': target_stock['volume'],
                        'code': target_stock['code']
                    }
                    data_list.append(row_data)
                
                # 避免請求過於頻繁
                time.sleep(self.request_delay)
            
            current_date += timedelta(days=1)
        
        # 創建DataFrame
        if data_list:
            df = pd.DataFrame(data_list)
            df = df.sort_values('date').tail(days)  # 取最近的指定天數
            
            # 保存快取
            cache_data = df.to_dict('records')
            # 轉換datetime為字符串以便JSON序列化
            for record in cache_data:
                record['date'] = record['date'].strftime('%Y-%m-%d')
            self._save_cache(cache_key, cache_data)
            
            logger.info(f"成功獲取股票 {stock_code} 的 {len(df)} 天歷史數據")
            return df
        else:
            logger.warning(f"未能獲取股票 {stock_code} 的歷史數據")
            return pd.DataFrame()

# 測試代碼
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 創建數據獲取器
    fetcher = TWStockDataFetcher()
    
    # 測試獲取不同時段的股票
    time_slots = ['morning_scan', 'mid_morning_scan', 'mid_day_scan', 'afternoon_scan']
    
    for slot in time_slots:
        print(f"\n=== {slot} ===")
        stocks = fetcher.get_stocks_by_time_slot(slot)
        print(f"獲取了 {len(stocks)} 支股票")
        
        # 顯示前5支股票
        for i, stock in enumerate(stocks[:5]):
            print(f"{i+1}. {stock['code']} {stock['name']} - 成交金額: {stock['trade_value']:,.0f}")
    
    # 測試獲取單支股票歷史數據
    print(f"\n=== 測試獲取台積電歷史數據 ===")
    df = fetcher.get_stock_historical_data('2330', days=10)
    if not df.empty:
        print(f"獲取了 {len(df)} 天的歷史數據")
        print(df.head())
    else:
        print("未能獲取歷史數據")
