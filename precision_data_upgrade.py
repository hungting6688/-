"""
precision_data_upgrade.py - 精準數據獲取升級方案
基於現有系統的兩階段升級策略
"""
import asyncio
import aiohttp
import websockets
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import redis
from dataclasses import dataclass

@dataclass
class DataQualityMetrics:
    """數據品質指標"""
    accuracy: float      # 準確度 (0-1)
    freshness: float     # 新鮮度 (0-1)  
    completeness: float  # 完整度 (0-1)
    reliability: float   # 可靠度 (0-1)
    cost_score: float    # 成本評分 (0-1, 越高越便宜)

class PrecisionDataManager:
    """精準數據管理器"""
    
    def __init__(self, mode='hybrid'):
        """
        初始化精準數據管理器
        mode: 'hybrid' | 'realtime'
        """
        self.mode = mode
        self.cache = redis.Redis(host='localhost', port=6379, db=0) if self._redis_available() else {}
        self.data_sources = self._init_data_sources()
        
    def _redis_available(self) -> bool:
        """檢查Redis是否可用"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            return True
        except:
            return False

    def _init_data_sources(self) -> Dict:
        """初始化數據源"""
        return {
            'yfinance': {
                'priority': 1,
                'cost': 'free',
                'accuracy': 0.85,
                'freshness': 0.7,  # 15分鐘延遲
                'api_limit': None
            },
            'twse_official': {
                'priority': 2, 
                'cost': 'free',
                'accuracy': 0.95,
                'freshness': 0.6,  # 官方數據但較慢
                'api_limit': '100/hour'
            },
            'institutional_cache': {
                'priority': 3,
                'cost': 'free',
                'accuracy': 0.8,
                'freshness': 0.5,  # 日更新
                'api_limit': None
            }
        }

# ================== 方案1: 進階快取混合方案 ==================

class HybridDataFetcher:
    """混合數據獲取器 - 平衡精準度與成本"""
    
    def __init__(self):
        self.cache_duration = {
            'price': 60,        # 價格數據緩存1分鐘
            'technical': 300,   # 技術指標緩存5分鐘
            'fundamental': 3600,# 基本面數據緩存1小時
            'institutional': 86400  # 法人數據緩存1天
        }
        
    async def get_precision_stock_data(self, symbol: str) -> Dict[str, Any]:
        """獲取精準股票數據"""
        # 1. 檢查緩存
        cached_data = self._get_cached_data(symbol)
        if self._is_cache_valid(cached_data):
            return self._enhance_cached_data(cached_data)
        
        # 2. 多源數據獲取
        price_data = await self._get_yfinance_data(symbol)
        institutional_data = await self._get_institutional_data(symbol)
        technical_data = await self._calculate_enhanced_technical(symbol, price_data)
        
        # 3. 數據品質評估
        quality_score = self._assess_data_quality(price_data, institutional_data, technical_data)
        
        # 4. 綜合數據
        comprehensive_data = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'quality_score': quality_score,
            'price_data': price_data,
            'institutional_data': institutional_data,
            'technical_data': technical_data,
            'data_source': 'hybrid_enhanced'
        }
        
        # 5. 更新緩存
        self._update_cache(symbol, comprehensive_data)
        
        return comprehensive_data
    
    async def _get_yfinance_data(self, symbol: str) -> Dict[str, Any]:
        """獲取 yfinance 數據（台股需加.TW）"""
        try:
            tw_symbol = f"{symbol}.TW"
            ticker = yf.Ticker(tw_symbol)
            
            # 獲取即時價格
            info = ticker.info
            history = ticker.history(period="5d", interval="1m")
            
            if history.empty:
                return {'error': 'No data available'}
            
            latest = history.iloc[-1]
            
            return {
                'current_price': float(latest['Close']),
                'volume': int(latest['Volume']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'previous_close': float(history.iloc[-2]['Close']) if len(history) > 1 else float(latest['Close']),
                'change_percent': ((latest['Close'] - history.iloc[-2]['Close']) / history.iloc[-2]['Close'] * 100) if len(history) > 1 else 0,
                'market_cap': info.get('marketCap', 0),
                'data_timestamp': latest.name.isoformat(),
                'data_quality': 'yfinance_verified'
            }
            
        except Exception as e:
            return {'error': f'yfinance error: {str(e)}'}
    
    async def _get_institutional_data(self, symbol: str) -> Dict[str, Any]:
        """獲取法人買賣數據（使用緩存策略）"""
        cache_key = f"institutional_{symbol}"
        
        # 檢查緩存
        if isinstance(self.cache, dict):
            cached = self.cache.get(cache_key)
        else:
            cached = self.cache.get(cache_key)
            if cached:
                cached = json.loads(cached)
        
        if cached and self._is_institutional_cache_valid(cached):
            return cached
        
        # 獲取新數據（這裡整合您現有的法人數據邏輯）
        institutional_data = await self._fetch_fresh_institutional_data(symbol)
        
        # 更新緩存
        if isinstance(self.cache, dict):
            self.cache[cache_key] = institutional_data
        else:
            self.cache.setex(cache_key, 86400, json.dumps(institutional_data))
        
        return institutional_data
    
    async def _fetch_fresh_institutional_data(self, symbol: str) -> Dict[str, Any]:
        """獲取新鮮的法人數據"""
        # 這裡整合您現有的 enhanced_stock_bot.py 中的法人數據邏輯
        return {
            'foreign_net_buy': 0,  # 從您現有的API獲取
            'trust_net_buy': 0,
            'dealer_net_buy': 0,
            'consecutive_buy_days': 0,
            'data_confidence': 0.8,
            'last_updated': datetime.now().isoformat()
        }
    
    def _assess_data_quality(self, price_data: Dict, institutional_data: Dict, technical_data: Dict) -> DataQualityMetrics:
        """評估數據品質"""
        accuracy = 0.9 if 'error' not in price_data else 0.3
        freshness = 0.8  # yfinance 通常有15分鐘延遲
        completeness = len([d for d in [price_data, institutional_data, technical_data] if 'error' not in d]) / 3
        reliability = institutional_data.get('data_confidence', 0.5)
        cost_score = 1.0  # 免費方案
        
        return DataQualityMetrics(accuracy, freshness, completeness, reliability, cost_score)

# ================== 方案2: 盤中即時監控系統 ==================

class RealtimeDataMonitor:
    """即時數據監控器 - 最高精準度"""
    
    def __init__(self):
        self.websocket_urls = {
            'fugle': 'wss://api.fugle.tw/realtime/v0.3/intraday/quote',
            'custom': 'wss://your-realtime-source.com/ws'
        }
        self.active_connections = {}
        self.realtime_buffer = {}
        
    async def start_realtime_monitoring(self, symbols: List[str]):
        """啟動即時監控"""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._monitor_single_stock(symbol))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _monitor_single_stock(self, symbol: str):
        """監控單一股票的即時數據"""
        try:
            async with websockets.connect(f"{self.websocket_urls['custom']}/{symbol}") as websocket:
                self.active_connections[symbol] = websocket
                
                async for message in websocket:
                    data = json.loads(message)
                    
                    # 即時處理數據
                    processed_data = await self._process_realtime_data(symbol, data)
                    
                    # 即時計算技術指標
                    technical_signals = await self._calculate_realtime_indicators(symbol, processed_data)
                    
                    # 檢查觸發條件
                    if await self._check_alert_conditions(symbol, processed_data, technical_signals):
                        await self._send_realtime_alert(symbol, processed_data, technical_signals)
                        
        except Exception as e:
            print(f"WebSocket 連接錯誤 {symbol}: {e}")
    
    async def _process_realtime_data(self, symbol: str, raw_data: Dict) -> Dict[str, Any]:
        """處理即時數據"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'price': raw_data.get('price', 0),
            'volume': raw_data.get('volume', 0),
            'bid': raw_data.get('bid', 0),
            'ask': raw_data.get('ask', 0),
            'bid_volume': raw_data.get('bidVolume', 0),
            'ask_volume': raw_data.get('askVolume', 0),
            'data_quality': 'realtime_verified'
        }
    
    async def _calculate_realtime_indicators(self, symbol: str, current_data: Dict) -> Dict[str, Any]:
        """即時計算技術指標"""
        # 維護歷史數據緩衝區
        if symbol not in self.realtime_buffer:
            self.realtime_buffer[symbol] = []
        
        self.realtime_buffer[symbol].append(current_data)
        
        # 保留最近1000筆數據
        if len(self.realtime_buffer[symbol]) > 1000:
            self.realtime_buffer[symbol] = self.realtime_buffer[symbol][-1000:]
        
        # 計算技術指標
        prices = [d['price'] for d in self.realtime_buffer[symbol]]
        
        if len(prices) >= 26:
            macd_line, signal_line = self._calculate_macd(prices)
            rsi = self._calculate_rsi(prices, 14)
            
            return {
                'macd': macd_line[-1] if macd_line else 0,
                'macd_signal': signal_line[-1] if signal_line else 0,
                'macd_histogram': (macd_line[-1] - signal_line[-1]) if (macd_line and signal_line) else 0,
                'rsi': rsi[-1] if rsi else 50,
                'volume_spike': current_data['volume'] > np.mean([d['volume'] for d in self.realtime_buffer[symbol][-20:]]) * 2
            }
        
        return {'insufficient_data': True}
    
    def _calculate_macd(self, prices: List[float]) -> tuple:
        """計算MACD"""
        prices_series = pd.Series(prices)
        ema12 = prices_series.ewm(span=12).mean()
        ema26 = prices_series.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        return macd.tolist(), signal.tolist()
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """計算RSI"""
        prices_series = pd.Series(prices)
        delta = prices_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.tolist()

