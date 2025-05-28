# ultimate_stock_recommender.py - 終極版股票推薦系統
"""
完整整合版增強股票推薦系統
整合功能：
1. 全球景氣分析
2. 社群情感分析 
3. 多因子模型
4. 機器學習融合
5. 風險管理
6. 替代數據
7. 自適應學習
8. 市場微結構
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import os
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_stock_system.log'),
        logging.StreamHandler()
    ]
)

class RiskLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low" 
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class MarketRegime(Enum):
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"

@dataclass
class StockRecommendation:
    """股票推薦結果"""
    code: str
    name: str
    sector: str
    final_score: float
    confidence: float
    risk_level: RiskLevel
    
    # 各模組分數
    fundamental_score: float
    technical_score: float
    sentiment_score: float
    macro_score: float
    ml_score: float
    alternative_data_score: float
    
    # 風險指標
    volatility: float
    beta: float
    var_95: float
    liquidity_risk: float
    
    # 預測信號
    target_price: Optional[float]
    price_trend: str
    hold_period: int
    
    # 額外資訊
    reasoning: str
    risk_factors: List[str]
    catalysts: List[str]
    timestamp: datetime

class GlobalEconomicAnalyzer:
    """全球經濟分析器"""
    
    def __init__(self):
        self.cache = {}
        self.last_update = None
        self.economic_indicators = {}
        
    async def get_global_economic_data(self) -> Dict:
        """獲取全球經濟數據"""
        try:
            # 美國數據
            us_data = await self._get_us_economic_data()
            
            # 中國數據  
            china_data = await self._get_china_economic_data()
            
            # 日本數據 (新增)
            japan_data = await self._get_japan_economic_data()
            
            # 台灣數據
            taiwan_data = await self._get_taiwan_economic_data()
            
            # 歐洲數據
            europe_data = await self._get_europe_economic_data()
            
            # 綜合分析
            global_score = self._calculate_global_score(us_data, china_data, japan_data, taiwan_data, europe_data)
            market_regime = self._determine_market_regime(global_score)
            
            return {
                'global_score': global_score,
                'market_regime': market_regime,
                'regional_data': {
                    'us': us_data,
                    'china': china_data,
                    'japan': japan_data,  # 新增日本數據
                    'taiwan': taiwan_data,
                    'europe': europe_data
                },
                'sector_outlook': self._get_sector_outlook(market_regime),
                'currency_outlook': self._get_currency_outlook(),
                'commodity_outlook': self._get_commodity_outlook(),
                'japan_taiwan_correlation': self._analyze_japan_taiwan_correlation(japan_data, taiwan_data),  # 新增相關性分析
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logging.error(f"獲取全球經濟數據失敗: {e}")
            return self._get_default_economic_data()
    
    async def _get_us_economic_data(self) -> Dict:
        """獲取美國經濟數據"""
        try:
            # 使用yfinance獲取美股指數和經濟指標
            spy = yf.Ticker("SPY")
            vix = yf.Ticker("^VIX") 
            tnx = yf.Ticker("^TNX")
            dxy = yf.Ticker("DX-Y.NYB")
            
            spy_data = spy.history(period="6mo")
            vix_data = vix.history(period="1mo")
            tnx_data = tnx.history(period="3mo")
            dxy_data = dxy.history(period="3mo")
            
            spy_momentum = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-60] - 1) * 100
            current_vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 20
            current_yield = tnx_data['Close'].iloc[-1] if not tnx_data.empty else 4.5
            dxy_level = dxy_data['Close'].iloc[-1] if not dxy_data.empty else 105
            
            return {
                'spy_momentum_3m': spy_momentum,
                'vix_level': current_vix,
                'ten_year_yield': current_yield,
                'dollar_index': dxy_level,
                'economic_score': self._calculate_us_score(spy_momentum, current_vix, current_yield)
            }
            
        except Exception as e:
            logging.warning(f"美國數據獲取失敗: {e}")
            return {'economic_score': 60, 'vix_level': 20, 'ten_year_yield': 4.5}
    
    async def _get_china_economic_data(self) -> Dict:
        """獲取中國經濟數據"""
        try:
            # 恆生指數作為中國市場代理
            hsi = yf.Ticker("^HSI")
            hsi_data = hsi.history(period="3mo")
            
            hsi_momentum = (hsi_data['Close'].iloc[-1] / hsi_data['Close'].iloc[-60] - 1) * 100 if len(hsi_data) >= 60 else 0
            
            # 模擬PMI數據 (實際可接入經濟數據API)
            manufacturing_pmi = np.random.normal(50.5, 1.5)
            services_pmi = np.random.normal(52, 2)
            
            return {
                'hsi_momentum_3m': hsi_momentum,
                'manufacturing_pmi': manufacturing_pmi,
                'services_pmi': services_pmi,
                'economic_score': self._calculate_china_score(hsi_momentum, manufacturing_pmi, services_pmi)
            }
            
        except Exception:
            return {'economic_score': 55, 'manufacturing_pmi': 50.2}
    
    async def _get_taiwan_economic_data(self) -> Dict:
        """獲取台灣經濟數據"""
        try:
            # 台股加權指數
            twii = yf.Ticker("^TWII")
            twii_data = twii.history(period="3mo")
            
            twii_momentum = (twii_data['Close'].iloc[-1] / twii_data['Close'].iloc[-60] - 1) * 100 if len(twii_data) >= 60 else 0
            
            # 模擬台灣經濟指標
            export_orders = np.random.normal(48, 3)  # 外銷訂單
            leading_index = np.random.normal(102, 2)  # 領先指標
            
            return {
                'twii_momentum_3m': twii_momentum,
                'export_orders_yoy': export_orders,
                'leading_index': leading_index,
                'economic_score': self._calculate_taiwan_score(twii_momentum, export_orders, leading_index)
            }
            
        except Exception:
            return {'economic_score': 58, 'twii_momentum_3m': 2.5}
    
    async def _get_europe_economic_data(self) -> Dict:
        """獲取歐洲經濟數據"""
        try:
            # 歐洲STOXX 50指數
            sx5e = yf.Ticker("^STOXX50E")
            sx5e_data = sx5e.history(period="3mo")
            
            europe_momentum = (sx5e_data['Close'].iloc[-1] / sx5e_data['Close'].iloc[-60] - 1) * 100 if len(sx5e_data) >= 60 else 0
            
            return {
                'stoxx50_momentum_3m': europe_momentum,
                'economic_score': max(0, min(100, 50 + europe_momentum))
            }
            
        except Exception:
            return {'economic_score': 52}
    
    def _calculate_global_score(self, us_data: Dict, china_data: Dict, japan_data: Dict, 
                               taiwan_data: Dict, europe_data: Dict) -> float:
        """計算全球經濟綜合分數"""
        # 調整權重，加入日本
        weights = {
            'us': 0.35,      # 美國權重略減
            'china': 0.20,   # 中國保持
            'japan': 0.15,   # 新增日本權重
            'taiwan': 0.15,  # 台灣保持
            'europe': 0.15   # 歐洲保持
        }
        
        global_score = (
            us_data['economic_score'] * weights['us'] +
            china_data['economic_score'] * weights['china'] +
            japan_data['economic_score'] * weights['japan'] +
            taiwan_data['economic_score'] * weights['taiwan'] +
            europe_data['economic_score'] * weights['europe']
        )
        
        return max(0, min(100, global_score))
    
    def _determine_market_regime(self, global_score: float) -> MarketRegime:
        """判斷市場狀態"""
        if global_score >= 75:
            return MarketRegime.BULL_MARKET
        elif global_score <= 35:
            return MarketRegime.BEAR_MARKET
        elif 45 <= global_score <= 65:
            return MarketRegime.SIDEWAYS
        else:
            return MarketRegime.HIGH_VOLATILITY
    
    def _get_sector_outlook(self, regime: MarketRegime) -> Dict:
        """獲取板塊展望"""
        sector_outlooks = {
            MarketRegime.BULL_MARKET: {
                'technology': 1.3, 'growth': 1.2, 'cyclical': 1.15, 'defensive': 0.9
            },
            MarketRegime.BEAR_MARKET: {
                'defensive': 1.2, 'utilities': 1.15, 'healthcare': 1.1, 'technology': 0.8
            },
            MarketRegime.SIDEWAYS: {
                'dividend': 1.1, 'value': 1.05, 'defensive': 1.0, 'growth': 0.95
            },
            MarketRegime.HIGH_VOLATILITY: {
                'low_beta': 1.15, 'defensive': 1.1, 'high_quality': 1.05, 'speculative': 0.7
            }
        }
        return sector_outlooks.get(regime, {})
    
    def _get_currency_outlook(self) -> Dict:
        """貨幣展望"""
        return {
            'usd_strength': 'neutral',
            'twd_outlook': 'stable', 
            'impact_on_exports': 'neutral'
        }
    
    def _get_commodity_outlook(self) -> Dict:
        """商品展望"""
        return {
            'oil_trend': 'stable',
            'gold_trend': 'neutral',
            'copper_trend': 'positive'
        }
    
    def _calculate_us_score(self, spy_momentum: float, vix: float, yield_rate: float) -> float:
        """計算美國經濟分數"""
        score = 50
        
        # S&P 500動能
        if spy_momentum > 10:
            score += 15
        elif spy_momentum > 5:
            score += 10
        elif spy_momentum > 0:
            score += 5
        elif spy_momentum < -10:
            score -= 15
        elif spy_momentum < -5:
            score -= 10
        
        # VIX恐慌指數
        if vix < 15:
            score += 10
        elif vix < 20:
            score += 5
        elif vix > 30:
            score -= 15
        elif vix > 25:
            score -= 8
        
        # 十年期公債殖利率
        if 3.5 <= yield_rate <= 5.0:
            score += 5
        elif yield_rate > 5.5:
            score -= 8
        elif yield_rate < 3.0:
            score -= 5
        
        return max(0, min(100, score))
    
    def _calculate_china_score(self, hsi_momentum: float, manufacturing_pmi: float, services_pmi: float) -> float:
        """計算中國經濟分數"""
        score = 50
        
        if hsi_momentum > 5:
            score += 10
        elif hsi_momentum < -10:
            score -= 10
        
        if manufacturing_pmi > 50:
            score += 8
        else:
            score -= 8
        
        if services_pmi > 50:
            score += 7
        else:
            score -= 7
        
        return max(0, min(100, score))
    
    def _calculate_taiwan_score(self, twii_momentum: float, export_orders: float, leading_index: float) -> float:
        """計算台灣經濟分數"""
        score = 50
        
        if twii_momentum > 5:
            score += 12
        elif twii_momentum < -5:
            score -= 12
        
        if export_orders > 0:
            score += 8
        else:
            score -= 8
        
        if leading_index > 100:
            score += 5
        else:
            score -= 5
        
        return max(0, min(100, score))
    
    def _get_default_economic_data(self) -> Dict:
        """預設經濟數據"""
        return {
            'global_score': 60,
            'market_regime': MarketRegime.SIDEWAYS,
            'regional_data': {},
            'sector_outlook': {'technology': 1.1, 'healthcare': 1.05},
            'timestamp': datetime.now()
        }

class SentimentAnalyzer:
    """社群情感分析器"""
    
    def __init__(self):
        self.session = None
        self.sentiment_cache = {}
        
    async def analyze_market_sentiment(self, stock_codes: List[str]) -> Dict:
        """分析市場整體和個股情感"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        market_sentiment = await self._analyze_overall_market_sentiment()
        
        individual_sentiments = {}
        for code in stock_codes[:20]:  # 限制處理數量
            individual_sentiments[code] = await self._analyze_stock_sentiment(code)
        
        return {
            'market_sentiment': market_sentiment,
            'individual_sentiments': individual_sentiments,
            'sentiment_extremes': self._find_sentiment_extremes(individual_sentiments),
            'fear_greed_index': self._calculate_fear_greed_index(market_sentiment)
        }
    
    async def _analyze_overall_market_sentiment(self) -> Dict:
        """分析整體市場情感"""
        try:
            # 模擬PTT股板整體情感分析
            ptt_sentiment = await self._get_ptt_overall_sentiment()
            
            # 模擬新聞情感
            news_sentiment = await self._get_news_sentiment()
            
            # 模擬Google搜尋趨勢
            search_trends = await self._get_search_trends(['台股', '股市', '投資'])
            
            composite_sentiment = (ptt_sentiment * 0.4 + news_sentiment * 0.35 + search_trends * 0.25)
            
            return {
                'composite_score': composite_sentiment,
                'ptt_sentiment': ptt_sentiment,
                'news_sentiment': news_sentiment,
                'search_trends': search_trends,
                'market_mood': self._classify_market_mood(composite_sentiment)
            }
            
        except Exception as e:
            logging.warning(f"市場情感分析失敗: {e}")
            return {'composite_score': 0, 'market_mood': 'neutral'}
    
    async def _analyze_stock_sentiment(self, stock_code: str) -> Dict:
        """分析個股情感"""
        try:
            # 檢查快取
            if stock_code in self.sentiment_cache:
                cache_time = self.sentiment_cache[stock_code]['timestamp']
                if datetime.now() - cache_time < timedelta(hours=1):
                    return self.sentiment_cache[stock_code]['data']
            
            # PTT提及分析
            ptt_mentions = await self._get_ptt_stock_mentions(stock_code)
            
            # 新聞提及分析
            news_mentions = await self._get_news_stock_mentions(stock_code)
            
            # 社群媒體情感
            social_sentiment = await self._get_social_media_sentiment(stock_code)
            
            # 綜合情感分數
            composite = (ptt_mentions['sentiment'] * 0.4 + 
                        news_mentions['sentiment'] * 0.35 + 
                        social_sentiment * 0.25)
            
            result = {
                'sentiment_score': composite,
                'mention_volume': ptt_mentions['volume'] + news_mentions['volume'],
                'trend': self._determine_sentiment_trend(composite),
                'reliability': min(1.0, (ptt_mentions['volume'] + news_mentions['volume']) / 100)
            }
            
            # 更新快取
            self.sentiment_cache[stock_code] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            logging.warning(f"個股情感分析失敗 {stock_code}: {e}")
            return {'sentiment_score': 0, 'mention_volume': 0, 'trend': 'neutral', 'reliability': 0.3}
    
    async def _get_ptt_overall_sentiment(self) -> float:
        """獲取PTT整體情感 (模擬)"""
        return np.random.normal(0.1, 0.3)  # 略偏樂觀
    
    async def _get_news_sentiment(self) -> float:
        """獲取新聞情感 (模擬)"""
        return np.random.normal(0.05, 0.25)
    
    async def _get_search_trends(self, keywords: List[str]) -> float:
        """獲取搜尋趨勢 (模擬)"""
        return np.random.normal(0, 0.2)
    
    async def _get_ptt_stock_mentions(self, stock_code: str) -> Dict:
        """獲取PTT個股提及 (模擬)"""
        volume = max(0, int(np.random.exponential(20)))
        sentiment = np.random.normal(0, 0.4) if volume > 5 else 0
        return {'volume': volume, 'sentiment': sentiment}
    
    async def _get_news_stock_mentions(self, stock_code: str) -> Dict:
        """獲取新聞個股提及 (模擬)"""
        volume = max(0, int(np.random.exponential(15)))
        sentiment = np.random.normal(0.1, 0.3) if volume > 3 else 0
        return {'volume': volume, 'sentiment': sentiment}
    
    async def _get_social_media_sentiment(self, stock_code: str) -> float:
        """獲取社群媒體情感 (模擬)"""
        return np.random.normal(0, 0.35)
    
    def _classify_market_mood(self, sentiment: float) -> str:
        """分類市場情緒"""
        if sentiment > 0.3:
            return 'euphoric'
        elif sentiment > 0.1:
            return 'optimistic'  
        elif sentiment > -0.1:
            return 'neutral'
        elif sentiment > -0.3:
            return 'pessimistic'
        else:
            return 'panic'
    
    def _determine_sentiment_trend(self, sentiment: float) -> str:
        """判斷情感趨勢"""
        if sentiment > 0.2:
            return 'very_positive'
        elif sentiment > 0.05:
            return 'positive'
        elif sentiment > -0.05:
            return 'neutral'
        elif sentiment > -0.2:
            return 'negative'
        else:
            return 'very_negative'
    
    def _find_sentiment_extremes(self, sentiments: Dict) -> Dict:
        """找出情感極值"""
        if not sentiments:
            return {'most_positive': None, 'most_negative': None}
        
        sorted_by_sentiment = sorted(sentiments.items(), key=lambda x: x[1]['sentiment_score'])
        
        return {
            'most_negative': sorted_by_sentiment[0] if sorted_by_sentiment else None,
            'most_positive': sorted_by_sentiment[-1] if sorted_by_sentiment else None
        }
    
    def _calculate_fear_greed_index(self, market_sentiment: Dict) -> float:
        """計算恐懼貪婪指數"""
        sentiment_score = market_sentiment.get('composite_score', 0)
        # 轉換為0-100的恐懼貪婪指數
        fear_greed = max(0, min(100, 50 + sentiment_score * 50))
        return fear_greed
    
    async def close(self):
        """關閉連線"""
        if self.session:
            await self.session.close()

