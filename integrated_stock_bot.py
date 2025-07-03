"""
integrated_stock_bot.py - 整合版股市分析系統
支援基礎、增強、優化三種分析模式的統一股市機器人
"""
import os
import sys
import time
import json
import schedule
import argparse
import logging
import importlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def setup_logging():
    """設置日誌"""
    try:
        from config import LOG_DIR, LOG_CONFIG
        
        # 確保日誌目錄存在
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # 配置日誌
        logging.basicConfig(
            filename=LOG_CONFIG['filename'],
            level=getattr(logging, LOG_CONFIG['level']),
            format=LOG_CONFIG['format']
        )
        
        # 同時輸出到控制台
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, LOG_CONFIG['level']))
        console.setFormatter(logging.Formatter(LOG_CONFIG['format']))
        logging.getLogger().addHandler(console)
    except ImportError:
        # 如果沒有config模組，使用默認設置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

def log_event(message, level='info'):
    """記錄事件並打印到控制台"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    if level == 'error':
        logging.error(message)
        print(f"[{timestamp}] ❌ {message}")
    elif level == 'warning':
        logging.warning(message)
        print(f"[{timestamp}] ⚠️ {message}")
    else:
        logging.info(message)
        print(f"[{timestamp}] ℹ️ {message}")

def check_environment():
    """檢查環境是否配置正確"""
    try:
        # 嘗試導入必要的模塊
        import requests
        import pandas
        import schedule
        import numpy
        from dotenv import load_dotenv
        
        # 檢查配置文件
        try:
            from config import EMAIL_CONFIG, LOG_DIR, CACHE_DIR, DATA_DIR
            
            if EMAIL_CONFIG['enabled']:
                if not all([EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'], EMAIL_CONFIG['receiver']]):
                    # 檢查是否在GitHub Actions或CI環境中運行
                    if 'GITHUB_ACTIONS' in os.environ or 'CI' in os.environ:
                        print("⚠️ 警告: 在CI環境中檢測到電子郵件設定不完整，請檢查GitHub Secrets是否正確配置")
                        print(f"目前環境變數: EMAIL_SENDER={'已設置' if os.getenv('EMAIL_SENDER') else '未設置'}")
                        print(f"             EMAIL_RECEIVER={'已設置' if os.getenv('EMAIL_RECEIVER') else '未設置'}")
                        print(f"             EMAIL_PASSWORD={'已設置' if os.getenv('EMAIL_PASSWORD') else '未設置'}")
                    else:
                        print("⚠️ 警告: 電子郵件設定不完整，請檢查.env文件")
                    return False
            
            # 檢查目錄結構
            for directory in [LOG_DIR, CACHE_DIR, DATA_DIR]:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    print(f"已創建目錄: {directory}")
        except ImportError:
            print("⚠️ 警告: 無法導入config模組，將使用默認設置")
        
        # 檢查是否在CI環境中運行
        if 'GITHUB_ACTIONS' in os.environ or 'CI' in os.environ:
            print("檢測到CI環境，正在使用GitHub Secrets作為配置來源")
        
        return True
        
    except ImportError as e:
        print(f"❌ 錯誤: 缺少必要的套件: {e}")
        print("請執行 pip install -r requirements.txt 安裝必要的套件")
        return False
    
    except Exception as e:
        print(f"❌ 錯誤: 環境檢查失敗: {e}")
        return False

class IntegratedStockBot:
    """整合版股市分析機器人"""
    
    def __init__(self, mode='basic'):
        """
        初始化機器人
        mode: 'basic', 'enhanced', 'optimized'
        """
        self.mode = mode
        self.data_fetcher = None
        self.enhanced_analyzer = None
        self.optimized_bot = None
        self.notifier = None
        
        # 初始化數據獲取器
        self._init_data_fetcher()
        
        # 根據模式初始化相應的分析器
        if mode == 'enhanced':
            self._init_enhanced_mode()
        elif mode == 'optimized':
            self._init_optimized_mode()
        else:
            self._init_basic_mode()
        
        # 初始化通知系統
        self._init_notifier()
        
        # 設置緩存目錄
        self.cache_dir = os.path.join(os.getcwd(), 'data', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 時段配置
        self.time_slot_config = {
            'morning_scan': {
                'name': '早盤掃描',
                'stock_count': 200 if mode == 'optimized' else (100 if mode == 'basic' else 100),
                'analysis_focus': 'short_term',
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 2 if mode != 'optimized' else 3,
                    'weak_stocks': 2
                }
            },
            'mid_morning_scan': {
                'name': '盤中掃描',
                'stock_count': 300 if mode == 'optimized' else 150,
                'analysis_focus': 'short_term',
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 2 if mode != 'optimized' else 3,
                    'weak_stocks': 1
                }
            },
            'mid_day_scan': {
                'name': '午間掃描',
                'stock_count': 300 if mode == 'optimized' else 150,
                'analysis_focus': 'mixed',
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 3 if mode != 'optimized' else 4,
                    'weak_stocks': 2
                }
            },
            'afternoon_scan': {
                'name': '盤後掃描',
                'stock_count': 1000 if mode == 'optimized' else 750,
                'analysis_focus': 'mixed',
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 3 if mode != 'optimized' else 5,
                    'weak_stocks': 2
                }
            },
            'weekly_summary': {
                'name': '週末總結',
                'stock_count': 1000 if mode == 'optimized' else 750,
                'analysis_focus': 'long_term',
                'recommendation_limits': {
                    'short_term': 3,
                    'long_term': 4 if mode != 'optimized' else 6,
                    'weak_stocks': 3
                }
            }
        }
        
        log_event(f"✅ 整合版股市機器人初始化完成 (模式: {mode.upper()})")
    
    def _init_data_fetcher(self):
        """初始化數據獲取器"""
        try:
            from twse_data_fetcher import TWStockDataFetcher
            self.data_fetcher = TWStockDataFetcher()
            log_event("✅ 數據獲取器初始化成功")
        except Exception as e:
            log_event(f"⚠️ 數據獲取器初始化失敗: {e}", level='warning')
    
    def _init_basic_mode(self):
        """初始化基礎模式"""
        log_event("🔧 初始化基礎分析模式")
    
    def _init_enhanced_mode(self):
        """初始化增強模式"""
        try:
            from enhanced_analysis_system import EnhancedStockAnalyzer
            self.enhanced_analyzer = EnhancedStockAnalyzer()
            log_event("✅ 增強分析器初始化成功")
        except Exception as e:
            log_event(f"⚠️ 增強分析器初始化失敗，回退到基礎模式: {e}", level='warning')
            self.mode = 'basic'
    
    def _init_optimized_mode(self):
        """初始化優化模式"""
        try:
            from enhanced_stock_bot_optimized import OptimizedStockBot
            self.optimized_bot = OptimizedStockBot()
            log_event("✅ 優化版分析器初始化成功")
        except Exception as e:
            log_event(f"⚠️ 優化版分析器初始化失敗，回退到增強模式: {e}", level='warning')
            self._init_enhanced_mode()
    
    def _init_notifier(self):
        """初始化通知系統"""
        try:
            if self.mode == 'optimized':
                import optimized_notifier as notifier
            else:
                import notifier
            
            self.notifier = notifier
            notifier.init()
            log_event("✅ 通知系統初始化成功")
        except Exception as e:
            log_event(f"⚠️ 通知系統初始化失敗: {e}", level='warning')
    
    def get_stocks_for_analysis(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """獲取要分析的股票"""
        log_event(f"🔍 開始獲取 {time_slot} 時段的股票數據")
        
        try:
            if self.data_fetcher:
                stocks = self.data_fetcher.get_stocks_by_time_slot(time_slot, date)
            else:
                # 如果沒有數據獲取器，創建模擬數據
                stocks = self._create_mock_stocks()
            
            # 基本過濾條件
            valid_stocks = []
            for stock in stocks:
                if (stock.get('close', 0) > 0 and 
                    stock.get('volume', 0) > 1000 and
                    stock.get('trade_value', 0) > 100000):
                    valid_stocks.append(stock)
            
            log_event(f"✅ 獲取了 {len(valid_stocks)} 支有效股票")
            return valid_stocks
            
        except Exception as e:
            log_event(f"❌ 獲取股票數據失敗: {e}", level='error')
            return self._create_mock_stocks()
    
    def _create_mock_stocks(self) -> List[Dict[str, Any]]:
        """創建模擬股票數據"""
        import random
        
        mock_stocks = []
        stock_list = [
            ('2330', '台積電'), ('2317', '鴻海'), ('2454', '聯發科'),
            ('2881', '富邦金'), ('2882', '國泰金'), ('2609', '陽明'),
            ('2603', '長榮'), ('1301', '台塑'), ('1303', '南亞')
        ]
        
        for code, name in stock_list:
            stock = {
                'code': code,
                'name': name,
                'close': round(random.uniform(50, 600), 1),
                'change_percent': round(random.uniform(-5, 5), 2),
                'volume': random.randint(10000, 100000),
                'trade_value': random.randint(1000000, 10000000000)
            }
            mock_stocks.append(stock)
        
        return mock_stocks
    
    def analyze_stock(self, stock_info: Dict[str, Any], analysis_focus: str) -> Dict[str, Any]:
        """根據模式分析股票"""
        if self.mode == 'optimized' and self.optimized_bot:
            return self._analyze_optimized(stock_info, analysis_focus)
        elif self.mode == 'enhanced' and self.enhanced_analyzer:
            return self._analyze_enhanced(stock_info, analysis_focus)
        else:
            return self._analyze_basic(stock_info)
    
    def _analyze_optimized(self, stock_info: Dict[str, Any], analysis_focus: str) -> Dict[str, Any]:
        """優化版分析"""
        try:
            result = self.optimized_bot.analyze_stock_optimized(stock_info, analysis_focus)
            result['analysis_method'] = 'optimized'
            return result
        except Exception as e:
            log_event(f"⚠️ 優化分析失敗，回退到增強分析: {e}", level='warning')
            return self._analyze_enhanced(stock_info, analysis_focus)
    
    def _analyze_enhanced(self, stock_info: Dict[str, Any], analysis_focus: str) -> Dict[str, Any]:
        """增強版分析"""
        try:
            if self.enhanced_analyzer:
                result = self.enhanced_analyzer.analyze_stock_enhanced(stock_info, analysis_focus)
                result['analysis_method'] = 'enhanced'
                return result
            else:
                return self._analyze_basic(stock_info)
        except Exception as e:
            log_event(f"⚠️ 增強分析失敗，回退到基礎分析: {e}", level='warning')
            return self._analyze_basic(stock_info)
    
    def _analyze_basic(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """基礎分析"""
        stock_code = stock_info['code']
        stock_name = stock_info['name']
        current_price = stock_info['close']
        change_percent = stock_info['change_percent']
        volume = stock_info['volume']
        trade_value = stock_info['trade_value']
        
        # 基礎評分邏輯
        score = 0
        
        # 價格變動評分
        if change_percent > 5:
            score += 4
        elif change_percent > 3:
            score += 3
        elif change_percent > 1:
            score += 2
        elif change_percent > 0:
            score += 1
        elif change_percent < -5:
            score -= 4
        elif change_percent < -3:
            score -= 3
        elif change_percent < -1:
            score -= 2
        elif change_percent < 0:
            score -= 1
        
        # 成交量評分
        if trade_value > 5000000000:
            score += 2
        elif trade_value > 1000000000:
            score += 1
        elif trade_value < 10000000:
            score -= 1
        
        # 特殊行業加權
        if any(keyword in stock_name for keyword in ['航運', '海運', '長榮', '陽明', '萬海']):
            score += 0.5
        elif any(keyword in stock_name for keyword in ['台積電', '聯發科', '鴻海']):
            score += 0.5
        
        # 根據得分判斷趨勢和建議
        if score >= 4:
            trend = "強烈看漲"
            suggestion = "適合積極買入"
            target_price = round(current_price * 1.08, 1)
            stop_loss = round(current_price * 0.95, 1)
        elif score >= 2:
            trend = "看漲"
            suggestion = "可考慮買入"
            target_price = round(current_price * 1.05, 1)
            stop_loss = round(current_price * 0.97, 1)
        elif score >= 0:
            trend = "中性偏多"
            suggestion = "適合中長期投資"
            target_price = round(current_price * 1.08, 1)
            stop_loss = round(current_price * 0.95, 1)
        elif score > -2:
            trend = "中性"
            suggestion = "觀望為宜"
            target_price = None
            stop_loss = round(current_price * 0.95, 1)
        elif score >= -4:
            trend = "看跌"
            suggestion = "建議減碼"
            target_price = None
            stop_loss = round(current_price * 0.97, 1)
        else:
            trend = "強烈看跌"
            suggestion = "建議賣出"
            target_price = None
            stop_loss = round(current_price * 0.98, 1)
        
        # 生成推薦理由
        reason = self._generate_basic_reason(change_percent, trade_value, stock_name)
        
        return {
            "code": stock_code,
            "name": stock_name,
            "current_price": current_price,
            "change_percent": round(change_percent, 1),
            "volume": volume,
            "trade_value": trade_value,
            "weighted_score": round(score, 1),
            "trend": trend,
            "suggestion": suggestion,
            "reason": reason,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "analysis_time": datetime.now().isoformat(),
            "analysis_method": "basic",
            "data_quality": "current_day"
        }
    
    def _generate_basic_reason(self, change_percent: float, trade_value: float, stock_name: str) -> str:
        """生成基礎推薦理由"""
        reasons = []
        
        # 價格變動理由
        if change_percent > 5:
            reasons.append(f"今日大漲 {change_percent:.1f}%，動能強勁")
        elif change_percent > 3:
            reasons.append(f"今日上漲 {change_percent:.1f}%，表現強勢")
        elif change_percent > 1:
            reasons.append(f"今日上漲 {change_percent:.1f}%，走勢良好")
        elif change_percent > 0:
            reasons.append(f"今日微漲 {change_percent:.1f}%，穩健表現")
        elif change_percent < -5:
            reasons.append(f"今日大跌 {abs(change_percent):.1f}%，風險較高")
        elif change_percent < -3:
            reasons.append(f"今日下跌 {abs(change_percent):.1f}%，需注意風險")
        elif change_percent < 0:
            reasons.append(f"今日小跌 {abs(change_percent):.1f}%，短線偏弱")
        
        # 成交量理由
        if trade_value > 5000000000:
            reasons.append("成交金額龐大，市場高度關注")
        elif trade_value > 1000000000:
            reasons.append("成交活躍，資金關注度高")
        elif trade_value > 500000000:
            reasons.append("成交量適中，流動性良好")
        
        # 特殊股票理由
        if any(keyword in stock_name for keyword in ['台積電', '聯發科', '鴻海']):
            reasons.append("權值股表現，指標意義重大")
        elif any(keyword in stock_name for keyword in ['航運', '海運', '長榮', '陽明', '萬海']):
            reasons.append("航運股表現，關注產業動態")
        
        return "、".join(reasons) if reasons else "技術面穩健，適合中長期投資"
    
    def generate_recommendations(self, analyses: List[Dict[str, Any]], time_slot: str) -> Dict[str, List[Dict[str, Any]]]:
        """生成推薦"""
        if not analyses:
            return {"short_term": [], "long_term": [], "weak_stocks": []}
        
        # 獲取配置
        config = self.time_slot_config[time_slot]
        limits = config['recommendation_limits']
        
        # 過濾有效分析
        valid_analyses = [a for a in analyses if a.get('data_quality') != 'limited']
        
        # 短線推薦（得分 >= 2）
        short_term_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) >= 2]
        short_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        short_term = []
        for analysis in short_term_candidates[:limits['short_term']]:
            short_term.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "reason": analysis["reason"],
                "target_price": analysis["target_price"],
                "stop_loss": analysis["stop_loss"],
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        # 長線推薦（得分 0-2 之間且成交量 > 1億）
        long_term_candidates = [a for a in valid_analyses 
                              if 0 <= a.get('weighted_score', 0) < 2 
                              and a.get('trade_value', 0) > 100000000]
        long_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        long_term = []
        for analysis in long_term_candidates[:limits['long_term']]:
            long_term.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "reason": analysis["reason"],
                "target_price": analysis["target_price"],
                "stop_loss": analysis["stop_loss"],
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        # 極弱股（得分 <= -3）
        weak_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) <= -3]
        weak_candidates.sort(key=lambda x: x.get('weighted_score', 0))
        
        weak_stocks = []
        for analysis in weak_candidates[:limits['weak_stocks']]:
            weak_stocks.append({
                "code": analysis["code"],
                "name": analysis["name"],
                "current_price": analysis["current_price"],
                "alert_reason": analysis["reason"],
                "trade_value": analysis["trade_value"],
                "analysis": analysis
            })
        
        return {
            "short_term": short_term,
            "long_term": long_term,
            "weak_stocks": weak_stocks
        }
    
    def run_analysis(self, time_slot: str) -> None:
        """執行分析並發送通知"""
        start_time = time.time()
        log_event(f"🚀 開始執行 {time_slot} 分析 (模式: {self.mode.upper()})")
        
        try:
            # 確保通知系統可用
            if self.notifier and hasattr(self.notifier, 'is_notification_available'):
                if not self.notifier.is_notification_available():
                    log_event("⚠️ 通知系統不可用，嘗試初始化", level='warning')
                    self.notifier.init()
            
            # 獲取股票數據
            stocks = self.get_stocks_for_analysis(time_slot)
            
            if not stocks:
                log_event("❌ 無法獲取股票數據", level='error')
                return
            
            # 獲取配置
            config = self.time_slot_config[time_slot]
            analysis_focus = config['analysis_focus']
            expected_count = config['stock_count']
            
            log_event(f"📊 成功獲取 {len(stocks)} 支股票（預期 {expected_count} 支）")
            log_event(f"🔍 分析重點: {analysis_focus}")
            log_event(f"🔧 分析模式: {self.mode.upper()}")
            
            # 分析股票
            all_analyses = []
            total_stocks = len(stocks)
            batch_size = 50
            method_count = {}
            
            for i in range(0, total_stocks, batch_size):
                batch = stocks[i:i + batch_size]
                batch_end = min(i + batch_size, total_stocks)
                
                log_event(f"🔍 分析第 {i//batch_size + 1} 批次: 股票 {i+1}-{batch_end}/{total_stocks}")
                
                # 批次分析
                for j, stock in enumerate(batch):
                    try:
                        analysis = self.analyze_stock(stock, analysis_focus)
                        all_analyses.append(analysis)
                        
                        # 統計分析方法
                        method = analysis.get('analysis_method', 'unknown')
                        method_count[method] = method_count.get(method, 0) + 1
                        
                        # 每50支股票顯示進度
                        if (i + j + 1) % 50 == 0:
                            elapsed = time.time() - start_time
                            log_event(f"⏱️ 已分析 {i+j+1}/{total_stocks} 支股票，耗時 {elapsed:.1f}秒")
                        
                    except Exception as e:
                        log_event(f"⚠️ 分析股票 {stock['code']} 失敗: {e}", level='warning')
                        continue
                
                # 批次間短暫休息
                if i + batch_size < total_stocks:
                    time.sleep(0.5)
            
            elapsed_time = time.time() - start_time
            log_event(f"✅ 完成 {len(all_analyses)} 支股票分析，耗時 {elapsed_time:.1f} 秒")
            
            # 顯示分析方法統計
            method_stats = [f"{method}:{count}支" for method, count in method_count.items()]
            log_event(f"📈 分析方法統計: {', '.join(method_stats)}")
            
            # 生成推薦
            recommendations = self.generate_recommendations(all_analyses, time_slot)
            
            # 顯示推薦統計
            short_count = len(recommendations['short_term'])
            long_count = len(recommendations['long_term'])
            weak_count = len(recommendations['weak_stocks'])
            
            log_event(f"📊 推薦結果: 短線 {short_count} 支, 長線 {long_count} 支, 極弱股 {weak_count} 支")
            
            # 顯示推薦詳情
            if short_count > 0:
                log_event("🔥 短線推薦:")
                for stock in recommendations['short_term']:
                    analysis_info = stock['analysis']
                    method = analysis_info.get('analysis_method', 'unknown')
                    score = analysis_info.get('weighted_score', 0)
                    log_event(f"   {stock['code']} {stock['name']} (評分:{score}, 方法:{method})")
            
            # 發送通知
            display_name = config['name']
            if self.notifier:
                if self.mode == 'optimized' and hasattr(self.notifier, 'send_optimized_combined_recommendations'):
                    self.notifier.send_optimized_combined_recommendations(recommendations, display_name)
                elif hasattr(self.notifier, 'send_combined_recommendations'):
                    self.notifier.send_combined_recommendations(recommendations, display_name)
                else:
                    log_event("⚠️ 通知系統不支持發送推薦", level='warning')
            
            # 保存分析結果
            self.save_analysis_results(all_analyses, recommendations, time_slot)
            
            total_time = time.time() - start_time
            log_event(f"🎉 {time_slot} 分析完成，總耗時 {total_time:.1f} 秒")
            
        except Exception as e:
            log_event(f"❌ 執行 {time_slot} 分析時發生錯誤: {e}", level='error')
            import traceback
            log_event(traceback.format_exc(), level='error')
    
    def save_analysis_results(self, analyses: List[Dict[str, Any]], recommendations: Dict[str, List], time_slot: str) -> None:
        """保存分析結果"""
        try:
            # 創建日期目錄
            date_str = datetime.now().strftime('%Y%m%d')
            results_dir = os.path.join(os.getcwd(), 'data', 'analysis_results', date_str)
            os.makedirs(results_dir, exist_ok=True)
            
            # 保存分析結果
            analyses_path = os.path.join(results_dir, f"{time_slot}_analyses_{self.mode}.json")
            with open(analyses_path, 'w', encoding='utf-8') as f:
                json.dump(analyses, f, ensure_ascii=False, indent=2)
            
            # 保存推薦結果
            recommendations_path = os.path.join(results_dir, f"{time_slot}_recommendations_{self.mode}.json")
            with open(recommendations_path, 'w', encoding='utf-8') as f:
                json.dump(recommendations, f, ensure_ascii=False, indent=2)
            
            log_event(f"💾 分析結果已保存到 {results_dir}")
            
        except Exception as e:
            log_event(f"⚠️ 保存分析結果時發生錯誤: {e}", level='warning')

def setup_schedule(bot: IntegratedStockBot):
    """設置排程任務"""
    try:
        from config import NOTIFICATION_SCHEDULE
    except ImportError:
        # 默認時間表
        NOTIFICATION_SCHEDULE = {
            'morning_scan': '09:00',
            'mid_morning_scan': '10:30',
            'mid_day_scan': '12:30',
            'afternoon_scan': '15:00',
            'weekly_summary': '17:00',
            'heartbeat': '08:30'
        }
    
    print("⏰ 設置排程任務...")
    
    # 工作日排程
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    
    # 早盤掃描
    for day in weekdays:
        getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['morning_scan']).do(
            bot.run_analysis, 'morning_scan'
        )
    
    # 盤中掃描
    for day in weekdays:
        getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(
            bot.run_analysis, 'mid_morning_scan'
        )
    
    # 午間掃描
    for day in weekdays:
        getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(
            bot.run_analysis, 'mid_day_scan'
        )
    
    # 盤後掃描
    for day in weekdays:
        getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(
            bot.run_analysis, 'afternoon_scan'
        )
    
    # 週末總結
    schedule.every().friday.at(NOTIFICATION_SCHEDULE['weekly_summary']).do(
        bot.run_analysis, 'weekly_summary'
    )
    
    # 心跳檢測
    if bot.notifier and hasattr(bot.notifier, 'send_heartbeat'):
        schedule.every().day.at(NOTIFICATION_SCHEDULE['heartbeat']).do(bot.notifier.send_heartbeat)
    
    print("✅ 排程任務設置完成")
    return True

def run_daemon(mode='basic'):
    """運行後台服務"""
    print(f"🚀 啟動整合版股市分析系統 (模式: {mode.upper()})")
    print("=" * 60)
    
    # 顯示模式特色
    if mode == 'optimized':
        print("💎 優化版特色:")
        print("  • 長線推薦權重優化: 基本面 1.2倍, 法人 0.8倍")
        print("  • 重視高殖利率股票 (>2.5% 優先推薦)")
        print("  • 重視EPS高成長股票 (>8% 優先推薦)")
        print("  • 重視法人買超股票 (>5000萬優先推薦)")
        print("  • 強化通知顯示: 詳細基本面資訊")
    elif mode == 'enhanced':
        print("🔧 增強版特色:")
        print("  • 技術面與基本面雙重分析")
        print("  • 智能風險評估")
        print("  • 更精確的目標價位設定")
        print("  • 增強版推薦算法")
    else:
        print("⚡ 基礎版特色:")
        print("  • 快速技術面分析")
        print("  • 穩定可靠的推薦算法")
        print("  • 輕量級資源占用")
        print("  • 適合快速部署")
    
    print("=" * 60)
    
    # 初始化機器人
    bot = IntegratedStockBot(mode)
    
    # 設置排程
    if not setup_schedule(bot):
        print("❌ 排程設置失敗，程序退出")
        return
    
    # 啟動時發送心跳
    if bot.notifier and hasattr(bot.notifier, 'send_heartbeat'):
        print("💓 發送啟動心跳...")
        bot.notifier.send_heartbeat()
    
    print(f"\n🎯 {mode.upper()}模式系統已啟動，開始執行排程任務...")
    print("📝 按 Ctrl+C 停止系統")
    
    # 運行排程循環
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # 每30秒檢查一次
    except KeyboardInterrupt:
        print("\n\n⚠️ 收到用戶中斷信號")
        print("🛑 正在優雅關閉系統...")
        
        # 發送關閉通知
        if bot.notifier and hasattr(bot.notifier, 'send_notification'):
            try:
                close_message = f"""📴 整合版股市分析系統關閉通知

