"""
stock_analyzer.py - 股票技術分析模組（增強版）
加入現價和漲跌百分比顯示功能
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import logging

# 配置日誌
logger = logging.getLogger(__name__)

class StockAnalyzer:
    """股票技術分析器"""
    
    def __init__(self):
        """初始化分析器"""
        # 技術指標參數
        self.rsi_period = 14
        self.ma_short = 5
        self.ma_medium = 20
        self.ma_long = 60
        self.volume_ma = 5
        
    def analyze_single_stock(self, stock_data: Dict, historical_data: pd.DataFrame = None) -> Dict:
        """
        分析單支股票
        
        參數:
        - stock_data: 當日股票數據
        - historical_data: 歷史數據DataFrame（可選）
        
        返回:
        - 分析結果字典
        """
        analysis = {
            'code': stock_data['code'],
            'name': stock_data['name'],
            'close': stock_data['close'],
            'change': stock_data.get('change', 0),
            'change_percent': stock_data.get('change_percent', 0),
            'volume': stock_data['volume'],
            'trade_value': stock_data['trade_value'],
            'signals': [],
            'patterns': [],
            'indicators': {},
            'score': 0
        }
        
        # 如果有歷史數據，進行技術分析
        if historical_data is not None and len(historical_data) > 0:
            # 計算技術指標
            indicators = self._calculate_indicators(historical_data)
            analysis['indicators'] = indicators
            
            # 識別技術形態
            patterns = self._identify_patterns(historical_data, indicators)
            analysis['patterns'] = patterns
            
            # 生成交易信號
            signals = self._generate_signals(stock_data, indicators, patterns)
            analysis['signals'] = signals
            
            # 計算綜合評分
            score = self._calculate_score(indicators, patterns, signals)
            analysis['score'] = score
        
        return analysis
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """計算技術指標"""
        indicators = {}
        
        # 計算移動平均線
        if len(df) >= self.ma_short:
            indicators['ma5'] = df['close'].rolling(window=self.ma_short).mean().iloc[-1]
        
        if len(df) >= self.ma_medium:
            indicators['ma20'] = df['close'].rolling(window=self.ma_medium).mean().iloc[-1]
        
        if len(df) >= self.ma_long:
            indicators['ma60'] = df['close'].rolling(window=self.ma_long).mean().iloc[-1]
        
        # 計算RSI
        if len(df) >= self.rsi_period + 1:
            rsi = self._calculate_rsi(df['close'], self.rsi_period)
            if len(rsi) > 0:
                indicators['rsi'] = rsi.iloc[-1]
        
        # 計算MACD
        if len(df) >= 26:
            macd, signal, histogram = self._calculate_macd(df['close'])
            if len(macd) > 0:
                indicators['macd'] = macd.iloc[-1]
                indicators['macd_signal'] = signal.iloc[-1]
                indicators['macd_histogram'] = histogram.iloc[-1]
        
        # 計算成交量指標
        if len(df) >= self.volume_ma:
            indicators['volume_ma'] = df['volume'].rolling(window=self.volume_ma).mean().iloc[-1]
            indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_ma']
        
        return indicators
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """計算MACD指標"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return macd, signal, histogram
    
    def _identify_patterns(self, df: pd.DataFrame, indicators: Dict) -> List[str]:
        """識別技術形態"""
        patterns = []
        
        if len(df) < 2:
            return patterns
        
        # 檢查突破形態
        current_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        
        # 檢查均線突破
        if 'ma20' in indicators and current_close > indicators['ma20'] and prev_close <= indicators['ma20']:
            patterns.append('突破20日均線')
        
        if 'ma60' in indicators and current_close > indicators['ma60'] and prev_close <= indicators['ma60']:
            patterns.append('突破60日均線')
        
        # 檢查成交量突破
        if 'volume_ratio' in indicators and indicators['volume_ratio'] > 2:
            patterns.append('成交量突破')
        
        # 檢查RSI超買超賣
        if 'rsi' in indicators:
            if indicators['rsi'] > 70:
                patterns.append('RSI超買')
            elif indicators['rsi'] < 30:
                patterns.append('RSI超賣')
        
        # 檢查MACD金叉死叉
        if len(df) >= 2 and 'macd' in indicators and 'macd_signal' in indicators:
            current_macd = indicators['macd']
            current_signal = indicators['macd_signal']
            
            # 需要計算前一天的MACD值來判斷金叉死叉
            if len(df) >= 27:  # 確保有足夠數據計算前一天的MACD
                prev_prices = df['close'].iloc[:-1]
                prev_macd, prev_signal, _ = self._calculate_macd(prev_prices)
                
                if len(prev_macd) > 0 and len(prev_signal) > 0:
                    prev_macd_val = prev_macd.iloc[-1]
                    prev_signal_val = prev_signal.iloc[-1]
                    
                    if current_macd > current_signal and prev_macd_val <= prev_signal_val:
                        patterns.append('MACD金叉')
                    elif current_macd < current_signal and prev_macd_val >= prev_signal_val:
                        patterns.append('MACD死叉')
        
        return patterns
    
    def _generate_signals(self, stock_data: Dict, indicators: Dict, patterns: List[str]) -> List[str]:
        """生成交易信號"""
        signals = []
        
        # 基於形態的信號
        if '突破20日均線' in patterns and '成交量突破' in patterns:
            signals.append('強勢突破信號')
        
        if 'RSI超賣' in patterns and 'MACD金叉' in patterns:
            signals.append('買入信號')
        
        if 'RSI超買' in patterns and 'MACD死叉' in patterns:
            signals.append('賣出信號')
        
        # 基於指標的信號
        if indicators.get('rsi', 50) < 30 and indicators.get('volume_ratio', 1) > 1.5:
            signals.append('超賣反彈信號')
        
        # 基於價格動能的信號
        if stock_data.get('change_percent', 0) > 5 and indicators.get('volume_ratio', 1) > 2:
            signals.append('強勢上漲信號')
        
        return signals
    
    def _calculate_score(self, indicators: Dict, patterns: List[str], signals: List[str]) -> float:
        """計算綜合評分（0-100）"""
        score = 50  # 基礎分數
        
        # 根據技術指標調整分數
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if 30 <= rsi <= 70:
                score += 5  # RSI在正常範圍
            elif rsi < 30:
                score += 10  # 超賣可能反彈
            else:
                score -= 5  # 超買風險
        
        # 根據均線位置調整分數
        if 'ma20' in indicators and 'ma60' in indicators:
            if indicators.get('ma5', 0) > indicators['ma20'] > indicators['ma60']:
                score += 10  # 多頭排列
        
        # 根據形態調整分數
        positive_patterns = ['突破20日均線', '突破60日均線', 'MACD金叉', '成交量突破']
        negative_patterns = ['MACD死叉', 'RSI超買']
        
        for pattern in patterns:
            if pattern in positive_patterns:
                score += 5
            elif pattern in negative_patterns:
                score -= 5
        
        # 根據信號調整分數
        positive_signals = ['強勢突破信號', '買入信號', '超賣反彈信號', '強勢上漲信號']
        negative_signals = ['賣出信號']
        
        for signal in signals:
            if signal in positive_signals:
                score += 8
            elif signal in negative_signals:
                score -= 8
        
        # 確保分數在0-100範圍內
        score = max(0, min(100, score))
        
        return score
    
    def batch_analyze(self, stocks_data: List[Dict], get_historical_func=None) -> List[Dict]:
        """
        批量分析股票
        
        參數:
        - stocks_data: 股票數據列表
        - get_historical_func: 獲取歷史數據的函數
        
        返回:
        - 分析結果列表
        """
        results = []
        
        for stock in stocks_data:
            try:
                # 獲取歷史數據
                historical_data = None
                if get_historical_func:
                    historical_data = get_historical_func(stock['code'])
                
                # 分析股票
                analysis = self.analyze_single_stock(stock, historical_data)
                results.append(analysis)
                
            except Exception as e:
                logger.error(f"分析股票 {stock['code']} 時發生錯誤: {e}")
                # 即使出錯也返回基本信息
                results.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'close': stock['close'],
                    'change': stock.get('change', 0),
                    'change_percent': stock.get('change_percent', 0),
                    'volume': stock['volume'],
                    'trade_value': stock['trade_value'],
                    'signals': [],
                    'patterns': [],
                    'indicators': {},
                    'score': 0
                })
        
        return results
    
    def filter_by_criteria(self, analysis_results: List[Dict], criteria: Dict) -> List[Dict]:
        """
        根據條件篩選股票
        
        參數:
        - analysis_results: 分析結果列表
        - criteria: 篩選條件
        
        返回:
        - 符合條件的股票列表
        """
        filtered = []
        
        for result in analysis_results:
            # 檢查分數條件
            if 'min_score' in criteria and result['score'] < criteria['min_score']:
                continue
            
            # 檢查必須包含的形態
            if 'required_patterns' in criteria:
                if not all(pattern in result['patterns'] for pattern in criteria['required_patterns']):
                    continue
            
            # 檢查必須包含的信號
            if 'required_signals' in criteria:
                if not all(signal in result['signals'] for signal in criteria['required_signals']):
                    continue
            
            # 檢查成交量條件
            if 'min_volume_ratio' in criteria:
                volume_ratio = result['indicators'].get('volume_ratio', 0)
                if volume_ratio < criteria['min_volume_ratio']:
                    continue
            
            # 檢查RSI條件
            if 'rsi_range' in criteria:
                rsi = result['indicators'].get('rsi', 50)
                if not (criteria['rsi_range'][0] <= rsi <= criteria['rsi_range'][1]):
                    continue
            
            filtered.append(result)
        
        return filtered

# 測試代碼
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 創建分析器
    analyzer = StockAnalyzer()
    
    # 測試數據
    test_stock = {
        'code': '2330',
        'name': '台積電',
        'close': 850.0,
        'change': 15.0,
        'change_percent': 1.8,
        'volume': 25000000,
        'trade_value': 21250000000
    }
    
    # 創建模擬歷史數據
    dates = pd.date_range(end=datetime.now(), periods=30)
    historical_data = pd.DataFrame({
        'date': dates,
        'close': np.random.normal(850, 20, 30),
        'volume': np.random.normal(25000000, 5000000, 30),
        'high': np.random.normal(860, 20, 30),
        'low': np.random.normal(840, 20, 30),
        'open': np.random.normal(850, 20, 30)
    })
    
    # 分析股票
    result = analyzer.analyze_single_stock(test_stock, historical_data)
    
    print(f"股票: {result['name']} ({result['code']})")
    print(f"現價: {result['close']} 漲跌: {result['change']} ({result['change_percent']}%)")
    print(f"評分: {result['score']}")
    print(f"形態: {', '.join(result['patterns']) if result['patterns'] else '無'}")
    print(f"信號: {', '.join(result['signals']) if result['signals'] else '無'}")
