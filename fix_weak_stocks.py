"""
fix_weak_stocks.py - 修復極弱股判定邏輯
解決優化版系統中極弱股提醒消失的問題
"""

def generate_recommendations_optimized_fixed(self, analyses: List[Dict[str, Any]], time_slot: str) -> Dict[str, List[Dict[str, Any]]]:
    """生成優化的推薦（修復極弱股判定）"""
    if not analyses:
        return {"short_term": [], "long_term": [], "weak_stocks": []}
    
    # 獲取配置
    config = self.time_slot_config[time_slot]
    limits = config['recommendation_limits']
    
    # 過濾有效分析
    valid_analyses = [a for a in analyses if a.get('data_quality') != 'limited']
    
    # 短線推薦（評分 >= 4，標準稍微提高）
    short_term_candidates = [a for a in valid_analyses if a.get('weighted_score', 0) >= 4]
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
    
    # 長線推薦（優化篩選條件）
    long_term_candidates = []
    for a in valid_analyses:
        score = a.get('weighted_score', 0)
        
        # 長線推薦條件（更嚴格）
        conditions_met = 0
        
        # 1. 基本評分條件（降低權重）
        if score >= 2:
            conditions_met += 1
        
        # 2. 基本面條件（重點）
        if a.get('dividend_yield', 0) > 2.5:  # 殖利率 > 2.5%
            conditions_met += 2
        if a.get('eps_growth', 0) > 8:  # EPS成長 > 8%
            conditions_met += 2
        if a.get('roe', 0) > 12:  # ROE > 12%
            conditions_met += 1
        if a.get('pe_ratio', 999) < 20:  # 本益比 < 20
            conditions_met += 1
        
        # 3. 法人買超條件（重點）
        foreign_net = a.get('foreign_net_buy', 0)
        trust_net = a.get('trust_net_buy', 0)
        if foreign_net > 5000 or trust_net > 3000:  # 法人買超
            conditions_met += 2
        if foreign_net > 20000 or trust_net > 10000:  # 大額買超
            conditions_met += 1
        
        # 4. 成交量條件（基本門檻）
        if a.get('trade_value', 0) > 50000000:  # 成交金額 > 5000萬
            conditions_met += 1
        
        # 5. 股息穩定性
        if a.get('dividend_consecutive_years', 0) > 5:
            conditions_met += 1
        
        # 滿足條件數量 >= 4 且評分 >= 0 才納入長線推薦
        if conditions_met >= 4 and score >= 0:
            # 計算長線綜合得分
            long_term_score = score + (conditions_met - 4) * 0.5
            a['long_term_score'] = long_term_score
            long_term_candidates.append(a)
    
    # 按長線綜合得分排序
    long_term_candidates.sort(key=lambda x: x.get('long_term_score', 0), reverse=True)
    
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
    
    # ⭐ 修復：極弱股判定邏輯
    # 使用多重條件判定，不只依賴加權分數
    weak_candidates = []
    
    for a in valid_analyses:
        weighted_score = a.get('weighted_score', 0)
        base_score = a.get('base_score', 0)
        change_percent = a.get('change_percent', 0)
        
        # 極弱股條件（任一條件滿足即可）
        is_weak = False
        weak_reasons = []
        
        # 條件1：加權分數極低（原條件）
        if weighted_score <= -3:
            is_weak = True
            weak_reasons.append("技術面和基本面綜合評分極低")
        
        # 條件2：基礎分數極低且無基本面支撐
        elif base_score <= -3 and a.get('fundamental_score', 0) < 2:
            is_weak = True
            weak_reasons.append("技術面極弱且基本面無支撐")
        
        # 條件3：大跌且法人賣超
        elif change_percent <= -3 and a.get('foreign_net_buy', 0) < -5000:
            is_weak = True
            weak_reasons.append(f"今日大跌 {abs(change_percent):.1f}% 且外資賣超")
        
        # 條件4：連續下跌且成交量放大
        elif change_percent <= -2 and a.get('volume_ratio', 1) > 2:
            is_weak = True
            weak_reasons.append("放量下跌，賣壓沉重")
        
        # 條件5：技術指標全面轉弱
        technical_signals = a.get('technical_signals', {})
        if (technical_signals.get('macd_death_cross') or 
            technical_signals.get('ma_death_cross') or 
            (a.get('rsi', 50) > 70 and change_percent < 0)):
            is_weak = True
            weak_reasons.append("技術指標顯示趨勢轉弱")
        
        # 條件6：基本面惡化
        if (a.get('eps_growth', 0) < -10 or 
            (a.get('roe', 999) < 5 and a.get('pe_ratio', 0) > 30)):
            is_weak = True
            weak_reasons.append("基本面惡化，獲利能力下降")
        
        if is_weak:
            # 計算風險分數（越低越危險）
            risk_score = weighted_score
            if change_percent < -3:
                risk_score -= 2
            if a.get('foreign_net_buy', 0) < -10000:
                risk_score -= 2
            if a.get('eps_growth', 0) < -10:
                risk_score -= 1
            
            a['risk_score'] = risk_score
            a['weak_reasons'] = weak_reasons
            weak_candidates.append(a)
    
    # 按風險分數排序（越低越危險）
    weak_candidates.sort(key=lambda x: x.get('risk_score', 0))
    
    weak_stocks = []
    for analysis in weak_candidates[:limits['weak_stocks']]:
        # 生成警示理由
        reasons = analysis.get('weak_reasons', [])
        main_reason = reasons[0] if reasons else "多項指標顯示風險增加"
        
        # 加入具體數據
        change_percent = analysis.get('change_percent', 0)
        foreign_net = analysis.get('foreign_net_buy', 0)
        
        if change_percent < 0:
            main_reason += f"，今日下跌 {abs(change_percent):.1f}%"
        if foreign_net < -5000:
            main_reason += f"，外資賣超 {abs(foreign_net)/10000:.1f}億"
        
        weak_stocks.append({
            "code": analysis["code"],
            "name": analysis["name"],
            "current_price": analysis["current_price"],
            "alert_reason": main_reason,
            "trade_value": analysis["trade_value"],
            "analysis": analysis
        })
    
    return {
        "short_term": short_term,
        "long_term": long_term,
        "weak_stocks": weak_stocks
    }


# 在 enhanced_stock_bot_optimized.py 中替換原有的 generate_recommendations_optimized 方法
# 或在 OptimizedStockBot 類中添加這個修復版方法