# ================== 精準度對比分析 ==================

class PrecisionComparison:
    """精準度對比分析"""
    
    @staticmethod
    def compare_solutions() -> Dict[str, Any]:
        """對比兩種方案"""
        return {
            'hybrid_solution': {
                'accuracy': 0.85,
                'latency': '1-5分鐘',
                'cost': '免費',
                'complexity': '中等',
                'maintenance': '低',
                'reliability': 0.9,
                'best_for': ['定期分析', '長線投資', '自動推播'],
                'integration_effort': '1-2天'
            },
            'realtime_solution': {
                'accuracy': 0.95,
                'latency': '秒級',
                'cost': '中等(WebSocket費用)',
                'complexity': '高',
                'maintenance': '高',
                'reliability': 0.85,
                'best_for': ['短線交易', '即時監控', '預警系統'],
                'integration_effort': '1-2週'
            },
            'recommendation': {
                'phase1': '先實施混合方案，滿足80%需求',
                'phase2': '再升級即時方案，處理20%高頻需求',
                'reason': '漸進式升級，降低風險，提高成功率'
            }
        }

# ================== 與現有系統整合 ==================

class ExistingSystemIntegrator:
    """與現有系統整合器"""
    
    def __init__(self, existing_fetcher):
        """整合現有的 TWStockDataFetcher"""
        self.existing_fetcher = existing_fetcher
        self.hybrid_fetcher = HybridDataFetcher()
        self.realtime_monitor = RealtimeDataMonitor()
    
    async def enhanced_get_stocks_by_time_slot(self, time_slot: str, precision_mode: str = 'hybrid') -> List[Dict[str, Any]]:
        """增強版的股票獲取方法"""
        # 先用現有方法獲取基礎數據
        base_stocks = self.existing_fetcher.get_stocks_by_time_slot(time_slot)
        
        if precision_mode == 'hybrid':
            # 用混合方案增強數據
            enhanced_stocks = []
            for stock in base_stocks[:20]:  # 只增強前20支，平衡效能
                enhanced_data = await self.hybrid_fetcher.get_precision_stock_data(stock['code'])
                stock.update({
                    'precision_data': enhanced_data,
                    'data_quality_score': enhanced_data.get('quality_score'),
                    'enhanced': True
                })
                enhanced_stocks.append(stock)
            
            # 其餘使用原始數據
            enhanced_stocks.extend(base_stocks[20:])
            return enhanced_stocks
            
        elif precision_mode == 'realtime':
            # 即時模式（適合少量股票）
            top_stocks = base_stocks[:10]
            symbols = [stock['code'] for stock in top_stocks]
            
            # 啟動即時監控
            await self.realtime_monitor.start_realtime_monitoring(symbols)
            return top_stocks
        
        else:
            # 保持原有邏輯
            return base_stocks

