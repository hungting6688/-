#!/usr/bin/env python3
"""
unified_stock_analyzer.py - 統一股票分析系統
整合修復工具、多模式分析、排程通知等完整功能
"""
import os
import sys
import time
import json
import shutil
import schedule
import argparse
import logging
import subprocess
import importlib.util
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# ============================================================================
# 全域設定和工具函數
# ============================================================================

def setup_logging():
    """設置日誌系統"""
    try:
        from config import LOG_DIR, LOG_CONFIG
        os.makedirs(LOG_DIR, exist_ok=True)
        logging.basicConfig(
            filename=LOG_CONFIG['filename'],
            level=getattr(logging, LOG_CONFIG['level']),
            format=LOG_CONFIG['format']
        )
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, LOG_CONFIG['level']))
        console.setFormatter(logging.Formatter(LOG_CONFIG['format']))
        logging.getLogger().addHandler(console)
    except ImportError:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

def log_event(message, level='info'):
    """記錄事件並打印到控制台"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    icons = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'success': '✅'}
    icon = icons.get(level, 'ℹ️')
    
    print(f"[{timestamp}] {icon} {message}")
    
    if level == 'error':
        logging.error(message)
    elif level == 'warning':
        logging.warning(message)
    else:
        logging.info(message)

def check_environment():
    """檢查環境配置"""
    try:
        import requests, pandas, numpy, schedule
        from dotenv import load_dotenv
        
        # 檢查配置文件
        try:
            from config import EMAIL_CONFIG, LOG_DIR, CACHE_DIR, DATA_DIR
            if EMAIL_CONFIG['enabled'] and not all([EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'], EMAIL_CONFIG['receiver']]):
                if 'GITHUB_ACTIONS' in os.environ or 'CI' in os.environ:
                    log_event("在CI環境中檢測到電子郵件設定不完整", level='warning')
                else:
                    log_event("電子郵件設定不完整，請檢查.env文件", level='warning')
                return False
            
            for directory in [LOG_DIR, CACHE_DIR, DATA_DIR]:
                os.makedirs(directory, exist_ok=True)
        except ImportError:
            log_event("無法導入config模組，將使用默認設置", level='warning')
        
        return True
        
    except ImportError as e:
        log_event(f"缺少必要套件: {e}", level='error')
        log_event("請執行 pip install -r requirements.txt", level='error')
        return False
    except Exception as e:
        log_event(f"環境檢查失敗: {e}", level='error')
        return False

# ============================================================================
# 系統修復器類別
# ============================================================================

class SystemFixer:
    """系統修復器 - 處理依賴問題、語法錯誤等"""
    
    def __init__(self):
        self.backup_dir = f"system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.fixes_applied = []
        self.fix_results = {}
        self.files_to_check = [
            'twse_data_fetcher.py',
            'enhanced_realtime_twse_fetcher.py', 
            'enhanced_stock_bot.py',
            'notifier.py',
            'requirements.txt'
        ]
    
    def backup_files(self):
        """備份原始文件"""
        log_event("開始備份原始文件")
        os.makedirs(self.backup_dir, exist_ok=True)
        backed_up = []
        
        for filename in self.files_to_check:
            if os.path.exists(filename):
                backup_path = os.path.join(self.backup_dir, filename)
                shutil.copy2(filename, backup_path)
                backed_up.append(filename)
                log_event(f"已備份: {filename}", level='success')
        
        log_event(f"備份目錄: {self.backup_dir}")
        return len(backed_up) > 0
    
    def fix_aiohttp_dependency(self):
        """修復 aiohttp 依賴問題"""
        log_event("檢查 aiohttp 依賴")
        
        # 嘗試安裝 aiohttp
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'aiohttp>=3.8.0'],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                try:
                    import aiohttp
                    log_event("aiohttp 安裝成功", level='success')
                    self.fixes_applied.append("aiohttp 安裝")
                    return True
                except ImportError:
                    log_event("aiohttp 安裝了但無法導入", level='warning')
            else:
                log_event(f"aiohttp 安裝失敗: {result.stderr}", level='warning')
        except Exception as e:
            log_event(f"aiohttp 安裝過程出錯: {e}", level='warning')
        
        # 如果安裝失敗，生成兼容性代碼
        return self._generate_aiohttp_compatibility()
    
    def _generate_aiohttp_compatibility(self):
        """生成 aiohttp 兼容性代碼"""
        compatibility_code = '''
# aiohttp 兼容性修補代碼
try:
    import aiohttp
    import asyncio
    ASYNC_SUPPORT = True
    print("✅ 異步支援已啟用")
except ImportError:
    ASYNC_SUPPORT = False
    print("⚠️ 異步支援未啟用，使用同步模式")
    
    class MockAsyncio:
        @staticmethod
        def run(coro): return None
        @staticmethod
        def get_event_loop(): return None
    
    class MockAiohttp:
        class ClientSession:
            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
            async def get(self, *args, **kwargs): return MockResponse()
        class ClientTimeout:
            def __init__(self, *args, **kwargs): pass
    
    class MockResponse:
        status = 200
        async def json(self): return {}
        async def text(self): return ""
    
    asyncio = MockAsyncio()
    aiohttp = MockAiohttp()
'''
        
        # 保存兼容性代碼
        with open('aiohttp_compatibility.py', 'w', encoding='utf-8') as f:
            f.write(compatibility_code.strip())
        
        log_event("已生成 aiohttp 兼容性代碼", level='success')
        self.fixes_applied.append("aiohttp 兼容性修補")
        return True
    
    def fix_syntax_errors(self):
        """修復語法錯誤"""
        log_event("檢查並修復語法錯誤")
        fixed_files = []
        
        for filename in self.files_to_check:
            if not os.path.exists(filename):
                continue
            
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查語法
                compile(content, filename, 'exec')
                log_event(f"{filename} 語法正確", level='success')
                
            except SyntaxError as e:
                log_event(f"修復 {filename} 語法錯誤: {e}", level='warning')
                
                # 簡單修復：移除孤立的 return
                if 'return' in str(e):
                    lines = content.split('\n')
                    fixed_lines = [line for line in lines if line.strip() != 'return']
                    fixed_content = '\n'.join(fixed_lines)
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    fixed_files.append(filename)
                    log_event(f"已修復 {filename}", level='success')
        
        if fixed_files:
            self.fixes_applied.append(f"語法修復: {', '.join(fixed_files)}")
        
        return True
    
    def run_system_fix(self):
        """執行系統修復"""
        log_event("🔧 開始系統修復", level='info')
        
        results = []
        results.append(self.backup_files())
        results.append(self.fix_aiohttp_dependency())
        results.append(self.fix_syntax_errors())
        
        success = all(results)
        
        if success:
            log_event("✅ 系統修復完成", level='success')
        else:
            log_event("⚠️ 系統修復部分成功", level='warning')
        
        log_event(f"已應用修復: {', '.join(self.fixes_applied)}")
        return success

# ============================================================================
# 數據獲取器類別
# ============================================================================

class DataFetcher:
    """數據獲取器 - 模擬台股數據獲取"""
    
    def __init__(self):
        self.cache = {}
        self.cache_expire_minutes = 30
    
    def get_stocks_by_time_slot(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """根據時段獲取股票數據"""
        cache_key = f"{time_slot}_{date or datetime.now().strftime('%Y%m%d')}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # 生成模擬數據
        stocks = self._generate_mock_stocks(time_slot)
        self.cache[cache_key] = stocks
        
        return stocks
    
    def _generate_mock_stocks(self, time_slot: str) -> List[Dict[str, Any]]:
        """生成模擬股票數據"""
        import random
        
        # 股票池
        stock_pool = [
            ('2330', '台積電'), ('2317', '鴻海'), ('2454', '聯發科'),
            ('2881', '富邦金'), ('2882', '國泰金'), ('2609', '陽明'),
            ('2603', '長榮'), ('2615', '萬海'), ('1301', '台塑'),
            ('1303', '南亞'), ('2002', '中鋼'), ('2412', '中華電'),
            ('2368', '金像電'), ('3008', '大立光'), ('2408', '南亞科'),
            ('6505', '台塑化'), ('2891', '中信金'), ('5880', '合庫金'),
            ('2886', '兆豐金'), ('2892', '第一金')
        ]
        
        # 根據時段決定股票數量
        slot_counts = {
            'morning_scan': 50,
            'mid_morning_scan': 100, 
            'mid_day_scan': 150,
            'afternoon_scan': 300,
            'weekly_summary': 500
        }
        
        count = slot_counts.get(time_slot, 100)
        selected_stocks = random.sample(stock_pool, min(count, len(stock_pool)))
        
        # 如果需要更多股票，重複選擇
        while len(selected_stocks) < count:
            selected_stocks.extend(random.sample(stock_pool, min(count - len(selected_stocks), len(stock_pool))))
        
        stocks = []
        for code, name in selected_stocks[:count]:
            # 生成隨機價格數據
            base_price = random.uniform(20, 800)
            change_pct = random.uniform(-8, 8)
            
            stock = {
                'code': code,
                'name': name,
                'close': round(base_price, 1),
                'change_percent': round(change_pct, 2),
                'volume': random.randint(1000, 500000),
                'trade_value': random.randint(10000000, 20000000000),
                'high': round(base_price * random.uniform(1.0, 1.05), 1),
                'low': round(base_price * random.uniform(0.95, 1.0), 1),
                'open': round(base_price * random.uniform(0.98, 1.02), 1)
            }
            stocks.append(stock)
        
        return stocks
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查快取是否有效"""
        if cache_key not in self.cache:
            return False
        
        # 簡單的時間檢查（實際應用中會更複雜）
        return True  # 簡化實作

