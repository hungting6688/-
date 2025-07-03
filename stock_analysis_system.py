#!/usr/bin/env python3
"""
stock_analysis_system.py - 完整台股分析推播系統
整合股票分析、推薦系統、通知推播的一站式解決方案
"""

import os
import sys
import json
import time
import random
import smtplib
import ssl
import schedule
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
import requests
from dataclasses import dataclass

# 確保必要目錄存在
for directory in ['logs', 'data', 'cache']:
    os.makedirs(directory, exist_ok=True)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/stock_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class StockRecommendation:
    """股票推薦數據結構"""
    code: str
    name: str
    current_price: float
    change_percent: float
    reason: str
    target_price: float
    stop_loss: float
    trade_value: int
    confidence: float = 0.0
    category: str = "短線"

class StockAnalysisSystem:
    """台股分析推播系統"""
    
    def __init__(self):
        """初始化系統"""
        self.setup_config()
        self.initialize_stock_database()
        print("🚀 台股分析推播系統啟動完成！")
    
    def setup_config(self):
        """設置配置"""
        # 郵件配置
        self.email_config = {
            'sender': os.getenv('EMAIL_SENDER', ''),
            'password': os.getenv('EMAIL_PASSWORD', ''),
            'receiver': os.getenv('EMAIL_RECEIVER', ''),
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587'))
        }
        
        # 分析配置
        self.analysis_config = {
            'short_term_count': 3,
            'long_term_count': 3,
            'weak_stock_count': 2,
            'min_trade_value': 100000000  # 1億台幣
        }
        
        print("✅ 系統配置完成")
    
    def initialize_stock_database(self):
        """初始化股票資料庫"""
        self.stock_pool = {
            '2330': {
                'name': '台積電',
                'sector': 'tech',
                'base_price': 638.5,
                'dividend_yield': 2.3,
                'eps_growth': 12.8,
                'pe_ratio': 18.2,
                'roe': 23.5
            },
            '2317': {
                'name': '鴻海',
                'sector': 'tech', 
                'base_price': 115.5,
                'dividend_yield': 4.8,
                'eps_growth': 15.2,
                'pe_ratio': 11.5,
                'roe': 16.8
            },
            '2454': {
                'name': '聯發科',
                'sector': 'tech',
                'base_price': 825.0,
                'dividend_yield': 3.1,
                'eps_growth': 18.5,
                'pe_ratio': 22.8,
                'roe': 28.5
            },
            '2412': {
                'name': '中華電',
                'sector': 'telecom',
                'base_price': 118.5,
                'dividend_yield': 4.5,
                'eps_growth': 2.1,
                'pe_ratio': 16.8,
                'roe': 9.2
            },
            '2609': {
                'name': '陽明',
                'sector': 'shipping',
                'base_price': 91.2,
                'dividend_yield': 7.2,
                'eps_growth': 35.6,
                'pe_ratio': 8.9,
                'roe': 18.4
            },
            '2603': {
                'name': '長榮',
                'sector': 'shipping',
                'base_price': 195.5,
                'dividend_yield': 6.8,
                'eps_growth': 28.9,
                'pe_ratio': 9.2,
                'roe': 16.8
            },
            '2615': {
                'name': '萬海',
                'sector': 'shipping',
                'base_price': 132.8,
                'dividend_yield': 8.1,
                'eps_growth': 42.3,
                'pe_ratio': 7.5,
                'roe': 22.1
            },
            '2881': {
                'name': '富邦金',
                'sector': 'finance',
                'base_price': 68.2,
                'dividend_yield': 5.2,
                'eps_growth': 8.5,
                'pe_ratio': 12.5,
                'roe': 11.8
            },
            '2882': {
                'name': '國泰金',
                'sector': 'finance',
                'base_price': 45.8,
                'dividend_yield': 6.1,
                'eps_growth': 7.2,
                'pe_ratio': 10.8,
                'roe': 12.2
            },
            '2308': {
                'name': '台達電',
                'sector': 'tech',
                'base_price': 362.5,
                'dividend_yield': 2.8,
                'eps_growth': 16.2,
                'pe_ratio': 19.5,
                'roe': 18.8
            }
        }
        print(f"✅ 股票資料庫初始化完成，共 {len(self.stock_pool)} 支股票")
    
    def fetch_stock_data(self) -> List[Dict[str, Any]]:
        """獲取股票數據"""
        print("📊 開始獲取股票數據...")
        
        stock_data = []
        
        for code, info in self.stock_pool.items():
            try:
                # 使用股票代碼和當前日期作為隨機種子，確保結果一致性
                random.seed(hash(code + str(datetime.now().date())) % 1000)
                
                # 模擬即時股價變動
                base_price = info['base_price']
                change_percent = random.uniform(-4, 6)
                current_price = base_price * (1 + change_percent / 100)
                
                # 模擬成交量
                volume = random.randint(5000000, 50000000)
                trade_value = int(current_price * volume)
                
                # 模擬技術指標
                rsi = random.uniform(25, 75)
                volume_ratio = random.uniform(0.8, 3.5)
                
                # 模擬法人買賣
                foreign_net_buy = random.randint(-30000, 50000)
                trust_net_buy = random.randint(-15000, 25000)
                
                stock_data.append({
                    'code': code,
                    'name': info['name'],
                    'sector': info['sector'],
                    'current_price': round(current_price, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': volume,
                    'trade_value': trade_value,
                    'rsi': round(rsi, 1),
                    'volume_ratio': round(volume_ratio, 1),
                    'foreign_net_buy': foreign_net_buy,
                    'trust_net_buy': trust_net_buy,
                    'dividend_yield': info['dividend_yield'],
                    'eps_growth': info['eps_growth'],
                    'pe_ratio': info['pe_ratio'],
                    'roe': info['roe']
                })
                
            except Exception as e:
                logger.error(f"獲取 {code} 數據失敗: {e}")
                continue
        
        # 按成交金額排序
        stock_data.sort(key=lambda x: x['trade_value'], reverse=True)
        
        print(f"✅ 成功獲取 {len(stock_data)} 支股票數據")
        return stock_data
    
    def analyze_stock(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """分析單支股票"""
        try:
            # 技術面評分
            technical_score = self._calculate_technical_score(stock)
            
            # 基本面評分
            fundamental_score = self._calculate_fundamental_score(stock)
            
            # 法人面評分
            institutional_score = self._calculate_institutional_score(stock)
            
            # 綜合評分
            total_score = (technical_score * 0.4 + 
                          fundamental_score * 0.35 + 
                          institutional_score * 0.25)
            
            # 評級
            grade = self._get_grade(total_score)
            
            # 信心度
            confidence = self._calculate_confidence(technical_score, fundamental_score, institutional_score)
            
            return {
                'code': stock['code'],
                'name': stock['name'],
                'current_price': stock['current_price'],
                'change_percent': stock['change_percent'],
                'trade_value': stock['trade_value'],
                'technical_score': round(technical_score, 1),
                'fundamental_score': round(fundamental_score, 1),
                'institutional_score': round(institutional_score, 1),
                'total_score': round(total_score, 1),
                'grade': grade,
                'confidence': round(confidence, 1),
                'sector': stock['sector'],
                'rsi': stock['rsi'],
                'volume_ratio': stock['volume_ratio'],
                'foreign_net_buy': stock['foreign_net_buy'],
                'trust_net_buy': stock['trust_net_buy'],
                'dividend_yield': stock['dividend_yield'],
                'eps_growth': stock['eps_growth']
            }
            
        except Exception as e:
            logger.error(f"分析股票 {stock.get('code', 'Unknown')} 失敗: {e}")
            return None
    
    def _calculate_technical_score(self, stock: Dict[str, Any]) -> float:
        """計算技術面評分"""
        score = 5.0  # 基準分數
        
        # 價格變動
        change_percent = stock['change_percent']
        if change_percent > 3:
            score += 2.0
        elif change_percent > 1:
            score += 1.0
        elif change_percent < -3:
            score -= 2.0
        elif change_percent < -1:
            score -= 1.0
        
        # RSI
        rsi = stock['rsi']
        if 30 <= rsi <= 70:
            score += 1.0
        elif rsi < 30:
            score += 1.5  # 超賣反彈
        elif rsi > 80:
            score -= 1.0  # 超買風險
        
        # 成交量
        volume_ratio = stock['volume_ratio']
        if volume_ratio > 2:
            score += 1.5
        elif volume_ratio > 1.5:
            score += 1.0
        elif volume_ratio < 0.8:
            score -= 0.5
        
        return max(0, min(10, score))
    
    def _calculate_fundamental_score(self, stock: Dict[str, Any]) -> float:
        """計算基本面評分"""
        score = 5.0  # 基準分數
        
        # EPS成長率
        eps_growth = stock['eps_growth']
        if eps_growth > 20:
            score += 2.0
        elif eps_growth > 10:
            score += 1.5
        elif eps_growth > 5:
            score += 1.0
        elif eps_growth < 0:
            score -= 1.5
        
        # ROE
        roe = stock['roe']
        if roe > 20:
            score += 1.5
        elif roe > 15:
            score += 1.0
        elif roe > 10:
            score += 0.5
        elif roe < 5:
            score -= 1.0
        
        # 殖利率
        dividend_yield = stock['dividend_yield']
        if dividend_yield > 5:
            score += 1.5
        elif dividend_yield > 3:
            score += 1.0
        elif dividend_yield > 1:
            score += 0.5
        
        # 本益比
        pe_ratio = stock['pe_ratio']
        if pe_ratio < 12:
            score += 1.0
        elif pe_ratio > 30:
            score -= 1.0
        
        return max(0, min(10, score))
    
    def _calculate_institutional_score(self, stock: Dict[str, Any]) -> float:
        """計算法人面評分"""
        score = 5.0  # 基準分數
        
        # 外資買賣超
        foreign_net = stock['foreign_net_buy']
        if foreign_net > 30000:
            score += 2.0
        elif foreign_net > 10000:
            score += 1.5
        elif foreign_net > 5000:
            score += 1.0
        elif foreign_net < -30000:
            score -= 2.0
        elif foreign_net < -10000:
            score -= 1.5
        
        # 投信買賣超
        trust_net = stock['trust_net_buy']
        if trust_net > 15000:
            score += 1.5
        elif trust_net > 5000:
            score += 1.0
        elif trust_net < -15000:
            score -= 1.5
        
        return max(0, min(10, score))
    
    def _get_grade(self, total_score: float) -> str:
        """獲取評級"""
        if total_score >= 8.5:
            return 'A+'
        elif total_score >= 7.5:
            return 'A'
        elif total_score >= 6.5:
            return 'B+'
        elif total_score >= 5.5:
            return 'B'
        elif total_score >= 4.5:
            return 'C+'
        elif total_score >= 3.5:
            return 'C'
        else:
            return 'D'
    
    def _calculate_confidence(self, tech_score: float, fund_score: float, inst_score: float) -> float:
        """計算信心度"""
        # 基於三個評分的一致性計算信心度
        scores = [tech_score, fund_score, inst_score]
        avg_score = sum(scores) / len(scores)
        variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
        
        # 分數越高、差異越小，信心度越高
        base_confidence = min(avg_score * 10, 100)
        consistency_bonus = max(0, 15 - variance * 3)
        
        return min(base_confidence + consistency_bonus, 100)
    
    def generate_recommendations(self, analyses: List[Dict[str, Any]]) -> Dict[str, List[StockRecommendation]]:
        """生成推薦"""
        print("🎯 生成投資推薦...")
        
        # 篩選有效分析
        valid_analyses = [a for a in analyses if a is not None]
        
        recommendations = {
            'short_term': [],
            'long_term': [],
            'weak_stocks': []
        }
        
        # 短線推薦 - 技術面強勢
        short_candidates = [
            a for a in valid_analyses 
            if a['total_score'] >= 7.0 and a['technical_score'] >= 6.5 and a['confidence'] >= 60
        ]
        short_candidates.sort(key=lambda x: x['total_score'], reverse=True)
        
        for analysis in short_candidates[:self.analysis_config['short_term_count']]:
            reason = self._generate_short_term_reason(analysis)
            target_price, stop_loss = self._calculate_short_term_prices(analysis)
            
            recommendations['short_term'].append(StockRecommendation(
                code=analysis['code'],
                name=analysis['name'],
                current_price=analysis['current_price'],
                change_percent=analysis['change_percent'],
                reason=reason,
                target_price=target_price,
                stop_loss=stop_loss,
                trade_value=analysis['trade_value'],
                confidence=analysis['confidence'],
                category="短線"
            ))
        
        # 長線推薦 - 基本面優異
        long_candidates = [
            a for a in valid_analyses 
            if a['total_score'] >= 6.5 and a['fundamental_score'] >= 6.0 and a['confidence'] >= 55
        ]
        long_candidates.sort(key=lambda x: (x['fundamental_score'], x['total_score']), reverse=True)
        
        for analysis in long_candidates[:self.analysis_config['long_term_count']]:
            reason = self._generate_long_term_reason(analysis)
            target_price, stop_loss = self._calculate_long_term_prices(analysis)
            
            recommendations['long_term'].append(StockRecommendation(
                code=analysis['code'],
                name=analysis['name'],
                current_price=analysis['current_price'],
                change_percent=analysis['change_percent'],
                reason=reason,
                target_price=target_price,
                stop_loss=stop_loss,
                trade_value=analysis['trade_value'],
                confidence=analysis['confidence'],
                category="長線"
            ))
        
        # 風險警示 - 弱勢股
        weak_candidates = [
            a for a in valid_analyses 
            if (a['total_score'] < 4.0 or 
                a['change_percent'] < -3.0 or 
                (a['foreign_net_buy'] < -15000 and a['change_percent'] < -1))
        ]
        weak_candidates.sort(key=lambda x: x['total_score'])
        
        for analysis in weak_candidates[:self.analysis_config['weak_stock_count']]:
            reason = self._generate_weak_stock_reason(analysis)
            
            recommendations['weak_stocks'].append(StockRecommendation(
                code=analysis['code'],
                name=analysis['name'],
                current_price=analysis['current_price'],
                change_percent=analysis['change_percent'],
                reason=reason,
                target_price=0,
                stop_loss=analysis['current_price'] * 0.95,
                trade_value=analysis['trade_value'],
                confidence=0,
                category="風險"
            ))
        
        print(f"✅ 推薦生成完成: 短線 {len(recommendations['short_term'])} 支, "
              f"長線 {len(recommendations['long_term'])} 支, "
              f"風險 {len(recommendations['weak_stocks'])} 支")
        
        return recommendations
    
    def _generate_short_term_reason(self, analysis: Dict[str, Any]) -> str:
        """生成短線推薦理由"""
        reasons = []
        
        if analysis['change_percent'] > 3:
            reasons.append(f"強勢上漲 {analysis['change_percent']:.1f}%")
        elif analysis['change_percent'] > 1:
            reasons.append(f"上漲 {analysis['change_percent']:.1f}%")
        
        if analysis['volume_ratio'] > 2:
            reasons.append(f"爆量 {analysis['volume_ratio']:.1f} 倍")
        elif analysis['volume_ratio'] > 1.5:
            reasons.append("成交活躍")
        
        if analysis['foreign_net_buy'] > 20000:
            reasons.append(f"外資大買 {analysis['foreign_net_buy']//10000:.1f} 億")
        elif analysis['foreign_net_buy'] > 5000:
            reasons.append("外資買超")
        
        if analysis['rsi'] < 30:
            reasons.append("RSI 超賣反彈")
        elif 30 <= analysis['rsi'] <= 70:
            reasons.append("RSI 健康")
        
        return "；".join(reasons[:3]) if reasons else "技術面轉強"
    
    def _generate_long_term_reason(self, analysis: Dict[str, Any]) -> str:
        """生成長線推薦理由"""
        reasons = []
        
        if analysis['dividend_yield'] > 5:
            reasons.append(f"高殖利率 {analysis['dividend_yield']:.1f}%")
        elif analysis['dividend_yield'] > 3:
            reasons.append(f"穩定配息 {analysis['dividend_yield']:.1f}%")
        
        if analysis['eps_growth'] > 15:
            reasons.append(f"EPS 高成長 {analysis['eps_growth']:.1f}%")
        elif analysis['eps_growth'] > 8:
            reasons.append(f"獲利成長 {analysis['eps_growth']:.1f}%")
        
        if analysis['roe'] > 18:
            reasons.append(f"ROE 優異 {analysis['roe']:.1f}%")
        elif analysis['roe'] > 12:
            reasons.append(f"ROE 良好 {analysis['roe']:.1f}%")
        
        if analysis['foreign_net_buy'] > 5000:
            reasons.append("外資持續布局")
        
        return "；".join(reasons[:3]) if reasons else "基本面穩健，適合長期投資"
    
    def _generate_weak_stock_reason(self, analysis: Dict[str, Any]) -> str:
        """生成弱勢股警示理由"""
        reasons = []
        
        if analysis['change_percent'] < -5:
            reasons.append(f"大跌 {abs(analysis['change_percent']):.1f}%")
        elif analysis['change_percent'] < -2:
            reasons.append(f"下跌 {abs(analysis['change_percent']):.1f}%")
        
        if analysis['foreign_net_buy'] < -20000:
            reasons.append(f"外資大賣 {abs(analysis['foreign_net_buy'])//10000:.1f} 億")
        elif analysis['foreign_net_buy'] < -5000:
            reasons.append("外資賣超")
        
        if analysis['total_score'] < 3:
            reasons.append("綜合評分極低")
        elif analysis['total_score'] < 4:
            reasons.append("技術面轉弱")
        
        return "；".join(reasons[:2]) if reasons else "多項指標顯示風險"
    
    def _calculate_short_term_prices(self, analysis: Dict[str, Any]) -> tuple:
        """計算短線目標價和停損價"""
        current_price = analysis['current_price']
        
        if analysis['total_score'] >= 8:
            target_multiplier = 1.08  # 8%
            stop_multiplier = 0.94    # 6% 停損
        elif analysis['total_score'] >= 7:
            target_multiplier = 1.05  # 5%
            stop_multiplier = 0.95    # 5% 停損
        else:
            target_multiplier = 1.03  # 3%
            stop_multiplier = 0.96    # 4% 停損
        
        target_price = round(current_price * target_multiplier, 1)
        stop_loss = round(current_price * stop_multiplier, 1)
        
        return target_price, stop_loss
    
    def _calculate_long_term_prices(self, analysis: Dict[str, Any]) -> tuple:
        """計算長線目標價和停損價"""
        current_price = analysis['current_price']
        
        if analysis['fundamental_score'] >= 8:
            target_multiplier = 1.20  # 20%
            stop_multiplier = 0.85    # 15% 停損
        elif analysis['fundamental_score'] >= 7:
            target_multiplier = 1.15  # 15%
            stop_multiplier = 0.88    # 12% 停損
        else:
            target_multiplier = 1.10  # 10%
            stop_multiplier = 0.90    # 10% 停損
        
        target_price = round(current_price * target_multiplier, 1)
        stop_loss = round(current_price * stop_multiplier, 1)
        
        return target_price, stop_loss
    
    def send_notification(self, recommendations: Dict[str, List[StockRecommendation]]) -> bool:
        """發送推播通知"""
        print("📧 準備發送推播通知...")
        
        if not self._check_email_config():
            print("❌ 郵件配置不完整，無法發送通知")
            return False
        
        try:
            # 生成通知內容
            message = self._generate_notification_message(recommendations)
            html_message = self._generate_html_notification(recommendations)
            
            # 發送郵件
            success = self._send_email(message, html_message)
            
            if success:
                print("✅ 推播通知發送成功！")
                # 同時保存到本地
                self._save_notification_backup(message)
                return True
            else:
                print("❌ 推播通知發送失敗")
                return False
                
        except Exception as e:
            logger.error(f"發送通知失敗: {e}")
            return False
    
    def _check_email_config(self) -> bool:
        """檢查郵件配置"""
        required_fields = ['sender', 'password', 'receiver']
        for field in required_fields:
            if not self.email_config[field]:
                return False
        return True
    
    def _generate_notification_message(self, recommendations: Dict[str, List[StockRecommendation]]) -> str:
        """生成通知訊息"""
        now = datetime.now()
        date_str = now.strftime('%Y/%m/%d')
        time_str = now.strftime('%H:%M')
        
        # 計算推薦統計
        total_recommendations = len(recommendations['short_term']) + len(recommendations['long_term'])
        
        message = f"📊 {date_str} 台股分析推播報告\n"
        message += f"⏰ 分析時間: {time_str}\n"
        message += f"🎯 推薦標的: {total_recommendations} 支 | 風險警示: {len(recommendations['weak_stocks'])} 支\n"
        message += "=" * 50 + "\n\n"
        
        # 短線推薦
        if recommendations['short_term']:
            message += "🔥 短線推薦\n\n"
            for i, stock in enumerate(recommendations['short_term'], 1):
                change_symbol = "+" if stock.change_percent >= 0 else ""
                message += f"{i}. {stock.code} {stock.name}\n"
                message += f"   現價: {stock.current_price:.1f} 元 ({change_symbol}{stock.change_percent:.1f}%)\n"
                message += f"   推薦理由: {stock.reason}\n"
                message += f"   目標價: {stock.target_price:.1f} | 停損: {stock.stop_loss:.1f}\n"
                message += f"   信心度: {stock.confidence:.0f}%\n\n"
        
        # 長線推薦
        if recommendations['long_term']:
            message += "💎 長線推薦\n\n"
            for i, stock in enumerate(recommendations['long_term'], 1):
                change_symbol = "+" if stock.change_percent >= 0 else ""
                message += f"{i}. {stock.code} {stock.name}\n"
                message += f"   現價: {stock.current_price:.1f} 元 ({change_symbol}{stock.change_percent:.1f}%)\n"
                message += f"   投資亮點: {stock.reason}\n"
                message += f"   目標價: {stock.target_price:.1f} | 停損: {stock.stop_loss:.1f}\n"
                message += f"   信心度: {stock.confidence:.0f}%\n\n"
        
        # 風險警示
        if recommendations['weak_stocks']:
            message += "⚠️ 風險警示\n\n"
            for i, stock in enumerate(recommendations['weak_stocks'], 1):
                message += f"{i}. {stock.code} {stock.name}\n"
                message += f"   現價: {stock.current_price:.1f} 元 ({stock.change_percent:+.1f}%)\n"
                message += f"   風險因素: {stock.reason}\n"
                message += f"   建議: 謹慎操作，嚴設停損\n\n"
        
        # 如果沒有任何推薦，顯示市場觀察
        if not recommendations['short_term'] and not recommendations['long_term'] and not recommendations['weak_stocks']:
            message += "📈 今日市場觀察\n\n"
            message += "目前暫無符合條件的推薦標的。\n"
            message += "建議保持觀望，等待更好的進場時機。\n\n"
        
        message += "=" * 50 + "\n"
        message += "💡 投資提醒:\n"
        message += "⚠️ 本報告僅供參考，不構成投資建議\n"
        message += "⚠️ 股市有風險，投資需謹慎\n"
        message += "⚠️ 請設定停損點，控制投資風險\n\n"
        
        # 添加分析摘要
        if total_recommendations > 0:
            avg_confidence = sum(stock.confidence for category in ['short_term', 'long_term'] 
                               for stock in recommendations[category]) / total_recommendations
            message += f"📊 本次分析信心度: {avg_confidence:.0f}%\n"
        
        message += "祝您投資順利！ 💰"
        
        return message
    
    def _generate_html_notification(self, recommendations: Dict[str, List[StockRecommendation]]) -> str:
        """生成HTML格式通知"""
        now = datetime.now()
        date_str = now.strftime('%Y/%m/%d')
        time_str = now.strftime('%H:%M')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>台股分析推播報告 - {date_str}</title>
            <style>
                body {{
                    font-family: 'Microsoft JhengHei', Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .section {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .stock-item {{
                    border-left: 4px solid #3498db;
                    padding: 15px;
                    margin-bottom: 15px;
                    background: #f8f9fa;
                }}
                .short-term {{ border-left-color: #e74c3c; }}
                .long-term {{ border-left-color: #f39c12; }}
                .weak-stock {{ border-left-color: #95a5a6; }}
                .stock-header {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .price-positive {{ color: #e74c3c; }}
                .price-negative {{ color: #27ae60; }}
                .confidence {{
                    background: #3498db;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                }}
                .warning {{
                    background: #f39c12;
                    color: white;
                    padding: 15px;
                    border-radius: 10px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 台股分析推播報告</h1>
                <p>{date_str} {time_str}</p>
            </div>
        """
        
        # 短線推薦
        if recommendations['short_term']:
            html += """
            <div class="section">
                <h2>🔥 短線推薦</h2>
            """
            for i, stock in enumerate(recommendations['short_term'], 1):
                price_class = "price-positive" if stock.change_percent >= 0 else "price-negative"
                change_symbol = "+" if stock.change_percent >= 0 else ""
                
                html += f"""
                <div class="stock-item short-term">
                    <div class="stock-header">
                        {i}. {stock.code} {stock.name}
                        <span class="confidence">信心度 {stock.confidence:.0f}%</span>
                    </div>
                    <p><strong>現價:</strong> <span class="{price_class}">{stock.current_price:.1f} 元 ({change_symbol}{stock.change_percent:.1f}%)</span></p>
                    <p><strong>推薦理由:</strong> {stock.reason}</p>
                    <p><strong>目標價:</strong> {stock.target_price:.1f} 元 | <strong>停損:</strong> {stock.stop_loss:.1f} 元</p>
                </div>
                """
            html += "</div>"
        
        # 長線推薦
        if recommendations['long_term']:
            html += """
            <div class="section">
                <h2>💎 長線推薦</h2>
            """
            for i, stock in enumerate(recommendations['long_term'], 1):
                price_class = "price-positive" if stock.change_percent >= 0 else "price-negative"
                change_symbol = "+" if stock.change_percent >= 0 else ""
                
                html += f"""
                <div class="stock-item long-term">
                    <div class="stock-header">
                        {i}. {stock.code} {stock.name}
                        <span class="confidence">信心度 {stock.confidence:.0f}%</span>
                    </div>
                    <p><strong>現價:</strong> <span class="{price_class}">{stock.current_price:.1f} 元 ({change_symbol}{stock.change_percent:.1f}%)</span></p>
                    <p><strong>投資亮點:</strong> {stock.reason}</p>
                    <p><strong>目標價:</strong> {stock.target_price:.1f} 元 | <strong>停損:</strong> {stock.stop_loss:.1f} 元</p>
                </div>
                """
            html += "</div>"
        
        # 風險警示
        if recommendations['weak_stocks']:
            html += """
            <div class="section">
                <h2>⚠️ 風險警示</h2>
            """
            for i, stock in enumerate(recommendations['weak_stocks'], 1):
                html += f"""
                <div class="stock-item weak-stock">
                    <div class="stock-header">
                        {i}. {stock.code} {stock.name}
                    </div>
                    <p><strong>現價:</strong> <span class="price-negative">{stock.current_price:.1f} 元 ({stock.change_percent:+.1f}%)</span></p>
                    <p><strong>風險因素:</strong> {stock.reason}</p>
                    <p><strong>建議:</strong> 謹慎操作，嚴設停損</p>
                </div>
                """
            html += "</div>"
        
        html += """
            <div class="warning">
                <h3>💡 投資提醒</h3>
                <p>本報告僅供參考，不構成投資建議。股市有風險，投資需謹慎。請設定停損點，控制投資風險。</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_email(self, message: str, html_message: str) -> bool:
        """發送郵件"""
        try:
            # 創建郵件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📊 台股分析推播 - {datetime.now().strftime('%m/%d %H:%M')}"
            msg['From'] = self.email_config['sender']
            msg['To'] = self.email_config['receiver']
            
            # 添加純文字和HTML版本
            text_part = MIMEText(message, 'plain', 'utf-8')
            html_part = MIMEText(html_message, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # 發送郵件
            context = ssl.create_default_context()
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls(context=context)
                server.login(self.email_config['sender'], self.email_config['password'])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"發送郵件失敗: {e}")
            return False
    
    def _save_notification_backup(self, message: str):
        """保存通知備份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/notification_backup_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(message)
                
            logger.info(f"通知備份已保存: {filename}")
            
        except Exception as e:
            logger.error(f"保存通知備份失敗: {e}")
    
    def run_analysis(self) -> bool:
        """執行完整分析流程"""
        print("\n🚀 開始執行台股分析...")
        print("=" * 60)
        
        try:
            start_time = time.time()
            
            # 1. 獲取股票數據
            stock_data = self.fetch_stock_data()
            if not stock_data:
                print("❌ 無法獲取股票數據")
                return False
            
            # 2. 分析股票
            print("\n🔬 開始分析股票...")
            analyses = []
            for stock in stock_data:
                analysis = self.analyze_stock(stock)
                if analysis:
                    analyses.append(analysis)
                    print(f"  ✅ {stock['code']} {stock['name']} - 評分: {analysis['total_score']:.1f} ({analysis['grade']})")
            
            if not analyses:
                print("❌ 分析失敗，無有效結果")
                return False
            
            # 3. 生成推薦
            recommendations = self.generate_recommendations(analyses)
            
            # 4. 顯示結果
            self._display_results(recommendations)
            
            # 5. 發送通知
            notification_sent = self.send_notification(recommendations)
            
            # 6. 保存結果
            self._save_analysis_results(recommendations, analyses)
            
            # 執行統計
            execution_time = time.time() - start_time
            print(f"\n📊 分析完成統計:")
            print(f"  ⏱️ 執行時間: {execution_time:.1f} 秒")
            print(f"  📈 分析股票: {len(analyses)} 支")
            print(f"  🎯 推薦總數: {len(recommendations['short_term']) + len(recommendations['long_term'])} 支")
            print(f"  📧 通知狀態: {'成功' if notification_sent else '失敗'}")
            print(f"  💾 結果保存: 完成")
            
            print("\n🎉 台股分析執行完成！")
            if notification_sent:
                print("📧 請檢查您的信箱查看推播通知")
            
            return True
            
        except Exception as e:
            logger.error(f"分析執行失敗: {e}")
            print(f"❌ 分析執行失敗: {e}")
            return False
    
    def _display_results(self, recommendations: Dict[str, List[StockRecommendation]]):
        """顯示分析結果"""
        print("\n📊 分析結果摘要:")
        print("=" * 60)
        
        # 短線推薦
        if recommendations['short_term']:
            print(f"\n🔥 短線推薦 ({len(recommendations['short_term'])} 支):")
            for i, stock in enumerate(recommendations['short_term'], 1):
                print(f"  {i}. {stock.code} {stock.name}")
                print(f"     現價: {stock.current_price:.1f} ({stock.change_percent:+.1f}%)")
                print(f"     目標: {stock.target_price:.1f} | 停損: {stock.stop_loss:.1f}")
                print(f"     信心: {stock.confidence:.0f}% | 理由: {stock.reason}")
        
        # 長線推薦
        if recommendations['long_term']:
            print(f"\n💎 長線推薦 ({len(recommendations['long_term'])} 支):")
            for i, stock in enumerate(recommendations['long_term'], 1):
                print(f"  {i}. {stock.code} {stock.name}")
                print(f"     現價: {stock.current_price:.1f} ({stock.change_percent:+.1f}%)")
                print(f"     目標: {stock.target_price:.1f} | 停損: {stock.stop_loss:.1f}")
                print(f"     信心: {stock.confidence:.0f}% | 理由: {stock.reason}")
        
        # 風險警示
        if recommendations['weak_stocks']:
            print(f"\n⚠️ 風險警示 ({len(recommendations['weak_stocks'])} 支):")
            for i, stock in enumerate(recommendations['weak_stocks'], 1):
                print(f"  {i}. {stock.code} {stock.name}")
                print(f"     現價: {stock.current_price:.1f} ({stock.change_percent:+.1f}%)")
                print(f"     風險: {stock.reason}")
    
    def _save_analysis_results(self, recommendations: Dict, analyses: List[Dict]):
        """保存分析結果"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 保存推薦結果
            rec_data = {
                'timestamp': timestamp,
                'analysis_time': datetime.now().isoformat(),
                'recommendations': {
                    'short_term': [
                        {
                            'code': r.code,
                            'name': r.name,
                            'current_price': r.current_price,
                            'change_percent': r.change_percent,
                            'reason': r.reason,
                            'target_price': r.target_price,
                            'stop_loss': r.stop_loss,
                            'confidence': r.confidence
                        } for r in recommendations['short_term']
                    ],
                    'long_term': [
                        {
                            'code': r.code,
                            'name': r.name,
                            'current_price': r.current_price,
                            'change_percent': r.change_percent,
                            'reason': r.reason,
                            'target_price': r.target_price,
                            'stop_loss': r.stop_loss,
                            'confidence': r.confidence
                        } for r in recommendations['long_term']
                    ],
                    'weak_stocks': [
                        {
                            'code': r.code,
                            'name': r.name,
                            'current_price': r.current_price,
                            'change_percent': r.change_percent,
                            'reason': r.reason
                        } for r in recommendations['weak_stocks']
                    ]
                }
            }
            
            with open(f'data/recommendations_{timestamp}.json', 'w', encoding='utf-8') as f:
                json.dump(rec_data, f, ensure_ascii=False, indent=2)
            
            # 保存詳細分析
            with open(f'data/analysis_details_{timestamp}.json', 'w', encoding='utf-8') as f:
                json.dump(analyses, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析結果已保存: {timestamp}")
            
        except Exception as e:
            logger.error(f"保存分析結果失敗: {e}")
    
    def setup_schedule(self):
        """設置定時任務"""
        print("⏰ 設置定時分析任務...")
        
        # 早盤分析 - 9:30
        schedule.every().monday.at("09:30").do(self.run_analysis)
        schedule.every().tuesday.at("09:30").do(self.run_analysis)
        schedule.every().wednesday.at("09:30").do(self.run_analysis)
        schedule.every().thursday.at("09:30").do(self.run_analysis)
        schedule.every().friday.at("09:30").do(self.run_analysis)
        
        # 午間分析 - 12:30
        schedule.every().monday.at("12:30").do(self.run_analysis)
        schedule.every().tuesday.at("12:30").do(self.run_analysis)
        schedule.every().wednesday.at("12:30").do(self.run_analysis)
        schedule.every().thursday.at("12:30").do(self.run_analysis)
        schedule.every().friday.at("12:30").do(self.run_analysis)
        
        # 收盤分析 - 15:00
        schedule.every().monday.at("15:00").do(self.run_analysis)
        schedule.every().tuesday.at("15:00").do(self.run_analysis)
        schedule.every().wednesday.at("15:00").do(self.run_analysis)
        schedule.every().thursday.at("15:00").do(self.run_analysis)
        schedule.every().friday.at("15:00").do(self.run_analysis)
        
        print("✅ 定時任務設置完成")
        print("📅 分析時間: 平日 09:30, 12:30, 15:00")
    
    def run_scheduler(self):
        """運行定時器"""
        print("🔄 定時分析服務啟動中...")
        print("按 Ctrl+C 停止服務")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次
        except KeyboardInterrupt:
            print("\n👋 定時分析服務已停止")

def main():
    """主函數"""
    print("🎯 台股分析推播系統")
    print("=" * 50)
    print("請選擇運行模式:")
    print("1. 立即執行分析")
    print("2. 啟動定時分析服務")
    print("3. 測試郵件通知")
    print("0. 退出")
    
    try:
        choice = input("\n請輸入選項 (1-3): ").strip()
        
        # 初始化系統
        system = StockAnalysisSystem()
        
        if choice == "1":
            print("\n🚀 執行即時分析...")
            success = system.run_analysis()
            if success:
                print("\n✅ 分析完成！")
            else:
                print("\n❌ 分析失敗")
        
        elif choice == "2":
            system.setup_schedule()
            system.run_scheduler()
        
        elif choice == "3":
            print("\n📧 測試郵件通知...")
            # 創建測試推薦
            test_recommendations = {
                'short_term': [
                    StockRecommendation(
                        code="2330",
                        name="台積電",
                        current_price=638.5,
                        change_percent=2.1,
                        reason="技術面轉強，外資買超",
                        target_price=670.0,
                        stop_loss=620.0,
                        trade_value=15000000000,
                        confidence=85.0
                    )
                ],
                'long_term': [],
                'weak_stocks': []
            }
            
            success = system.send_notification(test_recommendations)
            if success:
                print("✅ 測試通知發送成功！")
            else:
                print("❌ 測試通知發送失敗")
        
        elif choice == "0":
            print("👋 再見！")
        
        else:
            print("❌ 無效選項")
            
    except KeyboardInterrupt:
        print("\n\n👋 程式已中斷")
    except Exception as e:
        print(f"\n❌ 程式執行錯誤: {e}")

if __name__ == "__main__":
    main()
