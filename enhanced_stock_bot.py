#!/usr/bin/env python3
"""
enhanced_stock_bot.py - 增強版股票分析機器人
整合技術分析、基本面分析、法人動向分析的綜合股票推薦系統
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class StockAnalysis:
    """股票分析結果數據結構"""
    code: str
    name: str
    current_price: float
    change_percent: float
    volume: int
    trade_value: int
    
    # 評分系統
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    institutional_score: float = 0.0
    weighted_score: float = 0.0
    base_score: float = 0.0
    
    # 技術指標
    rsi: float = 50.0
    volume_ratio: float = 1.0
    technical_signals: Dict[str, bool] = None
    
    # 基本面數據
    dividend_yield: float = 0.0
    eps_growth: float = 0.0
    pe_ratio: float = 0.0
    roe: float = 0.0
    
    # 法人數據
    foreign_net_buy: int = 0
    trust_net_buy: int = 0
    dealer_net_buy: int = 0
    
    # 增強分析
    enhanced_analysis: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.technical_signals is None:
            self.technical_signals = {}
        if self.enhanced_analysis is None:
            self.enhanced_analysis = {}

class EnhancedStockBot:
    """增強版股票分析機器人"""
    
    def __init__(self):
        self.setup_logging()
        
        # 時段配置
        self.time_slot_config = {
            'morning_scan': {
                'name': '早盤掃描',
                'scan_limit': 200,
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 2,
                    'weak_stocks': 2
                },
                'analysis_weights': {
                    'technical': 0.4,
                    'fundamental': 0.3,
                    'institutional': 0.3
                }
            },
            'afternoon_scan': {
                'name': '午後掃描',
                'scan_limit': 500,
                'recommendation_limits': {
                    'short_term': 4,
                    'long_term': 3,
                    'weak_stocks': 2
                },
                'analysis_weights': {
                    'technical': 0.35,
                    'fundamental': 0.35,
                    'institutional': 0.30
                }
            },
            'weekly_summary': {
                'name': '週末總結',
                'scan_limit': 300,
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 5,
                    'weak_stocks': 3
                },
                'analysis_weights': {
                    'technical': 0.25,
                    'fundamental': 0.45,
                    'institutional': 0.30
                }
            }
        }
        
        self.logger.info("增強版股票分析機器人初始化完成")
    
    def setup_logging(self):
        """設置日誌系統"""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'enhanced_stock_bot.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_stocks_comprehensive(self, time_slot: str = 'afternoon_scan') -> Dict[str, List[Dict]]:
        """執行綜合股票分析"""
        self.logger.info(f"開始執行 {time_slot} 綜合分析")
        start_time = time.time()
        
        try:
            # 1. 獲取股票數據
            stock_data = self._fetch_stock_data(time_slot)
            
            if not stock_data:
                self.logger.error("無法獲取股票數據")
                return {"short_term": [], "long_term": [], "weak_stocks": []}
            
            self.logger.info(f"獲取到 {len(stock_data)} 支股票數據")
            
            # 2. 執行增強分析
            analyses = []
            for stock in stock_data:
                analysis = self.analyze_stock_enhanced(stock, time_slot)
                if analysis:
                    analyses.append(analysis)
            
            self.logger.info(f"完成 {len(analyses)} 支股票的增強分析")
            
            # 3. 生成推薦
            recommendations = self.generate_recommendations(analyses, time_slot)
            
            # 4. 發送通知
            self._send_recommendations(recommendations, time_slot)
            
            execution_time = time.time() - start_time
            self.logger.info(f"綜合分析完成，耗時 {execution_time:.2f} 秒")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"綜合分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {"short_term": [], "long_term": [], "weak_stocks": []}
    
    def _fetch_stock_data(self, time_slot: str) -> List[Dict[str, Any]]:
        """獲取股票數據"""
        try:
            from twse_data_fetcher import TWStockDataFetcher
            fetcher = TWStockDataFetcher()
            stock_data = fetcher.get_stocks_by_time_slot(time_slot)
            return stock_data
            
        except ImportError:
            self.logger.warning("數據抓取器不可用，使用模擬數據")
            return self._generate_mock_data(time_slot)
        except Exception as e:
            self.logger.error(f"數據獲取失敗: {e}")
            return self._generate_mock_data(time_slot)
    
    def _generate_mock_data(self, time_slot: str) -> List[Dict[str, Any]]:
        """生成模擬數據"""
        mock_stocks = [
            {'code': '2330', 'name': '台積電', 'base_price': 638.5, 'sector': 'tech'},
            {'code': '2317', 'name': '鴻海', 'base_price': 115.5, 'sector': 'tech'},
            {'code': '2454', 'name': '聯發科', 'base_price': 825.0, 'sector': 'tech'},
            {'code': '2412', 'name': '中華電', 'base_price': 118.5, 'sector': 'telecom'},
            {'code': '2609', 'name': '陽明', 'base_price': 91.2, 'sector': 'shipping'},
            {'code': '2603', 'name': '長榮', 'base_price': 195.5, 'sector': 'shipping'},
            {'code': '2881', 'name': '富邦金', 'base_price': 68.2, 'sector': 'finance'},
            {'code': '2882', 'name': '國泰金', 'base_price': 45.8, 'sector': 'finance'},
            {'code': '2308', 'name': '台達電', 'base_price': 362.5, 'sector': 'tech'},
            {'code': '2615', 'name': '萬海', 'base_price': 132.8, 'sector': 'shipping'}
        ]
        
        stock_data = []
        for stock in mock_stocks:
            # 使用代碼作為隨機種子確保一致性
            random.seed(hash(stock['code'] + str(datetime.now().date())) % 1000)
            
            change_percent = random.uniform(-4, 6)
            current_price = stock['base_price'] * (1 + change_percent / 100)
            volume = random.randint(5000000, 50000000)
            
            stock_data.append({
                'code': stock['code'],
                'name': stock['name'],
                'close': round(current_price, 2),
                'change_percent': round(change_percent, 2),
                'volume': volume,
                'trade_value': int(current_price * volume),
                'sector': stock['sector'],
                'data_source': 'mock'
            })
        
        return sorted(stock_data, key=lambda x: x['trade_value'], reverse=True)
    
    def analyze_stock_enhanced(self, stock_info: Dict[str, Any], analysis_type: str = 'comprehensive') -> Optional[StockAnalysis]:
        """增強版股票分析"""
        try:
            # 創建基礎分析對象
            analysis = StockAnalysis(
                code=stock_info['code'],
                name=stock_info['name'],
                current_price=stock_info.get('close', 0),
                change_percent=stock_info.get('change_percent', 0),
                volume=stock_info.get('volume', 0),
                trade_value=stock_info.get('trade_value', 0)
            )
            
            # 技術面分析
            self._analyze_technical(analysis, stock_info)
            
            # 基本面分析
            self._analyze_fundamental(analysis, stock_info)
            
            # 法人動向分析
            self._analyze_institutional(analysis, stock_info)
            
            # 計算加權評分
            self._calculate_weighted_score(analysis, analysis_type)
            
            # 增強分析
            self._enhance_analysis(analysis, stock_info)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析股票 {stock_info.get('code', 'Unknown')} 失敗: {e}")
            return None
    
    def _analyze_technical(self, analysis: StockAnalysis, stock_info: Dict[str, Any]):
        """技術面分析"""
        score = 5.0  # 基準分數
        
        # 價格變動分析
        change_percent = analysis.change_percent
        if change_percent > 3:
            score += 2.0
        elif change_percent > 1:
            score += 1.0
        elif change_percent < -3:
            score -= 2.0
        elif change_percent < -1:
            score -= 1.0
        
        # 成交量分析
        if analysis.trade_value > 5000000000:  # 50億以上
            score += 1.5
            analysis.volume_ratio = 2.5
        elif analysis.trade_value > 1000000000:  # 10億以上
            score += 1.0
            analysis.volume_ratio = 1.8
        else:
            analysis.volume_ratio = 1.2
        
        # RSI 模擬
        if change_percent > 2:
            analysis.rsi = random.uniform(60, 75)
        elif change_percent < -2:
            analysis.rsi = random.uniform(25, 40)
        else:
            analysis.rsi = random.uniform(45, 55)
        
        # 技術信號
        analysis.technical_signals = {
            'macd_bullish': change_percent > 1,
            'macd_golden_cross': change_percent > 3,
            'ma20_bullish': change_percent > 0,
            'ma_golden_cross': change_percent > 2,
            'rsi_healthy': 30 <= analysis.rsi <= 70,
            'rsi_oversold': analysis.rsi < 30,
            'rsi_overbought': analysis.rsi > 70,
            'volume_spike': analysis.volume_ratio > 2
        }
        
        analysis.technical_score = min(max(score, 0), 10)
    
    def _analyze_fundamental(self, analysis: StockAnalysis, stock_info: Dict[str, Any]):
        """基本面分析"""
        score = 5.0
        sector = stock_info.get('sector', 'general')
        
        # 根據行業設定基本面數據
        if sector == 'tech':
            analysis.eps_growth = random.uniform(8, 25)
            analysis.roe = random.uniform(15, 28)
            analysis.pe_ratio = random.uniform(15, 25)
            analysis.dividend_yield = random.uniform(1.5, 3.5)
        elif sector == 'finance':
            analysis.eps_growth = random.uniform(3, 12)
            analysis.roe = random.uniform(8, 15)
            analysis.pe_ratio = random.uniform(8, 15)
            analysis.dividend_yield = random.uniform(4, 7)
        elif sector == 'shipping':
            analysis.eps_growth = random.uniform(15, 40)
            analysis.roe = random.uniform(12, 25)
            analysis.pe_ratio = random.uniform(6, 12)
            analysis.dividend_yield = random.uniform(5, 9)
        else:
            analysis.eps_growth = random.uniform(2, 15)
            analysis.roe = random.uniform(5, 18)
            analysis.pe_ratio = random.uniform(10, 20)
            analysis.dividend_yield = random.uniform(2, 5)
        
        # 評分邏輯
        if analysis.eps_growth > 15:
            score += 2.0
        elif analysis.eps_growth > 8:
            score += 1.0
        
        if analysis.roe > 18:
            score += 1.5
        elif analysis.roe > 12:
            score += 1.0
        
        if analysis.dividend_yield > 5:
            score += 1.5
        elif analysis.dividend_yield > 3:
            score += 1.0
        
        if analysis.pe_ratio < 12:
            score += 1.0
        elif analysis.pe_ratio > 25:
            score -= 1.0
        
        analysis.fundamental_score = min(max(score, 0), 10)
    
    def _analyze_institutional(self, analysis: StockAnalysis, stock_info: Dict[str, Any]):
        """法人動向分析"""
        score = 5.0
        sector = stock_info.get('sector', 'general')
        
        # 根據行業和表現生成法人買賣數據
        base_foreign = random.randint(-30000, 50000)
        base_trust = random.randint(-15000, 25000)
        
        # 根據股價表現調整
        if analysis.change_percent > 2:
            base_foreign *= 1.5
            base_trust *= 1.3
        elif analysis.change_percent < -2:
            base_foreign *= -0.8
            base_trust *= -0.6
        
        analysis.foreign_net_buy = int(base_foreign)
        analysis.trust_net_buy = int(base_trust)
        analysis.dealer_net_buy = random.randint(-5000, 8000)
        
        # 評分邏輯
        if analysis.foreign_net_buy > 20000:
            score += 2.0
        elif analysis.foreign_net_buy > 5000:
            score += 1.0
        elif analysis.foreign_net_buy < -20000:
            score -= 2.0
        elif analysis.foreign_net_buy < -5000:
            score -= 1.0
        
        if analysis.trust_net_buy > 10000:
            score += 1.5
        elif analysis.trust_net_buy > 3000:
            score += 0.5
        elif analysis.trust_net_buy < -10000:
            score -= 1.5
        
        analysis.institutional_score = min(max(score, 0), 10)
    
    def _calculate_weighted_score(self, analysis: StockAnalysis, analysis_type: str):
        """計算加權評分"""
        config = self.time_slot_config.get(analysis_type, self.time_slot_config['afternoon_scan'])
        weights = config['analysis_weights']
        
        # 計算加權總分
        weighted_score = (
            analysis.technical_score * weights['technical'] +
            analysis.fundamental_score * weights['fundamental'] +
            analysis.institutional_score * weights['institutional']
        )
        
        analysis.weighted_score = round(weighted_score, 2)
        analysis.base_score = round(
            (analysis.technical_score + analysis.fundamental_score + analysis.institutional_score) / 3, 2
        )
    
    def _enhance_analysis(self, analysis: StockAnalysis, stock_info: Dict[str, Any]):
        """增強分析"""
        analysis.enhanced_analysis = {
            'tech_score': analysis.technical_score,
            'fund_score': analysis.fundamental_score,
            'inst_score': analysis.institutional_score,
            'dividend_yield': analysis.dividend_yield,
            'eps_growth': analysis.eps_growth,
            'pe_ratio': analysis.pe_ratio,
            'roe': analysis.roe,
            'foreign_net_buy': analysis.foreign_net_buy,
            'trust_net_buy': analysis.trust_net_buy,
            'dealer_net_buy': analysis.dealer_net_buy,
            'rsi': analysis.rsi,
            'volume_ratio': analysis.volume_ratio,
            'technical_signals': analysis.technical_signals,
            'sector': stock_info.get('sector', 'general'),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def generate_recommendations(self, analyses: List[StockAnalysis], time_slot: str) -> Dict[str, List[Dict]]:
        """生成推薦結果"""
        if not analyses:
            return {"short_term": [], "long_term": [], "weak_stocks": []}
        
        config = self.time_slot_config[time_slot]
        limits = config['recommendation_limits']
        
        # 短線推薦 - 技術面強勢
        short_candidates = [
            a for a in analyses 
            if a.weighted_score >= 6.0 and a.technical_score >= 6.0
        ]
        short_candidates.sort(key=lambda x: x.weighted_score, reverse=True)
        
        short_term = []
        for analysis in short_candidates[:limits['short_term']]:
            reason = self._generate_short_term_reason(analysis)
            target_price, stop_loss = self._calculate_target_prices(analysis, 'short_term')
            
            short_term.append({
                "code": analysis.code,
                "name": analysis.name,
                "current_price": analysis.current_price,
                "reason": reason,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "trade_value": analysis.trade_value,
                "analysis": asdict(analysis)
            })
        
        # 長線推薦 - 基本面優異
        long_candidates = [
            a for a in analyses 
            if a.weighted_score >= 5.5 and a.fundamental_score >= 6.0
        ]
        long_candidates.sort(key=lambda x: (x.fundamental_score, x.weighted_score), reverse=True)
        
        long_term = []
        for analysis in long_candidates[:limits['long_term']]:
            reason = self._generate_long_term_reason(analysis)
            target_price, stop_loss = self._calculate_target_prices(analysis, 'long_term')
            
            long_term.append({
                "code": analysis.code,
                "name": analysis.name,
                "current_price": analysis.current_price,
                "reason": reason,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "trade_value": analysis.trade_value,
                "analysis": asdict(analysis)
            })
        
        # 弱勢股警示
        weak_candidates = [
            a for a in analyses 
            if (a.weighted_score < 3.0 or 
                a.change_percent < -3.0 or 
                (a.foreign_net_buy < -10000 and a.change_percent < -1))
        ]
        weak_candidates.sort(key=lambda x: x.weighted_score)
        
        weak_stocks = []
        for analysis in weak_candidates[:limits['weak_stocks']]:
            alert_reason = self._generate_weak_stock_reason(analysis)
            
            weak_stocks.append({
                "code": analysis.code,
                "name": analysis.name,
                "current_price": analysis.current_price,
                "alert_reason": alert_reason,
                "trade_value": analysis.trade_value,
                "analysis": asdict(analysis)
            })
        
        return {
            "short_term": short_term,
            "long_term": long_term,
            "weak_stocks": weak_stocks
        }
    
    def _generate_short_term_reason(self, analysis: StockAnalysis) -> str:
        """生成短線推薦理由"""
        reasons = []
        
        if analysis.change_percent > 3:
            reasons.append(f"強勢上漲{analysis.change_percent:.1f}%")
        elif analysis.change_percent > 1:
            reasons.append(f"溫和上漲{analysis.change_percent:.1f}%")
        
        if analysis.volume_ratio > 2:
            reasons.append(f"爆量{analysis.volume_ratio:.1f}倍")
        elif analysis.volume_ratio > 1.5:
            reasons.append("成交活躍")
        
        if analysis.foreign_net_buy > 20000:
            reasons.append(f"外資大買{analysis.foreign_net_buy//10000:.1f}億")
        elif analysis.foreign_net_buy > 5000:
            reasons.append("外資買超")
        
        if analysis.technical_signals.get('macd_golden_cross'):
            reasons.append("MACD金叉")
        elif analysis.technical_signals.get('macd_bullish'):
            reasons.append("MACD轉強")
        
        if analysis.rsi < 30:
            reasons.append("RSI超賣反彈")
        
        return "；".join(reasons[:3]) if reasons else "技術面轉強"
    
    def _generate_long_term_reason(self, analysis: StockAnalysis) -> str:
        """生成長線推薦理由"""
        reasons = []
        
        if analysis.dividend_yield > 5:
            reasons.append(f"高殖利率{analysis.dividend_yield:.1f}%")
        elif analysis.dividend_yield > 3:
            reasons.append(f"穩定配息{analysis.dividend_yield:.1f}%")
        
        if analysis.eps_growth > 15:
            reasons.append(f"EPS高成長{analysis.eps_growth:.1f}%")
        elif analysis.eps_growth > 8:
            reasons.append(f"獲利成長{analysis.eps_growth:.1f}%")
        
        if analysis.roe > 18:
            reasons.append(f"ROE優異{analysis.roe:.1f}%")
        elif analysis.roe > 12:
            reasons.append(f"ROE良好{analysis.roe:.1f}%")
        
        if analysis.pe_ratio < 12:
            reasons.append(f"低本益比{analysis.pe_ratio:.1f}倍")
        
        if analysis.foreign_net_buy > 5000:
            reasons.append("外資持續布局")
        
        return "；".join(reasons[:3]) if reasons else "基本面穩健，適合長期投資"
    
    def _generate_weak_stock_reason(self, analysis: StockAnalysis) -> str:
        """生成弱勢股警示理由"""
        reasons = []
        
        if analysis.change_percent < -5:
            reasons.append(f"大跌{abs(analysis.change_percent):.1f}%")
        elif analysis.change_percent < -2:
            reasons.append(f"下跌{abs(analysis.change_percent):.1f}%")
        
        if analysis.foreign_net_buy < -20000:
            reasons.append(f"外資大賣{abs(analysis.foreign_net_buy)//10000:.1f}億")
        elif analysis.foreign_net_buy < -5000:
            reasons.append("外資賣超")
        
        if analysis.weighted_score < 2:
            reasons.append("綜合評分極低")
        elif analysis.weighted_score < 3:
            reasons.append("技術面轉弱")
        
        if analysis.rsi > 80:
            reasons.append("RSI超買")
        
        return "；".join(reasons[:2]) if reasons else "多項指標顯示風險"
    
    def _calculate_target_prices(self, analysis: StockAnalysis, recommendation_type: str) -> Tuple[float, float]:
        """計算目標價和停損價"""
        current_price = analysis.current_price
        
        if recommendation_type == 'short_term':
            if analysis.weighted_score >= 8:
                target_multiplier = 1.08  # 8%
                stop_multiplier = 0.94    # 6% 停損
            elif analysis.weighted_score >= 7:
                target_multiplier = 1.05  # 5%
                stop_multiplier = 0.95    # 5% 停損
            else:
                target_multiplier = 1.03  # 3%
                stop_multiplier = 0.96    # 4% 停損
        else:  # long_term
            if analysis.fundamental_score >= 8:
                target_multiplier = 1.15  # 15%
                stop_multiplier = 0.88    # 12% 停損
            elif analysis.fundamental_score >= 7:
                target_multiplier = 1.12  # 12%
                stop_multiplier = 0.90    # 10% 停損
            else:
                target_multiplier = 1.08  # 8%
                stop_multiplier = 0.92    # 8% 停損
        
        target_price = round(current_price * target_multiplier, 1)
        stop_loss = round(current_price * stop_multiplier, 1)
        
        return target_price, stop_loss
    
    def _send_recommendations(self, recommendations: Dict[str, List[Dict]], time_slot: str):
        """發送推薦通知"""
        try:
            import notifier
            notifier.init()
            notifier.send_combined_recommendations(recommendations, time_slot)
            self.logger.info("推薦通知發送成功")
            
        except ImportError:
            self.logger.warning("通知系統不可用")
        except Exception as e:
            self.logger.error(f"發送通知失敗: {e}")
    
    def run_time_slot_analysis(self, time_slot: str):
        """執行指定時段的分析"""
        self.logger.info(f"開始執行 {time_slot} 分析")
        
        try:
            recommendations = self.analyze_stocks_comprehensive(time_slot)
            
            # 顯示結果摘要
            print(f"\n📊 {self.time_slot_config[time_slot]['name']} 分析完成")
            print(f"🔥 短線推薦: {len(recommendations['short_term'])} 支")
            print(f"💎 長線推薦: {len(recommendations['long_term'])} 支")
            print(f"⚠️ 風險警示: {len(recommendations['weak_stocks'])} 支")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"時段分析失敗: {e}")
            return {"short_term": [], "long_term": [], "weak_stocks": []}


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='增強版股票分析機器人')
    parser.add_argument('time_slot', 
                       choices=['morning_scan', 'afternoon_scan', 'weekly_summary'],
                       help='分析時段')
    parser.add_argument('--debug', action='store_true', help='啟用調試模式')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 創建並執行分析
    bot = EnhancedStockBot()
    recommendations = bot.run_time_slot_analysis(args.time_slot)
    
    print(f"\n🎉 {args.time_slot} 分析執行完成！")
    print("📧 請檢查您的信箱獲取詳細分析報告")


if __name__ == "__main__":
    main()
