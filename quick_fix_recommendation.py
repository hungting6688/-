"""
quick_fix_recommendation.py - 立即修復版推薦理由生成器
針對技術面單薄、法人買超缺乏背景、目標價無依據等問題的快速修復
"""
from typing import Dict, Any, Optional

def generate_enhanced_reason_quick_fix(analysis: Dict[str, Any], analysis_type: str = 'short_term') -> str:
    """
    快速修復版推薦理由生成
    立即可整合到現有系統中
    """
    stock_name = analysis.get('name', '')
    stock_code = analysis.get('code', '')
    current_price = analysis.get('current_price', 0)
    change_percent = analysis.get('change_percent', 0)
    trade_value = analysis.get('trade_value', 0)
    
    # 收集技術面證據（加入具體數值）
    tech_parts = []
    
    # MACD證據
    technical_signals = analysis.get('technical_signals', {})
    if technical_signals.get('macd_golden_cross'):
        tech_parts.append("MACD金叉確認")
    elif technical_signals.get('macd_bullish'):
        tech_parts.append("MACD轉強")
    
    # RSI證據（加入數值）
    rsi = analysis.get('rsi', 0)
    if rsi > 0:
        if 30 <= rsi <= 70:
            tech_parts.append(f"RSI健康區間({rsi:.0f})")
        elif rsi < 30:
            tech_parts.append(f"RSI超賣反彈({rsi:.0f})")
    
    # 均線證據
    if technical_signals.get('ma20_bullish'):
        ma20 = analysis.get('ma20_value', 0)
        if ma20 > 0:
            tech_parts.append(f"站穩20MA({current_price:.1f}>{ma20:.1f})")
        else:
            tech_parts.append("突破20日均線")
    
    # 收集法人證據（加入背景脈絡）
    institutional_parts = []
    
    foreign_net = analysis.get('foreign_net_buy', 0)
    trust_net = analysis.get('trust_net_buy', 0)
    consecutive_days = analysis.get('consecutive_buy_days', 0)
    
    # 外資買超分析
    if foreign_net > 0:
        foreign_億 = foreign_net / 10000
        if consecutive_days > 3:
            institutional_parts.append(f"外資連{consecutive_days}日買超{foreign_億:.1f}億")
        elif foreign_net > 50000:  # 5億以上
            institutional_parts.append(f"外資大幅買超{foreign_億:.1f}億")
        elif foreign_net > 10000:  # 1億以上
            institutional_parts.append(f"外資買超{foreign_億:.1f}億")
    
    # 投信買超分析
    if trust_net > 5000:  # 5000萬以上
        trust_億 = trust_net / 10000
        institutional_parts.append(f"投信買超{trust_億:.1f}億")
    
    # 成交量分析（考慮個股常態）
    volume_parts = []
    
    # 個股常態成交金額(億)
    stock_normal_volumes = {
        '台積電': 150, '鴻海': 50, '聯發科': 60, '台達電': 20,
        '國泰金': 25, '富邦金': 20, '長榮': 45, '陽明': 35
    }
    
    normal_volume = stock_normal_volumes.get(stock_name, 10)  # 預設10億
    current_volume_億 = trade_value / 100000000
    
    # 只有顯著放大才提及成交量
    if current_volume_億 > normal_volume * 2:
        volume_parts.append(f"爆量{current_volume_億:.0f}億(常態{normal_volume}億)")
    elif current_volume_億 > normal_volume * 1.5:
        increase_pct = (current_volume_億 / normal_volume - 1) * 100
        volume_parts.append(f"放量{current_volume_億:.0f}億(較常態+{increase_pct:.0f}%)")
    
    # 組合推薦理由
    reason_parts = []
    
    # 技術面部分
    if tech_parts:
        tech_summary = "、".join(tech_parts[:3])  # 最多3個技術指標
        reason_parts.append(f"技術面{tech_summary}")
    
    # 法人部分
    if institutional_parts:
        inst_summary = "、".join(institutional_parts)
        reason_parts.append(inst_summary)
    
    # 成交量部分（只有顯著時才加入）
    if volume_parts:
        reason_parts.append(volume_parts[0])
    
    # 如果是長線分析，加入基本面
    if analysis_type == 'long_term':
        fundamental_parts = []
        
        dividend_yield = analysis.get('dividend_yield', 0)
        if dividend_yield > 3:
            fundamental_parts.append(f"殖利率{dividend_yield:.1f}%")
        
        eps_growth = analysis.get('eps_growth', 0)
        if eps_growth > 8:
            fundamental_parts.append(f"EPS成長{eps_growth:.1f}%")
        
        roe = analysis.get('roe', 0)
        if roe > 12:
            fundamental_parts.append(f"ROE {roe:.1f}%")
        
        if fundamental_parts:
            reason_parts.append("、".join(fundamental_parts))
    
    # 生成最終理由
    if not reason_parts:
        return f"今日{'上漲' if change_percent > 0 else '下跌'}{abs(change_percent):.1f}%，綜合指標{'偏多' if change_percent > 0 else '偏弱'}"
    
    return "，".join(reason_parts)

