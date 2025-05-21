"""
text_formatter.py - 白話文轉換模塊
將技術分析結果轉換為易於理解的白話文描述
"""
import random
from typing import Dict, Any, List

# 語句模板庫
TEMPLATES = {
    # 整體評價模板
    "overall_bullish": [
        "這檔股票整體走勢看好，{reason}",
        "目前看來這支股票相當強勢，{reason}",
        "從多項指標來看，這檔股票展現出上漲潛力，{reason}",
        "市場情緒對這檔股票偏向正面，{reason}",
        "多項技術指標都顯示這檔股票處於有利位置，{reason}"
    ],
    "overall_bearish": [
        "這檔股票目前走勢較弱，{reason}",
        "從多項指標來看，這檔股票呈現疲軟態勢，{reason}",
        "市場對這檔股票顯得謹慎，{reason}",
        "技術面上，這檔股票展現下跌風險，{reason}",
        "目前來看這支股票可能面臨調整壓力，{reason}"
    ],
    "overall_neutral": [
        "這檔股票目前處於盤整階段，{reason}",
        "從指標來看，這檔股票走勢偏向中性，{reason}",
        "市場對這檔股票態度觀望，{reason}",
        "短期內這檔股票可能維持區間震盪，{reason}",
        "目前這檔股票沒有明確方向，{reason}"
    ],
    
    # 短線理由模板
    "short_term": {
        "ma_cross": [
            "短期均線突破長期均線，顯示短期買盤力道增強",
            "均線剛形成黃金交叉，代表短線動能正在加強",
            "價格突破主要均線，顯示市場買氣明顯增加",
            "均線系統開始轉為多頭排列，買盤力道較強",
            "最近幾天均線出現多頭排列，短期動能增強"
        ],
        "macd_golden": [
            "MACD指標出現黃金交叉，短線買進訊號明確",
            "動能指標轉為向上，短期內有望持續上漲",
            "MACD柱狀體由負轉正，顯示動能開始轉強",
            "主要技術指標剛轉為看漲，動能開始加速",
            "買賣動能指標轉強，短線有不錯表現空間"
        ],
        "rsi_recovery": [
            "RSI指標從超賣區回升，意味著賣壓減緩轉為買壓",
            "相對強弱指標顯示股價已止穩並開始反彈",
            "強弱指標剛從低檔回升，反彈動能正在積聚",
            "技術指標顯示賣壓已減緩，可能開始展開反彈",
            "走勢已經從超賣情況恢復，投資人開始回補"
        ],
        "volume_price": [
            "成交量明顯放大且股價上漲，資金介入意願提高",
            "大量買盤湧入使股價突破阻力，表明短線資金積極進場",
            "成交量放大帶動股價上揚，市場人氣聚集",
            "伴隨高交易量的上漲行情，短期買盤積極",
            "在增加的交易量支撐下，股價持續走高"
        ],
        "bollinger_bounce": [
            "股價觸及布林通道下軌後開始反彈，短線超賣有回升空間",
            "從布林通道下緣反彈，價格向中線回歸的機率較高",
            "股價已觸及技術支撐位並開始反彈，風險報酬比看好",
            "在價格通道的支撐位找到買盤支持，開始回升",
            "從超賣區域開始反彈，向上修正的力道初現"
        ],
        "general_bullish": [
            "多項技術指標顯示股價短期內有上漲潛力",
            "從走勢圖來看，短線出現多個看漲信號",
            "近期的市場行為顯示投資人情緒正在好轉",
            "技術面轉佳，短期有望突破盤整",
            "籌碼面和技術面同步好轉，上漲動能增強"
        ]
    },
    
    # 長線理由模板
    "long_term": {
        "price_above_ma": [
            "股價穩定在長期均線之上，顯示長期趨勢健康",
            "穩定站上重要均線支撐，長線走勢較為穩健",
            "股價持續站穩長期趨勢線，基本面支撐力道強",
            "位於主要長期移動平均線之上，顯示基本面穩定",
            "長期均線呈現向上走勢，公司基本面表現佳"
        ],
        "ma_arrangement": [
            "均線系統呈多頭排列，長期向上趨勢明確",
            "主要技術指標顯示長期向上趨勢完整",
            "移動平均線排列顯示長期投資人持續進場",
            "均線系統支撐明確，上升通道形成完整",
            "從均線排列看來，機構投資人持續累積部位"
        ],
        "healthy_rsi": [
            "RSI指標維持在健康區間，顯示上漲動能穩定持續",
            "技術指標顯示股價處於健康上升階段，不過熱也不過冷",
            "技術指標顯示市場情緒穩定平衡，利於長期發展",
            "強弱指標處於健康水平，沒有過熱風險",
            "相對強弱維持在理想區間，長線趨勢穩定"
        ],
        "volume_growth": [
            "成交量穩定增加，反映投資人對公司未來展望正面",
            "交易量呈現緩步增加，顯示機構投資人正逐步累積",
            "市場參與度持續提高，代表投資人信心增強",
            "在穩定的交易量支持下，股價逐步墊高，長線看好",
            "市場交易活動逐漸活躍，長期投資價值受到認可"
        ],
        "general_stable": [
            "整體技術面呈現穩健格局，適合納入中長期投資組合",
            "財務面和技術面共同支撐，長期投資潛力佳",
            "公司基本面良好，技術指標亦支持長期持有",
            "綜合分析顯示公司營運前景看好，值得長期關注",
            "從長期趨勢來看，這檔股票展現良好的成長性"
        ],
        "eps_growth": [
            "每股盈餘持續成長，公司獲利能力強健",
            "獲利表現優於產業平均，顯示競爭力提升",
            "長期EPS維持成長趨勢，基本面穩固",
            "財報數據顯示公司盈利能力持續優化",
            "業績持續向上，長期投資價值明確"
        ],
        "dividend_yield": [
            "高殖利率提供良好的現金流回報，長期持有價值高",
            "穩定的股息政策顯示公司重視股東權益",
            "殖利率優於定存，且具股價上漲潛力",
            "股息配發記錄良好，是穩健型投資的優質選擇",
            "較高的殖利率提供投資安全邊際"
        ]
    },
    
    # 弱勢股理由模板
    "weak_stock": {
        "ma_death_cross": [
            "短期均線跌破長期均線，形成死亡交叉，賣壓持續增加",
            "均線系統已轉為空頭排列，下跌趨勢成形",
            "主要均線轉向下彎，且價格跌破重要支撐",
            "均線系統出現死亡交叉，技術面轉為不利",
            "價格跌破所有主要均線，技術面全面轉弱"
        ],
        "macd_death_cross": [
            "MACD指標出現死亡交叉，顯示賣壓加大",
            "動能指標由正轉負，賣壓開始主導市場",
            "MACD指標轉為負值，且呈現加速下跌趨勢",
            "賣出訊號已被觸發，且尚未看到止跌跡象",
            "主要技術指標全面轉弱，賣壓持續湧現"
        ],
        "rsi_overbought": [
            "RSI指標在高檔出現回落，獲利了結賣壓出現",
            "從超買區回落，顯示漲多後的回檔風險",
            "技術指標顯示市場過熱，修正風險增加",
            "相對強弱指標顯示股價已漲過頭，面臨獲利回吐壓力",
            "從過熱區域回落，投資人開始獲利了結"
        ],
        "volume_decline": [
            "股價下跌同時成交量放大，顯示拋售壓力沉重",
            "在大量拋售壓力下，股價快速滑落",
            "近期成交量明顯放大，但多為賣壓主導",
            "機構投資人可能正在減碼，成交量和價格同步下降",
            "大量的拋售湧現，股價支撐不足"
        ],
        "bollinger_breakdown": [
            "股價突破布林通道上軌後大幅回落，顯示反轉風險高",
            "從布林通道上方回落，反轉趨勢已確立",
            "布林通道指標顯示股價已過度擴張，修正壓力明顯",
            "股價快速回落至布林帶中心，動能減弱明顯",
            "價格無法維持在高檔，回落趨勢加速"
        ],
        "general_bearish": [
            "多項技術指標顯示股價可能面臨較大調整",
            "近期走勢明顯轉弱，建議暫時觀望",
            "從籌碼和技術面判斷，短線不宜介入",
            "各項指標都顯示賣壓沉重，不建議現階段進場",
            "技術面全面惡化，風險大於報酬"
        ]
    },
    
    # 操作建議模板
    "action_suggestion": {
        "strong_buy": [
            "強烈建議買進，並設定 {stop_loss} 元為停損點",
            "此時進場時機佳，止損設在 {stop_loss} 元可控制風險",
            "目前是相對理想的買點，建議以 {stop_loss} 元為停損",
            "可考慮分批買進，並嚴守 {stop_loss} 元的停損紀律",
            "適合積極買進，但需設定 {stop_loss} 元停損控管風險"
        ],
        "buy_hold": [
            "建議買進持有，目標價位看至 {target}，停損 {stop_loss}",
            "適合中期布局，預期目標 {target}，風險控制在 {stop_loss}",
            "可考慮納入投資組合，目標 {target}，壓力測試 {stop_loss}",
            "建議逢回買進，目標價 {target}，風控設在 {stop_loss}",
            "值得納入中長期投資組合，目標 {target}，停損 {stop_loss}"
        ],
        "hold": [
            "持有者可繼續持有，目標上看 {target}",
            "現有部位可持續持有，上檔目標 {target}",
            "已有部位者可以繼續持有，目標價 {target}",
            "中長期持有，預期目標價位 {target}",
            "維持持有策略，目標等待 {target}"
        ],
        "reduce": [
            "建議獲利了結或減碼，止損設於 {stop_loss}",
            "可考慮分批獲利了結，不跌破 {stop_loss} 前持有",
            "風險增加，建議減碼持有，止損 {stop_loss}",
            "宜降低持股比例，剩餘部位止損設 {stop_loss}",
            "可逢高賣出，剩餘部位守住 {stop_loss} 停損點"
        ],
        "sell": [
            "建議賣出，若不跌破 {stop_loss} 可再評估",
            "此階段不宜繼續持有，待跌勢結束再評估",
            "技術指標惡化，建議立即出場",
            "趨勢反轉風險增加，建議出清持股",
            "多項警訊顯示應儘速賣出，減少損失"
        ]
    },
    
    # 引言模板
    "introduction": {
        "morning": [
            "早盤掃描完成，已為您篩選出今日最值得關注的股票：",
            "根據今日早盤數據分析，以下是我們精選的投資機會：",
            "經過晨間市場數據分析，以下股票展現較高投資價值：",
            "今日開盤前分析已完成，以下是最具潛力的投資標的：",
            "早安！今天市場開盤前，這些股票值得您特別關注："
        ],
        "mid_morning": [
            "盤中最新掃描結果出爐，這些股票走勢值得關注：",
            "根據盤中即時數據，以下股票展現不錯的交易機會：",
            "盤中掃描顯示，這些股票的技術指標正在轉強：",
            "市場盤中表現分析完成，以下標的值得進一步觀察：",
            "盤中分析更新，這些股票的走勢開始出現轉機："
        ],
        "mid_day": [
            "午間分析結果已更新，以下是值得下午持續關注的標的：",
            "根據上午的交易情況，這些股票在下午可能有不錯表現：",
            "午間市場更新，以下股票展現出較佳的投資機會：",
            "中午好！根據上半日交易數據，這些股票趨勢較為明確：",
            "午間掃描完成，下午可重點觀察以下幾檔股票："
        ],
        "afternoon": [
            "今日收盤分析結果出爐，以下是綜合表現最佳的股票：",
            "根據全天交易數據，這些股票技術面有明顯轉變：",
            "今日大盤收盤後分析，以下標的的走勢最為明確：",
            "完整的日盤分析顯示，這些股票值得納入觀察名單：",
            "今日收盤後的綜合評估，以下股票脫穎而出："
        ],
        "weekly": [
            "本週市場總結分析，以下是未來一週最值得關注的投資機會：",
            "週末市場掃描顯示，下週這些股票可能有較大表現空間：",
            "根據本週交易數據綜合分析，以下股票展現出較佳趨勢：",
            "週末好！根據本週市場表現，這些標的值得下週持續追蹤：",
            "本週交易總結，以下股票的技術面和基本面表現最為突出："
        ]
    },
    
    # 市場環境模板
    "market_environment": {
        "bullish": [
            "今日大盤氣氛偏向正面，投資人可適度積極布局。",
            "整體市場呈現上漲趨勢，可考慮增加持股部位。",
            "大盤指數保持強勢，個股表現活躍，交易機會增加。",
            "市場氛圍熱絡，主要指數走揚，投資人信心增強。",
            "大盤維持在上升通道中，個股輪動效應明顯。"
        ],
        "bearish": [
            "今日大盤氣氛偏向保守，建議投資人謹慎為上。",
            "整體市場承壓回檔，短線操作宜減少部位。",
            "大盤指數走弱，個股表現疲弱，宜提高現金部位。",
            "市場氛圍趨於謹慎，主要指數向下，風險意識應提高。",
            "大盤跌破重要支撐位，建議降低持股比例。"
        ],
        "neutral": [
            "今日大盤呈現盤整格局，可選擇性布局強勢個股。",
            "市場多空力道相當，建議選股不選市。",
            "大盤指數區間震盪，個股表現分歧，精選個股為宜。",
            "市場觀望氣氛濃厚，建議以價值投資思維布局。",
            "大盤缺乏明確方向，但強勢族群輪動明顯，可順勢操作。"
        ]
    }
}

