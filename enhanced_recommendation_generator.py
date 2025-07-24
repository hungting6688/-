"""
enhanced_recommendation_generator.py - 增強版推薦理由生成器
解決技術面理由單薄、法人買超缺乏脈絡、目標價無依據等問題
"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class EnhancedRecommendationGenerator:
    """增強版推薦理由生成器"""
    
    def __init__(self):
        """初始化生成器"""
        # 技術指標權重
        self.technical_weights = {
            'macd': 0.25,       # MACD權重
            'rsi': 0.20,        # RSI權重
            'ma_trend': 0.25,   # 均線趨勢權重
            'volume': 0.15,     # 成交量權重
            'price_action': 0.15 # 價格行為權重
        }
        
        # 行業常態成交金額(億元)
        self.industry_normal_volume = {
            '台積電': 150,
            '鴻海': 50,
            '聯發科': 60,
            '台達電': 20,
            '中華電': 15
        }
    
    def generate_enhanced_short_term_reason(self, analysis: Dict[str, Any]) -> str:
        """生成增強版短線推薦理由"""
        
        stock_name = analysis.get('name', '')
        current_price = analysis.get('current_price', 0)
        change_percent = analysis.get('change_percent', 0)
        
        # 收集技術指標證據
        technical_evidences = self._extract_technical_evidences(analysis)
        
        # 收集法人動向證據
        institutional_evidences = self._extract_institutional_evidences(analysis)
        
        # 收集成交量證據
        volume_evidences = self._extract_volume_evidences(analysis, stock_name)
        
        # 收集價格行為證據
        price_evidences = self._extract_price_action_evidences(analysis)
        
        # 組合推薦理由
        reason_parts = []
        
        # 1. 技術面核心理由
        if technical_evidences:
            tech_summary = self._summarize_technical_evidences(technical_evidences)
            reason_parts.append(f"技術面: {tech_summary}")
        
        # 2. 法人動向理由
        if institutional_evidences:
            inst_summary = self._summarize_institutional_evidences(institutional_evidences)
            reason_parts.append(f"法人動向: {inst_summary}")
        
        # 3. 成交量理由
        if volume_evidences:
            volume_summary = self._summarize_volume_evidences(volume_evidences)
            reason_parts.append(f"成交量: {volume_summary}")
        
        # 4. 價格動能理由
        if price_evidences:
            price_summary = self._summarize_price_evidences(price_evidences)
            reason_parts.append(f"價格動能: {price_summary}")
        
        # 如果沒有足夠證據，給予基本描述
        if not reason_parts:
            return f"今日上漲{abs(change_percent):.1f}%，綜合指標偏多"
        
        return "；".join(reason_parts)
    
    def generate_enhanced_long_term_reason(self, analysis: Dict[str, Any]) -> str:
        """生成增強版長線推薦理由"""
        
        # 收集基本面證據
        fundamental_evidences = self._extract_fundamental_evidences(analysis)
        
        # 收集法人持續性證據
        institutional_trend_evidences = self._extract_institutional_trend_evidences(analysis)
        
        # 收集估值證據
        valuation_evidences = self._extract_valuation_evidences(analysis)
        
        # 收集產業地位證據
        industry_evidences = self._extract_industry_evidences(analysis)
        
        # 組合長線理由
        reason_parts = []
        
        # 1. 基本面核心優勢
        if fundamental_evidences:
            fund_summary = self._summarize_fundamental_evidences(fundamental_evidences)
            reason_parts.append(f"基本面: {fund_summary}")
        
        # 2. 法人持續布局
        if institutional_trend_evidences:
            inst_trend_summary = self._summarize_institutional_trend_evidences(institutional_trend_evidences)
            reason_parts.append(f"法人布局: {inst_trend_summary}")
        
        # 3. 估值合理性
        if valuation_evidences:
            val_summary = self._summarize_valuation_evidences(valuation_evidences)
            reason_parts.append(f"估值: {val_summary}")
        
        # 4. 產業地位
        if industry_evidences:
            industry_summary = self._summarize_industry_evidences(industry_evidences)
            reason_parts.append(f"產業地位: {industry_summary}")
        
        if not reason_parts:
            return "基本面穩健，適合長期投資"
        
        return "；".join(reason_parts)
    
    def _extract_technical_evidences(self, analysis: Dict[str, Any]) -> List[str]:
        """提取技術指標證據"""
        evidences = []
        
        technical_signals = analysis.get('technical_signals', {})
        
        # MACD證據
        if technical_signals.get('macd_golden_cross'):
            macd_value = analysis.get('macd_value', 0)
            signal_value = analysis.get('macd_signal_value', 0)
            evidences.append(f"MACD金叉({macd_value:.3f}>{signal_value:.3f})")
        elif technical_signals.get('macd_bullish'):
            evidences.append("MACD轉強")
        
        # RSI證據
        rsi_value = analysis.get('rsi', 0)
        if rsi_value > 0:
            if 30 <= rsi_value <= 70:
                evidences.append(f"RSI健康({rsi_value:.0f})")
            elif rsi_value < 30:
                evidences.append(f"RSI超賣反彈({rsi_value:.0f})")
            elif rsi_value > 80:
                evidences.append(f"RSI過熱({rsi_value:.0f})")
        
        # 均線證據
        if technical_signals.get('ma20_bullish'):
            ma20_value = analysis.get('ma20_value', 0)
            current_price = analysis.get('current_price', 0)
            if ma20_value > 0:
                evidences.append(f"站穩20MA({current_price:.1f}>{ma20_value:.1f})")
        
        if technical_signals.get('ma_golden_cross'):
            evidences.append("均線多頭排列")
        
        # KD證據（如果有）
        if analysis.get('kd_golden_cross'):
            k_value = analysis.get('k_value', 0)
            d_value = analysis.get('d_value', 0)
            evidences.append(f"KD金叉({k_value:.0f}>{d_value:.0f})")
        
        return evidences
    
    def _extract_institutional_evidences(self, analysis: Dict[str, Any]) -> List[str]:
        """提取法人動向證據"""
        evidences = []
        
        foreign_net = analysis.get('foreign_net_buy', 0)
        trust_net = analysis.get('trust_net_buy', 0)
        consecutive_days = analysis.get('consecutive_buy_days', 0)
        
        # 外資證據
        if foreign_net > 50000:  # 5億以上
            if consecutive_days > 3:
                evidences.append(f"外資連{consecutive_days}日大買{foreign_net//10000:.1f}億")
            else:
                evidences.append(f"外資大買{foreign_net//10000:.1f}億")
        elif foreign_net > 10000:  # 1億以上
            if consecutive_days > 3:
                evidences.append(f"外資連{consecutive_days}日買超{foreign_net//10000:.1f}億")
            else:
                evidences.append(f"外資買超{foreign_net//10000:.1f}億")
        
        # 投信證據
        if trust_net > 20000:  # 2億以上
            evidences.append(f"投信大買{trust_net//10000:.1f}億")
        elif trust_net > 5000:  # 5000萬以上
            evidences.append(f"投信買超{trust_net//10000:.1f}億")
        
        # 三大法人合計
        total_net = foreign_net + trust_net + analysis.get('dealer_net_buy', 0)
        if total_net > 100000:  # 10億以上
            evidences.append(f"三大法人合計買超{total_net//10000:.1f}億")
        
        return evidences
    
    def _extract_volume_evidences(self, analysis: Dict[str, Any], stock_name: str) -> List[str]:
        """提取成交量證據"""
        evidences = []
        
        trade_value = analysis.get('trade_value', 0)
        volume_ratio = analysis.get('volume_ratio', 1)
        
        # 獲取該股票的常態成交金額
        normal_volume = self.industry_normal_volume.get(stock_name, 10)  # 預設10億
        
        trade_value_億 = trade_value / 100000000
        
        # 判斷是否顯著放大
        if trade_value_億 > normal_volume * 2:
            evidences.append(f"爆量{trade_value_億:.0f}億(常態{normal_volume}億)")
        elif trade_value_億 > normal_volume * 1.5:
            evidences.append(f"放量{trade_value_億:.0f}億(較常態+{(trade_value_億/normal_volume-1)*100:.0f}%)")
        elif volume_ratio > 2:
            evidences.append(f"成交量{volume_ratio:.1f}倍放大")
        
        return evidences
    
    def _extract_price_action_evidences(self, analysis: Dict[str, Any]) -> List[str]:
        """提取價格行為證據"""
        evidences = []
        
        change_percent = analysis.get('change_percent', 0)
        current_price = analysis.get('current_price', 0)
        
        # 價格突破證據
        resistance_level = analysis.get('resistance_level', 0)
        if resistance_level > 0 and current_price > resistance_level:
            evidences.append(f"突破壓力{resistance_level:.1f}")
        
        # 漲幅強度
        if change_percent > 5:
            evidences.append(f"強漲{change_percent:.1f}%")
        elif change_percent > 3:
            evidences.append(f"上漲{change_percent:.1f}%")
        
        return evidences
    
    def _extract_fundamental_evidences(self, analysis: Dict[str, Any]) -> List[str]:
        """提取基本面證據"""
        evidences = []
        
        # 殖利率證據
        dividend_yield = analysis.get('dividend_yield', 0)
        if dividend_yield > 5:
            evidences.append(f"高殖利率{dividend_yield:.1f}%")
        elif dividend_yield > 3:
            evidences.append(f"殖利率{dividend_yield:.1f}%")
        
        # EPS成長證據
        eps_growth = analysis.get('eps_growth', 0)
        if eps_growth > 20:
            evidences.append(f"EPS高成長{eps_growth:.1f}%")
        elif eps_growth > 10:
            evidences.append(f"EPS成長{eps_growth:.1f}%")
        
        # ROE證據
        roe = analysis.get('roe', 0)
        if roe > 15:
            evidences.append(f"ROE優異{roe:.1f}%")
        elif roe > 10:
            evidences.append(f"ROE良好{roe:.1f}%")
        
        # 連續配息證據
        dividend_years = analysis.get('dividend_consecutive_years', 0)
        if dividend_years > 10:
            evidences.append(f"連續{dividend_years}年配息")
        elif dividend_years > 5:
            evidences.append(f"穩定配息{dividend_years}年")
        
        return evidences
    
    def _extract_valuation_evidences(self, analysis: Dict[str, Any]) -> List[str]:
        """提取估值證據"""
        evidences = []
        
        pe_ratio = analysis.get('pe_ratio', 0)
        pb_ratio = analysis.get('pb_ratio', 0)
        
        if pe_ratio > 0:
            if pe_ratio < 12:
                evidences.append(f"低本益比{pe_ratio:.1f}倍")
            elif pe_ratio < 18:
                evidences.append(f"合理本益比{pe_ratio:.1f}倍")
        
        if pb_ratio > 0 and pb_ratio < 1.5:
            evidences.append(f"淨值比偏低{pb_ratio:.1f}")
        
        return evidences
    
    def calculate_enhanced_target_price(self, analysis: Dict[str, Any], analysis_type: str) -> Optional[float]:
        """計算增強版目標價（含估值邏輯）"""
        current_price = analysis.get('current_price', 0)
        if current_price <= 0:
            return None
        
        # 短線目標價（技術分析為主）
        if analysis_type == 'short_term':
            # 技術壓力位
            resistance_level = analysis.get('resistance_level', 0)
            if resistance_level > current_price:
                return round(resistance_level * 0.95, 1)  # 接近壓力位
            
            # 基於漲幅和技術強度
            technical_strength = self._calculate_technical_strength(analysis)
            if technical_strength > 0.8:
                return round(current_price * 1.10, 1)  # 強勢股10%
            elif technical_strength > 0.6:
                return round(current_price * 1.06, 1)  # 中強勢6%
            else:
                return round(current_price * 1.03, 1)  # 溫和3%
        
        # 長線目標價（基本面為主）
        else:
            pe_ratio = analysis.get('pe_ratio', 0)
            eps = analysis.get('eps', 0)
            
            # 基於本益比估算
            if pe_ratio > 0 and eps > 0:
                # 給予合理本益比（15-18倍）
                if pe_ratio < 12:  # 目前偏低
                    target_pe = 15
                elif pe_ratio > 20:  # 目前偏高
                    target_pe = 18
                else:
                    target_pe = pe_ratio * 1.1  # 微幅提升
                
                target_price = eps * target_pe
                return round(target_price, 1)
            
            # 基於股息殖利率估算
            dividend_yield = analysis.get('dividend_yield', 0)
            if dividend_yield > 0:
                # 假設合理殖利率4%
                target_yield = 4.0
                annual_dividend = current_price * dividend_yield / 100
                target_price = annual_dividend / target_yield * 100
                return round(target_price, 1)
            
            # 預設基於基本面強度
            fundamental_strength = self._calculate_fundamental_strength(analysis)
            if fundamental_strength > 0.8:
                return round(current_price * 1.20, 1)  # 優質股20%
            elif fundamental_strength > 0.6:
                return round(current_price * 1.15, 1)  # 良好股15%
            else:
                return round(current_price * 1.08, 1)  # 穩健股8%
    
    def generate_target_price_reasoning(self, analysis: Dict[str, Any], target_price: float, analysis_type: str) -> str:
        """生成目標價推理說明"""
        current_price = analysis.get('current_price', 0)
        upside = ((target_price - current_price) / current_price * 100) if current_price > 0 else 0
        
        if analysis_type == 'short_term':
            # 短線推理
            resistance_level = analysis.get('resistance_level', 0)
            if resistance_level > 0:
                return f"目標價{target_price}(技術壓力位{resistance_level}附近，上漲空間{upside:.1f}%)"
            else:
                technical_strength = self._calculate_technical_strength(analysis)
                if technical_strength > 0.8:
                    return f"目標價{target_price}(技術面強勢，上漲空間{upside:.1f}%)"
                else:
                    return f"目標價{target_price}(技術面轉強，上漲空間{upside:.1f}%)"
        else:
            # 長線推理
            pe_ratio = analysis.get('pe_ratio', 0)
            if pe_ratio > 0:
                return f"目標價{target_price}(基於合理本益比估算，上漲空間{upside:.1f}%)"
            else:
                return f"目標價{target_price}(基於基本面價值，上漲空間{upside:.1f}%)"
    
    def _calculate_technical_strength(self, analysis: Dict[str, Any]) -> float:
        """計算技術面強度(0-1)"""
        strength = 0.5  # 基準值
        
        # MACD貢獻
        if analysis.get('technical_signals', {}).get('macd_golden_cross'):
            strength += 0.2
        elif analysis.get('technical_signals', {}).get('macd_bullish'):
            strength += 0.1
        
        # RSI貢獻
        rsi = analysis.get('rsi', 50)
        if 40 <= rsi <= 70:
            strength += 0.1
        elif rsi < 30:
            strength += 0.15  # 超賣反彈
        
        # 均線貢獻
        if analysis.get('technical_signals', {}).get('ma20_bullish'):
            strength += 0.1
        if analysis.get('technical_signals', {}).get('ma_golden_cross'):
            strength += 0.1
        
        return min(1.0, max(0.0, strength))
    
    def _calculate_fundamental_strength(self, analysis: Dict[str, Any]) -> float:
        """計算基本面強度(0-1)"""
        strength = 0.5  # 基準值
        
        # 殖利率貢獻
        dividend_yield = analysis.get('dividend_yield', 0)
        if dividend_yield > 4:
            strength += 0.15
        elif dividend_yield > 2:
            strength += 0.1
        
        # EPS成長貢獻
        eps_growth = analysis.get('eps_growth', 0)
        if eps_growth > 15:
            strength += 0.2
        elif eps_growth > 8:
            strength += 0.15
        
        # ROE貢獻
        roe = analysis.get('roe', 0)
        if roe > 15:
            strength += 0.15
        elif roe > 10:
            strength += 0.1
        
        return min(1.0, max(0.0, strength))
    
    # 摘要生成方法
    def _summarize_technical_evidences(self, evidences: List[str]) -> str:
        if len(evidences) >= 3:
            return f"{evidences[0]}、{evidences[1]}等多項轉強"
        elif len(evidences) == 2:
            return f"{evidences[0]}、{evidences[1]}"
        else:
            return evidences[0] if evidences else "技術面轉強"
    
    def _summarize_institutional_evidences(self, evidences: List[str]) -> str:
        if len(evidences) >= 2:
            return f"{evidences[0]}，{evidences[1]}"
        else:
            return evidences[0] if evidences else "法人買超"
    
    def _summarize_volume_evidences(self, evidences: List[str]) -> str:
        return evidences[0] if evidences else "成交活躍"
    
    def _summarize_price_evidences(self, evidences: List[str]) -> str:
        return "、".join(evidences) if evidences else "價格轉強"
    
    def _summarize_fundamental_evidences(self, evidences: List[str]) -> str:
        if len(evidences) >= 3:
            return f"{evidences[0]}、{evidences[1]}等優勢明顯"
        else:
            return "、".join(evidences) if evidences else "基本面穩健"
    
    def _summarize_institutional_trend_evidences(self, evidences: List[str]) -> str:
        return "、".join(evidences) if evidences else "法人持續布局"
    
    def _summarize_valuation_evidences(self, evidences: List[str]) -> str:
        return "、".join(evidences) if evidences else "估值合理"
    
    def _summarize_industry_evidences(self, evidences: List[str]) -> str:
        return "、".join(evidences) if evidences else "產業地位穩固"
    
    def _extract_institutional_trend_evidences(self, analysis: Dict[str, Any]) -> List[str]:
        """提取法人趨勢證據"""
        evidences = []
        consecutive_days = analysis.get('consecutive_buy_days', 0)
        if consecutive_days > 5:
            evidences.append(f"持續{consecutive_days}日布局")
        return evidences
    
    def _extract_industry_evidences(self, analysis: Dict[str, Any]) -> List[str]:
        """提取產業地位證據"""
        evidences = []
        stock_name = analysis.get('name', '')
        
        # 根據股票名稱判斷產業地位
        if '台積電' in stock_name:
            evidences.append("半導體龍頭")
        elif '鴻海' in stock_name:
            evidences.append("代工巨頭")
        elif '聯發科' in stock_name:
            evidences.append("IC設計領導者")
        
        return evidences

# 使用範例
def demo_enhanced_recommendation():
    """示範增強版推薦理由"""
    generator = EnhancedRecommendationGenerator()
    
    # 模擬鴻海的分析數據
    hon_hai_analysis = {
        'name': '鴻海',
        'code': '2317',
        'current_price': 168.5,
        'change_percent': 1.2,
        'trade_value': 9000000000,  # 90億
        'volume_ratio': 1.8,
        'foreign_net_buy': 15000,  # 1.5億
        'trust_net_buy': 3000,     # 3000萬
        'consecutive_buy_days': 4,
        'technical_signals': {
            'macd_bullish': True,
            'ma20_bullish': True,
            'rsi_healthy': True
        },
        'macd_value': 0.235,
        'macd_signal_value': 0.198,
        'rsi': 58,
        'ma20_value': 165.2,
        'dividend_yield': 4.8,
        'eps_growth': 8.3,
        'pe_ratio': 12.1,
        'roe': 15.6,
        'dividend_consecutive_years': 12,
        'resistance_level': 175.0
    }
    
    # 生成短線推薦理由
    short_reason = generator.generate_enhanced_short_term_reason(hon_hai_analysis)
    print("增強版短線推薦理由:")
    print(short_reason)
    
    # 生成目標價
    target_price = generator.calculate_enhanced_target_price(hon_hai_analysis, 'short_term')
    target_reasoning = generator.generate_target_price_reasoning(hon_hai_analysis, target_price, 'short_term')
    print(f"\n目標價設定: {target_reasoning}")
    
    # 生成長線推薦理由
    long_reason = generator.generate_enhanced_long_term_reason(hon_hai_analysis)
    print(f"\n增強版長線推薦理由:")
    print(long_reason)

if __name__ == "__main__":
    demo_enhanced_recommendation()