class MultiFactorModel:
    """多因子模型"""
    
    def __init__(self):
        self.factor_weights = {
            'value': 0.2,
            'quality': 0.25, 
            'growth': 0.2,
            'momentum': 0.15,
            'low_volatility': 0.1,
            'profitability': 0.1
        }
        self.factor_performance_history = {}
        
    def calculate_factor_scores(self, stock_data: Dict) -> Dict:
        """計算多因子分數"""
        
        factor_scores = {}
        
        # Value因子 (價值)
        factor_scores['value'] = self._calculate_value_factor(stock_data)
        
        # Quality因子 (品質)
        factor_scores['quality'] = self._calculate_quality_factor(stock_data)
        
        # Growth因子 (成長)
        factor_scores['growth'] = self._calculate_growth_factor(stock_data)
        
        # Momentum因子 (動量)
        factor_scores['momentum'] = self._calculate_momentum_factor(stock_data)
        
        # Low Volatility因子 (低波動)
        factor_scores['low_volatility'] = self._calculate_low_vol_factor(stock_data)
        
        # Profitability因子 (獲利能力)
        factor_scores['profitability'] = self._calculate_profitability_factor(stock_data)
        
        # 計算綜合因子分數
        composite_score = sum(
            factor_scores[factor] * self.factor_weights[factor]
            for factor in factor_scores
        )
        
        return {
            'composite_score': composite_score,
            'individual_scores': factor_scores,
            'factor_weights': self.factor_weights.copy()
        }
    
    def _calculate_value_factor(self, stock_data: Dict) -> float:
        """價值因子"""
        score = 50
        
        pe_ratio = stock_data.get('pe_ratio', 20)
        pb_ratio = stock_data.get('pb_ratio', 2)
        ps_ratio = stock_data.get('ps_ratio', 3)
        
        # P/E比評分
        if pe_ratio < 10:
            score += 20
        elif pe_ratio < 15:
            score += 15
        elif pe_ratio < 20:
            score += 5
        elif pe_ratio > 30:
            score -= 15
        elif pe_ratio > 25:
            score -= 8
        
        # P/B比評分  
        if pb_ratio < 1:
            score += 15
        elif pb_ratio < 1.5:
            score += 10
        elif pb_ratio < 2:
            score += 5
        elif pb_ratio > 3:
            score -= 10
        
        # P/S比評分
        if ps_ratio < 1:
            score += 10
        elif ps_ratio < 2:
            score += 5
        elif ps_ratio > 5:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_quality_factor(self, stock_data: Dict) -> float:
        """品質因子"""
        score = 50
        
        roe = stock_data.get('roe', 10)
        debt_ratio = stock_data.get('debt_ratio', 50)
        current_ratio = stock_data.get('current_ratio', 1.5)
        
        # ROE評分
        if roe > 20:
            score += 20
        elif roe > 15:
            score += 15
        elif roe > 10:
            score += 8
        elif roe < 5:
            score -= 15
        
        # 負債比評分
        if debt_ratio < 20:
            score += 15
        elif debt_ratio < 40:
            score += 10
        elif debt_ratio < 60:
            score += 0
        else:
            score -= 15
        
        # 流動比率評分
        if current_ratio > 2:
            score += 10
        elif current_ratio > 1.5:
            score += 5
        elif current_ratio < 1:
            score -= 15
        
        return max(0, min(100, score))
    
    def _calculate_growth_factor(self, stock_data: Dict) -> float:
        """成長因子"""
        score = 50
        
        revenue_growth = stock_data.get('revenue_growth', 0)
        eps_growth = stock_data.get('eps_growth', 0)
        
        # 營收成長評分
        if revenue_growth > 20:
            score += 25
        elif revenue_growth > 10:
            score += 15
        elif revenue_growth > 5:
            score += 8
        elif revenue_growth < -5:
            score -= 15
        elif revenue_growth < 0:
            score -= 8
        
        # EPS成長評分
        if eps_growth > 30:
            score += 25
        elif eps_growth > 15:
            score += 18
        elif eps_growth > 8:
            score += 10
        elif eps_growth < -10:
            score -= 20
        elif eps_growth < 0:
            score -= 12
        
        return max(0, min(100, score))
    
    def _calculate_momentum_factor(self, stock_data: Dict) -> float:
        """動量因子"""
        score = 50
        
        price_momentum_1m = stock_data.get('price_momentum_1m', 0)
        price_momentum_3m = stock_data.get('price_momentum_3m', 0)
        price_momentum_12m = stock_data.get('price_momentum_12m', 0)
        
        # 1個月動量
        if price_momentum_1m > 10:
            score += 15
        elif price_momentum_1m > 5:
            score += 8
        elif price_momentum_1m < -10:
            score -= 15
        elif price_momentum_1m < -5:
            score -= 8
        
        # 3個月動量
        if price_momentum_3m > 15:
            score += 20
        elif price_momentum_3m > 8:
            score += 12
        elif price_momentum_3m < -15:
            score -= 20
        elif price_momentum_3m < -8:
            score -= 12
        
        # 12個月動量
        if price_momentum_12m > 30:
            score += 15
        elif price_momentum_12m > 15:
            score += 10
        elif price_momentum_12m < -20:
            score -= 15
        elif price_momentum_12m < -10:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_low_vol_factor(self, stock_data: Dict) -> float:
        """低波動因子"""
        score = 50
        
        volatility = stock_data.get('volatility', 0.25)
        beta = stock_data.get('beta', 1.0)
        
        # 波動率評分 (低波動給高分)
        if volatility < 0.15:
            score += 25
        elif volatility < 0.2:
            score += 20
        elif volatility < 0.25:
            score += 10
        elif volatility > 0.4:
            score -= 20
        elif volatility > 0.35:
            score -= 15
        
        # Beta評分
        if beta < 0.7:
            score += 15
        elif beta < 0.9:
            score += 10
        elif beta < 1.1:
            score += 5
        elif beta > 1.5:
            score -= 15
        elif beta > 1.3:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_profitability_factor(self, stock_data: Dict) -> float:
        """獲利能力因子"""
        score = 50
        
        gross_margin = stock_data.get('gross_margin', 20)
        operating_margin = stock_data.get('operating_margin', 10)
        net_margin = stock_data.get('net_margin', 5)
        
        # 毛利率評分
        if gross_margin > 40:
            score += 15
        elif gross_margin > 25:
            score += 10
        elif gross_margin > 15:
            score += 5
        elif gross_margin < 10:
            score -= 10
        
        # 營業利益率評分
        if operating_margin > 20:
            score += 15
        elif operating_margin > 12:
            score += 10
        elif operating_margin > 8:
            score += 5
        elif operating_margin < 3:
            score -= 15
        
        # 淨利率評分
        if net_margin > 15:
            score += 20
        elif net_margin > 8:
            score += 12
        elif net_margin > 5:
            score += 6
        elif net_margin < 2:
            score -= 15
        
        return max(0, min(100, score))
    
    def update_factor_weights(self, performance_data: Dict):
        """動態更新因子權重"""
        if not performance_data:
            return
        
        # 基於近期表現調整權重
        total_performance = sum(performance_data.values())
        if total_performance > 0:
            for factor in self.factor_weights:
                if factor in performance_data:
                    # 表現好的因子增加權重
                    adjustment = performance_data[factor] / total_performance * 0.1
                    self.factor_weights[factor] = max(0.05, min(0.4, 
                        self.factor_weights[factor] + adjustment))
        
        # 權重正規化
        total_weight = sum(self.factor_weights.values())
        for factor in self.factor_weights:
            self.factor_weights[factor] /= total_weight