def calculate_target_price_with_reasoning(analysis: Dict[str, Any], analysis_type: str = 'short_term') -> tuple[Optional[float], str]:
    """
    計算目標價並提供推理說明
    返回: (目標價, 推理說明)
    """
    current_price = analysis.get('current_price', 0)
    if current_price <= 0:
        return None, ""
    
    # 短線目標價邏輯
    if analysis_type == 'short_term':
        # 檢查是否有技術壓力位
        resistance_level = analysis.get('resistance_level', 0)
        if resistance_level > current_price:
            target_price = round(resistance_level * 0.95, 1)  # 接近壓力位
            upside = ((target_price - current_price) / current_price * 100)
            reasoning = f"目標價{target_price}元(技術壓力位{resistance_level}附近，上漲空間{upside:.1f}%)"
            return target_price, reasoning
        
        # 基於技術強度
        technical_signals = analysis.get('technical_signals', {})
        signal_count = sum([
            technical_signals.get('macd_golden_cross', False),
            technical_signals.get('macd_bullish', False),
            technical_signals.get('ma20_bullish', False),
            technical_signals.get('rsi_healthy', False)
        ])
        
        if signal_count >= 3:
            target_price = round(current_price * 1.08, 1)  # 強勢8%
            reasoning = f"目標價{target_price}元(多項技術指標轉強，上漲空間8%)"
        elif signal_count >= 2:
            target_price = round(current_price * 1.05, 1)  # 中強勢5%
            reasoning = f"目標價{target_price}元(技術面轉強，上漲空間5%)"
        else:
            target_price = round(current_price * 1.03, 1)  # 溫和3%
            reasoning = f"目標價{target_price}元(短線技術面偏多，上漲空間3%)"
        
        return target_price, reasoning
    
    # 長線目標價邏輯
    else:
        pe_ratio = analysis.get('pe_ratio', 0)
        eps = analysis.get('eps', 0)
        
        # 基於本益比估算
        if pe_ratio > 0 and eps > 0:
            if pe_ratio < 12:  # 低估
                target_pe = 15
                target_price = round(eps * target_pe, 1)
                reasoning = f"目標價{target_price}元(目前P/E {pe_ratio:.1f}倍偏低，合理P/E 15倍估算)"
            elif pe_ratio > 20:  # 高估
                target_pe = 18
                target_price = round(eps * target_pe, 1)
                reasoning = f"目標價{target_price}元(基於合理P/E 18倍估算)"
            else:  # 合理區間
                target_price = round(current_price * 1.12, 1)
                reasoning = f"目標價{target_price}元(P/E {pe_ratio:.1f}倍合理，基本面溢價12%)"
            
            return target_price, reasoning
        
        # 基於殖利率估算
        dividend_yield = analysis.get('dividend_yield', 0)
        if dividend_yield > 0:
            annual_dividend = current_price * dividend_yield / 100
            target_yield = 4.0  # 假設合理殖利率4%
            target_price = round(annual_dividend / target_yield * 100, 1)
            upside = ((target_price - current_price) / current_price * 100)
            reasoning = f"目標價{target_price}元(基於4%合理殖利率估算，上漲空間{upside:.1f}%)"
            return target_price, reasoning
        
        # 預設基本面估算
        target_price = round(current_price * 1.15, 1)
        reasoning = f"目標價{target_price}元(基於基本面價值，長線上漲空間15%)"
        return target_price, reasoning