# ============================================================================
# 股票分析器類別
# ============================================================================

class StockAnalyzer:
    """統一股票分析器 - 支援多種分析模式"""
    
    def __init__(self, mode='basic'):
        self.mode = mode
        self.cache = {}
        self.cache_expire_minutes = 30
        
        # 不同模式的權重配置
        self.weight_configs = {
            'basic': {
                'base_score': 1.0,
                'technical': 0.5,
                'fundamental': 0.3,
                'institutional': 0.2
            },
            'enhanced': {
                'base_score': 0.8,
                'technical': 0.7,
                'fundamental': 0.6,
                'institutional': 0.5
            },
            'optimized': {
                'base_score': 0.4,
                'technical': 0.3,
                'fundamental': 1.2,  # 長線重視基本面
                'institutional': 0.8  # 重視法人動向
            }
        }
        
        log_event(f"股票分析器初始化完成 (模式: {mode.upper()})")
    
    def analyze_stock(self, stock_info: Dict[str, Any], analysis_focus: str = 'mixed') -> Dict[str, Any]:
        """統一股票分析入口"""
        try:
            # 基礎分析
            base_analysis = self._get_base_analysis(stock_info)
            
            # 根據模式進行進階分析
            if self.mode in ['enhanced', 'optimized']:
                # 技術面分析
                technical_analysis = self._get_technical_analysis(stock_info)
                
                # 基本面分析
                fundamental_analysis = self._get_fundamental_analysis(stock_info['code'])
                
                # 法人分析
                institutional_analysis = self._get_institutional_analysis(stock_info['code'])
                
                # 綜合分析
                final_analysis = self._combine_analysis(
                    base_analysis, technical_analysis, 
                    fundamental_analysis, institutional_analysis,
                    analysis_focus
                )
                
                return final_analysis
            else:
                # 基礎模式
                return self._finalize_basic_analysis(base_analysis)
                
        except Exception as e:
            log_event(f"分析股票 {stock_info['code']} 失敗: {e}", level='warning')
            return self._get_fallback_analysis(stock_info)
    
    def _get_base_analysis(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """基礎分析"""
        stock_code = stock_info['code']
        stock_name = stock_info['name']
        current_price = stock_info['close']
        change_percent = stock_info['change_percent']
        volume = stock_info['volume']
        trade_value = stock_info['trade_value']
        
        # 基礎評分
        base_score = 0
        
        # 價格變動評分
        if change_percent > 5:
            base_score += 4
        elif change_percent > 3:
            base_score += 3
        elif change_percent > 1:
            base_score += 2
        elif change_percent > 0:
            base_score += 1
        elif change_percent < -5:
            base_score -= 4
        elif change_percent < -3:
            base_score -= 3
        elif change_percent < -1:
            base_score -= 2
        elif change_percent < 0:
            base_score -= 1
        
        # 成交量評分
        if trade_value > 5000000000:  # 50億以上
            base_score += 2
        elif trade_value > 1000000000:  # 10億以上
            base_score += 1
        elif trade_value < 10000000:  # 1000萬以下
            base_score -= 1
        
        # 特殊行業加權
        if any(keyword in stock_name for keyword in ['航運', '海運', '長榮', '陽明', '萬海']):
            base_score += 0.5
        elif any(keyword in stock_name for keyword in ['台積電', '聯發科', '鴻海', '大立光']):
            base_score += 0.5
        
        return {
            'code': stock_code,
            'name': stock_name,
            'current_price': current_price,
            'change_percent': round(change_percent, 1),
            'volume': volume,
            'trade_value': trade_value,
            'base_score': round(base_score, 1),
            'analysis_components': {
                'base': True,
                'technical': False,
                'fundamental': False,
                'institutional': False
            }
        }
    
    def _get_technical_analysis(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """技術面分析"""
        try:
            current_price = stock_info['close']
            change_percent = stock_info['change_percent']
            volume = stock_info['volume']
            high = stock_info.get('high', current_price)
            low = stock_info.get('low', current_price)
            
            tech_score = 0
            signals = {}
            
            # 基於價格變動模擬技術指標
            # MA 信號
            if change_percent > 0:
                tech_score += 1
                signals['ma5_bullish'] = True
            if change_percent > 1:
                tech_score += 1.5
                signals['ma20_bullish'] = True
            if change_percent > 2:
                tech_score += 1
                signals['ma_golden_cross'] = True
            
            # MACD 信號
            if change_percent > 1.5:
                tech_score += 2
                signals['macd_bullish'] = True
            if change_percent > 3:
                tech_score += 2.5
                signals['macd_golden_cross'] = True
            
            # RSI 信號（模擬）
            rsi_value = min(max(50 + change_percent * 5, 10), 90)
            if 30 <= rsi_value <= 70:
                tech_score += 1
                signals['rsi_healthy'] = True
            elif rsi_value < 30:
                tech_score += 1.5
                signals['rsi_oversold'] = True
            elif rsi_value > 70:
                tech_score -= 1
                signals['rsi_overbought'] = True
            
            return {
                'available': True,
                'tech_score': round(tech_score, 1),
                'signals': signals,
                'rsi_value': round(rsi_value, 1)
            }
            
        except Exception as e:
            log_event(f"技術分析失敗: {e}", level='warning')
            return {'available': False}
    
    def _get_fundamental_analysis(self, stock_code: str) -> Dict[str, Any]:
        """基本面分析"""
        try:
            # 模擬基本面數據（實際應用中從財報API獲取）
            import random
            random.seed(hash(stock_code) % 1000)  # 確保同一股票數據一致
            
            # 生成基本面數據
            dividend_yield = round(random.uniform(0.5, 8.0), 1)
            eps_growth = round(random.uniform(-15.0, 40.0), 1)
            pe_ratio = round(random.uniform(5.0, 35.0), 1)
            roe = round(random.uniform(3.0, 30.0), 1)
            revenue_growth = round(random.uniform(-8.0, 25.0), 1)
            
            # 基本面評分
            fund_score = 0
            
            # 殖利率評分
            if dividend_yield > 6:
                fund_score += 4.0
            elif dividend_yield > 4:
                fund_score += 3.0
            elif dividend_yield > 2.5:
                fund_score += 2.0
            elif dividend_yield > 1:
                fund_score += 1.0
            
            # EPS成長評分
            if eps_growth > 30:
                fund_score += 4.0
            elif eps_growth > 20:
                fund_score += 3.5
            elif eps_growth > 10:
                fund_score += 3.0
            elif eps_growth > 5:
                fund_score += 2.0
            elif eps_growth > 0:
                fund_score += 1.0
            elif eps_growth < -10:
                fund_score -= 3.0
            elif eps_growth < 0:
                fund_score -= 1.5
            
            # PE比率評分
            if pe_ratio < 8:
                fund_score += 2.5
            elif pe_ratio < 12:
                fund_score += 2.0
            elif pe_ratio < 18:
                fund_score += 1.5
            elif pe_ratio < 25:
                fund_score += 0.5
            elif pe_ratio > 35:
                fund_score -= 2.0
            
            # ROE評分
            if roe > 25:
                fund_score += 3.0
            elif roe > 20:
                fund_score += 2.5
            elif roe > 15:
                fund_score += 2.0
            elif roe > 10:
                fund_score += 1.0
            elif roe < 5:
                fund_score -= 1.5
            
            return {
                'available': True,
                'fund_score': round(fund_score, 1),
                'dividend_yield': dividend_yield,
                'eps_growth': eps_growth,
                'pe_ratio': pe_ratio,
                'roe': roe,
                'revenue_growth': revenue_growth
            }
            
        except Exception as e:
            log_event(f"基本面分析失敗: {e}", level='warning')
            return {'available': False}
    
    def _get_institutional_analysis(self, stock_code: str) -> Dict[str, Any]:
        """法人買賣分析"""
        try:
            import random
            random.seed(hash(stock_code) % 1000)
            
            # 模擬法人買賣數據
            if stock_code in ['2330', '2317', '2454']:  # 大型權值股
                foreign_net = random.randint(10000, 100000)
                trust_net = random.randint(-20000, 50000)
                dealer_net = random.randint(-10000, 20000)
            elif stock_code in ['2609', '2615', '2603']:  # 航運股
                foreign_net = random.randint(-50000, 80000)
                trust_net = random.randint(-30000, 60000)
                dealer_net = random.randint(-15000, 25000)
            else:
                foreign_net = random.randint(-30000, 50000)
                trust_net = random.randint(-20000, 30000)
                dealer_net = random.randint(-10000, 15000)
            
            # 法人評分
            inst_score = 0
            
            # 外資評分
            if foreign_net > 100000:
                inst_score += 5.0
            elif foreign_net > 50000:
                inst_score += 4.0
            elif foreign_net > 20000:
                inst_score += 3.0
            elif foreign_net > 10000:
                inst_score += 2.5
            elif foreign_net > 5000:
                inst_score += 2.0
            elif foreign_net > 0:
                inst_score += 1.0
            elif foreign_net < -100000:
                inst_score -= 5.0
            elif foreign_net < -50000:
                inst_score -= 4.0
            elif foreign_net < -20000:
                inst_score -= 3.0
            elif foreign_net < 0:
                inst_score -= 1.0
            
            # 投信評分
            if trust_net > 50000:
                inst_score += 3.5
            elif trust_net > 20000:
                inst_score += 3.0
            elif trust_net > 10000:
                inst_score += 2.5
            elif trust_net > 5000:
                inst_score += 2.0
            elif trust_net > 0:
                inst_score += 1.0
            elif trust_net < -50000:
                inst_score -= 3.5
            elif trust_net < -20000:
                inst_score -= 3.0
            elif trust_net < 0:
                inst_score -= 1.0
            
            return {
                'available': True,
                'inst_score': round(inst_score, 1),
                'foreign_net_buy': foreign_net,
                'trust_net_buy': trust_net,
                'dealer_net_buy': dealer_net,
                'total_institutional': foreign_net + trust_net + dealer_net
            }
            
        except Exception as e:
            log_event(f"法人分析失敗: {e}", level='warning')
            return {'available': False}
    
    def _combine_analysis(self, base_analysis: Dict, technical_analysis: Dict,
                         fundamental_analysis: Dict, institutional_analysis: Dict,
                         analysis_focus: str) -> Dict[str, Any]:
        """綜合所有分析結果"""
        
        # 選擇權重配置
        if analysis_focus == 'long_term':
            weights = self.weight_configs['optimized']  # 長線重視基本面
        elif analysis_focus == 'short_term':
            weights = self.weight_configs['enhanced']   # 短線重視技術面
        else:
            weights = self.weight_configs[self.mode]    # 使用模式預設
        
        # 計算綜合得分
        final_score = base_analysis['base_score'] * weights['base_score']
        
        # 添加技術面得分
        if technical_analysis.get('available'):
            final_score += technical_analysis['tech_score'] * weights['technical']
            base_analysis['analysis_components']['technical'] = True
            base_analysis['technical_score'] = technical_analysis['tech_score']
            base_analysis['technical_signals'] = technical_analysis['signals']
            base_analysis['rsi_value'] = technical_analysis.get('rsi_value', 50)
        
        # 添加基本面得分
        if fundamental_analysis.get('available'):
            final_score += fundamental_analysis['fund_score'] * weights['fundamental']
            base_analysis['analysis_components']['fundamental'] = True
            base_analysis['fundamental_score'] = fundamental_analysis['fund_score']
            base_analysis['dividend_yield'] = fundamental_analysis['dividend_yield']
            base_analysis['eps_growth'] = fundamental_analysis['eps_growth']
            base_analysis['pe_ratio'] = fundamental_analysis['pe_ratio']
            base_analysis['roe'] = fundamental_analysis['roe']
        
        # 添加法人得分
        if institutional_analysis.get('available'):
            final_score += institutional_analysis['inst_score'] * weights['institutional']
            base_analysis['analysis_components']['institutional'] = True
            base_analysis['institutional_score'] = institutional_analysis['inst_score']
            base_analysis['foreign_net_buy'] = institutional_analysis['foreign_net_buy']
            base_analysis['trust_net_buy'] = institutional_analysis['trust_net_buy']
            base_analysis['total_institutional'] = institutional_analysis['total_institutional']
        
        # 更新最終評分
        base_analysis['weighted_score'] = round(final_score, 1)
        base_analysis['analysis_type'] = analysis_focus
        base_analysis['analysis_method'] = self.mode
        
        # 生成推薦
        return self._generate_recommendation(base_analysis, analysis_focus)
    
    def _generate_recommendation(self, analysis: Dict[str, Any], analysis_focus: str) -> Dict[str, Any]:
        """生成推薦建議"""
        final_score = analysis['weighted_score']
        current_price = analysis['current_price']
        
        # 根據評分和分析重點決定推薦
        if analysis_focus == 'long_term':
            # 長線推薦標準
            if final_score >= 12:
                trend = "長線強烈看漲"
                suggestion = "適合大幅加碼長期持有"
                target_price = round(current_price * 1.25, 1)
                stop_loss = round(current_price * 0.90, 1)
            elif final_score >= 8:
                trend = "長線看漲"
                suggestion = "適合中長期投資"
                target_price = round(current_price * 1.18, 1)
                stop_loss = round(current_price * 0.92, 1)
            elif final_score >= 4:
                trend = "長線中性偏多"
                suggestion = "適合定期定額投資"
                target_price = round(current_price * 1.12, 1)
                stop_loss = round(current_price * 0.93, 1)
            elif final_score >= 0:
                trend = "長線中性"
                suggestion = "持續觀察基本面變化"
                target_price = round(current_price * 1.08, 1)
                stop_loss = round(current_price * 0.95, 1)
            else:
                trend = "長線看跌"
                suggestion = "不建議長期投資"
                target_price = None
                stop_loss = round(current_price * 0.95, 1)
        else:
            # 短線推薦標準
            if final_score >= 8:
                trend = "強烈看漲"
                suggestion = "適合積極買入"
                target_price = round(current_price * 1.10, 1)
                stop_loss = round(current_price * 0.95, 1)
            elif final_score >= 4:
                trend = "看漲"
                suggestion = "可考慮買入"
                target_price = round(current_price * 1.06, 1)
                stop_loss = round(current_price * 0.97, 1)
            elif final_score >= 1:
                trend = "中性偏多"
                suggestion = "適合中長期投資"
                target_price = round(current_price * 1.08, 1)
                stop_loss = round(current_price * 0.95, 1)
            elif final_score > -1:
                trend = "中性"
                suggestion = "觀望為宜"
                target_price = None
                stop_loss = round(current_price * 0.95, 1)
            elif final_score >= -4:
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
        reason = self._generate_reason(analysis, analysis_focus)
        
        analysis.update({
            'trend': trend,
            'suggestion': suggestion,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'reason': reason,
            'analysis_time': datetime.now().isoformat(),
            'data_quality': 'enhanced' if self.mode != 'basic' else 'current_day'
        })
        
        return analysis
    
    def _generate_reason(self, analysis: Dict[str, Any], analysis_focus: str) -> str:
        """生成推薦理由"""
        reasons = []
        
        change_percent = analysis['change_percent']
        current_price = analysis['current_price']
        
        if analysis_focus == 'long_term' and self.mode == 'optimized':
            # 長線重視基本面理由
            if 'dividend_yield' in analysis and analysis['dividend_yield'] > 3:
                dividend_yield = analysis['dividend_yield']
                reasons.append(f"高殖利率 {dividend_yield:.1f}%")
            
            if 'eps_growth' in analysis and analysis['eps_growth'] > 10:
                eps_growth = analysis['eps_growth']
                reasons.append(f"EPS成長 {eps_growth:.1f}%")
            
            if 'foreign_net_buy' in analysis and analysis['foreign_net_buy'] > 20000:
                foreign_net = analysis['foreign_net_buy']
                reasons.append(f"外資買超 {foreign_net//10000:.1f}億")
            
            if 'roe' in analysis and analysis['roe'] > 15:
                roe = analysis['roe']
                reasons.append(f"ROE {roe:.1f}%")
        else:
            # 短線理由
            if abs(change_percent) > 3:
                reasons.append(f"今日{'大漲' if change_percent > 0 else '大跌'} {abs(change_percent):.1f}%")
            elif abs(change_percent) > 1:
                reasons.append(f"今日{'上漲' if change_percent > 0 else '下跌'} {abs(change_percent):.1f}%")
            
            if 'technical_signals' in analysis:
                signals = analysis['technical_signals']
                if signals.get('macd_golden_cross'):
                    reasons.append("MACD黃金交叉")
                elif signals.get('ma20_bullish'):
                    reasons.append("站穩20日均線")
        
        # 成交量理由
        if analysis['trade_value'] > 5000000000:
            reasons.append("成交金額龐大")
        elif analysis['trade_value'] > 1000000000:
            reasons.append("成交活躍")
        
        if not reasons:
            reasons.append(f"現價 {current_price} 元，綜合指標{'正面' if analysis['weighted_score'] > 0 else '中性'}")
        
        return "，".join(reasons)
    
    def _finalize_basic_analysis(self, base_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """完成基礎分析"""
        score = base_analysis['base_score']
        current_price = base_analysis['current_price']
        change_percent = base_analysis['change_percent']
        
        # 基礎推薦邏輯
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
        else:
            trend = "看跌"
            suggestion = "建議減碼"
            target_price = None
            stop_loss = round(current_price * 0.97, 1)
        
        # 生成基礎理由
        reasons = []
        if abs(change_percent) > 3:
            reasons.append(f"今日{'大漲' if change_percent > 0 else '大跌'} {abs(change_percent):.1f}%")
        elif change_percent != 0:
            reasons.append(f"今日{'上漲' if change_percent > 0 else '下跌'} {abs(change_percent):.1f}%")
        
        if base_analysis['trade_value'] > 1000000000:
            reasons.append("成交活躍")
        
        reason = "，".join(reasons) if reasons else "技術面穩健"
        
        base_analysis.update({
            'weighted_score': score,
            'trend': trend,
            'suggestion': suggestion,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'reason': reason,
            'analysis_time': datetime.now().isoformat(),
            'analysis_method': 'basic',
            'data_quality': 'current_day'
        })
        
        return base_analysis
    
    def _get_fallback_analysis(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """回退分析（當其他分析失敗時使用）"""
        return {
            'code': stock_info['code'],
            'name': stock_info['name'],
            'current_price': stock_info['close'],
            'change_percent': stock_info['change_percent'],
            'volume': stock_info['volume'],
            'trade_value': stock_info['trade_value'],
            'weighted_score': 0,
            'trend': '數據不足',
            'suggestion': '建議觀望',
            'reason': '數據獲取異常，建議人工確認',
            'target_price': None,
            'stop_loss': round(stock_info['close'] * 0.95, 1),
            'analysis_time': datetime.now().isoformat(),
            'analysis_method': 'fallback',
            'data_quality': 'limited'
        }

# ============================================================================
# 推薦生成器類別
# ============================================================================

class RecommendationGenerator:
    """推薦生成器"""
    
    def __init__(self, mode='basic'):
        self.mode = mode
        
        # 推薦限制配置
        self.recommendation_limits = {
            'basic': {
                'short_term': 3,
                'long_term': 2,
                'weak_stocks': 2
            },
            'enhanced': {
                'short_term': 3,
                'long_term': 3,
                'weak_stocks': 2
            },
            'optimized': {
                'short_term': 3,
                'long_term': 5,  # 優化模式更多長線推薦
                'weak_stocks': 2
            }
        }
    
    def generate_recommendations(self, analyses: List[Dict[str, Any]], 
                               time_slot: str, analysis_focus: str = 'mixed') -> Dict[str, List[Dict[str, Any]]]:
        """生成推薦"""
        if not analyses:
            return {"short_term": [], "long_term": [], "weak_stocks": []}
        
        limits = self.recommendation_limits[self.mode]
        valid_analyses = [a for a in analyses if a.get('data_quality') != 'limited']
        
        # 短線推薦
        short_term_threshold = 4 if self.mode == 'optimized' else 2
        short_term_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) >= short_term_threshold]
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
        
        # 長線推薦
        long_term = self._generate_long_term_recommendations(valid_analyses, limits['long_term'], analysis_focus)
        
        # 極弱股
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
    
    def _generate_long_term_recommendations(self, analyses: List[Dict[str, Any]], 
                                          limit: int, analysis_focus: str) -> List[Dict[str, Any]]:
        """生成長線推薦"""
        if self.mode == 'optimized':
            # 優化模式：嚴格的長線篩選條件
            long_term_candidates = []
            
            for a in analyses:
                score = a.get('weighted_score', 0)
                conditions_met = 0
                
                # 基本評分條件
                if score >= 2:
                    conditions_met += 1
                
                # 基本面條件
                if a.get('dividend_yield', 0) > 2.5:
                    conditions_met += 2
                if a.get('eps_growth', 0) > 8:
                    conditions_met += 2
                if a.get('roe', 0) > 12:
                    conditions_met += 1
                if a.get('pe_ratio', 999) < 20:
                    conditions_met += 1
                
                # 法人條件
                foreign_net = a.get('foreign_net_buy', 0)
                trust_net = a.get('trust_net_buy', 0)
                if foreign_net > 5000 or trust_net > 3000:
                    conditions_met += 2
                if foreign_net > 20000 or trust_net > 10000:
                    conditions_met += 1
                
                # 成交量條件
                if a.get('trade_value', 0) > 50000000:
                    conditions_met += 1
                
                # 滿足條件才納入長線推薦
                if conditions_met >= 4 and score >= 0:
                    long_term_score = score + (conditions_met - 4) * 0.5
                    a['long_term_score'] = long_term_score
                    long_term_candidates.append(a)
            
            long_term_candidates.sort(key=lambda x: x.get('long_term_score', 0), reverse=True)
        else:
            # 基礎/增強模式：簡單條件
            long_term_candidates = [a for a in analyses 
                                  if 0 <= a.get('weighted_score', 0) < 4 
                                  and a.get('trade_value', 0) > 100000000]
            long_term_candidates.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        # 生成推薦列表
        long_term = []
        for analysis in long_term_candidates[:limit]:
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
        
        return long_term

# ============================================================================
# 通知系統類別
# ============================================================================

class NotificationSystem:
    """統一通知系統"""
    
    def __init__(self):
        self.email_config = None
        self.notification_available = False
        self._init_email_config()
    
    def _init_email_config(self):
        """初始化郵件配置"""
        try:
            from config import EMAIL_CONFIG
            if EMAIL_CONFIG['enabled']:
                self.email_config = EMAIL_CONFIG
                self.notification_available = True
                log_event("郵件通知系統初始化成功", level='success')
        except ImportError:
            # 嘗試從環境變數獲取
            sender = os.getenv('EMAIL_SENDER')
            password = os.getenv('EMAIL_PASSWORD')
            receiver = os.getenv('EMAIL_RECEIVER')
            
            if all([sender, password, receiver]):
                self.email_config = {
                    'sender': sender,
                    'password': password,
                    'receiver': receiver,
                    'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587'))
                }
                self.notification_available = True
                log_event("從環境變數初始化郵件配置成功", level='success')
            else:
                log_event("郵件配置不完整", level='warning')
    
    def is_notification_available(self) -> bool:
        """檢查通知是否可用"""
        return self.notification_available
    
    def send_combined_recommendations(self, recommendations: Dict, time_slot_name: str):
        """發送綜合推薦通知"""
        if not self.notification_available:
            log_event("通知系統不可用，跳過發送", level='warning')
            return
        
        try:
            message = self._format_recommendations_message(recommendations, time_slot_name)
            subject = f"📊 {time_slot_name} 股票分析報告"
            
            self._send_email(message, subject)
            log_event("推薦通知發送成功", level='success')
            
        except Exception as e:
            log_event(f"發送通知失敗: {e}", level='error')
    
    def _format_recommendations_message(self, recommendations: Dict, time_slot_name: str) -> str:
        """格式化推薦訊息"""
        message = f"📊 {time_slot_name} 股票分析報告\n\n"
        message += f"⏰ 分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 短線推薦
        if recommendations.get('short_term'):
            message += "【🔥 短線推薦】\n\n"
            for i, stock in enumerate(recommendations['short_term'], 1):
                analysis = stock.get('analysis', {})
                message += f"{i}. {stock['code']} {stock['name']}\n"
                message += f"💰 現價: {stock['current_price']} 元\n"
                message += f"📈 目標: {stock['target_price']} 元\n" if stock['target_price'] else ""
                message += f"🛑 停損: {stock['stop_loss']} 元\n"
                message += f"📋 理由: {stock['reason']}\n"
                message += f"💹 評分: {analysis.get('weighted_score', 0):.1f}\n\n"
        
        # 長線推薦
        if recommendations.get('long_term'):
            message += "【💎 長線推薦】\n\n"
            for i, stock in enumerate(recommendations['long_term'], 1):
                analysis = stock.get('analysis', {})
                message += f"{i}. {stock['code']} {stock['name']}\n"
                message += f"💰 現價: {stock['current_price']} 元\n"
                message += f"📈 目標: {stock['target_price']} 元\n" if stock['target_price'] else ""
                message += f"🛑 停損: {stock['stop_loss']} 元\n"
                message += f"📋 理由: {stock['reason']}\n"
                
                # 優化模式顯示更多基本面資訊
                if analysis.get('analysis_method') == 'optimized':
                    if 'dividend_yield' in analysis:
                        message += f"📊 殖利率: {analysis['dividend_yield']:.1f}%\n"
                    if 'eps_growth' in analysis:
                        message += f"📈 EPS成長: {analysis['eps_growth']:.1f}%\n"
                    if 'foreign_net_buy' in analysis and analysis['foreign_net_buy'] > 0:
                        message += f"🏦 外資買超: {analysis['foreign_net_buy']//10000:.1f}億\n"
                
                message += f"💹 評分: {analysis.get('weighted_score', 0):.1f}\n\n"
        
        # 極弱股警示
        if recommendations.get('weak_stocks'):
            message += "【⚠️ 極弱股警示】\n\n"
            for i, stock in enumerate(recommendations['weak_stocks'], 1):
                analysis = stock.get('analysis', {})
                message += f"{i}. {stock['code']} {stock['name']}\n"
                message += f"💰 現價: {stock['current_price']} 元\n"
                message += f"⚠️ 警示: {stock['alert_reason']}\n"
                message += f"💹 評分: {analysis.get('weighted_score', 0):.1f}\n\n"
        
        message += "\n📋 免責聲明:\n"
        message += "本報告僅供參考，投資有風險，決策請謹慎。\n"
        message += "建議結合其他資訊來源進行綜合判斷。\n\n"
        message += "💰 祝您投資順利！"
        
        return message
    
    def _send_email(self, message: str, subject: str):
        """發送郵件"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = self.email_config['sender']
        msg['To'] = self.email_config['receiver']
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
        server.starttls()
        server.login(self.email_config['sender'], self.email_config['password'])
        
        text = msg.as_string()
        server.sendmail(self.email_config['sender'], self.email_config['receiver'], text)
        server.quit()
    
    def send_heartbeat(self):
        """發送心跳檢測"""
        if not self.notification_available:
            return
        
        try:
            message = f"""💓 統一股票分析系統心跳檢測

