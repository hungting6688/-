"""
global_economic_monitor.py - 全球經濟指標監控系統
獲取和分析全球主要股市指數、經濟指標
"""
import os
import json
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class GlobalEconomicMonitor:
    """全球經濟指標監控器"""
    
    def __init__(self, cache_dir: str = 'cache/global'):
        """初始化全球經濟監控器"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 全球指數代碼映射
        self.global_indices = {
            # 美國市場
            'SPX': {'name': 'S&P 500', 'region': 'US', 'symbol': '^GSPC'},
            'NASDAQ': {'name': 'NASDAQ', 'region': 'US', 'symbol': '^IXIC'},
            'DOW': {'name': 'Dow Jones', 'region': 'US', 'symbol': '^DJI'},
            'VIX': {'name': 'VIX恐慌指數', 'region': 'US', 'symbol': '^VIX'},
            
            # 亞洲市場
            'NIKKEI': {'name': '日經225', 'region': 'Japan', 'symbol': '^N225'},
            'HSI': {'name': '恆生指數', 'region': 'HongKong', 'symbol': '^HSI'},
            'KOSPI': {'name': '韓國KOSPI', 'region': 'Korea', 'symbol': '^KS11'},
            'TWII': {'name': '台灣加權', 'region': 'Taiwan', 'symbol': '^TWII'},
            
            # 歐洲市場
            'DAX': {'name': '德國DAX', 'region': 'Germany', 'symbol': '^GDAXI'},
            'FTSE': {'name': '英國FTSE', 'region': 'UK', 'symbol': '^FTSE'},
            'CAC': {'name': '法國CAC', 'region': 'France', 'symbol': '^FCHI'},
            
            # 大宗商品和貨幣
            'GOLD': {'name': '黃金', 'region': 'Commodity', 'symbol': 'GC=F'},
            'OIL': {'name': '原油', 'region': 'Commodity', 'symbol': 'CL=F'},
            'DXY': {'name': '美元指數', 'region': 'Currency', 'symbol': 'DX-Y.NYB'},
        }
        
        # 經濟指標
        self.economic_indicators = {
            'US10Y': {'name': '美國10年期公債', 'type': 'bond'},
            'USD_TWD': {'name': '美元兌台幣', 'type': 'fx'},
            'USD_JPY': {'name': '美元兌日圓', 'type': 'fx'},
        }
        
        # API 設定（可使用 Yahoo Finance 或其他免費API）
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 快取時間（分鐘）
        self.cache_duration = {
            'market_hours': 5,      # 交易時間5分鐘
            'after_hours': 30,      # 盤後30分鐘
            'weekend': 240          # 週末4小時
        }
    
    def get_global_indices_data(self) -> Dict[str, Any]:
        """獲取全球主要指數數據"""
        cache_key = 'global_indices_data'
        
        # 檢查快取
        cached_data = self._load_cache(cache_key)
        if cached_data:
            return cached_data
        
        logger.info("正在獲取全球指數數據...")
        
        indices_data = {}
        
        # 使用Yahoo Finance API獲取數據
        for code, info in self.global_indices.items():
            try:
                data = self._fetch_yahoo_data(info['symbol'])
                if data:
                    indices_data[code] = {
                        'name': info['name'],
                        'region': info['region'],
                        'price': data['price'],
                        'change': data['change'],
                        'change_percent': data['change_percent'],
                        'timestamp': data['timestamp']
                    }
                time.sleep(0.5)  # 避免API限制
            except Exception as e:
                logger.error(f"獲取 {code} 數據失敗: {e}")
                continue
        
        # 保存快取
        if indices_data:
            self._save_cache(cache_key, indices_data)
        
        return indices_data
    
    def _fetch_yahoo_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """從Yahoo Finance獲取數據"""
        try:
            # Yahoo Finance 查詢API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'range': '1d',
                'interval': '1m',
                'includePrePost': 'true'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' not in data or not data['chart']['result']:
                return None
            
            result = data['chart']['result'][0]
            meta = result['meta']
            
            current_price = meta.get('regularMarketPrice', 0)
            previous_close = meta.get('previousClose', 0)
            
            if current_price and previous_close:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
                
                return {
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'timestamp': datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"獲取Yahoo數據失敗 {symbol}: {e}")
        
        return None
    
    def analyze_global_sentiment(self) -> Dict[str, Any]:
        """分析全球市場情緒"""
        indices_data = self.get_global_indices_data()
        
        if not indices_data:
            return {'error': '無法獲取全球指數數據'}
        
        # 區域分析
        regional_performance = {}
        regions = ['US', 'Japan', 'HongKong', 'Korea', 'Germany', 'UK']
        
        for region in regions:
            region_indices = {k: v for k, v in indices_data.items() if v['region'] == region}
            if region_indices:
                changes = [data['change_percent'] for data in region_indices.values()]
                regional_performance[region] = {
                    'avg_change': round(np.mean(changes), 2),
                    'indices_count': len(region_indices),
                    'positive_count': sum(1 for c in changes if c > 0)
                }
        
        # 全球情緒評分計算
        all_changes = []
        for data in indices_data.values():
            if data['region'] != 'Commodity':  # 排除大宗商品
                all_changes.append(data['change_percent'])
        
        if all_changes:
            avg_change = np.mean(all_changes)
            positive_ratio = sum(1 for c in all_changes if c > 0) / len(all_changes)
            
            # 情緒評分 (-5 到 +5)
            sentiment_score = avg_change * 0.5 + (positive_ratio - 0.5) * 4
            
            # VIX影響
            vix_data = indices_data.get('VIX')
            if vix_data:
                vix_value = vix_data['price']
                if vix_value > 30:
                    sentiment_score -= 2  # 高恐慌減分
                elif vix_value < 15:
                    sentiment_score += 1  # 低恐慌加分
        else:
            sentiment_score = 0
        
        # 情緒分類
        if sentiment_score > 2:
            sentiment = "非常樂觀"
        elif sentiment_score > 0.5:
            sentiment = "樂觀"
        elif sentiment_score > -0.5:
            sentiment = "中性"
        elif sentiment_score > -2:
            sentiment = "悲觀"
        else:
            sentiment = "非常悲觀"
        
        return {
            'global_sentiment_score': round(sentiment_score, 2),
            'sentiment': sentiment,
            'regional_performance': regional_performance,
            'vix_value': indices_data.get('VIX', {}).get('price', 0),
            'total_indices': len(indices_data),
            'positive_indices': sum(1 for d in indices_data.values() if d.get('change_percent', 0) > 0),
            'analysis_time': datetime.now().isoformat()
        }
    
    def get_correlation_analysis(self) -> Dict[str, Any]:
        """分析各指數間的相關性"""
        try:
            # 這裡可以擴展為從歷史數據計算真實相關性
            # 暫時使用理論相關性
            correlations = {
                'SPX_NASDAQ': {'correlation': 0.85, 'description': '美國大型股與科技股高度相關'},
                'SPX_TWII': {'correlation': 0.65, 'description': '美股對台股有中高度影響'},
                'NIKKEI_HSI': {'correlation': 0.72, 'description': '亞洲市場間相關性較高'},
                'VIX_SPX': {'correlation': -0.78, 'description': '恐慌指數與美股呈負相關'},
                'GOLD_DXY': {'correlation': -0.68, 'description': '黃金與美元指數負相關'}
            }
            
            return {
                'correlations': correlations,
                'analysis_note': '基於歷史數據的理論相關性，實際相關性會隨市場環境變化',
                'update_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"相關性分析失敗: {e}")
            return {'error': '相關性分析失敗'}
    
    def get_economic_calendar(self) -> List[Dict[str, Any]]:
        """獲取重要經濟事件日曆（簡化版）"""
        # 這裡可以接入真實的經濟日曆API
        # 暫時使用模擬數據
        upcoming_events = [
            {
                'date': '2025-06-01',
                'event': '美國非農就業數據',
                'importance': 'HIGH',
                'impact': '美股、美元'
            },
            {
                'date': '2025-06-03',
                'event': '歐洲央行利率決議',
                'importance': 'HIGH',
                'impact': '歐股、歐元'
            },
            {
                'date': '2025-06-05',
                'event': '日本央行貨幣政策',
                'importance': 'MEDIUM',
                'impact': '日股、日圓'
            }
        ]
        
        return upcoming_events
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日全球市場報告"""
        logger.info("生成每日全球市場報告...")
        
        try:
            # 獲取各項分析
            sentiment_analysis = self.analyze_global_sentiment()
            indices_data = self.get_global_indices_data()
            correlation_analysis = self.get_correlation_analysis()
            economic_calendar = self.get_economic_calendar()
            
            # 生成摘要
            summary_points = []
            
            if 'global_sentiment_score' in sentiment_analysis:
                score = sentiment_analysis['global_sentiment_score']
                sentiment = sentiment_analysis['sentiment']
                summary_points.append(f"全球市場情緒{sentiment} (評分: {score:.1f})")
                
                # VIX 分析
                vix_value = sentiment_analysis.get('vix_value', 0)
                if vix_value > 25:
                    summary_points.append(f"VIX指數 {vix_value:.1f} 顯示市場恐慌情緒較高")
                elif vix_value < 15:
                    summary_points.append(f"VIX指數 {vix_value:.1f} 顯示市場情緒穩定")
                
                # 區域表現
                regional_perf = sentiment_analysis.get('regional_performance', {})
                best_region = max(regional_perf.items(), key=lambda x: x[1]['avg_change']) if regional_perf else None
                if best_region:
                    summary_points.append(f"{best_region[0]}市場表現最佳 (+{best_region[1]['avg_change']:.1f}%)")
            
            # 台股相關建議
            taiwan_suggestions = []
            if indices_data.get('SPX', {}).get('change_percent', 0) > 1:
                taiwan_suggestions.append("美股強勢，台股有望跟隨上漲")
            if indices_data.get('NIKKEI', {}).get('change_percent', 0) > 1:
                taiwan_suggestions.append("日股上漲，亞洲市場氣氛正面")
            
            report = {
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'summary': '。'.join(summary_points),
                'sentiment_analysis': sentiment_analysis,
                'indices_data': indices_data,
                'correlation_analysis': correlation_analysis,
                'economic_calendar': economic_calendar,
                'taiwan_investment_suggestions': taiwan_suggestions,
                'generated_time': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成每日報告失敗: {e}")
            return {
                'error': '生成報告失敗',
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'generated_time': datetime.now().isoformat()
            }
    
    def _load_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """載入快取"""
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            # 檢查快取是否過期
            file_time = os.path.getmtime(cache_file)
            current_time = time.time()
            
            # 根據時間決定快取期限
            now = datetime.now()
            if now.weekday() >= 5:  # 週末
                cache_limit = self.cache_duration['weekend'] * 60
            elif 9 <= now.hour <= 17:  # 營業時間
                cache_limit = self.cache_duration['market_hours'] * 60
            else:  # 盤後
                cache_limit = self.cache_duration['after_hours'] * 60
            
            if (current_time - file_time) > cache_limit:
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"載入快取失敗: {e}")
            return None
    
    def _save_cache(self, key: str, data: Dict[str, Any]) -> None:
        """保存快取"""
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存快取失敗: {e}")


# 測試代碼
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    monitor = GlobalEconomicMonitor()
    
    print("🌍 全球經濟指標監控系統測試")
    print("=" * 50)
    
    # 測試獲取全球指數
    print("📊 獲取全球指數數據...")
    indices = monitor.get_global_indices_data()
    if indices:
        print(f"成功獲取 {len(indices)} 個指數")
        for code, data in list(indices.items())[:5]:
            print(f"  {data['name']}: {data['price']} ({data['change_percent']:+.2f}%)")
    
    # 測試情緒分析
    print(f"\n📈 全球市場情緒分析...")
    sentiment = monitor.analyze_global_sentiment()
    if 'global_sentiment_score' in sentiment:
        print(f"全球情緒評分: {sentiment['global_sentiment_score']:.2f}")
        print(f"情緒狀態: {sentiment['sentiment']}")
    
    # 測試每日報告
    print(f"\n📋 生成每日報告...")
    report = monitor.generate_daily_report()
    if 'summary' in report:
        print(f"報告摘要: {report['summary']}")
    
    print(f"\n✅ 測試完成！")