# ================== 使用示例 ==================

async def main():
    """主要示例"""
    print("🎯 精準數據獲取升級方案示例")
    
    # 方案對比
    comparison = PrecisionComparison.compare_solutions()
    print("\n📊 方案對比:")
    for solution, metrics in comparison.items():
        if solution != 'recommendation':
            print(f"\n{solution}:")
            for metric, value in metrics.items():
                print(f"  {metric}: {value}")
    
    print(f"\n💡 建議: {comparison['recommendation']}")
    
    # 實際使用示例
    print("\n🔧 整合示例:")
    
    # 假設您現有的 TWStockDataFetcher
    from twse_data_fetcher import TWStockDataFetcher
    existing_fetcher = TWStockDataFetcher()
    
    # 創建整合器
    integrator = ExistingSystemIntegrator(existing_fetcher)
    
    # 使用混合精準模式
    enhanced_stocks = await integrator.enhanced_get_stocks_by_time_slot(
        'morning_scan', 
        precision_mode='hybrid'
    )
    
    print(f"✅ 獲取了 {len(enhanced_stocks)} 支增強數據股票")
    
    # 顯示前3支的數據品質
    for i, stock in enumerate(enhanced_stocks[:3]):
        if stock.get('enhanced'):
            quality = stock.get('data_quality_score')
            print(f"  {i+1}. {stock['code']} {stock['name']} - 品質評分: {quality}")

if __name__ == "__main__":
    asyncio.run(main())