def generate_plain_text(analysis: Dict[str, Any], category: str) -> Dict[str, str]:
    """
    生成白話文描述
    
    參數:
    - analysis: 股票分析結果
    - category: 類別 (short_term, long_term, weak_stock)
    
    返回:
    - 包含白話文描述的字典
    """
    result = {}
    
    # 根據技術指標識別關鍵特徵
    signals = analysis.get("signals", {})
    score = analysis.get("weighted_score", 0)
    
    # 判斷整體傾向
    if score >= 5:
        overall_template = random.choice(TEMPLATES["overall_bullish"])
    elif score <= -5:
        overall_template = random.choice(TEMPLATES["overall_bearish"])
    else:
        overall_template = random.choice(TEMPLATES["overall_neutral"])
    
    # 根據類別生成細節描述
    if category == "short_term":
        reasons = []
        
        # 檢查各類技術信號并選擇相應的描述模板
        if signals.get("ma5_crosses_above_ma20"):
            reasons.append(random.choice(TEMPLATES["short_term"]["ma_cross"]))
        if signals.get("macd_crosses_above_signal"):
            reasons.append(random.choice(TEMPLATES["short_term"]["macd_golden"]))
        if signals.get("rsi_bullish"):
            reasons.append(random.choice(TEMPLATES["short_term"]["rsi_recovery"]))
        if signals.get("volume_spike") and signals.get("price_up"):
            reasons.append(random.choice(TEMPLATES["short_term"]["volume_price"]))
        if signals.get("price_below_lower_band"):
            reasons.append(random.choice(TEMPLATES["short_term"]["bollinger_bounce"]))
            
        # 如果沒有特別明顯的信號
        if not reasons:
            reasons.append(random.choice(TEMPLATES["short_term"]["general_bullish"]))
        
        # 最多選擇兩個理由，避免過長
        if len(reasons) > 2:
            reasons = random.sample(reasons, 2)
        
        main_reason = "。".join(reasons)
        
        # 生成操作建議
        target_price = analysis.get("target_price")
        stop_loss = analysis.get("stop_loss")
        
        if score >= 8:
            suggestion_template = random.choice(TEMPLATES["action_suggestion"]["strong_buy"])
            suggestion = suggestion_template.format(stop_loss=stop_loss)
        else:
            suggestion_template = random.choice(TEMPLATES["action_suggestion"]["buy_hold"])
            suggestion = suggestion_template.format(target=target_price, stop_loss=stop_loss)
            
    elif category == "long_term":
        reasons = []
        
        # 檢查各類技術信號并選擇相應的描述模板
        if signals.get("price_above_ma20"):
            reasons.append(random.choice(TEMPLATES["long_term"]["price_above_ma"]))
        if signals.get("ma5_above_ma20") and signals.get("ma10_above_ma20"):
            reasons.append(random.choice(TEMPLATES["long_term"]["ma_arrangement"]))
        if 40 <= analysis.get("rsi", 0) <= 60:
            reasons.append(random.choice(TEMPLATES["long_term"]["healthy_rsi"]))
        if signals.get("volume_increasing"):
            reasons.append(random.choice(TEMPLATES["long_term"]["volume_growth"]))
            
        # 如果有基本面數據，添加相關描述
        if analysis.get("eps_growth", False):
            reasons.append(random.choice(TEMPLATES["long_term"]["eps_growth"]))
        if analysis.get("dividend_yield", 0) > 3:
            reasons.append(random.choice(TEMPLATES["long_term"]["dividend_yield"]))
            
        # 如果沒有特別明顯的信號
        if not reasons:
            reasons.append(random.choice(TEMPLATES["long_term"]["general_stable"]))
        
        # 最多選擇兩個理由，避免過長
        if len(reasons) > 2:
            reasons = random.sample(reasons, 2)
        
        main_reason = "。".join(reasons)
        
        # 生成操作建議
        target_price = analysis.get("target_price")
        stop_loss = analysis.get("stop_loss")
        
        suggestion_template = random.choice(TEMPLATES["action_suggestion"]["buy_hold"])
        suggestion = suggestion_template.format(target=target_price, stop_loss=stop_loss)
            
    elif category == "weak_stock":
        reasons = []
        
        # 檢查各類技術信號并選擇相應的描述模板
        if signals.get("ma5_crosses_below_ma20"):
            reasons.append(random.choice(TEMPLATES["weak_stock"]["ma_death_cross"]))
        if signals.get("macd_crosses_below_signal"):
            reasons.append(random.choice(TEMPLATES["weak_stock"]["macd_death_cross"]))
        if signals.get("rsi_bearish") or signals.get("rsi_overbought"):
            reasons.append(random.choice(TEMPLATES["weak_stock"]["rsi_overbought"]))
        if signals.get("volume_spike") and signals.get("price_down"):
            reasons.append(random.choice(TEMPLATES["weak_stock"]["volume_decline"]))
        if signals.get("price_above_upper_band"):
            reasons.append(random.choice(TEMPLATES["weak_stock"]["bollinger_breakdown"]))
            
        # 如果沒有特別明顯的信號
        if not reasons:
            reasons.append(random.choice(TEMPLATES["weak_stock"]["general_bearish"]))
        
        # 最多選擇兩個理由，避免過長
        if len(reasons) > 2:
            reasons = random.sample(reasons, 2)
        
        main_reason = "。".join(reasons)
        
        # 生成操作建議
        stop_loss = analysis.get("stop_loss")
        
        if score <= -8:
            suggestion_template = random.choice(TEMPLATES["action_suggestion"]["sell"])
            suggestion = suggestion_template.format(stop_loss=stop_loss)
        else:
            suggestion_template = random.choice(TEMPLATES["action_suggestion"]["reduce"])
            suggestion = suggestion_template.format(stop_loss=stop_loss)
    
    # 生成整體描述
    overall_description = overall_template.format(reason=main_reason)
    
    result = {
        "description": overall_description,
        "suggestion": suggestion
    }
    
    return result