class RiskManager:
    """風險管理器"""
    
    def __init__(self):
        self.risk_free_rate = 0.02
        self.market_volatility = 0.18
        
    def calculate_comprehensive_risk(self, stock_data: Dict, portfolio_context: Optional[Dict] = None) -> Dict:
        """計算綜合風險指標"""
        
        # 個股風險指標
        individual_risk = self._calculate_individual_risk(stock_data)
        
        # 市場風險指標
        market_risk = self._calculate_market_risk(stock_data)
        
        # 流動性風險
        liquidity_risk = self._calculate_liquidity_risk(stock_data)
        
        # 集中度風險
        concentration_risk = self._calculate_concentration_risk(stock_data)
        
        # 下檔風險
        downside_risk = self._calculate_downside_risk(stock_data)
        
        # 綜合風險分數
        composite_risk_score = self._calculate_composite_risk_score({
            'individual': individual_risk,
            'market': market_risk,
            'liquidity': liquidity_risk,
            'concentration': concentration_risk,
            'downside': downside_risk
        })
        
        return {
            'composite_risk_score': composite_risk_score,
            'risk_level': self._classify_risk_level(composite_risk_score),
            'individual_risk': individual_risk,
            'market_risk': market_risk,
            'liquidity_risk': liquidity_risk,
            'concentration_risk': concentration_risk,
            'downside_risk': downside_risk,
            'risk_recommendations': self._generate_risk_recommendations(composite_risk_score),
            'position_sizing': self._recommend_position_size(composite_risk_score)
        }
    
    def _calculate_individual_risk(self, stock_data: Dict) -> Dict:
        """計算個股風險"""
        volatility = stock_data.get('volatility', 0.25)
        beta = stock_data.get('beta', 1.0)
        
        # VaR計算 (95%信心水準)
        var_95 = volatility * 1.645 * np.sqrt(1/252)
        
        # CVaR計算 (期望尾部損失)
        cvar_95 = var_95 * 1.2  # 簡化計算
        
        return {
            'volatility': volatility,
            'beta': beta, 
            'var_95': var_95,
            'cvar_95': cvar_95,
            'risk_score': max(0, 100 - volatility * 200)  # 波動率越高分數越低
        }
    
    def _calculate_market_risk(self, stock_data: Dict) -> Dict:
        """計算市場風險"""
        beta = stock_data.get('beta', 1.0)
        sector_beta = stock_data.get('sector_beta', 1.0)
        
        # 系統性風險暴露
        systematic_risk = abs(beta - 1) * self.market_volatility
        
        # 板塊風險
        sector_risk = abs(sector_beta - 1) * 0.15
        
        return {
            'systematic_risk': systematic_risk,
            'sector_risk': sector_risk,
            'beta': beta,
            'market_correlation': min(1, abs(beta)),
            'risk_score': max(0, 100 - systematic_risk * 500)
        }
    
    def _calculate_liquidity_risk(self, stock_data: Dict) -> Dict:
        """計算流動性風險"""
        avg_volume = stock_data.get('avg_volume', 1000000)
        market_cap = stock_data.get('market_cap', 10000000000)
        
        # 成交量風險 (成交量越低風險越高)
        volume_risk = max(0, (10000000 - avg_volume) / 10000000)
        
        # 市值風險 (市值越小流動性風險越高)
        market_cap_risk = max(0, (50000000000 - market_cap) / 50000000000)
        
        # 買賣價差風險 (模擬)
        bid_ask_spread = stock_data.get('bid_ask_spread', 0.01)
        spread_risk = min(1, bid_ask_spread * 100)
        
        composite_liquidity_risk = (volume_risk * 0.4 + market_cap_risk * 0.4 + spread_risk * 0.2)
        
        return {
            'volume_risk': volume_risk,
            'market_cap_risk': market_cap_risk,
            'spread_risk': spread_risk,
            'composite_risk': composite_liquidity_risk,
            'risk_score': max(0, 100 - composite_liquidity_risk * 100)
        }
    
    def _calculate_concentration_risk(self, stock_data: Dict) -> Dict:
        """計算集中度風險"""
        major_shareholder_ratio = stock_data.get('major_shareholder_ratio', 50)
        foreign_ownership = stock_data.get('foreign_ownership', 30)
        
        # 大股東持股集中度風險
        ownership_concentration = max(0, (major_shareholder_ratio - 50) / 50)
        
        # 外資持股集中度 (過高或過低都有風險)
        foreign_risk = abs(foreign_ownership - 40) / 40
        
        return {
            'ownership_concentration': ownership_concentration,
            'foreign_ownership_risk': foreign_risk,
            'risk_score': max(0, 100 - (ownership_concentration + foreign_risk) * 50)
        }
    
    def _calculate_downside_risk(self, stock_data: Dict) -> Dict:
        """計算下檔風險"""
        # 模擬歷史價格數據來計算下檔風險
        historical_returns = np.random.normal(0.08/252, stock_data.get('volatility', 0.25)/np.sqrt(252), 252)
        
        # 最大回撤
        cumulative_returns = np.cumprod(1 + historical_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(drawdowns.min())
        
        # 下檔偏差
        negative_returns = historical_returns[historical_returns < 0]
        downside_deviation = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else 0
        
        return {
            'max_drawdown': max_drawdown,
            'downside_deviation': downside_deviation,
            'negative_return_frequency': len(negative_returns) / len(historical_returns),
            'risk_score': max(0, 100 - max_drawdown * 200)
        }
    
    def _calculate_composite_risk_score(self, risk_components: Dict) -> float:
        """計算綜合風險分數"""
        weights = {
            'individual': 0.3,
            'market': 0.2,
            'liquidity': 0.2,
            'concentration': 0.15,
            'downside': 0.15
        }
        
        composite_score = sum(
            risk_components[component]['risk_score'] * weights[component]
            for component in risk_components
        )
        
        return max(0, min(100, composite_score))
    
    def _classify_risk_level(self, risk_score: float) -> RiskLevel:
        """分類風險等級"""
        if risk_score >= 80:
            return RiskLevel.VERY_LOW
        elif risk_score >= 65:
            return RiskLevel.LOW
        elif risk_score >= 45:
            return RiskLevel.MEDIUM
        elif risk_score >= 25:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _generate_risk_recommendations(self, risk_score: float) -> List[str]:
        """生成風險建議"""
        recommendations = []
        
        if risk_score < 30:
            recommendations.extend([
                "建議降低部位大小",
                "考慮設置停損點",
                "密切監控市場變化",
                "避免集中投資"
            ])
        elif risk_score < 50:
            recommendations.extend([
                "適度控制部位大小", 
                "定期檢視投資組合",
                "注意市場風險變化"
            ])
        elif risk_score < 70:
            recommendations.extend([
                "維持適當部位大小",
                "持續監控基本面變化"
            ])
        else:
            recommendations.extend([
                "可考慮增加部位",
                "適合長期投資"
            ])
        
        return recommendations
    
    def _recommend_position_size(self, risk_score: float) -> Dict:
        """建議部位大小"""
        if risk_score >= 80:
            return {'recommended_weight': 0.08, 'max_weight': 0.12}
        elif risk_score >= 65:
            return {'recommended_weight': 0.06, 'max_weight': 0.10}
        elif risk_score >= 45:
            return {'recommended_weight': 0.04, 'max_weight': 0.08}
        elif risk_score >= 25:
            return {'recommended_weight': 0.02, 'max_weight': 0.05}
        else:
            return {'recommended_weight': 0.01, 'max_weight': 0.03}

class MLEnsemblePredictor:
    """機器學習集成預測器"""
    
    def __init__(self):
        self.models = {}
        self.model_weights = {}
        self.feature_importance = {}
        
    def train_ensemble_models(self, training_data: pd.DataFrame, target: str):
        """訓練集成模型"""
        try:
            from sklearn.ensemble import RandomForestRegressor, GradientBookingRegressor
            from sklearn.linear_model import LinearRegression
            from sklearn.svm import SVR
            from sklearn.model_selection import cross_val_score
            
            X = training_data.drop(columns=[target])
            y = training_data[target]
            
            # 定義模型
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBookingRegressor(n_estimators=100, random_state=42),
                'linear_regression': LinearRegression(),
                'svr': SVR(kernel='rbf')
            }
            
            # 訓練並評估模型
            for name, model in models.items():
                try:
                    model.fit(X, y)
                    cv_scores = cross_val_score(model, X, y, cv=5)
                    
                    self.models[name] = model
                    self.model_weights[name] = cv_scores.mean()
                    
                    # 特徵重要性 (如果支持)
                    if hasattr(model, 'feature_importances_'):
                        self.feature_importance[name] = dict(zip(X.columns, model.feature_importances_))
                        
                except Exception as e:
                    logging.warning(f"模型 {name} 訓練失敗: {e}")
            
            # 正規化權重
            total_weight = sum(self.model_weights.values())
            if total_weight > 0:
                for name in self.model_weights:
                    self.model_weights[name] /= total_weight
                    
        except ImportError:
            logging.warning("sklearn 未安裝，使用簡化預測模型")
            self._use_simple_models()
    
    def predict_ensemble(self, features: Dict) -> Dict:
        """集成預測"""
        if not self.models:
            return self._simple_prediction(features)
        
        try:
            feature_vector = np.array([list(features.values())])
            predictions = {}
            
            for name, model in self.models.items():
                try:
                    pred = model.predict(feature_vector)[0]
                    predictions[name] = pred
                except Exception as e:
                    logging.warning(f"模型 {name} 預測失敗: {e}")
                    predictions[name] = 50  # 預設值
            
            # 加權平均
            ensemble_prediction = sum(
                predictions[name] * self.model_weights.get(name, 0)
                for name in predictions
            )
            
            # 預測信心度
            prediction_std = np.std(list(predictions.values()))
            confidence = max(0, min(1, 1 - prediction_std / 25))
            
            return {
                'ensemble_prediction': ensemble_prediction,
                'individual_predictions': predictions,
                'confidence': confidence,
                'model_weights': self.model_weights.copy()
            }
            
        except Exception as e:
            logging.error(f"集成預測失敗: {e}")
            return self._simple_prediction(features)
    
    def _use_simple_models(self):
        """使用簡化模型"""
        # 簡化的線性組合模型
        self.models['simple'] = lambda x: sum(x) / len(x) if x else 50
        self.model_weights['simple'] = 1.0
    
    def _simple_prediction(self, features: Dict) -> Dict:
        """簡化預測"""
        feature_values = list(features.values())
        simple_pred = sum(feature_values) / len(feature_values) if feature_values else 50
        
        return {
            'ensemble_prediction': simple_pred,
            'individual_predictions': {'simple': simple_pred},
            'confidence': 0.6,
            'model_weights': {'simple': 1.0}
        }

