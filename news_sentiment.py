"""
news_sentiment.py - 新聞情緒分析系統
爬取財經新聞並分析市場情緒

功能：
1. 多來源新聞爬取（Yahoo 財經、鉅亨網、經濟日報等）
2. 中文情緒分析
3. 股票相關新聞過濾
4. 情緒分數計算
"""

import requests
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

# 嘗試導入 jieba 進行中文分詞
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logger.info("jieba 未安裝，使用簡化版本")


class ChineseSentimentAnalyzer:
    """
    中文情緒分析器
    使用詞典法進行情緒分析
    """

    def __init__(self):
        # 正面詞彙（股市相關）
        self.positive_words = {
            # 強烈正面
            '大漲', '暴漲', '飆升', '飆漲', '強漲', '急漲', '創新高',
            '突破', '噴出', '井噴', '爆量', '大買超', '狂買',
            # 正面
            '上漲', '漲', '漲停', '紅盤', '收紅', '走高', '攀升',
            '回升', '反彈', '轉強', '上揚', '走揚', '拉升',
            '買進', '買超', '買盤', '加碼', '布局', '卡位',
            '看好', '看多', '看漲', '樂觀', '利多', '正面',
            '成長', '獲利', '盈餘', '營收增', '業績佳',
            '創高', '新高', '歷史高', '亮眼', '優於預期',
            '推薦', '首選', '潛力', '題材', '熱門',
            '外資買', '法人買', '投信買', '主力買'
        }

        # 負面詞彙
        self.negative_words = {
            # 強烈負面
            '大跌', '暴跌', '崩盤', '崩跌', '急跌', '重挫', '慘跌',
            '跳水', '殺盤', '倒貨', '大賣超', '狂賣',
            # 負面
            '下跌', '跌', '跌停', '綠盤', '收黑', '走低', '下挫',
            '回落', '回檔', '轉弱', '下探', '破底', '探底',
            '賣出', '賣超', '賣壓', '減碼', '出脫', '獲利了結',
            '看壞', '看空', '看跌', '悲觀', '利空', '負面',
            '衰退', '虧損', '下滑', '營收減', '業績差',
            '創低', '新低', '跌破', '低於預期',
            '外資賣', '法人賣', '投信賣', '主力賣',
            '警示', '風險', '危機', '泡沫', '過熱'
        }

        # 程度副詞
        self.intensifiers = {
            '大': 1.5, '非常': 1.5, '極': 2.0, '超': 1.5,
            '特別': 1.3, '相當': 1.2, '很': 1.2, '更': 1.2,
            '持續': 1.1, '連續': 1.2, '再': 1.1
        }

        # 否定詞
        self.negations = {'不', '沒', '未', '非', '無', '難'}

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        分析文本情緒

        Returns:
            {
                'score': float,  # -1 到 1
                'sentiment': str,  # positive, negative, neutral
                'confidence': float,
                'positive_count': int,
                'negative_count': int,
                'keywords': List[str]
            }
        """
        if not text:
            return {'score': 0, 'sentiment': 'neutral', 'confidence': 0}

        # 分詞
        if JIEBA_AVAILABLE:
            words = list(jieba.cut(text))
        else:
            words = list(text)  # 簡單按字分割

        positive_count = 0
        negative_count = 0
        positive_score = 0
        negative_score = 0
        keywords = []

        # 計算情緒分數
        i = 0
        while i < len(words):
            word = words[i]

            # 檢查程度副詞
            intensity = 1.0
            if i > 0 and words[i-1] in self.intensifiers:
                intensity = self.intensifiers[words[i-1]]

            # 檢查否定
            negated = i > 0 and words[i-1] in self.negations

            if word in self.positive_words:
                if negated:
                    negative_count += 1
                    negative_score += intensity
                else:
                    positive_count += 1
                    positive_score += intensity
                    keywords.append(word)

            elif word in self.negative_words:
                if negated:
                    positive_count += 1
                    positive_score += intensity
                else:
                    negative_count += 1
                    negative_score += intensity
                    keywords.append(word)

            # 檢查詞組（兩個字以上）
            if i < len(words) - 1:
                bigram = word + words[i+1]
                if bigram in self.positive_words:
                    positive_count += 1
                    positive_score += intensity * 1.2
                    keywords.append(bigram)
                elif bigram in self.negative_words:
                    negative_count += 1
                    negative_score += intensity * 1.2
                    keywords.append(bigram)

            i += 1

        # 計算最終分數
        total = positive_score + negative_score
        if total == 0:
            score = 0
            confidence = 0
        else:
            score = (positive_score - negative_score) / total
            confidence = min(total / 10, 1.0)  # 越多關鍵詞信心越高

        # 判斷情緒
        if score > 0.2:
            sentiment = 'positive'
        elif score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        return {
            'score': round(score, 4),
            'sentiment': sentiment,
            'confidence': round(confidence, 4),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'keywords': list(set(keywords))[:10]
        }


class NewsCollector:
    """
    新聞收集器
    從多個來源收集財經新聞
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.request_delay = 1.0

    def collect_yahoo_finance_news(self, stock_code: str = None,
                                   limit: int = 10) -> List[Dict]:
        """
        從 Yahoo 財經收集新聞
        """
        news_list = []

        try:
            if stock_code:
                # 個股新聞
                url = f"https://tw.stock.yahoo.com/quote/{stock_code}.TW/news"
            else:
                # 一般財經新聞
                url = "https://tw.stock.yahoo.com/news"

            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 找新聞標題
                articles = soup.find_all('h3', class_=re.compile('Mb'))
                for article in articles[:limit]:
                    title = article.get_text().strip()
                    link = article.find('a')
                    href = link.get('href', '') if link else ''

                    if title:
                        news_list.append({
                            'title': title,
                            'link': href,
                            'source': 'Yahoo財經',
                            'timestamp': datetime.now().isoformat()
                        })

        except Exception as e:
            logger.warning(f"Yahoo 財經新聞獲取失敗: {e}")

        return news_list

    def collect_cnyes_news(self, limit: int = 10) -> List[Dict]:
        """
        從鉅亨網收集新聞
        """
        news_list = []

        try:
            url = "https://news.cnyes.com/api/v3/news/category/tw_stock"
            params = {'limit': limit}

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', {}).get('data', [])

                for item in items:
                    news_list.append({
                        'title': item.get('title', ''),
                        'summary': item.get('summary', ''),
                        'link': f"https://news.cnyes.com/news/id/{item.get('newsId', '')}",
                        'source': '鉅亨網',
                        'timestamp': item.get('publishAt', datetime.now().isoformat())
                    })

        except Exception as e:
            logger.warning(f"鉅亨網新聞獲取失敗: {e}")

        return news_list

    def collect_udn_news(self, limit: int = 10) -> List[Dict]:
        """
        從經濟日報收集新聞
        """
        news_list = []

        try:
            url = "https://money.udn.com/rank/newest/1001/0/0"

            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                articles = soup.find_all('div', class_='story-content')
                for article in articles[:limit]:
                    title_elem = article.find('a', class_='story-title')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        href = title_elem.get('href', '')

                        news_list.append({
                            'title': title,
                            'link': f"https://money.udn.com{href}" if href.startswith('/') else href,
                            'source': '經濟日報',
                            'timestamp': datetime.now().isoformat()
                        })

        except Exception as e:
            logger.warning(f"經濟日報新聞獲取失敗: {e}")

        return news_list

    def collect_all_news(self, stock_code: str = None, limit: int = 30) -> List[Dict]:
        """
        從所有來源收集新聞
        """
        all_news = []

        # Yahoo 財經
        yahoo_news = self.collect_yahoo_finance_news(stock_code, limit=limit//3)
        all_news.extend(yahoo_news)
        time.sleep(self.request_delay)

        # 鉅亨網
        cnyes_news = self.collect_cnyes_news(limit=limit//3)
        all_news.extend(cnyes_news)
        time.sleep(self.request_delay)

        # 經濟日報
        udn_news = self.collect_udn_news(limit=limit//3)
        all_news.extend(udn_news)

        return all_news


class NewsSentimentSystem:
    """
    新聞情緒分析系統
    整合新聞收集和情緒分析
    """

    def __init__(self):
        self.collector = NewsCollector()
        self.analyzer = ChineseSentimentAnalyzer()

    def analyze_market_sentiment(self, limit: int = 30) -> Dict[str, Any]:
        """
        分析整體市場情緒

        Returns:
            {
                'overall_score': float,  # -1 到 1
                'sentiment': str,
                'confidence': float,
                'positive_ratio': float,
                'negative_ratio': float,
                'top_positive_news': List,
                'top_negative_news': List,
                'keywords': List
            }
        """
        # 收集新聞
        news_list = self.collector.collect_all_news(limit=limit)

        if not news_list:
            return {
                'overall_score': 0,
                'sentiment': 'neutral',
                'confidence': 0,
                'news_count': 0
            }

        # 分析每條新聞
        analyzed_news = []
        all_keywords = []

        for news in news_list:
            text = news.get('title', '') + ' ' + news.get('summary', '')
            result = self.analyzer.analyze(text)

            analyzed_news.append({
                **news,
                'sentiment_score': result['score'],
                'sentiment': result['sentiment'],
                'keywords': result['keywords']
            })

            all_keywords.extend(result['keywords'])

        # 計算整體情緒
        scores = [n['sentiment_score'] for n in analyzed_news]
        overall_score = sum(scores) / len(scores) if scores else 0

        positive_count = sum(1 for n in analyzed_news if n['sentiment'] == 'positive')
        negative_count = sum(1 for n in analyzed_news if n['sentiment'] == 'negative')

        # 計算信心度
        confidence = min(len(analyzed_news) / 20, 1.0) * min(abs(overall_score) * 2, 1.0)

        # 判斷情緒
        if overall_score > 0.15:
            sentiment = 'positive'
        elif overall_score < -0.15:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # 找出最正面和最負面的新聞
        sorted_by_score = sorted(analyzed_news, key=lambda x: x['sentiment_score'], reverse=True)
        top_positive = [n for n in sorted_by_score[:5] if n['sentiment_score'] > 0]
        top_negative = [n for n in sorted_by_score[-5:] if n['sentiment_score'] < 0]

        # 統計關鍵詞
        keyword_counts = {}
        for kw in all_keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'overall_score': round(overall_score, 4),
            'sentiment': sentiment,
            'confidence': round(confidence, 4),
            'news_count': len(analyzed_news),
            'positive_ratio': positive_count / len(analyzed_news) if analyzed_news else 0,
            'negative_ratio': negative_count / len(analyzed_news) if analyzed_news else 0,
            'top_positive_news': top_positive[:3],
            'top_negative_news': top_negative[:3],
            'keywords': [kw[0] for kw in top_keywords],
            'analyzed_news': analyzed_news[:10]  # 返回前10條分析結果
        }

    def analyze_stock_sentiment(self, stock_code: str,
                                stock_name: str = None) -> Dict[str, Any]:
        """
        分析特定股票的新聞情緒
        """
        # 收集該股票相關新聞
        news_list = self.collector.collect_yahoo_finance_news(stock_code, limit=20)

        # 也搜尋股票名稱相關新聞
        if stock_name:
            all_news = self.collector.collect_all_news(limit=30)
            related_news = [n for n in all_news
                          if stock_code in n.get('title', '') or
                          stock_name in n.get('title', '')]
            news_list.extend(related_news)

        if not news_list:
            return {
                'stock_code': stock_code,
                'overall_score': 0,
                'sentiment': 'neutral',
                'confidence': 0,
                'news_count': 0
            }

        # 分析
        analyzed = []
        for news in news_list:
            text = news.get('title', '') + ' ' + news.get('summary', '')
            result = self.analyzer.analyze(text)
            analyzed.append({
                **news,
                'sentiment_score': result['score'],
                'sentiment': result['sentiment']
            })

        scores = [n['sentiment_score'] for n in analyzed]
        overall_score = sum(scores) / len(scores) if scores else 0

        return {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'overall_score': round(overall_score, 4),
            'sentiment': 'positive' if overall_score > 0.15 else ('negative' if overall_score < -0.15 else 'neutral'),
            'confidence': min(len(analyzed) / 10, 1.0),
            'news_count': len(analyzed),
            'latest_news': analyzed[:5]
        }

    def get_sentiment_signal(self) -> Dict[str, Any]:
        """
        獲取情緒信號（用於交易策略）

        Returns:
            {
                'signal': int,  # -1, 0, 1
                'strength': float,  # 0 到 1
                'description': str
            }
        """
        result = self.analyze_market_sentiment(limit=20)

        score = result['overall_score']
        confidence = result['confidence']

        # 計算信號
        if score > 0.3 and confidence > 0.5:
            signal = 1
            strength = min(score * confidence * 2, 1.0)
            description = '市場情緒樂觀，新聞面偏多'
        elif score < -0.3 and confidence > 0.5:
            signal = -1
            strength = min(abs(score) * confidence * 2, 1.0)
            description = '市場情緒悲觀，新聞面偏空'
        elif score > 0.15:
            signal = 1
            strength = score * confidence
            description = '市場情緒略偏樂觀'
        elif score < -0.15:
            signal = -1
            strength = abs(score) * confidence
            description = '市場情緒略偏悲觀'
        else:
            signal = 0
            strength = 0
            description = '市場情緒中性'

        return {
            'signal': signal,
            'strength': round(strength, 4),
            'description': description,
            'raw_score': score,
            'keywords': result.get('keywords', [])[:5],
            'news_count': result.get('news_count', 0)
        }


# ==================== 整合到預測系統 ====================

class SentimentEnhancedPredictor:
    """
    情緒增強預測器
    結合新聞情緒與技術分析
    """

    def __init__(self):
        self.sentiment_system = NewsSentimentSystem()
        self.sentiment_weight = 0.2  # 情緒在最終預測中的權重

    def get_enhanced_prediction(self, technical_score: float,
                                stock_code: str = None,
                                stock_name: str = None) -> Dict[str, Any]:
        """
        獲取情緒增強後的預測

        Args:
            technical_score: 技術分析分數 (-1 到 1)
            stock_code: 股票代碼（可選）
            stock_name: 股票名稱（可選）

        Returns:
            增強後的預測結果
        """
        # 獲取市場情緒
        market_sentiment = self.sentiment_system.get_sentiment_signal()

        # 如果有股票代碼，獲取個股情緒
        stock_sentiment = None
        if stock_code:
            try:
                stock_sentiment = self.sentiment_system.analyze_stock_sentiment(
                    stock_code, stock_name
                )
            except Exception as e:
                logger.warning(f"個股情緒分析失敗: {e}")

        # 計算情緒分數
        sentiment_score = market_sentiment['raw_score']
        if stock_sentiment and stock_sentiment['confidence'] > 0.3:
            # 結合個股和市場情緒
            sentiment_score = (
                market_sentiment['raw_score'] * 0.4 +
                stock_sentiment['overall_score'] * 0.6
            )

        # 結合技術分析和情緒分析
        combined_score = (
            technical_score * (1 - self.sentiment_weight) +
            sentiment_score * self.sentiment_weight
        )

        # 判斷最終信號
        if combined_score > 0.3:
            signal = 'bullish'
            action = '買入'
        elif combined_score > 0.1:
            signal = 'slightly_bullish'
            action = '偏多觀望'
        elif combined_score < -0.3:
            signal = 'bearish'
            action = '賣出'
        elif combined_score < -0.1:
            signal = 'slightly_bearish'
            action = '偏空觀望'
        else:
            signal = 'neutral'
            action = '觀望'

        return {
            'combined_score': round(combined_score, 4),
            'technical_score': round(technical_score, 4),
            'sentiment_score': round(sentiment_score, 4),
            'signal': signal,
            'action': action,
            'market_sentiment': market_sentiment,
            'stock_sentiment': stock_sentiment,
            'sentiment_keywords': market_sentiment.get('keywords', [])
        }


# ==================== 測試 ====================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("📰 新聞情緒分析系統測試")
    print("=" * 60)

    # 測試情緒分析器
    print("\n1. 中文情緒分析測試")
    analyzer = ChineseSentimentAnalyzer()

    test_texts = [
        "台積電大漲創新高，外資持續買超",
        "股市崩盤暴跌，投資人恐慌拋售",
        "今日大盤小漲，成交量持平",
        "法人看好半導體前景，建議加碼布局",
        "營收衰退，公司發布獲利警訊"
    ]

    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"文本: {text}")
        print(f"  → 情緒: {result['sentiment']}, 分數: {result['score']:.2f}")
        print(f"  → 關鍵詞: {result['keywords']}")
        print()

    # 測試新聞收集（需要網路）
    print("2. 新聞收集測試")
    collector = NewsCollector()
    try:
        news = collector.collect_cnyes_news(limit=3)
        print(f"鉅亨網新聞: 獲取 {len(news)} 條")
        for n in news[:2]:
            print(f"  • {n['title'][:40]}...")
    except Exception as e:
        print(f"新聞收集失敗: {e}")

    # 測試整體市場情緒
    print("\n3. 市場情緒分析")
    system = NewsSentimentSystem()
    try:
        result = system.analyze_market_sentiment(limit=10)
        print(f"整體情緒: {result['sentiment']}")
        print(f"情緒分數: {result['overall_score']:.2f}")
        print(f"信心度: {result['confidence']:.2f}")
        print(f"熱門關鍵詞: {result.get('keywords', [])[:5]}")
    except Exception as e:
        print(f"市場情緒分析失敗: {e}")

    # 測試情緒信號
    print("\n4. 交易情緒信號")
    try:
        signal = system.get_sentiment_signal()
        print(f"信號: {signal['signal']}")
        print(f"強度: {signal['strength']:.2f}")
        print(f"描述: {signal['description']}")
    except Exception as e:
        print(f"情緒信號獲取失敗: {e}")
