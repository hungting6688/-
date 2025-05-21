"""
stock_analyzer_integrator.py - 整合進階分析模組
將進階股票分析功能整合到主程序
"""
import os
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

# 嘗試導入進階分析模組
try:
    from stock_analyzers import AdvancedStockAnalyzer
    ADVANCED_ANALYSIS_AVAILABLE = True
except ImportError:
    ADVANCED_ANALYSIS_AVAILABLE = False

# 配置日誌
logger = logging.getLogger(__name__)

class StockAnalyzerIntegrator:
    """股票分析整合器"""
    
    def __init__(self, data_dir='data'):
        """
        初始化分析整合器
        
        參數:
        - data_dir: 數據目錄
        """
        self.data_dir = data_dir
        
        # 初始化進階分析器
        if ADVANCED_ANALYSIS_AVAILABLE:
            try:
                self.advanced_analyzer = AdvancedStockAnalyzer(data_dir=data_dir)
                logger.info("已啟用進階分析功能")
            except Exception as e:
                logger.error(f"初始化進階分析器失敗: {e}")
                self.advanced_analyzer = None
                ADVANCED_ANALYSIS_AVAILABLE = False
        else:
            self.advanced_analyzer = None
            logger.info("進階分析功能未啟用 (未找到 stock_analyzers 模組)")
    
    def get_stock_list_for_time_slot(self, time_slot: str, all_stocks: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        根據時段選擇要分析的股票
        
        參數:
        - time_slot: 時段名稱
        - all_stocks: 所有股票列表
        
        返回:
        - 選擇的股票列表
        """
        # 嘗試從配置中獲取掃描限制
        try:
            from config import STOCK_ANALYSIS
            scan_limits = STOCK_ANALYSIS.get('scan_limits', {})
            limit = scan_limits.get(time_slot, 100)
        except (ImportError, AttributeError):
            # 使用默認值
            if time_slot == 'morning_scan':
                limit = 100
            elif time_slot in ['mid_morning_scan', 'mid_day_scan']:
                limit = 150
            elif time_slot == 'afternoon_scan':
                limit = 450
            else:
                limit = 100
        
        logger.info(f"時段 {time_slot} 將掃描 {limit} 支股票")
        
        # 如果有進階分析器，使用市值排序選擇股票
        if ADVANCED_ANALYSIS_AVAILABLE and self.advanced_analyzer:
            try:
                return self.advanced_analyzer.select_stocks_for_analysis(all_stocks, limit=limit)
            except Exception as e:
                logger.error(f"使用進階分析器選擇股票失敗: {e}")
        
        # 如果進階分析器不可用或失敗，簡單返回前N支股票
        return all_stocks[:min(limit, len(all_stocks))]
    
    def get_recommendation_limits(self, time_slot: str) -> Dict[str, int]:
        """
        獲取推薦數量限制
        
        參數:
        - time_slot: 時段名稱
        
        返回:
        - 推薦數量限制字典
        """
        # 嘗試從配置中獲取推薦限制
        try:
            from config import STOCK_ANALYSIS
            rec_limits = STOCK_ANALYSIS.get('recommendation_limits', {}).get(time_slot, {})
            if not rec_limits:
                # 使用默認值
                rec_limits = {
                    'long_term': 3,
                    'short_term': 3,
                    'weak_stocks': 0
                }
        except (ImportError, AttributeError):
            # 使用默認值
            if time_slot == 'morning_scan':
                rec_limits = {
                    'long_term': 2,
                    'short_term': 3,
                    'weak_stocks': 2
                }
            elif time_slot == 'mid_morning_scan':
                rec_limits = {
                    'long_term': 3,
                    'short_term': 2,
                    'weak_stocks': 0
                }
            elif time_slot == 'mid_day_scan':
                rec_limits = {
                    'long_term': 3,
                    'short_term': 2,
                    'weak_stocks': 0
                }
            elif time_slot == 'afternoon_scan':
                rec_limits = {
                    'long_term': 3,
                    'short_term': 3,
                    'weak_stocks': 0
                }
            else:
                rec_limits = {
                    'long_term': 3,
                    'short_term': 3,
                    'weak_stocks': 2
                }
        
        return rec_limits
    
    def enhance_stock_analysis(self, 
                              stock_data: pd.DataFrame, 
                              technical_analysis: Dict[str, Any],
                              analysis_type: str = 'short_term') -> Dict[str, Any]:
        """
        增強股票分析，整合多種分析方法
        
        參數:
        - stock_data: 股票價格數據
        - technical_analysis: 技術分析結果
        - analysis_type: 分析類型 ('short_term' 或 'long_term')
        
        返回:
        - 增強的分析結果
        """
        # 如果進階分析器不可用，直接返回原始技術分析
        if not ADVANCED_ANALYSIS_AVAILABLE or not self.advanced_analyzer:
            return technical_analysis
        
        try:
            # 獲取股票代碼
            stock_code = technical_analysis.get('code')
            
            # 分析基本面
            fundamental_analysis = self.advanced_analyzer.analyze_fundamental(stock_code)
            
            # 分析相對強弱
            rs_analysis = self.advanced_analyzer.analyze_relative_strength(stock_data)
            
            # 整合分析
            enhanced_analysis = self.advanced_analyzer.analyze_stock_comprehensive(
                technical_data=technical_analysis,
                fundamental_data=fundamental_analysis,
                rs_data=rs_analysis,
                analysis_type=analysis_type
            )
            
            # 保留原始的技術指標信號
            enhanced_analysis['signals'] = technical_analysis.get('signals', {})
            
            # 如果有基本面數據，添加到增強分析結果
            if fundamental_analysis and 'fundamental_score' in fundamental_analysis:
                for key in ['pe_ratio', 'pb_ratio', 'dividend_yield', 'eps', 'eps_growth', 'roe']:
                    if key in fundamental_analysis:
                        enhanced_analysis[key] = fundamental_analysis[key]
            
            # 如果有相對強弱數據，添加到增強分析結果
            if rs_analysis and 'rs_score' in rs_analysis:
                enhanced_analysis['rs_score'] = rs_analysis['rs_score']
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"增強股票分析失敗: {e}")
            # 失敗時返回原始技術分析
            return technical_analysis
    
    def update_fundamental_data(self, stock_code: str, data: Dict[str, Any]) -> None:
        """
        更新股票基本面數據
        
        參數:
        - stock_code: 股票代碼
        - data: 基本面數據
        """
        if ADVANCED_ANALYSIS_AVAILABLE and self.advanced_analyzer:
            try:
                self.advanced_analyzer.update_stock_fundamental(stock_code, data)
                logger.info(f"已更新股票 {stock_code} 的基本面數據")
            except Exception as e:
                logger.error(f"更新基本面數據失敗: {e}")
    
    def fetch_taiwan_stocks(self) -> List[Dict[str, str]]:
        """
        獲取台灣股市的股票列表
        
        返回:
        - 股票列表
        """
        if ADVANCED_ANALYSIS_AVAILABLE and self.advanced_analyzer:
            try:
                # 獲取上市股票
                tse_stocks = self.advanced_analyzer.fetch_taiwan_stocks_list(market_type='TSE')
                logger.info(f"已獲取 {len(tse_stocks)} 支上市股票")
                
                # 獲取上櫃股票
                otc_stocks = self.advanced_analyzer.fetch_taiwan_stocks_list(market_type='OTC')
                logger.info(f"已獲取 {len(otc_stocks)} 支上櫃股票")
                
                # 合併股票列表
                all_stocks = tse_stocks + otc_stocks
                
                return all_stocks
            except Exception as e:
                logger.error(f"獲取台灣股票列表失敗: {e}")
        
        # 如果進階分析器不可用或獲取失敗，從本地文件加載
        try:
            stock_list_path = os.path.join(self.data_dir, 'stock_list.json')
            if os.path.exists(stock_list_path):
                with open(stock_list_path, 'r', encoding='utf-8') as f:
                    stocks = json.load(f)
                logger.info(f"從本地文件加載 {len(stocks)} 支股票")
                return stocks
        except Exception as e:
            logger.error(f"從本地文件加載股票列表失敗: {e}")
        
        # 如果都失敗，返回默認的股票列表
        default_stocks = [
            {"code": "2330", "name": "台積電"},
            {"code": "2317", "name": "鴻海"},
            {"code": "2454", "name": "聯發科"},
            {"code": "2412", "name": "中華電"},
            {"code": "2308", "name": "台達電"},
            {"code": "2303", "name": "聯電"},
            {"code": "1301", "name": "台塑"},
            {"code": "1303", "name": "南亞"},
            {"code": "2002", "name": "中鋼"},
            {"code": "2882", "name": "國泰金"}
        ]
        logger.warning(f"使用默認的股票列表 ({len(default_stocks)} 支股票)")
        return default_stocks

# 如果直接運行此文件，則執行測試
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 創建分析整合器
    integrator = StockAnalyzerIntegrator()
    
    # 獲取台灣股票列表
    stocks = integrator.fetch_taiwan_stocks()
    print(f"獲取到 {len(stocks)} 支股票")
    
    # 測試不同時段選擇股票
    time_slots = ['morning_scan', 'mid_morning_scan', 'mid_day_scan', 'afternoon_scan']
    for slot in time_slots:
        selected = integrator.get_stock_list_for_time_slot(slot, stocks)
        print(f"時段 {slot}: 選擇 {len(selected)} 支股票")
        
        # 獲取推薦限制
        limits = integrator.get_recommendation_limits(slot)
        print(f"  推薦限制: 長線 {limits['long_term']}，短線 {limits['short_term']}，弱勢 {limits['weak_stocks']}")