def generate_intro_text(time_slot: str, market_trend: str = "neutral") -> str:
    """
    生成通知的介紹文字
    
    參數:
    - time_slot: 時段 (morning_scan, mid_morning_scan, mid_day_scan, afternoon_scan, weekly_summary)
    - market_trend: 大盤趨勢 (bullish, bearish, neutral)
    
    返回:
    - 介紹文字
    """
    # 映射時段到模板類別
    slot_map = {
        "morning_scan": "morning",
        "mid_morning_scan": "mid_morning",
        "mid_day_scan": "mid_day",
        "afternoon_scan": "afternoon",
        "weekly_summary": "weekly"
    }
    
    template_key = slot_map.get(time_slot, "morning")
    
    # 選擇介紹模板
    intro = random.choice(TEMPLATES["introduction"][template_key])
    
    # 選擇市場環境描述
    market_env = random.choice(TEMPLATES["market_environment"][market_trend])
    
    return f"{intro}\n\n{market_env}"

# 測試代碼
if __name__ == "__main__":
    # 模擬的股票分析結果
    mock_analysis = {
        "code": "2330",
        "name": "台積電",
        "current_price": 638.0,
        "weighted_score": 7,
        "target_price": 670.0,
        "stop_loss": 620.0,
        "rsi": 58,
        "signals": {
            "ma5_crosses_above_ma20": True,
            "macd_crosses_above_signal": True,
            "price_up": True,
            "volume_spike": True
        }
    }
    
    # 測試短線描述
    short_term = generate_plain_text(mock_analysis, "short_term")
    print("短線描述:")
    print(short_term["description"])
    print(short_term["suggestion"])
    print()
    
    # 測試長線描述
    long_term = generate_plain_text(mock_analysis, "long_term")
    print("長線描述:")
    print(long_term["description"])
    print(long_term["suggestion"])
    print()
    
    # 測試介紹文字
    intro = generate_intro_text("morning_scan", "bullish")
    print("介紹文字:")
    print(intro)