class AlternativeDataAnalyzer:
    """替代數據分析器"""
    
    def __init__(self):
        self.satellite_data_cache = {}
        self.supply_chain_cache = {}
        
    async def analyze_alternative_data(self, stock_code: str, company_info: Dict) -> Dict:
        """分析替代數據"""
        
        alternative_scores = {}
        
        # 衛星數據分析
        alternative_scores['satellite'] = await self._analyze_satellite_data(stock_code, company_info)
        
        # 供應鏈數據分析
        alternative_scores['supply_chain'] = await self._analyze_supply_chain(stock_code)
        
        # ESG數據分析
        alternative_scores['esg'] = await self._analyze_esg_data(stock_code)
        
        # 專利數據分析
        alternative_scores['patent'] = await self._analyze_patent_data(stock_code, company_info)
        
        # 管理層變動分析
        alternative_scores['management'] = await self._analyze_management_changes(stock_code)
        
        # 綜合替代數據分數
        composite_score = self._calculate_alternative_composite_score(alternative_scores)
        
        return {
            'composite_score': composite_score,
            'individual_scores': alternative_scores,
            'data_reliability': self._assess_data_reliability(alternative_scores),
            'insights': self._generate_alternative_insights(alternative_scores)
        }
    
    async def _analyze_satellite_data(self, stock_code: str, company_info: Dict) -> Dict:
        """衛星數據分析 (模擬)"""
        try:
            # 模擬工廠活動數據
            factory_activity = {
                'parking_lot_occupancy': np.random.uniform(0.6, 0.95),
                'night_light_intensity': np.random.uniform(80, 150),
                'truck_traffic': np.random.randint(20, 80),
                'construction_activity': np.random.choice(['low', 'medium', 'high']),
                'seasonal_pattern': 'normal'
            }
            
            # 計算活動分數
            activity_score = (
                factory_activity['parking_lot_occupancy'] * 40 +
                (factory_activity['night_light_intensity'] / 150) * 30 +
                (factory_activity['truck_traffic'] / 80) * 30
            )
            
            return {
                'activity_score': activity_score,
                'raw_data': factory_activity,
                'trend': 'increasing' if activity_score > 70 else 'stable' if activity_score > 50 else 'decreasing'
            }
            
        except Exception as e:
            logging.warning(f"衛星數據分析失敗 {stock_code}: {e}")
            return {'activity_score': 60, 'trend': 'stable'}
    
    async def _analyze_supply_chain(self, stock_code: str) -> Dict:
        """供應鏈分析 (模擬)"""
        try:
            # 模擬供應鏈數據
            supply_chain_health = {
                'supplier_diversity': np.random.uniform(0.4, 0.9),
                'geographic_spread': np.random.uniform(0.3, 0.8),
                'tier1_stability': np.random.uniform(0.6, 0.95),
                'logistics_efficiency': np.random.uniform(0.5, 0.9),
                'inventory_turnover': np.random.uniform(4, 12)
            }
            
            # 供應鏈風險評估
            supply_chain_score = (
                supply_chain_health['supplier_diversity'] * 20 +
                supply_chain_health['geographic_spread'] * 15 +
                supply_chain_health['tier1_stability'] * 30 +
                supply_chain_health['logistics_efficiency'] * 20 +
                min(1, supply_chain_health['inventory_turnover'] / 8) * 15
            )
            
            return {
                'supply_chain_score': supply_chain_score,
                'risk_level': 'low' if supply_chain_score > 75 else 'medium' if supply_chain_score > 50 else 'high',
                'raw_data': supply_chain_health
            }
            
        except Exception as e:
            logging.warning(f"供應鏈分析失敗 {stock_code}: {e}")
            return {'supply_chain_score': 65, 'risk_level': 'medium'}
    
    async def _analyze_esg_data(self, stock_code: str) -> Dict:
        """ESG數據分析 (模擬)"""
        try:
            # 模擬ESG評分
            esg_scores = {
                'environmental': np.random.uniform(40, 90),
                'social': np.random.uniform(45, 85),
                'governance': np.random.uniform(50, 95)
            }
            
            # 計算綜合ESG分數
            esg_composite = (
                esg_scores['environmental'] * 0.35 +
                esg_scores['social'] * 0.35 +
                esg_scores['governance'] * 0.30
            )
            
            # ESG趨勢
            esg_trend = np.random.choice(['improving', 'stable', 'declining'], p=[0.4, 0.5, 0.1])
            
            return {
                'esg_composite': esg_composite,
                'individual_scores': esg_scores,
                'esg_trend': esg_trend,
                'esg_grade': self._grade_esg_score(esg_composite)
            }
            
        except Exception as e:
            logging.warning(f"ESG分析失敗 {stock_code}: {e}")
            return {'esg_composite': 60, 'esg_grade': 'B'}
    
    async def _analyze_patent_data(self, stock_code: str, company_info: Dict) -> Dict:
        """專利數據分析 (模擬)"""
        try:
            # 模擬專利數據
            patent_data = {
                'total_patents': np.random.randint(10, 500),
                'recent_applications': np.random.randint(0, 50),
                'patent_citations': np.random.randint(5, 200),
                'r_and_d_intensity': np.random.uniform(0.02, 0.15),
                'innovation_score': np.random.uniform(30, 90)
            }
            
            # 創新能力評分
            innovation_score = (
                min(100, patent_data['total_patents'] / 5) * 0.3 +
                min(100, patent_data['recent_applications'] * 2) * 0.2 +
                min(100, patent_data['patent_citations'] / 2) * 0.2 +
                patent_data['r_and_d_intensity'] * 100 * 0.15 +
                patent_data['innovation_score'] * 0.15
            )
            
            return {
                'innovation_score': innovation_score,
                'patent_data': patent_data,
                'innovation_trend': 'strong' if innovation_score > 70 else 'moderate' if innovation_score > 50 else 'weak'
            }
            
        except Exception as e:
            logging.warning(f"專利分析失敗 {stock_code}: {e}")
            return {'innovation_score': 55, 'innovation_trend': 'moderate'}
    
    async def _analyze_management_changes(self, stock_code: str) -> Dict:
        """管理層變動分析 (模擬)"""
        try:
            # 模擬管理層變動數據
            management_data = {
                'ceo_tenure': np.random.uniform(1, 15),
                'recent_changes': np.random.randint(0, 5),
                'board_independence': np.random.uniform(0.3, 0.8),
                'management_ownership': np.random.uniform(0.05, 0.4),
                'insider_trading_activity': np.random.choice(['normal', 'increased_selling', 'increased_buying'])
            }
            
            # 管理品質評分
            management_score = 50
            
            # CEO任期評分
            if 3 <= management_data['ceo_tenure'] <= 10:
                management_score += 15
            elif management_data['ceo_tenure'] < 1:
                management_score -= 10
            elif management_data['ceo_tenure'] > 15:
                management_score -= 5
            
            # 近期變動評分
            if management_data['recent_changes'] == 0:
                management_score += 10
            elif management_data['recent_changes'] > 3:
                management_score -= 15
            
            # 董事會獨立性
            management_score += management_data['board_independence'] * 20
            
            # 內線交易活動
            if management_data['insider_trading_activity'] == 'increased_buying':
                management_score += 10
            elif management_data['insider_trading_activity'] == 'increased_selling':
                management_score -= 10
            
            return {
                'management_score': max(0, min(100, management_score)),
                'management_data': management_data,
                'stability': 'high' if management_score > 70 else 'medium' if management_score > 50 else 'low'
            }
            
        except Exception as e:
            logging.warning(f"管理層分析失敗 {stock_code}: {e}")
            return {'management_score': 60, 'stability': 'medium'}
    
    def _calculate_alternative_composite_score(self, scores: Dict) -> float:
        """計算替代數據綜合分數"""
        weights = {
            'satellite': 0.25,
            'supply_chain': 0.2,
            'esg': 0.2,
            'patent': 0.2,
            'management': 0.15
        }
        
        composite = 0
        for category, weight in weights.items():
            if category in scores and isinstance(scores[category], dict):
                score_key = f"{category}_score" if f"{category}_score" in scores[category] else list(scores[category].keys())[0]
                if score_key in scores[category]:
                    composite += scores[category][score_key] * weight
        
        return max(0, min(100, composite))
    
    def _assess_data_reliability(self, scores: Dict) -> float:
        """評估數據可靠性"""
        # 簡化的可靠性評估
        reliability_scores = []
        
        for category_data in scores.values():
            if isinstance(category_data, dict):
                # 基於數據完整性評估可靠性
                data_completeness = len([v for v in category_data.values() if v is not None]) / len(category_data)
                reliability_scores.append(data_completeness)
        
        return sum(reliability_scores) / len(reliability_scores) if reliability_scores else 0.5
    
    def _generate_alternative_insights(self, scores: Dict) -> List[str]:
        """生成替代數據洞察"""
        insights = []
        
        # 衛星數據洞察
        if 'satellite' in scores:
            satellite_data = scores['satellite']
            if satellite_data.get('trend') == 'increasing':
                insights.append("衛星數據顯示企業營運活動增加")
            elif satellite_data.get('trend') == 'decreasing':
                insights.append("衛星數據顯示企業營運活動減少")
        
        # ESG洞察
        if 'esg' in scores:
            esg_data = scores['esg']
            if esg_data.get('esg_composite', 0) > 75:
                insights.append("ESG評分優異，符合永續投資趨勢")
            elif esg_data.get('esg_trend') == 'improving':
                insights.append("ESG表現持續改善")
        
        # 創新洞察
        if 'patent' in scores:
            patent_data = scores['patent']
            if patent_data.get('innovation_trend') == 'strong':
                insights.append("專利數據顯示強勁創新能力")
        
        # 管理層洞察
        if 'management' in scores:
            mgmt_data = scores['management']
            if mgmt_data.get('stability') == 'high':
                insights.append("管理層穩定，治理品質良好")
        
        return insights
    
    def _grade_esg_score(self, score: float) -> str:
        """ESG分數評級"""
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'