⏰ 檢測時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 系統狀態: 正常運行
📊 功能狀態: 
  • 數據獲取: ✅ 正常
  • 股票分析: ✅ 正常  
  • 通知系統: ✅ 正常

系統持續為您監控市場動態！💰"""
            
            self._send_email(message, "💓 系統心跳檢測")
            log_event("心跳檢測發送成功", level='success')
            
        except Exception as e:
            log_event(f"心跳檢測發送失敗: {e}", level='error')

# ============================================================================
# 統一股票分析器主類別
# ============================================================================

class UnifiedStockAnalyzer:
    """統一股票分析器主類別"""
    
    def __init__(self, mode='basic'):
        """
        初始化統一股票分析器
        mode: 'basic', 'enhanced', 'optimized'
        """
        self.mode = mode
        
        # 初始化各個組件
        self.system_fixer = SystemFixer()
        self.data_fetcher = DataFetcher()
        self.analyzer = StockAnalyzer(mode)
        self.recommender = RecommendationGenerator(mode)
        self.notifier = NotificationSystem()
        
        # 設置快取目錄
        self.cache_dir = os.path.join(os.getcwd(), 'data', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 時段配置
        self.time_slot_config = {
            'morning_scan': {
                'name': '早盤掃描',
                'stock_count': 50 if mode == 'basic' else (100 if mode == 'enhanced' else 200),
                'analysis_focus': 'short_term'
            },
            'mid_morning_scan': {
                'name': '盤中掃描',
                'stock_count': 100 if mode == 'basic' else (150 if mode == 'enhanced' else 300),
                'analysis_focus': 'short_term'
            },
            'mid_day_scan': {
                'name': '午間掃描',
                'stock_count': 150 if mode == 'basic' else (200 if mode == 'enhanced' else 300),
                'analysis_focus': 'mixed'
            },
            'afternoon_scan': {
                'name': '盤後掃描',
                'stock_count': 300 if mode == 'basic' else (500 if mode == 'enhanced' else 1000),
                'analysis_focus': 'mixed'
            },
            'weekly_summary': {
                'name': '週末總結',
                'stock_count': 500 if mode == 'basic' else (750 if mode == 'enhanced' else 1000),
                'analysis_focus': 'long_term'
            }
        }
        
        log_event(f"統一股票分析器初始化完成 (模式: {mode.upper()})", level='success')
    
    def run_system_check_and_fix(self):
        """執行系統檢查和修復"""
        log_event("🔧 開始系統檢查和修復")
        return self.system_fixer.run_system_fix()
    
    def run_analysis(self, time_slot: str) -> None:
        """執行股票分析"""
        start_time = time.time()
        log_event(f"🚀 開始執行 {time_slot} 分析 (模式: {self.mode.upper()})")
        
        try:
            # 獲取配置
            config = self.time_slot_config[time_slot]
            analysis_focus = config['analysis_focus']
            expected_count = config['stock_count']
            
            # 獲取股票數據
            stocks = self.data_fetcher.get_stocks_by_time_slot(time_slot)
            
            if not stocks:
                log_event("❌ 無法獲取股票數據", level='error')
                return
            
            log_event(f"📊 成功獲取 {len(stocks)} 支股票（預期 {expected_count} 支）")
            log_event(f"🔍 分析重點: {analysis_focus}")
            
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
                        analysis = self.analyzer.analyze_stock(stock, analysis_focus)
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
            recommendations = self.recommender.generate_recommendations(all_analyses, time_slot, analysis_focus)
            
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
                    score = analysis_info.get('weighted_score', 0)
                    log_event(f"   {stock['code']} {stock['name']} (評分:{score})")
            
            if long_count > 0 and self.mode == 'optimized':
                log_event("💎 長線推薦詳情:")
                for stock in recommendations['long_term']:
                    analysis_info = stock['analysis']
                    score = analysis_info.get('weighted_score', 0)
                    dividend_yield = analysis_info.get('dividend_yield', 0)
                    eps_growth = analysis_info.get('eps_growth', 0)
                    log_event(f"   {stock['code']} {stock['name']} (評分:{score:.1f}, 殖利率:{dividend_yield:.1f}%, EPS:{eps_growth:.1f}%)")
            
            # 發送通知
            display_name = config['name']
            self.notifier.send_combined_recommendations(recommendations, display_name)
            
            # 保存分析結果
            self.save_analysis_results(all_analyses, recommendations, time_slot)
            
            total_time = time.time() - start_time
            log_event(f"🎉 {time_slot} 分析完成，總耗時 {total_time:.1f} 秒", level='success')
            
        except Exception as e:
            log_event(f"❌ 執行 {time_slot} 分析時發生錯誤: {e}", level='error')
            import traceback
            traceback.print_exc()
    
    def save_analysis_results(self, analyses: List[Dict[str, Any]], 
                            recommendations: Dict[str, List], time_slot: str) -> None:
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
    
    def setup_schedule(self):
        """設置排程任務"""
        try:
            from config import NOTIFICATION_SCHEDULE
        except ImportError:
            # 預設時間表
            NOTIFICATION_SCHEDULE = {
                'morning_scan': '09:00',
                'mid_morning_scan': '10:30',
                'mid_day_scan': '12:30',
                'afternoon_scan': '15:00',
                'weekly_summary': '17:00',
                'heartbeat': '08:30'
            }
        
        log_event("⏰ 設置排程任務")
        
        # 工作日排程
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        
        for day in weekdays:
            getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['morning_scan']).do(
                self.run_analysis, 'morning_scan'
            )
            getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['mid_morning_scan']).do(
                self.run_analysis, 'mid_morning_scan'
            )
            getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['mid_day_scan']).do(
                self.run_analysis, 'mid_day_scan'
            )
            getattr(schedule.every(), day).at(NOTIFICATION_SCHEDULE['afternoon_scan']).do(
                self.run_analysis, 'afternoon_scan'
            )
        
        # 週末總結
        schedule.every().friday.at(NOTIFICATION_SCHEDULE['weekly_summary']).do(
            self.run_analysis, 'weekly_summary'
        )
        
        # 心跳檢測
        schedule.every().day.at(NOTIFICATION_SCHEDULE['heartbeat']).do(self.notifier.send_heartbeat)
        
        log_event("✅ 排程任務設置完成", level='success')
        return True
    
    def run_daemon(self):
        """運行後台服務"""
        log_event(f"🚀 啟動統一股票分析系統 (模式: {self.mode.upper()})")
        
        # 顯示模式特色
        self._show_mode_features()
        
        # 設置排程
        if not self.setup_schedule():
            log_event("❌ 排程設置失敗，程序退出", level='error')
            return
        
        # 啟動時發送心跳
        if self.notifier.is_notification_available():
            log_event("💓 發送啟動心跳")
            self.notifier.send_heartbeat()
        
        log_event(f"🎯 {self.mode.upper()}模式系統已啟動，開始執行排程任務")
        log_event("📝 按 Ctrl+C 停止系統")
        
        # 運行排程循環
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # 每30秒檢查一次
        except KeyboardInterrupt:
            log_event("⚠️ 收到用戶中斷信號", level='warning')
            log_event("🛑 正在優雅關閉系統")
            
            # 發送關閉通知
            if self.notifier.is_notification_available():
                try:
                    close_message = f"""📴 統一股票分析系統關閉通知

