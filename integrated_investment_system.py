"""
integrated_investment_system.py - 整合全球投資分析系統
結合台股分析與全球經濟指標，提供完整投資視角
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 導入現有模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_stock_bot import EnhancedStockBot
    from global_economic_monitor import GlobalEconomicMonitor
    import notifier
    from config import STOCK_ANALYSIS
    TAIWAN_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 台股系統模組導入失敗: {e}")
    TAIWAN_SYSTEM_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegratedInvestmentSystem:
    """整合投資分析系統"""
    
    def __init__(self):
        """初始化整合投資系統"""
        self.global_monitor = GlobalEconomicMonitor()
        
        # 初始化台股系統（如果可用）
        if TAIWAN_SYSTEM_AVAILABLE:
            self.taiwan_bot = EnhancedStockBot()
            logger.info("✅ 台股分析系統已載入")
        else:
            self.taiwan_bot = None
            logger.warning("⚠️ 台股分析系統不可用")
        
        # 全球市場對台股的影響權重
        self.global_influence_weights = {
            'S&P500': 0.35,      # 美股對台股影響最大
            'NASDAQ': 0.25,      # 科技股指數重要
            'Nikkei225': 0.20,   # 日股區域影響
            'HSI': 0.15,         # 港股區域影響
            'VIX': -0.05         # 恐慌指數負影響
        }
        
        # 台股產業與全球指標關聯
        self.sector_correlations = {
            '半導體': ['NASDAQ', 'SOX'],  # SOX為費城半導體指數
            '電子': ['NASDAQ', 'S&P500'],
            '金融': ['US10Y', 'DXY'],     # 美債收益率、美元指數
            '航運': ['BDI'],              # 波羅的海乾散貨指數
            '傳產': ['Oil', 'Commodities'],
            'REIT': ['US10Y']
        }
        
        # 風險等級定義
        self.risk_levels = {
            'VERY_LOW': {'score_range': (0, 20), 'description': '極低風險'},
            'LOW': {'score_range': (20, 40), 'description': '低風險'},
            'MEDIUM': {'score_range': (40, 60), 'description': '中等風險'},
            'HIGH': {'score_range': (60, 80), 'description': '高風險'},
            'VERY_HIGH': {'score_range': (80, 100), 'description': '極高風險'}
        }
    
    def calculate_global_influence_on_taiwan(self) -> Dict[str, Any]:
        """計算全球市場對台股的影響分數"""
        logger.info("計算全球市場對台股影響...")
        
        # 獲取全球市場情緒
        global_sentiment = self.global_monitor.analyze_global_sentiment()
        
        # 計算影響分數
        influence_score = 0
        detailed_impacts = {}
        
        for region, performance in global_sentiment['regional_performance'].items():
            avg_change = performance['avg_change']
            
            # 計算各區域對台股的影響
            if region == 'US':
                impact = avg_change * 0.4  # 美國影響權重40%
                detailed_impacts['美國市場'] = {
                    'change': avg_change,
                    'impact_score': impact,
                    'description': '美股是台股最重要的領先指標'
                }
                influence_score += impact
                
            elif region == 'Japan':
                impact = avg_change * 0.2  # 日本影響權重20%
                detailed_impacts['日本市場'] = {
                    'change': avg_change,
                    'impact_score': impact,
                    'description': '日股與台股具有區域聯動性'
                }
                influence_score += impact
                
            elif region == 'China':
                impact = avg_change * 0.15  # 中國影響權重15%
                detailed_impacts['中國市場'] = {
                    'change': avg_change,
                    'impact_score': impact,
                    'description': '中國經濟影響台股基本面'
                }
                influence_score += impact
                
            elif region == 'HongKong':
                impact = avg_change * 0.1   # 香港影響權重10%
                detailed_impacts['香港市場'] = {
                    'change': avg_change,
                    'impact_score': impact,
                    'description': '港股與台股有資金流動關聯'
                }
                influence_score += impact
        
        # VIX恐慌指數影響
        vix_value = global_sentiment.get('vix_value', 20)
        vix_impact = -(vix_value - 20) * 0.1  # VIX每高於20，減少0.1分影響
        detailed_impacts['恐慌指數'] = {
            'vix_value': vix_value,
            'impact_score': vix_impact,
            'description': f'VIX={vix_value:.1f}，恐慌指數{"偏高" if vix_value > 25 else "正常" if vix_value > 15 else "偏低"}'
        }
        influence_score += vix_impact
        
        # 判斷影響等級
        if influence_score > 2:
            influence_level = "強烈正面"
            taiwan_outlook = "台股有望跟隨上漲"
        elif influence_score > 0.5:
            influence_level = "正面"
            taiwan_outlook = "台股偏向正面表現"
        elif influence_score > -0.5:
            influence_level = "中性"
            taiwan_outlook = "台股可能盤整為主"
        elif influence_score > -2:
            influence_level = "負面"
            taiwan_outlook = "台股面臨下跌壓力"
        else:
            influence_level = "強烈負面"
            taiwan_outlook = "台股可能大幅下跌"
        
        return {
            'influence_score': round(influence_score, 2),
            'influence_level': influence_level,
            'taiwan_outlook': taiwan_outlook,
            'detailed_impacts': detailed_impacts,
            'global_sentiment_score': global_sentiment['global_sentiment_score'],
            'analysis_time': datetime.now().isoformat()
        }
    
    def get_sector_specific_analysis(self, sector: str) -> Dict[str, Any]:
        """獲取特定產業的全球關聯分析"""
        if sector not in self.sector_correlations:
            return {'error': f'不支援的產業: {sector}'}
        
        related_indices = self.sector_correlations[sector]
        
        # 這裡可以擴展獲取相關指數的即時數據
        # 目前提供概念性分析
        
        analysis = {
            'sector': sector,
            'related_global_indices': related_indices,
            'analysis_points': []
        }
        
        if sector == '半導體':
            analysis['analysis_points'] = [
                "密切關注費城半導體指數(SOX)走勢",
                "美國科技股表現直接影響台積電等龍頭股",
                "中美科技戰發展影響產業前景"
            ]
        elif sector == '金融':
            analysis['analysis_points'] = [
                "美債收益率上升通常利好金融股",
                "美元走強影響台灣金融業獲利",
                "聯準會貨幣政策是關鍵變數"
            ]
        elif sector == '航運':
            analysis['analysis_points'] = [
                "波羅的海乾散貨指數反映航運需求",
                "全球貿易量變化影響航運獲利",
                "原油價格影響航運成本"
            ]
        
        return analysis
    
    def generate_risk_assessment(self) -> Dict[str, Any]:
        """生成綜合風險評估"""
        logger.info("生成綜合風險評估...")
        
        risk_factors = []
        risk_score = 0
        
        # 全球市場風險
        global_sentiment = self.global_monitor.analyze_global_sentiment()
        global_score = global_sentiment['global_sentiment_score']
        vix_value = global_sentiment.get('vix_value', 20)
        
        # VIX風險評估
        if vix_value > 30:
            risk_score += 25
            risk_factors.append(f"VIX恐慌指數高達{vix_value:.1f}，市場恐慌情緒濃厚")
        elif vix_value > 25:
            risk_score += 15
            risk_factors.append(f"VIX指數{vix_value:.1f}，市場波動性增加")
        elif vix_value < 12:
            risk_score += 10
            risk_factors.append(f"VIX指數過低({vix_value:.1f})，市場可能過度樂觀")
        
        # 全球情緒風險
        if global_score < -2:
            risk_score += 20
            risk_factors.append("全球市場情緒悲觀，系統性風險上升")
        elif global_score > 3:
            risk_score += 10
            risk_factors.append("全球市場可能過熱，注意回檔風險")
        
        # 區域風險評估
        regional_perf = global_sentiment['regional_performance']
        us_performance = regional_perf.get('US', {}).get('avg_change', 0)
        
        if us_performance < -2:
            risk_score += 15
            risk_factors.append("美股大跌，台股面臨跟跌壓力")
        
        # 相關性風險
        correlation_analysis = self.global_monitor.get_correlation_analysis()
        high_correlations = 0
        
        for pair, data in correlation_analysis['correlations'].items():
            if abs(data['correlation']) > 0.8:
                high_correlations += 1
        
        if high_correlations > 2:
            risk_score += 10
            risk_factors.append(f"發現{high_correlations}組高度相關資產，分散風險效果降低")
        
        # 經濟事件風險
        economic_events = self.global_monitor.get_economic_calendar()
        high_impact_events = [e for e in economic_events if e['importance'] == 'HIGH']
        
        if len(high_impact_events) > 0:
            risk_score += 5
            risk_factors.append(f"未來一週內有{len(high_impact_events)}個重要經濟事件")
        
        # 確定風險等級
        risk_level = 'MEDIUM'
        for level, config in self.risk_levels.items():
            if config['score_range'][0] <= risk_score < config['score_range'][1]:
                risk_level = level
                break
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_description': self.risk_levels[risk_level]['description'],
            'risk_factors': risk_factors,
            'recommendations': self._generate_risk_recommendations(risk_level, risk_score),
            'assessment_time': datetime.now().isoformat()
        }
    
    def _generate_risk_recommendations(self, risk_level: str, risk_score: int) -> List[str]:
        """根據風險等級生成建議"""
        recommendations = []
        
        if risk_level in ['VERY_HIGH', 'HIGH']:
            recommendations.extend([
                "建議降低股票配置至30-50%",
                "增加債券、黃金等避險資產",
                "避免使用槓桿交易",
                "密切關注全球經濟指標變化"
            ])
        elif risk_level == 'MEDIUM':
            recommendations.extend([
                "維持均衡的投資組合配置",
                "適度分散投資降低風險",
                "設定停損點控制下跌風險",
                "關注主要經濟事件影響"
            ])
        else:  # LOW, VERY_LOW
            recommendations.extend([
                "可適度增加成長型股票配置",
                "考慮定期定額投資策略",
                "仍需保持適當分散投資",
                "持續監控市場變化"
            ])
        
        # 特殊情況的額外建議
        if risk_score > 60:
            recommendations.append("考慮暫時轉為保守策略，等待市場明朗")
        
        return recommendations
    
    def generate_integrated_investment_report(self, time_slot: str = 'comprehensive') -> Dict[str, Any]:
        """生成整合投資報告"""
        logger.info("生成整合投資報告...")
        
        report = {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'analysis_scope': '全球市場 + 台股分析',
            'time_slot': time_slot
        }
        
        try:
            # 1. 全球市場分析
            logger.info("進行全球市場分析...")
            global_analysis = self.global_monitor.generate_daily_report()
            report['global_analysis'] = global_analysis
            
            # 2. 全球對台股影響分析
            logger.info("分析全球市場對台股影響...")
            taiwan_influence = self.calculate_global_influence_on_taiwan()
            report['taiwan_influence'] = taiwan_influence
            
            # 3. 風險評估
            logger.info("進行風險評估...")
            risk_assessment = self.generate_risk_assessment()
            report['risk_assessment'] = risk_assessment
            
            # 4. 台股分析（如果系統可用）
            if self.taiwan_bot and time_slot != 'global_only':
                logger.info("進行台股分析...")
                try:
                    # 這裡整合現有的台股分析
                    taiwan_analysis = self._get_taiwan_stock_analysis(time_slot)
                    report['taiwan_analysis'] = taiwan_analysis
                except Exception as e:
                    logger.error(f"台股分析失敗: {e}")
                    report['taiwan_analysis'] = {'error': str(e)}
            
            # 5. 整合投資建議
            logger.info("生成整合投資建議...")
            integrated_recommendations = self._generate_integrated_recommendations(
                global_analysis, taiwan_influence, risk_assessment
            )
            report['integrated_recommendations'] = integrated_recommendations
            
            # 6. 產業焦點分析
            sector_focus = self._analyze_sector_focus()
            report['sector_focus'] = sector_focus
            
        except Exception as e:
            logger.error(f"生成報告時發生錯誤: {e}")
            report['error'] = str(e)
        
        return report
    
    def _get_taiwan_stock_analysis(self, time_slot: str) -> Dict[str, Any]:
        """獲取台股分析結果"""
        # 調用現有的台股分析系統
        stocks = self.taiwan_bot.get_stocks_for_analysis(time_slot)
        
        if not stocks:
            return {'error': '無法獲取台股數據'}
        
        # 分析前50支股票（避免過度耗時）
        analysis_stocks = stocks[:50]
        analyses = []
        
        for stock in analysis_stocks:
            try:
                analysis = self.taiwan_bot.analyze_stock_enhanced(stock, 'mixed')
                analyses.append(analysis)
            except Exception as e:
                logger.warning(f"分析股票 {stock['code']} 失敗: {e}")
                continue
        
        # 生成推薦
        recommendations = self.taiwan_bot.generate_recommendations(analyses, time_slot)
        
        return {
            'total_analyzed': len(analyses),
            'recommendations': recommendations,
            'market_summary': {
                'total_stocks': len(stocks),
                'analyzed_count': len(analyses),
                'short_term_count': len(recommendations['short_term']),
                'long_term_count': len(recommendations['long_term']),
                'weak_stocks_count': len(recommendations['weak_stocks'])
            }
        }
    
    def _generate_integrated_recommendations(self, global_analysis, taiwan_influence, risk_assessment) -> Dict[str, Any]:
        """生成整合投資建議"""
        recommendations = {
            'overall_strategy': '',
            'asset_allocation': {},
            'specific_actions': [],
            'timing_suggestions': [],
            'risk_management': []
        }
        
        # 基於全球分析和風險評估決定整體策略
        global_score = global_analysis['sentiment_analysis']['global_sentiment_score']
        risk_level = risk_assessment['risk_level']
        taiwan_outlook = taiwan_influence['taiwan_outlook']
        
        # 整體策略
        if global_score > 1 and risk_level in ['LOW', 'VERY_LOW']:
            recommendations['overall_strategy'] = "積極成長策略"
            recommendations['asset_allocation'] = {
                '股票': '70-80%',
                '債券': '15-20%',
                '現金': '5-10%',
                '替代投資': '0-5%'
            }
        elif global_score > -1 and risk_level == 'MEDIUM':
            recommendations['overall_strategy'] = "平衡策略"
            recommendations['asset_allocation'] = {
                '股票': '50-60%',
                '債券': '25-35%',
                '現金': '10-15%',
                '替代投資': '5-10%'
            }
        else:
            recommendations['overall_strategy'] = "保守策略"
            recommendations['asset_allocation'] = {
                '股票': '30-40%',
                '債券': '40-50%',
                '現金': '15-25%',
                '避險資產': '5-10%'
            }
        
        # 具體行動建議
        if taiwan_influence['influence_level'] in ['強烈正面', '正面']:
            recommendations['specific_actions'].append("可適度增加台股配置")
            
        if risk_assessment['risk_score'] > 60:
            recommendations['specific_actions'].append("建議暫停新增投資，等待市場明朗")
        
        # 時機建議
        vix_value = global_analysis['sentiment_analysis'].get('vix_value', 20)
        if vix_value > 30:
            recommendations['timing_suggestions'].append("恐慌指數高，可考慮分批逢低布局")
        elif vix_value < 15:
            recommendations['timing_suggestions'].append("市場樂觀，注意獲利了結時機")
        
        # 風險管理
        recommendations['risk_management'] = risk_assessment['recommendations']
        
        return recommendations
    
    def _analyze_sector_focus(self) -> Dict[str, Any]:
        """分析產業焦點"""
        # 基於全球市場表現分析各產業機會
        sector_analysis = {}
        
        # 科技產業
        sector_analysis['科技股'] = {
            'global_drivers': ['NASDAQ表現', '美國科技股走勢'],
            'taiwan_stocks': ['台積電', '聯發科', '鴻海'],
            'outlook': '全球科技股復甦，台灣科技股有望受惠',
            'key_risks': '中美科技戰、利率政策'
        }
        
        # 金融產業
        sector_analysis['金融股'] = {
            'global_drivers': ['美債收益率', '聯準會政策'],
            'taiwan_stocks': ['國泰金', '富邦金', '中信金'],
            'outlook': '利率環境影響獲利表現',
            'key_risks': '經濟衰退、信用風險'
        }
        
        return sector_analysis
    
    def send_integrated_notification(self, report: Dict[str, Any]) -> bool:
        """發送整合分析通知"""
        if not TAIWAN_SYSTEM_AVAILABLE:
            logger.warning("通知系統不可用")
            return False
        
        try:
            # 生成通知內容
            subject = f"【全球投資分析】{report['report_date']} 整合報告"
            
            message = f"""📊 全球投資分析報告
            