class UltimateStockRecommender:
    """終極股票推薦系統"""
    
    def __init__(self):
        self.global_analyzer = GlobalEconomicAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.multi_factor_model = MultiFactorModel()
        self.risk_manager = RiskManager()
        self.ml_predictor = MLEnsemblePredictor()
        self.alternative_analyzer = AlternativeDataAnalyzer()
        
        self.system_config = {
            'max_recommendations': 20,
            'min_confidence_threshold': 0.6,
            'risk_tolerance': 'moderate',
            'enable_alternative_data': True,
            'enable_ml_prediction': True
        }
        
        self.performance_tracker = {
            'recommendations_made': 0,
            'successful_predictions': 0,
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }
    
    async def generate_ultimate_recommendations(self, stock_universe: List[Dict], 
                                             custom_config: Optional[Dict] = None) -> List[StockRecommendation]:
        """生成終極股票推薦"""
        
        if custom_config:
            self.system_config.update(custom_config)
        
        logging.info(f"開始分析 {len(stock_universe)} 檔股票")
        
        try:
            # 1. 全球經濟分析
            global_economic_data = await self.global_analyzer.get_global_economic_data()
            logging.info(f"全球經濟分數: {global_economic_data['global_score']:.1f}")
            
            # 2. 市場情感分析
            stock_codes = [stock['code'] for stock in stock_universe]
            sentiment_data = await self.sentiment_analyzer.analyze_market_sentiment(stock_codes)
            logging.info(f"市場情感: {sentiment_data['market_sentiment']['market_mood']}")
            
            # 3. 批量分析股票
            recommendations = []
            
            # 使用異步處理提高效率
            semaphore = asyncio.Semaphore(10)  # 限制併發數
            tasks = []
            
            for stock_data in stock_universe:
                task = self._analyze_single_stock_comprehensive(
                    stock_data, global_economic_data, sentiment_data, semaphore
                )
                tasks.append(task)
            
            # 等待所有分析完成
            analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            for i, result in enumerate(analysis_results):
                if isinstance(result, Exception):
                    logging.error(f"股票分析失敗 {stock_universe[i]['code']}: {result}")
                    continue
                
                if result and result.confidence >= self.system_config['min_confidence_threshold']:
                    recommendations.append(result)
            
            # 4. 排序和篩選
            recommendations.sort(key=lambda x: x.final_score, reverse=True)
            recommendations = recommendations[:self.system_config['max_recommendations']]
            
            # 5. 投資組合優化 (簡化版)
            optimized_recommendations = self._optimize_portfolio(recommendations)
            
            # 6. 更新績效追蹤
            self.performance_tracker['recommendations_made'] += len(optimized_recommendations)
            
            logging.info(f"生成 {len(optimized_recommendations)} 個推薦")
            
            return optimized_recommendations
            
        except Exception as e:
            logging.error(f"生成推薦失敗: {e}")
            return []
        
        finally:
            await self.sentiment_analyzer.close()
    
    async def _analyze_single_stock_comprehensive(self, stock_data: Dict, global_data: Dict, 
                                                sentiment_data: Dict, semaphore: asyncio.Semaphore) -> Optional[StockRecommendation]:
        """綜合分析單檔股票"""
        
        async with semaphore:
            try:
                stock_code = stock_data['code']
                stock_name = stock_data['name']
                
                # 1. 基本面分析 (多因子模型)
                factor_result = self.multi_factor_model.calculate_factor_scores(stock_data)
                fundamental_score = factor_result['composite_score']
                
                # 2. 技術面分析 (簡化)
                technical_score = self._calculate_technical_score(stock_data)
                
                # 3. 情感分析
                individual_sentiment = sentiment_data['individual_sentiments'].get(stock_code, {})
                sentiment_score = (individual_sentiment.get('sentiment_score', 0) + 1) * 50  # 轉換為0-100
                
                # 4. 總經分析
                macro_score = self._calculate_macro_score(stock_data, global_data)
                
                # 5. 機器學習預測
                ml_score = 50  # 預設值
                if self.system_config['enable_ml_prediction']:
                    ml_features = self._extract_ml_features(stock_data, global_data, individual_sentiment)
                    ml_result = self.ml_predictor.predict_ensemble(ml_features)
                    ml_score = ml_result['ensemble_prediction']
                
                # 6. 替代數據分析
                alternative_score = 50  # 預設值
                if self.system_config['enable_alternative_data']:
                    alternative_result = await self.alternative_analyzer.analyze_alternative_data(
                        stock_code, stock_data
                    )
                    alternative_score = alternative_result['composite_score']
                
                # 7. 風險分析
                risk_result = self.risk_manager.calculate_comprehensive_risk(stock_data)
                
                # 8. 綜合評分
                final_score = self._calculate_final_score({
                    'fundamental': fundamental_score,
                    'technical': technical_score,
                    'sentiment': sentiment_score,
                    'macro': macro_score,
                    'ml': ml_score,
                    'alternative': alternative_score
                }, risk_result, global_data['market_regime'])
                
                # 9. 信心度計算
                confidence = self._calculate_confidence(
                    factor_result, individual_sentiment, risk_result, ml_score
                )
                
                # 10. 價格目標和持有期間
                target_price, hold_period = self._calculate_price_target_and_period(
                    stock_data, final_score, risk_result
                )
                
                # 11. 生成推薦理由和風險因子
                reasoning = self._generate_reasoning(stock_data, final_score, factor_result, global_data)
                risk_factors = self._identify_risk_factors(stock_data, risk_result, global_data)
                catalysts = self._identify_catalysts(stock_data, global_data, individual_sentiment)
                
                return StockRecommendation(
                    code=stock_code,
                    name=stock_name,
                    sector=stock_data.get('sector', 'Unknown'),
                    final_score=final_score,
                    confidence=confidence,
                    risk_level=risk_result['risk_level'],
                    fundamental_score=fundamental_score,
                    technical_score=technical_score,
                    sentiment_score=sentiment_score,
                    macro_score=macro_score,
                    ml_score=ml_score,
                    alternative_data_score=alternative_score,
                    volatility=stock_data.get('volatility', 0.25),
                    beta=stock_data.get('beta', 1.0),
                    var_95=risk_result['individual_risk']['var_95'],
                    liquidity_risk=risk_result['liquidity_risk']['composite_risk'],
                    target_price=target_price,
                    price_trend=self._determine_price_trend(final_score),
                    hold_period=hold_period,
                    reasoning=reasoning,
                    risk_factors=risk_factors,
                    catalysts=catalysts,
                    timestamp=datetime.now()
                )
                
            except Exception as e:
                logging.error(f"分析股票失敗 {stock_data.get('code', 'Unknown')}: {e}")
                return None
    
    def _calculate_technical_score(self, stock_data: Dict) -> float:
        """計算技術分析分數"""
        score = 50
        
        # RSI
        rsi = stock_data.get('rsi', 50)
        if 30 <= rsi <= 70:
            score += 15
        elif rsi < 30:
            score += 20  # 超賣
        elif rsi > 70:
            score -= 10  # 超買
        
        # MACD
        macd_signal = stock_data.get('macd_signal', 'neutral')
        if macd_signal == 'bullish':
            score += 15
        elif macd_signal == 'bearish':
            score -= 15
        
        # 成交量
        volume_trend = stock_data.get('volume_trend', 'stable')
        if volume_trend == 'increasing':
            score += 10
        elif volume_trend == 'decreasing':
            score -= 8
        
        # 價格趨勢
        price_trend = stock_data.get('price_trend', 'neutral')
        if price_trend == 'bullish':
            score += 20
        elif price_trend == 'bearish':
            score -= 20
        
        return max(0, min(100, score))
    
    def _calculate_macro_score(self, stock_data: Dict, global_data: Dict) -> float:
        """計算總經分析分數"""
        score = 50
        
        # 根據全球經濟狀況調整
        global_score = global_data['global_score']
        score += (global_score - 50) * 0.4
        
        # 板塊輪動效應
        sector = stock_data.get('sector', '').lower()
        sector_outlook = global_data.get('sector_outlook', {})
        
        for sector_key, multiplier in sector_outlook.items():
            if sector_key in sector:
                score *= multiplier
                break
        
        # 匯率影響
        export_ratio = stock_data.get('export_ratio', 0)
        if export_ratio > 50:
            currency_outlook = global_data.get('currency_outlook', {})
            if currency_outlook.get('twd_outlook') == 'weakening':
                score += 10  # 台幣轉弱對出口股有利
            elif currency_outlook.get('twd_outlook') == 'strengthening':
                score -= 8
        
        return max(0, min(100, score))
    
    def _extract_ml_features(self, stock_data: Dict, global_data: Dict, sentiment_data: Dict) -> Dict:
        """提取機器學習特徵"""
        features = {}
        
        # 基本面特徵
        features.update({
            'pe_ratio': stock_data.get('pe_ratio', 20),
            'pb_ratio': stock_data.get('pb_ratio', 2),
            'roe': stock_data.get('roe', 15),
            'debt_ratio': stock_data.get('debt_ratio', 50),
            'eps_growth': stock_data.get('eps_growth', 10),
            'revenue_growth': stock_data.get('revenue_growth', 5)
        })
        
        # 技術面特徵
        features.update({
            'rsi': stock_data.get('rsi', 50),
            'beta': stock_data.get('beta', 1.0),
            'volatility': stock_data.get('volatility', 0.25),
            'price_momentum_3m': stock_data.get('price_momentum_3m', 0)
        })
        
        # 總經特徵
        features.update({
            'global_economic_score': global_data['global_score'],
            'vix_level': global_data['regional_data'].get('us', {}).get('vix_level', 20)
        })
        
        # 情感特徵
        features.update({
            'sentiment_score': sentiment_data.get('sentiment_score', 0),
            'mention_volume': sentiment_data.get('mention_volume', 0)
        })
        
        return features
    
    def _calculate_final_score(self, component_scores: Dict, risk_result: Dict, market_regime: MarketRegime) -> float:
        """計算最終綜合分數"""
        
        # 基礎權重
        base_weights = {
            'fundamental': 0.25,
            'technical': 0.15,
            'sentiment': 0.15,
            'macro': 0.15,
            'ml': 0.15,
            'alternative': 0.15
        }
        
        # 根據市場狀況調整權重
        adjusted_weights = self._adjust_weights_by_market_regime(base_weights, market_regime)
        
        # 計算加權分數
        weighted_score = sum(
            component_scores[component] * adjusted_weights[component]
            for component in component_scores
        )
        
        # 風險調整
        risk_adjustment = (risk_result['composite_risk_score'] - 50) / 50 * 0.1
        final_score = weighted_score * (1 + risk_adjustment)
        
        return max(0, min(100, final_score))
    
    def _adjust_weights_by_market_regime(self, base_weights: Dict, market_regime: MarketRegime) -> Dict:
        """根據市場狀況調整權重"""
        adjusted_weights = base_weights.copy()
        
        if market_regime == MarketRegime.BULL_MARKET:
            adjusted_weights['momentum'] = adjusted_weights.get('technical', 0.15) * 1.2
            adjusted_weights['sentiment'] *= 1.1
        elif market_regime == MarketRegime.BEAR_MARKET:
            adjusted_weights['fundamental'] *= 1.3
            adjusted_weights['sentiment'] *= 0.8
        elif market_regime == MarketRegime.HIGH_VOLATILITY:
            adjusted_weights['fundamental'] *= 1.2
            adjusted_weights['alternative'] *= 1.1
        
        # 重新正規化
        total_weight = sum(adjusted_weights.values())
        for key in adjusted_weights:
            adjusted_weights[key] /= total_weight
        
        return adjusted_weights
    
    def _calculate_confidence(self, factor_result: Dict, sentiment_data: Dict, 
                            risk_result: Dict, ml_score: float) -> float:
        """計算預測信心度"""
        
        confidence_factors = []
        
        # 因子一致性
        factor_scores = list(factor_result['individual_scores'].values())
        factor_std = np.std(factor_scores)
        consistency = max(0, 1 - factor_std / 25)
        confidence_factors.append(consistency * 0.3)
        
        # 情感數據品質
        sentiment_volume = sentiment_data.get('mention_volume', 0)
        sentiment_quality = min(1, sentiment_volume / 50)
        confidence_factors.append(sentiment_quality * 0.2)
        
        # 風險指標穩定性
        risk_stability = risk_result['composite_risk_score'] / 100
        confidence_factors.append(risk_stability * 0.2)
        
        # 機器學習預測信心
        ml_confidence = 0.8 if 40 <= ml_score <= 80 else 0.6
        confidence_factors.append(ml_confidence * 0.3)
        
        return max(0.3, min(1.0, sum(confidence_factors)))
    
    def _calculate_price_target_and_period(self, stock_data: Dict, final_score: float, 
                                         risk_result: Dict) -> Tuple[Optional[float], int]:
        """計算價格目標和持有期間"""
        
        current_price = stock_data.get('current_price')
        if not current_price:
            return None, 90  # 預設90天
        
        # 基於分數計算目標漲幅
        if final_score >= 80:
            target_return = 0.25  # 25%
            hold_period = 180  # 6個月
        elif final_score >= 70:
            target_return = 0.18  # 18%
            hold_period = 120  # 4個月
        elif final_score >= 60:
            target_return = 0.12  # 12%
            hold_period = 90   # 3個月
        else:
            target_return = 0.08  # 8%
            hold_period = 60   # 2個月
        
        # 風險調整
        risk_level = risk_result['risk_level']
        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            target_return *= 0.8
            hold_period = min(60, hold_period)
        
        target_price = current_price * (1 + target_return)
        
        return target_price, hold_period
    
    def _determine_price_trend(self, final_score: float) -> str:
        """判斷價格趨勢"""
        if final_score >= 75:
            return 'strong_bullish'
        elif final_score >= 65:
            return 'bullish'
        elif final_score >= 55:
            return 'neutral_bullish'
        elif final_score >= 45:
            return 'neutral'
        elif final_score >= 35:
            return 'neutral_bearish'
        elif final_score >= 25:
            return 'bearish'
        else:
            return 'strong_bearish'
    
    def _generate_reasoning(self, stock_data: Dict, final_score: float, 
                          factor_result: Dict, global_data: Dict) -> str:
        """生成推薦理由"""
        
        reasons = []
        
        # 基本面亮點
        factor_scores = factor_result['individual_scores']
        top_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        
        for factor, score in top_factors:
            if score > 70:
                if factor == 'growth':
                    reasons.append("成長性優異")
                elif factor == 'value':
                    reasons.append("估值具吸引力")
                elif factor == 'quality':
                    reasons.append("財務品質良好")
                elif factor == 'profitability':
                    reasons.append("獲利能力強勁")
        
        # 總經環境
        if global_data['global_score'] > 70:
            reasons.append("全球經濟環境有利")
        
        # 板塊展望
        sector_outlook = global_data.get('sector_outlook', {})
        sector = stock_data.get('sector', '').lower()
        for sector_key, multiplier in sector_outlook.items():
            if sector_key in sector and multiplier > 1.1:
                reasons.append(f"{sector_key}板塊前景看好")
                break
        
        # 綜合評價
        if final_score >= 80:
            reasons.append("綜合評分優異")
        elif final_score >= 70:
            reasons.append("整體表現良好")
        
        return "；".join(reasons) if reasons else "基於多因子分析結果"
    
    def _identify_risk_factors(self, stock_data: Dict, risk_result: Dict, global_data: Dict) -> List[str]:
        """識別風險因子"""
        
        risk_factors = []
        
        # 個股風險
        if risk_result['individual_risk']['volatility'] > 0.3:
            risk_factors.append("股價波動較大")
        
        if risk_result['individual_risk']['beta'] > 1.5:
            risk_factors.append("市場敏感度高")
        
        # 流動性風險
        if risk_result['liquidity_risk']['composite_risk'] > 0.6:
            risk_factors.append("流動性風險偏高")
        
        # 財務風險
        debt_ratio = stock_data.get('debt_ratio', 0)
        if debt_ratio > 60:
            risk_factors.append("負債比例偏高")
        
        # 市場風險
        if global_data['global_score'] < 40:
            risk_factors.append("全球經濟環境不佳")
        
        # 產業風險
        sector_outlook = global_data.get('sector_outlook', {})
        sector = stock_data.get('sector', '').lower()
        for sector_key, multiplier in sector_outlook.items():
            if sector_key in sector and multiplier < 0.9:
                risk_factors.append(f"{sector_key}板塊面臨逆風")
                break
        
        return risk_factors
    
    def _identify_catalysts(self, stock_data: Dict, global_data: Dict, sentiment_data: Dict) -> List[str]:
        """識別催化劑"""
        
        catalysts = []
        
        # 基本面催化劑
        eps_growth = stock_data.get('eps_growth', 0)
        if eps_growth > 20:
            catalysts.append("EPS高成長")
        
        revenue_growth = stock_data.get('revenue_growth', 0)
        if revenue_growth > 15:
            catalysts.append("營收快速成長")
        
        # 技術面催化劑
        if stock_data.get('price_trend') == 'bullish':
            catalysts.append("技術面突破")
        
        # 情感面催化劑
        if sentiment_data.get('sentiment_score', 0) > 0.3:
            catalysts.append("市場情感樂觀")
        
        # 總經催化劑
        if global_data['market_regime'] == MarketRegime.BULL_MARKET:
            catalysts.append("多頭市場環境")
        
        # 板塊催化劑
        sector_outlook = global_data.get('sector_outlook', {})
        sector = stock_data.get('sector', '').lower()
        for sector_key, multiplier in sector_outlook.items():
            if sector_key in sector and multiplier > 1.2:
                catalysts.append(f"{sector_key}板塊輪動")
                break
        
        return catalysts
    
    def _optimize_portfolio(self, recommendations: List[StockRecommendation]) -> List[StockRecommendation]:
        """投資組合優化 (簡化版)"""
        
        if len(recommendations) <= 10:
            return recommendations
        
        # 板塊分散
        sector_distribution = {}
        optimized = []
        
        for rec in recommendations:
            sector = rec.sector
            if sector not in sector_distribution:
                sector_distribution[sector] = 0
            
            # 限制單一板塊比重
            if sector_distribution[sector] < 3:
                sector_distribution[sector] += 1
                optimized.append(rec)
            
            if len(optimized) >= 15:
                break
        
        return optimized
    
    def generate_analysis_report(self, recommendations: List[StockRecommendation], 
                               global_data: Dict, sentiment_data: Dict) -> str:
        """生成分析報告"""
        
        report_lines = []
        
        # 報告標題
        report_lines.append("🚀 終極股票推薦系統分析報告")
        report_lines.append("=" * 50)
        report_lines.append(f"報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 市場概況
        report_lines.append("🌍 全球市場概況")
        report_lines.append(f"全球經濟分數: {global_data['global_score']:.1f}/100")
        report_lines.append(f"市場狀態: {global_data['market_regime'].value}")
        
        # 各區域經濟狀況
        regional_data = global_data.get('regional_data', {})
        if 'us' in regional_data:
            us_score = regional_data['us'].get('economic_score', 0)
            report_lines.append(f"美國經濟: {us_score:.1f}/100 | VIX: {regional_data['us'].get('vix_level', 0):.1f}")
        
        if 'china' in regional_data:
            china_score = regional_data['china'].get('economic_score', 0)
            report_lines.append(f"中國經濟: {china_score:.1f}/100 | 製造業PMI: {regional_data['china'].get('manufacturing_pmi', 0):.1f}")
        
        # 🆕 日本經濟狀況
        if 'japan' in regional_data:
            japan_score = regional_data['japan'].get('economic_score', 0)
            nikkei_momentum = regional_data['japan'].get('nikkei_momentum_3m', 0)
            usdjpy_rate = regional_data['japan'].get('usdjpy_rate', 150)
            yen_strength = regional_data['japan'].get('yen_strength', 'moderate')
            report_lines.append(f"日本經濟: {japan_score:.1f}/100 | 日經動能: {nikkei_momentum:+.1f}% | USD/JPY: {usdjpy_rate:.1f} ({yen_strength})")
        
        if 'taiwan' in regional_data:
            taiwan_score = regional_data['taiwan'].get('economic_score', 0)
            report_lines.append(f"台灣經濟: {taiwan_score:.1f}/100")
        
        # 台日關聯分析
        japan_taiwan_corr = global_data.get('japan_taiwan_correlation', {})
        if japan_taiwan_corr:
            correlation_level = japan_taiwan_corr.get('synchronization_level', 'medium')
            japan_impact = japan_taiwan_corr.get('japan_economic_impact', 'neutral')
            report_lines.append(f"台日經濟關聯: {correlation_level} | 日本影響: {japan_impact}")
            
            key_linkages = japan_taiwan_corr.get('key_linkages', [])
            if key_linkages:
                report_lines.append(f"主要關聯: {', '.join(key_linkages[:3])}")
        
        report_lines.append(f"市場情感: {sentiment_data['market_sentiment']['market_mood']}")
        report_lines.append(f"恐懼貪婪指數: {sentiment_data['fear_greed_index']:.0f}")
        report_lines.append("")
        
        # 推薦股票
        report_lines.append("📊 推薦股票清單")
        report_lines.append("-" * 30)
        
        for i, rec in enumerate(recommendations[:10], 1):
            report_lines.append(f"{i}. {rec.code} {rec.name}")
            report_lines.append(f"   綜合評分: {rec.final_score:.1f} | 信心度: {rec.confidence:.1%}")
            report_lines.append(f"   風險等級: {rec.risk_level.value} | 預期持有: {rec.hold_period}天")
            if rec.target_price:
                current_price = 100  # 假設當前價格
                upside = (rec.target_price / current_price - 1) * 100
                report_lines.append(f"   目標價: {rec.target_price:.1f} (上漲空間: {upside:.1f}%)")
            report_lines.append(f"   推薦理由: {rec.reasoning}")
            if rec.risk_factors:
                report_lines.append(f"   風險因子: {', '.join(rec.risk_factors[:2])}")
            report_lines.append("")
        
        # 投資建議
        report_lines.append("💡 投資建議")
        report_lines.append("- 建議分批建倉，控制單一持股比重")
        report_lines.append("- 密切關注全球經濟變化和市場情感指標")
        
        # 🆕 加入日本因素的投資建議
        japan_data = global_data.get('regional_data', {}).get('japan', {})
        if japan_data:
            japan_score = japan_data.get('economic_score', 50)
            yen_strength = japan_data.get('yen_strength', 'moderate')
            
            if japan_score > 65:
                report_lines.append("- 日本經濟復甦，可關注台日貿易受益股")
            
            if yen_strength in ['weak', 'very_weak']:
                report_lines.append("- 日圓走弱，出口導向企業可望受益")
            elif yen_strength in ['strong', 'very_strong']:
                report_lines.append("- 日圓走強，重點關注內需型產業")
            
            # 台日相關性建議
            japan_taiwan_corr = global_data.get('japan_taiwan_correlation', {})
            if japan_taiwan_corr.get('synchronization_level') == 'high':
                report_lines.append("- 台日市場高度同步，可參考日股走勢")
        
        report_lines.append("- 根據個人風險承受能力調整投資組合")
        report_lines.append("- 定期檢視投資組合表現並適時調整")
        report_lines.append("")
        
        # 風險提醒
        report_lines.append("⚠️ 風險提醒")
        report_lines.append("- 本分析僅供參考，投資有風險")
        report_lines.append("- 請根據自身財務狀況謹慎投資")
        report_lines.append("- 建議設置合適的停損點")
        report_lines.append("- 注意分散投資風險")
        
        return "\n".join(report_lines)

# 使用範例
async def main():
    """主程式範例"""
    
    # 模擬股票數據
    stock_universe = [
        {
            'code': '2330', 'name': '台積電', 'sector': 'technology',
            'current_price': 500, 'pe_ratio': 18.5, 'pb_ratio': 2.1, 'roe': 25.8,
            'debt_ratio': 12.3, 'eps_growth': 15.2, 'revenue_growth': 12.8,
            'rsi': 58, 'beta': 1.1, 'volatility': 0.22, 'price_momentum_3m': 8.5,
            'macd_signal': 'bullish', 'volume_trend': 'increasing',
            'price_trend': 'bullish', 'export_ratio': 85, 'avg_volume': 50000000,
            'market_cap': 12000000000000, 'major_shareholder_ratio': 45,
            'foreign_ownership': 78, 'gross_margin': 45, 'operating_margin': 38,
            'net_margin': 32, 'current_ratio': 2.1, 'ps_ratio': 6.8
        },
        {
            'code': '2454', 'name': '聯發科', 'sector': 'technology',
            'current_price': 800, 'pe_ratio': 16.2, 'pb_ratio': 1.8, 'roe': 18.9,
            'debt_ratio': 8.7, 'eps_growth': 22.1, 'revenue_growth': 18.5,
            'rsi': 45, 'beta': 1.3, 'volatility': 0.28, 'price_momentum_3m': 12.3,
            'macd_signal': 'neutral', 'volume_trend': 'stable',
            'price_trend': 'neutral', 'export_ratio': 92, 'avg_volume': 30000000,
            'market_cap': 1200000000000, 'major_shareholder_ratio': 38,
            'foreign_ownership': 65, 'gross_margin': 42, 'operating_margin': 25,
            'net_margin': 18, 'current_ratio': 1.8, 'ps_ratio': 4.2
        },
        {
            'code': '2317', 'name': '鴻海', 'sector': 'manufacturing',
            'current_price': 120, 'pe_ratio': 14.8, 'pb_ratio': 1.2, 'roe': 12.5,
            'debt_ratio': 35.6, 'eps_growth': 8.9, 'revenue_growth': 6.2,
            'rsi': 52, 'beta': 0.9, 'volatility': 0.25, 'price_momentum_3m': 3.1,
            'macd_signal': 'neutral', 'volume_trend': 'stable',
            'price_trend': 'neutral', 'export_ratio': 78, 'avg_volume': 80000000,
            'market_cap': 1800000000000, 'major_shareholder_ratio': 55,
            'foreign_ownership': 45, 'gross_margin': 8, 'operating_margin': 4,
            'net_margin': 2.8, 'current_ratio': 1.4, 'ps_ratio': 0.8
        },
        {
            'code': '2412', 'name': '中華電', 'sector': 'telecommunications',
            'current_price': 125, 'pe_ratio': 16.5, 'pb_ratio': 1.5, 'roe': 9.2,
            'debt_ratio': 28.4, 'eps_growth': 3.5, 'revenue_growth': 1.8,
            'rsi': 48, 'beta': 0.6, 'volatility': 0.18, 'price_momentum_3m': -1.2,
            'macd_signal': 'neutral', 'volume_trend': 'decreasing',
            'price_trend': 'neutral', 'export_ratio': 15, 'avg_volume': 25000000,
            'market_cap': 900000000000, 'major_shareholder_ratio': 65,
            'foreign_ownership': 28, 'gross_margin': 25, 'operating_margin': 18,
            'net_margin': 14, 'current_ratio': 1.2, 'ps_ratio': 2.1
        }
    ]
    
    # 初始化終極推薦系統
    recommender = UltimateStockRecommender()
    
    print("🚀 啟動終極股票推薦系統...")
    print("📊 整合功能: 全球景氣+情感分析+多因子+ML+風險管理+替代數據")
    print("=" * 60)
    
    try:
        # 生成推薦
        recommendations = await recommender.generate_ultimate_recommendations(
            stock_universe,
            custom_config={
                'max_recommendations': 10,
                'min_confidence_threshold': 0.5,
                'risk_tolerance': 'moderate'
            }
        )
        
        if recommendations:
            # 獲取市場數據用於報告
            global_data = await recommender.global_analyzer.get_global_economic_data()
            sentiment_data = await recommender.sentiment_analyzer.analyze_market_sentiment(
                [stock['code'] for stock in stock_universe]
            )
            
            # 生成詳細報告
            report = recommender.generate_analysis_report(recommendations, global_data, sentiment_data)
            print(report)
            
            # 額外顯示詳細分析
            print("\n" + "=" * 60)
            print("📈 詳細推薦分析")
            print("=" * 60)
            
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"\n{i}. 【{rec.code} {rec.name}】")
                print(f"   🎯 綜合評分: {rec.final_score:.1f}/100")
                print(f"   📊 各模組分數:")
                print(f"      基本面: {rec.fundamental_score:.1f} | 技術面: {rec.technical_score:.1f}")
                print(f"      情感面: {rec.sentiment_score:.1f} | 總經面: {rec.macro_score:.1f}")
                print(f"      ML預測: {rec.ml_score:.1f} | 替代數據: {rec.alternative_data_score:.1f}")
                print(f"   🎲 信心水準: {rec.confidence:.1%}")
                print(f"   ⚠️ 風險等級: {rec.risk_level.value}")
                print(f"   📅 建議持有: {rec.hold_period}天")
                if rec.target_price:
                    current_price = stock_universe[0]['current_price'] if i == 1 else 100
                    upside = (rec.target_price / current_price - 1) * 100
                    print(f"   💰 目標價位: {rec.target_price:.1f} (預期報酬: {upside:+.1f}%)")
                print(f"   💡 推薦理由: {rec.reasoning}")
                if rec.catalysts:
                    print(f"   🚀 催化因子: {', '.join(rec.catalysts[:3])}")
                if rec.risk_factors:
                    print(f"   ⚠️ 風險提醒: {', '.join(rec.risk_factors[:2])}")
        
        else:
            print("❌ 未能生成推薦，請檢查數據或調整篩選條件")
            
    except Exception as e:
        print(f"❌ 系統執行失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理資源
        await recommender.sentiment_analyzer.close()

if __name__ == "__main__":
    # 執行主程式
    asyncio.run(main())