⏰ 關閉時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 運行模式: {mode.upper()}

✅ 系統已安全關閉
感謝使用整合版股市分析系統！

祝您投資順利！💰"""
                
                bot.notifier.send_notification(close_message, f"📴 {mode.upper()}模式系統關閉通知")
            except:
                pass
        
        print("👋 系統已關閉")
    except Exception as e:
        print(f"\n❌ 系統運行出現錯誤: {e}")
        print("🔄 請檢查錯誤並重新啟動系統")

def run_single_analysis(time_slot, mode='basic'):
    """執行單次分析"""
    print(f"🔍 執行 {mode.upper()} 模式 {time_slot} 分析...")
    
    try:
        # 初始化機器人
        bot = IntegratedStockBot(mode)
        
        # 執行分析
        bot.run_analysis(time_slot)
        
        print(f"✅ {time_slot} 分析完成！")
        print("📧 分析報告已發送，請檢查您的郵箱")
        
    except Exception as e:
        print(f"❌ 分析執行失敗: {e}")
        import traceback
        print(traceback.format_exc())

def test_notification(test_type='all', mode='basic'):
    """測試通知系統"""
    print(f"📧 測試 {mode.upper()} 模式通知系統...")
    
    try:
        # 初始化機器人
        bot = IntegratedStockBot(mode)
        
        if not bot.notifier:
            print("❌ 通知系統不可用")
            return
        
        # 創建測試數據
        if mode == 'optimized':
            test_data = {
                "short_term": [
                    {
                        "code": "2330",
                        "name": "台積電", 
                        "current_price": 638.5,
                        "reason": "技術面轉強，MACD金叉",
                        "target_price": 670.0,
                        "stop_loss": 620.0,
                        "trade_value": 14730000000,
                        "analysis": {
                            "change_percent": 2.35,
                            "foreign_net_buy": 25000
                        }
                    }
                ],
                "long_term": [
                    {
                        "code": "2609",
                        "name": "陽明",
                        "current_price": 91.2,
                        "reason": "高殖利率7.2%，EPS高成長35.6%，三大法人大幅買超62億",
                        "target_price": 110.0,
                        "stop_loss": 85.0,
                        "trade_value": 4560000000,
                        "analysis": {
                            "change_percent": 1.8,
                            "dividend_yield": 7.2,
                            "eps_growth": 35.6,
                            "pe_ratio": 8.9,
                            "roe": 18.4,
                            "foreign_net_buy": 45000,
                            "trust_net_buy": 15000,
                            "total_institutional": 62000
                        }
                    }
                ],
                "weak_stocks": []
            }
            
            if hasattr(bot.notifier, 'send_optimized_combined_recommendations'):
                bot.notifier.send_optimized_combined_recommendations(test_data, f"{mode.upper()}模式功能測試")
            else:
                bot.notifier.send_combined_recommendations(test_data, f"{mode.upper()}模式功能測試")
        else:
            # 基礎/增強模式測試
            test_data = {
                "short_term": [
                    {
                        "code": "2330",
                        "name": "台積電",
                        "current_price": 638.5,
                        "reason": "今日上漲 2.3%，成交活躍",
                        "target_price": 670.0,
                        "stop_loss": 620.0,
                        "trade_value": 14730000000
                    }
                ],
                "long_term": [
                    {
                        "code": "2882",
                        "name": "國泰金",
                        "current_price": 58.3,
                        "reason": "金融股回穩，適合中長期投資",
                        "target_price": 65.0,
                        "stop_loss": 55.0,
                        "trade_value": 2100000000
                    }
                ],
                "weak_stocks": []
            }
            
            bot.notifier.send_combined_recommendations(test_data, f"{mode.upper()}模式功能測試")
        
        print("✅ 測試通知已發送！")
        print("📋 請檢查郵箱確認通知內容")
        
    except Exception as e:
        print(f"❌ 測試通知失敗: {e}")
        import traceback
        print(traceback.format_exc())

def show_status(mode='basic'):
    """顯示系統狀態"""
    print("📊 整合版股市分析系統狀態")
    print("=" * 50)
    print(f"🔧 當前模式: {mode.upper()}")
    
    try:
        # 嘗試初始化機器人
        bot = IntegratedStockBot(mode)
        print("✅ 機器人初始化: 成功")
        
        # 檢查通知狀態
        if bot.notifier:
            if hasattr(bot.notifier, 'is_notification_available'):
                if bot.notifier.is_notification_available():
                    print("📧 通知系統: 可用")
                else:
                    print("⚠️ 通知系統: 不可用")
            else:
                print("📧 通知系統: 已載入")
        else:
            print("❌ 通知系統: 不可用")
        
        # 顯示模式特色
        print(f"\n💎 {mode.upper()}模式特色:")
        if mode == 'optimized':
            print("  📈 長線推薦基本面權重: 1.2倍")
            print("  🏦 法人買賣權重: 0.8倍")
            print("  💸 殖利率 > 2.5% 優先推薦")
            print("  📊 EPS成長 > 8% 優先推薦")
            print("  💰 法人買超 > 5000萬優先推薦")
        elif mode == 'enhanced':
            print("  🔧 技術面與基本面雙重分析")
            print("  ⚡ 智能風險評估")
            print("  🎯 精確目標價位設定")
            print("  📊 增強版推薦算法")
        else:
            print("  ⚡ 快速技術面分析")
            print("  🛡️ 穩定推薦算法")
            print("  💡 輕量級資源占用")
            print("  🚀 快速部署")
        
        print("\n📅 排程時段:")
        config = bot.time_slot_config
        for slot, info in config.items():
            stock_count = info['stock_count']
            name = info['name']
            print(f"  📊 {name}: {stock_count}支股票")
        
    except Exception as e:
        print(f"❌ 系統狀態檢查失敗: {e}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='整合版台股分析系統')
    parser.add_argument('command', 
                       choices=['start', 'run', 'status', 'test'],
                       help='執行命令')
    parser.add_argument('--mode', '-m',
                       choices=['basic', 'enhanced', 'optimized'],
                       default='basic',
                       help='分析模式 (預設: basic)')
    parser.add_argument('--slot', '-s',
                       choices=['morning_scan', 'mid_morning_scan', 'mid_day_scan', 
                               'afternoon_scan', 'weekly_summary'],
                       help='分析時段 (配合 run 命令使用)')
    parser.add_argument('--daemon', '-d', action='store_true', help='後台運行')
    parser.add_argument('--test-type', '-t',
                       choices=['all', 'simple', 'html', 'urgent', 'stock', 'combined', 'heartbeat'],
                       default='all', help='測試類型')
    
    args = parser.parse_args()
    
    # 檢查環境
    if not check_environment():
        print("環境檢查失敗，請修復上述問題再嘗試")
        return
    
    # 設置日誌
    setup_logging()
    
    # 執行相應的命令
    if args.command == 'start':
        run_daemon(args.mode)
        
    elif args.command == 'run':
        if not args.slot:
            print("❌ 使用 run 命令時必須指定 --slot 參數")
            print("📝 範例: python integrated_stock_bot.py run --slot afternoon_scan --mode optimized")
            return
        
        run_single_analysis(args.slot, args.mode)
        
    elif args.command == 'status':
        show_status(args.mode)
        
    elif args.command == 'test':
        test_notification(args.test_type, args.mode)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