def enhanced_stop_loss_calculation(analysis: Dict[str, Any], target_price: float) -> tuple[float, str]:
    """
    增強版停損計算
    返回: (停損價, 停損說明)
    """
    current_price = analysis.get('current_price', 0)
    
    # 支撐位停損
    support_level = analysis.get('support_level', 0)
    if support_level > 0 and support_level < current_price:
        stop_loss = round(support_level * 0.98, 1)  # 支撐位下2%
        reasoning = f"停損{stop_loss}元(技術支撐位{support_level}下方)"
        return stop_loss, reasoning
    
    # 20日均線停損
    ma20 = analysis.get('ma20_value', 0)
    if ma20 > 0 and ma20 < current_price:
        stop_loss = round(ma20 * 0.97, 1)  # 20MA下3%
        reasoning = f"停損{stop_loss}元(20日均線{ma20:.1f}下方)"
        return stop_loss, reasoning
    
    # 預設停損
    stop_loss = round(current_price * 0.95, 1)  # 5%停損
    reasoning = f"停損{stop_loss}元(5%風控停損)"
    return stop_loss, reasoning

# 立即可用的修復函數
def apply_quick_fix_to_stock_analysis(analysis: Dict[str, Any], analysis_type: str = 'short_term') -> Dict[str, Any]:
    """
    對現有股票分析應用快速修復
    可直接整合到現有系統中
    """
    # 生成增強推薦理由
    enhanced_reason = generate_enhanced_reason_quick_fix(analysis, analysis_type)
    
    # 計算目標價和推理
    target_price, target_reasoning = calculate_target_price_with_reasoning(analysis, analysis_type)
    
    # 計算停損價和說明
    if target_price:
        stop_loss, stop_loss_reasoning = enhanced_stop_loss_calculation(analysis, target_price)
    else:
        stop_loss = round(analysis.get('current_price', 0) * 0.95, 1)
        stop_loss_reasoning = f"停損{stop_loss}元(5%風控)"
    
    # 更新分析結果
    analysis.update({
        'reason': enhanced_reason,
        'target_price': target_price,
        'target_price_reasoning': target_reasoning,
        'stop_loss': stop_loss,
        'stop_loss_reasoning': stop_loss_reasoning,
        'enhanced': True  # 標記為增強版
    })
    
    return analysis

# 使用範例
def demo_quick_fix():
    """示範快速修復效果"""
    
    # 模擬鴻海分析數據
    hon_hai_analysis = {
        'name': '鴻海',
        'code': '2317',
        'current_price': 168.5,
        'change_percent': 1.2,
        'trade_value': 9000000000,  # 90億（常態50億）
        'foreign_net_buy': 15000,   # 1.5億
        'consecutive_buy_days': 4,   # 連續4日
        'technical_signals': {
            'macd_bullish': True,
            'ma20_bullish': True,
            'rsi_healthy': True
        },
        'rsi': 58,
        'ma20_value': 165.2,
        'resistance_level': 175.0,
        'support_level': 162.0,
        'pe_ratio': 12.1,
        'eps': 14.0,
        'dividend_yield': 4.8,
        'roe': 15.6
    }
    
    print("=== 修復前 ===")
    print("推薦理由: 外資買超，成交金額90億")
    print("目標價: 171.1元")
    print("停損: 160.0元")
    
    print("\n=== 修復後 ===")
    
    # 短線分析
    fixed_analysis = apply_quick_fix_to_stock_analysis(hon_hai_analysis.copy(), 'short_term')
    print("短線推薦理由:", fixed_analysis['reason'])
    print("目標價說明:", fixed_analysis['target_price_reasoning'])
    print("停損說明:", fixed_analysis['stop_loss_reasoning'])
    
    print("\n=== 長線分析 ===")
    
    # 長線分析
    fixed_long_analysis = apply_quick_fix_to_stock_analysis(hon_hai_analysis.copy(), 'long_term')
    print("長線推薦理由:", fixed_long_analysis['reason'])
    print("目標價說明:", fixed_long_analysis['target_price_reasoning'])

if __name__ == "__main__":
    demo_quick_fix()