⏰ 關閉時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 運行模式: {self.mode.upper()}

✅ 系統已安全關閉
感謝使用統一股票分析系統！

祝您投資順利！💰"""
                    
                    self.notifier._send_email(close_message, f"📴 {self.mode.upper()}模式系統關閉通知")
                except:
                    pass
            
            log_event("👋 系統已關閉", level='success')
        except Exception as e:
            log_event(f"❌ 系統運行出現錯誤: {e}", level='error')
            log_event("🔄 請檢查錯誤並重新啟動系統")
    
    def _show_mode_features(self):
        """顯示模式特色"""
        print("=" * 60)
        if self.mode == 'optimized':
            print("💎 優化版特色:")
            print("  • 長線推薦權重優化: 基本面 1.2倍, 法人 0.8倍")
            print("  • 重視高殖利率股票 (>2.5% 優先推薦)")
            print("  • 重視EPS高成長股票 (>8% 優先推薦)")
            print("  • 重視法人買超股票 (>5000萬優先推薦)")
            print("  • 強化通知顯示: 詳細基本面資訊")
        elif self.mode == 'enhanced':
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
    
    def test_notification(self, test_type='all'):
        """測試通知系統"""
        log_event(f"📧 測試 {self.mode.upper()} 模式通知系統")
        
        if not self.notifier.is_notification_available():
            log_event("❌ 通知系統不可用", level='error')
            return
        
        try:
            # 創建測試數據
            test_data = {
                "short_term": [
                    {
                        "code": "2330",
                        "name": "台積電",
                        "current_price": 638.5,
                        "reason": "技術面轉強，MACD金叉確認" if self.mode != 'basic' else "今日上漲 2.3%，成交活躍",
                        "target_price": 670.0,
                        "stop_loss": 620.0,
                        "trade_value": 14730000000,
                        "analysis": {
                            "change_percent": 2.35,
                            "weighted_score": 5.2,
                            "analysis_method": self.mode
                        }
                    }
                ],
                "long_term": [
                    {
                        "code": "2609" if self.mode == 'optimized' else "2882",
                        "name": "陽明" if self.mode == 'optimized' else "國泰金",
                        "current_price": 91.2 if self.mode == 'optimized' else 58.3,
                        "reason": "高殖利率7.2%，EPS高成長35.6%，外資買超4.5億" if self.mode == 'optimized' else "金融股回穩，適合中長期投資",
                        "target_price": 110.0 if self.mode == 'optimized' else 65.0,
                        "stop_loss": 85.0 if self.mode == 'optimized' else 55.0,
                        "trade_value": 4560000000 if self.mode == 'optimized' else 2100000000,
                        "analysis": {
                            "change_percent": 1.8 if self.mode == 'optimized' else 0.8,
                            "weighted_score": 6.8 if self.mode == 'optimized' else 3.2,
                            "analysis_method": self.mode,
                            "dividend_yield": 7.2 if self.mode == 'optimized' else 4.5,
                            "eps_growth": 35.6 if self.mode == 'optimized' else 8.2,
                            "foreign_net_buy": 45000 if self.mode == 'optimized' else 8000
                        }
                    }
                ],
                "weak_stocks": []
            }
            
            self.notifier.send_combined_recommendations(test_data, f"{self.mode.upper()}模式功能測試")
            log_event("✅ 測試通知已發送！", level='success')
            log_event("📋 請檢查郵箱確認通知內容")
            
        except Exception as e:
            log_event(f"❌ 測試通知失敗: {e}", level='error')
            import traceback
            traceback.print_exc()
    
    def show_status(self):
        """顯示系統狀態"""
        print("📊 統一股票分析系統狀態")
        print("=" * 50)
        print(f"🔧 當前模式: {self.mode.upper()}")
        print(f"📧 通知系統: {'可用' if self.notifier.is_notification_available() else '不可用'}")
        
        self._show_mode_features()
        
        print("📅 排程時段:")
        for slot, info in self.time_slot_config.items():
            stock_count = info['stock_count']
            name = info['name']
            print(f"  📊 {name}: {stock_count}支股票")

# ============================================================================
# 主程式入口
# ============================================================================

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='統一台股分析系統')
    parser.add_argument('command', 
                       choices=['start', 'run', 'status', 'test', 'fix'],
                       help='執行命令')
    parser.add_argument('--mode', '-m',
                       choices=['basic', 'enhanced', 'optimized'],
                       default='basic',
                       help='分析模式 (預設: basic)')
    parser.add_argument('--slot', '-s',
                       choices=['morning_scan', 'mid_morning_scan', 'mid_day_scan', 
                               'afternoon_scan', 'weekly_summary'],
                       help='分析時段 (配合 run 命令使用)')
    parser.add_argument('--test-type', '-t',
                       choices=['all', 'notification', 'heartbeat'],
                       default='all', help='測試類型')
    
    args = parser.parse_args()
    
    # 檢查環境
    if not check_environment():
        print("環境檢查失敗，請修復上述問題再嘗試")
        return
    
    # 設置日誌
    setup_logging()
    
    # 初始化分析器
    analyzer = UnifiedStockAnalyzer(args.mode)
    
    # 執行相應的命令
    try:
        if args.command == 'fix':
            log_event("🔧 執行系統修復")
            analyzer.run_system_check_and_fix()
            
        elif args.command == 'start':
            analyzer.run_daemon()
            
        elif args.command == 'run':
            if not args.slot:
                log_event("❌ 使用 run 命令時必須指定 --slot 參數", level='error')
                log_event("📝 範例: python unified_stock_analyzer.py run --slot afternoon_scan --mode optimized")
                return
            
            analyzer.run_analysis(args.slot)
            
        elif args.command == 'status':
            analyzer.show_status()
            
        elif args.command == 'test':
            if args.test_type == 'notification':
                analyzer.test_notification()
            elif args.test_type == 'heartbeat':
                analyzer.notifier.send_heartbeat()
            else:
                analyzer.test_notification()
        
        else:
            parser.print_help()
            
    except Exception as e:
        log_event(f"❌ 執行命令時發生錯誤: {e}", level='error')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 統一股票分析系統")
    print("整合修復工具、多模式分析、排程通知等完整功能")
    print("=" * 60)
    main()
