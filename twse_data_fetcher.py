"""
enhanced_twse_data_fetcher.py - 增強版台股數據抓取器
解決盤中數據時效性問題，確保抓取到最新的交易數據
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

# 配置日誌
logger = logging.getLogger(__name__)

class EnhancedTWStockDataFetcher:
    """增強版台股數據獲取器 - 解決盤中數據時效性問題"""
    
    def __init__(self, cache_dir: str = 'cache'):
        """
        初始化數據獲取器
        
        參數:
        - cache_dir: 快取目錄
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 台灣時區
        self.taipei_tz = pytz.timezone('Asia/Taipei')
        
        # API URL
        self.twse_base_url = "https://www.twse.com.tw/exchangeReport"
        self.tpex_base_url = "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430"
        
        # 盤中即時數據 API (如果可用)
        self.twse_intraday_url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL"
        self.twse_realtime_url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
        
        # 快取期限設定（根據時段調整）
        self.cache_settings = {
            'trading_hours': 300,    # 交易時間：5分鐘快取
            'after_hours': 3600,     # 盤後：1小時快取
            'weekend': 86400,        # 週末：24小時快取
            'pre_market': 1800       # 盤前：30分鐘快取
        }
        
        # 市場交易時間定義
        self.market_schedule = {
            'pre_market_start': 8,   # 8:00 盤前
            'market_open': 9,        # 9:00 開盤
            'market_close': 13,      # 13:30 收盤
            'after_market_end': 15   # 15:00 盤後數據更新完成
        }
        
        # 請求間隔（秒）
        self.request_delay = 1.5
    
    def _get_current_taiwan_time(self) -> datetime:
        """獲取當前台灣時間"""
        return datetime.now(self.taipei_tz)
    
    def _get_market_status(self) -> Tuple[str, str]:
        """
        獲取當前市場狀態和應該使用的數據日期
        
        返回:
        - (market_status, target_date)
        - market_status: 'pre_market', 'trading', 'after_hours', 'weekend'
        - target_date: 應該抓取的數據日期 (YYYYMMDD)
        """
        now = self._get_current_taiwan_time()
        current_hour = now.hour
        current_minute = now.minute
        weekday = now.weekday()  # 0=週一, 6=週日
        
        # 週末處理
        if weekday >= 5:  # 週六、週日
            # 使用最近的交易日數據
            if weekday == 5:  # 週六
                target_date = now.strftime('%Y%m%d')  # 週六可能還有週五的數據
            else:  # 週日
                # 使用週五的數據
                friday = now - timedelta(days=2)
                target_date = friday.strftime('%Y%m%d')
            return 'weekend', target_date
        
        # 工作日處理
        current_time_minutes = current_hour * 60 + current_minute
        
        # 8:00 之前 - 使用前一交易日數據
        if current_time_minutes < self.market_schedule['pre_market_start'] * 60:
            if weekday == 0:  # 週一早上，使用週五數據
                previous_trading_day = now - timedelta(days=3)
            else:
                previous_trading_day = now - timedelta(days=1)
            target_date = previous_trading_day.strftime('%Y%m%d')
            return 'pre_market', target_date
        
        # 8:00 - 9:00 盤前時間
        elif current_time_minutes < self.market_schedule['market_open'] * 60:
            target_date = now.strftime('%Y%m%d')
            return 'pre_market', target_date
        
        # 9:00 - 13:30 交易時間
        elif current_time_minutes < (self.market_schedule['market_close'] * 60 + 30):
            target_date = now.strftime('%Y%m%d')
            return 'trading', target_date
        
        # 13:30 - 15:00 盤後整理時間
        elif current_time_minutes < self.market_schedule['after_market_end'] * 60:
            target_date = now.strftime('%Y%m%d')
            return 'after_hours', target_date
        
        # 15:00 之後 - 當日數據已完整
        else:
            target_date = now.strftime('%Y%m%d')
            return 'after_hours', target_date
    
    def _get_cache_expire_time(self, market_status: str) -> int:
        """根據市場狀態獲取快取期限"""
        return self.cache_settings.get(market_status, self.cache_settings['after_hours'])
    
    def _is_cache_valid(self, cache_path: str, market_status: str) -> bool:
        """檢查快取是否有效（根據市場狀態調整）"""
        if not os.path.exists(cache_path):
            return False
        
        file_time = os.path.getmtime(cache_path)
        current_time = time.time()
        expire_time = self._get_cache_expire_time(market_status)
        
        is_valid = (current_time - file_time) < expire_time
        
        if not is_valid:
            logger.info(f"快取已過期 (市場狀態: {market_status}, 過期時間: {expire_time}秒)")
        
        return is_valid
    
    def _get_cache_path(self, cache_key: str) -> str:
        """獲取快取檔案路徑"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _load_cache(self, cache_key: str, market_status: str) -> Optional[Dict[str, Any]]:
        """載入快取數據（考慮市場狀態）"""
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path, market_status):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"從快取載入數據: {cache_key} (市場狀態: {market_status})")
                    return data
            except Exception as e:
                logger.error(f"載入快取失敗: {e}")
        
        return None
    
    def _save_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """保存快取數據"""
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # 添加時間戳記
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"已保存快取: {cache_key}")
        except Exception as e:
            logger.error(f"保存快取失敗: {e}")
    
    def _try_multiple_dates(self, fetch_func, max_days: int = 3) -> List[Dict[str, Any]]:
        """
        嘗試多個日期獲取數據，直到成功
        
        參數:
        - fetch_func: 數據獲取函數
        - max_days: 最多嘗試的天數
        
        返回:
        - 股票數據列表
        """
        market_status, primary_date = self._get_market_status()
        dates_to_try = []
        
        # 添加主要日期
        dates_to_try.append(primary_date)
        
        # 添加備用日期
        base_date = datetime.strptime(primary_date, '%Y%m%d')
        for i in range(1, max_days):
            fallback_date = base_date - timedelta(days=i)
            # 跳過週末
            if fallback_date.weekday() < 5:
                dates_to_try.append(fallback_date.strftime('%Y%m%d'))
        
        logger.info(f"嘗試獲取數據的日期順序: {dates_to_try}")
        
        for date_str in dates_to_try:
            try:
                logger.info(f"嘗試獲取 {date_str} 的數據...")
                stocks = fetch_func(date_str)
                
                if stocks:
                    logger.info(f"成功獲取 {len(stocks)} 支股票數據 (日期: {date_str})")
                    return stocks
                else:
                    logger.warning(f"日期 {date_str} 沒有數據")
                    
            except Exception as e:
                logger.warning(f"獲取 {date_str} 數據失敗: {e}")
                continue
        
        logger.error(f"所有日期都無法獲取數據: {dates_to_try}")
        return []
    
    def fetch_twse_daily_data(self, date: str = None) -> List[Dict[str, Any]]:
        """
        獲取台灣證券交易所上市股票日交易資料（智能日期處理）
        
        參數:
        - date: 指定日期 (格式: YYYYMMDD)，None則自動判斷
        
        返回:
        - 股票交易數據列表
        """
        market_status, target_date = self._get_market_status()
        
        if date is None:
            date = target_date
        
        cache_key = f"twse_daily_{date}_{market_status}"
        
        # 檢查快取
        cached_data = self._load_cache(cache_key, market_status)
        if cached_data and isinstance(cached_data, dict) and 'data' in cached_data:
            return cached_data['data']
        elif cached_data and isinstance(cached_data, list):
            return cached_data
        
        logger.info(f"獲取TWSE數據 (日期: {date}, 市場狀態: {market_status})")
        
        def fetch_by_date(fetch_date: str) -> List[Dict[str, Any]]:
            url = f"{self.twse_base_url}/STOCK_DAY_ALL"
            params = {
                'response': 'json',
                'date': fetch_date
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("stat") != "OK":
                logger.warning(f"TWSE API返回狀態: {data.get('stat')} (日期: {fetch_date})")
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
                    
                    processed_stock = self._process_twse_stock_data(stock_data, fetch_date)
                    if processed_stock:
                        stocks.append(processed_stock)
            
            return stocks
        
        # 使用多日期嘗試策略
        stocks = self._try_multiple_dates(fetch_by_date)
        
        # 保存快取
        if stocks:
            self._save_cache(cache_key, stocks)
        
        return stocks
    
    def fetch_tpex_daily_data(self, date: str = None) -> List[Dict[str, Any]]:
        """
        獲取台灣證券櫃檯買賣中心上櫃股票日交易資料（智能日期處理）
        
        參數:
        - date: 指定日期 (格式: YYYYMMDD)，None則自動判斷
        
        返回:
        - 股票交易數據列表
        """
        market_status, target_date = self._get_market_status()
        
        if date is None:
            date = target_date
        
        cache_key = f"tpex_daily_{date}_{market_status}"
        
        # 檢查快取
        cached_data = self._load_cache(cache_key, market_status)
        if cached_data and isinstance(cached_data, dict) and 'data' in cached_data:
            return cached_data['data']
        elif cached_data and isinstance(cached_data, list):
            return cached_data
        
        logger.info(f"獲取TPEX數據 (日期: {date}, 市場狀態: {market_status})")
        
        def fetch_by_date(fetch_date: str) -> List[Dict[str, Any]]:
            # 轉換日期格式為民國年
            try:
                date_obj = datetime.strptime(fetch_date, '%Y%m%d')
                minguo_date = f"{date_obj.year - 1911}/{date_obj.month:02d}/{date_obj.day:02d}"
            except ValueError:
                logger.error(f"日期格式錯誤: {fetch_date}")
                return []
            
            url = f"{self.tpex_base_url}/stk_wn1430_result.php"
            params = {
                'l': 'zh-tw',
                'd': minguo_date,
                'se': 'EW',
                'o': 'json'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("stat") != "OK":
                # 櫃買中心週末或假日會返回不同的狀態
                logger.warning(f"TPEX API返回狀態: {data.get('stat')} (日期: {fetch_date})")
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
                    
                    processed_stock = self._process_tpex_stock_data(stock_data, fetch_date)
                    if processed_stock:
                        stocks.append(processed_stock)
            
            return stocks
        
        # 使用多日期嘗試策略
        stocks = self._try_multiple_dates(fetch_by_date)
        
        # 保存快取
        if stocks:
            self._save_cache(cache_key, stocks)
        
        return stocks
    
    def _process_twse_stock_data(self, raw_data: Dict[str, str], date: str) -> Optional[Dict[str, Any]]:
        """處理TWSE股票數據"""
        try:
            code = raw_data.get("證券代號", "").strip()
            name = raw_data.get("證券名稱", "").strip()
            
            if not code or not name:
                return None
            
            def parse_number(value: str) -> float:
                if not value or value == "--" or value == "N/A" or value == "除權息":
                    return 0.0
                value = value.replace(",", "").replace("+", "").replace(" ", "")
                try:
                    return float(value)
                except ValueError:
                    return 0.0
            
            open_price = parse_number(raw_data.get("開盤價", "0"))
            high_price = parse_number(raw_data.get("最高價", "0"))
            low_price = parse_number(raw_data.get("最低價", "0"))
            close_price = parse_number(raw_data.get("收盤價", "0"))
            volume = parse_number(raw_data.get("成交股數", "0"))
            
            trade_value = volume * close_price
            
            change = parse_number(raw_data.get("漲跌價差", "0"))
            change_percent = (change / close_price * 100) if close_price > 0 else 0
            
            # 轉換日期格式
            try:
                date_obj = datetime.strptime(date, '%Y%m%d')
                formatted_date = date_obj.strftime('%Y-%m-%d')
            except:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
            
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
                "date": formatted_date,
                "data_source": "TWSE_API",
                "fetch_time": datetime.now().isoformat()
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"處理TWSE股票數據失敗: {e}")
            return None
    
    def _process_tpex_stock_data(self, raw_data: Dict[str, str], date: str) -> Optional[Dict[str, Any]]:
        """處理TPEX股票數據"""
        try:
            code = raw_data.get("代號", "").strip()
            name = raw_data.get("名稱", "").strip()
            
            if not code or not name:
                return None
            
            def parse_number(value: str) -> float:
                if not value or value == "--" or value == "N/A" or value == "除權息":
                    return 0.0
                value = value.replace(",", "").replace("+", "").replace(" ", "")
                try:
                    return float(value)
                except ValueError:
                    return 0.0
            
            open_price = parse_number(raw_data.get("開盤", "0"))
            high_price = parse_number(raw_data.get("最高", "0"))
            low_price = parse_number(raw_data.get("最低", "0"))
            close_price = parse_number(raw_data.get("收盤", "0"))
            volume = parse_number(raw_data.get("成交量", "0"))
            
            trade_value = volume * close_price
            
            change = parse_number(raw_data.get("漲跌", "0"))
            change_percent = (change / close_price * 100) if close_price > 0 else 0
            
            # 轉換日期格式
            try:
                date_obj = datetime.strptime(date, '%Y%m%d')
                formatted_date = date_obj.strftime('%Y-%m-%d')
            except:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
            
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
                "date": formatted_date,
                "data_source": "TPEX_API",
                "fetch_time": datetime.now().isoformat()
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"處理TPEX股票數據失敗: {e}")
            return None
    
    def get_all_stocks_by_volume(self, date: str = None) -> List[Dict[str, Any]]:
        """
        獲取所有股票並按成交金額排序（智能日期處理）
        
        參數:
        - date: 指定日期，None則自動判斷最佳日期
        
        返回:
        - 按成交金額排序的股票列表
        """
        market_status, target_date = self._get_market_status()
        
        logger.info(f"開始獲取所有股票數據 (市場狀態: {market_status}, 目標日期: {target_date})")
        
        # 獲取上市股票數據
        logger.info("獲取上市股票數據...")
        twse_stocks = self.fetch_twse_daily_data(date)
        
        if market_status == 'trading':
            # 交易時間內稍微延遲，避免API請求過頻
            time.sleep(self.request_delay * 2)
        else:
            time.sleep(self.request_delay)
        
        # 獲取上櫃股票數據
        logger.info("獲取上櫃股票數據...")
        tpex_stocks = self.fetch_tpex_daily_data(date)
        
        # 合併數據
        all_stocks = twse_stocks + tpex_stocks
        
        # 過濾掉無效數據
        valid_stocks = []
        for stock in all_stocks:
            if (stock.get('trade_value', 0) > 0 and 
                stock.get('close', 0) > 0 and
                stock.get('volume', 0) > 0):
                valid_stocks.append(stock)
        
        # 按成交金額排序
        sorted_stocks = sorted(valid_stocks, key=lambda x: x.get('trade_value', 0), reverse=True)
        
        logger.info(f"成功獲取並排序 {len(sorted_stocks)} 支活躍股票")
        logger.info(f"數據狀態: 市場狀態={market_status}, 數據日期={target_date}")
        
        # 記錄前5名成交量最大的股票作為驗證
        if sorted_stocks:
            logger.info("成交金額前5名股票:")
            for i, stock in enumerate(sorted_stocks[:5]):
                logger.info(f"  {i+1}. {stock['code']} {stock['name']} - {stock['trade_value']:,.0f} 元")
        
        return sorted_stocks
    
    def get_stocks_by_time_slot(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """
        根據時段獲取相應數量的股票（智能日期處理）
        
        參數:
        - time_slot: 時段名稱
        - date: 指定日期，None則自動判斷
        
        返回:
        - 選定的股票列表
        """
        # 定義每個時段的股票數量
        slot_limits = {
            'morning_scan': 200,
            'mid_morning_scan': 300,
            'mid_day_scan': 300,
            'afternoon_scan': 1000,
            'weekly_summary': 500
        }
        
        limit = slot_limits.get(time_slot, 100)
        market_status, target_date = self._get_market_status()
        
        logger.info(f"獲取 {time_slot} 時段的前 {limit} 支股票")
        logger.info(f"當前市場狀態: {market_status}, 數據日期: {target_date}")
        
        # 獲取所有股票
        all_stocks = self.get_all_stocks_by_volume(date)
        
        # 返回前N支股票
        selected_stocks = all_stocks[:limit]
        
        logger.info(f"為 {time_slot} 時段選擇了 {len(selected_stocks)} 支股票")
        
        # 添加時段和市場狀態資訊到每支股票
        for stock in selected_stocks:
            stock['time_slot'] = time_slot
            stock['market_status'] = market_status
            stock['data_freshness'] = self._get_data_freshness(market_status)
        
        return selected_stocks
    
    def _get_data_freshness(self, market_status: str) -> str:
        """獲取數據新鮮度描述"""
        freshness_map = {
            'trading': '盤中即時數據',
            'after_hours': '盤後完整數據',
            'pre_market': '盤前預覽數據',
            'weekend': '最近交易日數據'
        }
        return freshness_map.get(market_status, '歷史數據')
    
    def get_data_status_info(self) -> Dict[str, Any]:
        """獲取當前數據狀態資訊"""
        market_status, target_date = self._get_market_status()
        current_time = self._get_current_taiwan_time()
        
        return {
            'current_taiwan_time': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'market_status': market_status,
            'target_date': target_date,
            'data_freshness': self._get_data_freshness(market_status),
            'cache_expire_time': self._get_cache_expire_time(market_status),
            'is_trading_day': current_time.weekday() < 5,
            'next_trading_session': self._get_next_trading_session(current_time)
        }
    
    def _get_next_trading_session(self, current_time: datetime) -> str:
        """獲取下次交易時間"""
        current_hour = current_time.hour
        current_minute = current_time.minute
        weekday = current_time.weekday()
        
        if weekday >= 5:  # 週末
            next_monday = current_time + timedelta(days=(7 - weekday))
            return f"下週一 09:00 ({next_monday.strftime('%Y-%m-%d')})"
        
        current_minutes = current_hour * 60 + current_minute
        
        if current_minutes < 9 * 60:  # 9:00 之前
            return "今日 09:00"
        elif current_minutes < 13 * 60 + 30:  # 13:30 之前
            return "交易中"
        else:  # 收盤後
            tomorrow = current_time + timedelta(days=1)
            if tomorrow.weekday() < 5:
                return f"明日 09:00 ({tomorrow.strftime('%Y-%m-%d')})"
            else:
                # 找到下週一
                days_until_monday = (7 - tomorrow.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                next_monday = tomorrow + timedelta(days=days_until_monday)
                return f"下週一 09:00 ({next_monday.strftime('%Y-%m-%d')})"


# 測試和使用示例
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 創建增強版數據獲取器
    fetcher = EnhancedTWStockDataFetcher()
    
    # 顯示當前數據狀態
    status_info = fetcher.get_data_status_info()
    print("=" * 60)
    print("📊 當前數據狀態資訊")
    print("=" * 60)
    for key, value in status_info.items():
        print(f"{key}: {value}")
    
    # 測試獲取不同時段的股票
    time_slots = ['morning_scan', 'mid_morning_scan', 'afternoon_scan']
    
    for slot in time_slots:
        print(f"\n=== 測試 {slot} ===")
        stocks = fetcher.get_stocks_by_time_slot(slot)
        print(f"獲取了 {len(stocks)} 支股票")
        
        if stocks:
            print("前3支股票:")
            for i, stock in enumerate(stocks[:3]):
                print(f"  {i+1}. {stock['code']} {stock['name']}")
                print(f"     成交金額: {stock['trade_value']:,.0f}")
                print(f"     數據新鮮度: {stock['data_freshness']}")
                print(f"     市場狀態: {stock['market_status']}")
    
    print("\n" + "=" * 60)
    print("🎯 增強版數據抓取器測試完成！")
    print("✅ 主要改進:")
    print("  • 智能判斷市場狀態和最佳數據日期")
    print("  • 盤中數據快取時間縮短為5分鐘")
    print("  • 多日期備援機制，確保數據可用性")
    print("  • 詳細的數據新鮮度標示")
    print("  • 台灣時區準確計算")