🌍 全球市場摘要:
{report['global_analysis']['summary']}

🇹🇼 對台股影響:
• 影響程度: {report['taiwan_influence']['influence_level']}
• 台股展望: {report['taiwan_influence']['taiwan_outlook']}
• 影響評分: {report['taiwan_influence']['influence_score']}

⚠️ 風險評估:
• 風險等級: {report['risk_assessment']['risk_description']}
• 風險評分: {report['risk_assessment']['risk_score']}/100

💡 投資建議:
• 整體策略: {report['integrated_recommendations']['overall_strategy']}
• 資產配置: {report['integrated_recommendations']['asset_allocation']}

本報告整合全球經濟指標與台股分析，提供完整投資視角。
詳細內容請參考完整報告。

⚠️ 投資有風險，請謹慎評估後做決定。
            """
            
            # 發送通知
            notifier.init()
            success = notifier.send_notification(message, subject)
            
            if success:
                logger.info("整合分析通知發送成功")
            else:
                logger.error("整合分析通知發送失敗")
            
            return success
            
        except Exception as e:
            logger.error(f"發送通知時發生錯誤: {e}")
            return False

# 主要執行函數
def run_integrated_analysis(time_slot: str = 'comprehensive', send_notification: bool = True) -> Dict[str, Any]:
    """執行整合分析"""
    print("🌍 啟動整合全球投資分析系統")
    print("=" * 60)
    
    try:
        # 創建整合系統
        system = IntegratedInvestmentSystem()
        
        # 生成整合報告
        print("📊 生成整合投資報告...")
        report = system.generate_integrated_investment_report(time_slot)
        
        # 顯示報告摘要
        print("\n" + "=" * 60)
        print("📋 整合分析報告摘要")
        print("=" * 60)
        
        if 'global_analysis' in report:
            print(f"🌏 全球市場情緒: {report['global_analysis']['sentiment_analysis']['sentiment']}")
            print(f"📊 全球評分: {report['global_analysis']['sentiment_analysis']['global_sentiment_score']:.1f}")
        
        if 'taiwan_influence' in report:
            print(f"🇹🇼 對台股影響: {report['taiwan_influence']['influence_level']}")
            print(f"💭 台股展望: {report['taiwan_influence']['taiwan_outlook']}")
        
        if 'risk_assessment' in report:
            print(f"⚠️ 風險等級: {report['risk_assessment']['risk_description']}")
            print(f"🎯 風險評分: {report['risk_assessment']['risk_score']}/100")
        
        if 'integrated_recommendations' in report:
            print(f"💡 投資策略: {report['integrated_recommendations']['overall_strategy']}")
        
        # 發送通知（如果啟用）
        if send_notification:
            print(f"\n📧 發送整合分析通知...")
            system.send_integrated_notification(report)
        
        print(f"\n✅ 整合分析完成！")
        return report
        
    except Exception as e:
        print(f"❌ 整合分析失敗: {e}")
        logger.error(f"整合分析失敗: {e}")
        return {'error': str(e)}

# 命令行界面
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='整合全球投資分析系統')
    parser.add_argument('--time-slot', '-t', 
                       choices=['morning_scan', 'afternoon_scan', 'comprehensive', 'global_only'],
                       default='comprehensive',
                       help='分析時段')
    parser.add_argument('--no-notification', '-n', action='store_true',
                       help='不發送通知')
    
    args = parser.parse_args()
    
    # 執行整合分析
    report = run_integrated_analysis(
        time_slot=args.time_slot,
        send_notification=not args.no_notification
    )
    
    # 保存報告
    if 'error' not in report:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"integrated_report_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📄 報告已保存: {filename}")
        except Exception as e:
            print(f"⚠️ 保存報告失敗: {e}")
    
    print(f"\n🎯 使用說明:")
    print(f"1. 執行完整分析: python integrated_investment_system.py")
    print(f"2. 僅全球分析: python integrated_investment_system.py -t global_only")
    print(f"3. 不發送通知: python integrated_investment_system.py -n")
    print(f"4. 建議每日運行以獲得最新投資洞察")
