“””
fix_display_and_filter.py - 修復技術指標、基本面、法人動向顯示問題並優化篩選邏輯
“””
import os
import shutil
from datetime import datetime

class DisplayAndFilterFixer:
“”“修復顯示問題和優化篩選邏輯”””

```
def __init__(self):
    self.backup_dir = f"backup_display_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
def backup_files(self):
    """備份原始文件"""
    print("📁 備份原始文件...")
    os.makedirs(self.backup_dir, exist_ok=True)
    
    files_to_backup = [
        'enhanced_stock_bot.py',
        'notifier.py',
        'config.py'
    ]
    
    for filename in files_to_backup:
        if os.path.exists(filename):
            backup_path = os.path.join(self.backup_dir, filename)
            shutil.copy2(filename, backup_path)
            print(f"✅ 已備份: {filename}")
    
    print(f"📁 備份目錄: {self.backup_dir}")

def create_enhanced_display_functions(self):
    """創建增強版顯示函數"""
    
    enhanced_notifier_code = '''
```

def extract_technical_indicators_detailed(analysis_data):
“”“提取詳細技術指標（修復版）”””
indicators = []

```
# RSI 指標
rsi_value = analysis_data.get('rsi', 0)
if rsi_value > 0:
    if rsi_value > 70:
        indicators.append(f"🔴 RSI過熱 ({rsi_value:.1f})")
    elif rsi_value < 30:
        indicators.append(f"🟢 RSI超賣 ({rsi_value:.1f})")
    else:
        indicators.append(f"🟡 RSI健康 ({rsi_value:.1f})")

# MACD 指標
technical_signals = analysis_data.get('technical_signals', {})
if technical_signals.get('macd_golden_cross'):
    indicators.append("🟢 MACD金叉")
elif technical_signals.get('macd_bullish'):
    indicators.append("🟡 MACD轉強")
elif technical_signals.get('macd_death_cross'):
    indicators.append("🔴 MACD死叉")

# 均線指標
if technical_signals.get('ma_golden_cross'):
    indicators.append("🟢 均線金叉")
elif technical_signals.get('ma20_bullish'):
    indicators.append("🟡 站穩20MA")
elif technical_signals.get('ma_death_cross'):
    indicators.append("🔴 均線死叉")

# 成交量指標
volume_ratio = analysis_data.get('volume_ratio', 1)
if volume_ratio > 3:
    indicators.append(f"🔥 爆量 ({volume_ratio:.1f}倍)")
elif volume_ratio > 2:
    indicators.append(f"📈 放量 ({volume_ratio:.1f}倍)")
elif volume_ratio > 1.5:
    indicators.append(f"📊 增量 ({volume_ratio:.1f}倍)")

# KD 指標（如果有）
if analysis_data.get('kd_golden_cross'):
    indicators.append("🟢 KD金叉")
elif analysis_data.get('kd_death_cross'):
    indicators.append("🔴 KD死叉")

return indicators
```

def extract_fundamental_advantages_detailed(analysis_data):
“”“提取詳細基本面優勢（修復版）”””
advantages = []

```
# 殖利率
dividend_yield = analysis_data.get('dividend_yield', 0)
if dividend_yield > 6:
    advantages.append(f"💰 超高殖利率 {dividend_yield:.1f}%")
elif dividend_yield > 4:
    advantages.append(f"💸 高殖利率 {dividend_yield:.1f}%")
elif dividend_yield > 2:
    advantages.append(f"💵 穩定殖利率 {dividend_yield:.1f}%")

# EPS成長
eps_growth = analysis_data.get('eps_growth', 0)
if eps_growth > 30:
    advantages.append(f"🚀 EPS爆發成長 {eps_growth:.1f}%")
elif eps_growth > 15:
    advantages.append(f"📈 EPS高成長 {eps_growth:.1f}%")
elif eps_growth > 8:
    advantages.append(f"📊 EPS穩健成長 {eps_growth:.1f}%")

# ROE
roe = analysis_data.get('roe', 0)
if roe > 20:
    advantages.append(f"⭐ ROE優異 {roe:.1f}%")
elif roe > 15:
    advantages.append(f"✨ ROE良好 {roe:.1f}%")
elif roe > 10:
    advantages.append(f"📋 ROE穩健 {roe:.1f}%")

# 本益比
pe_ratio = analysis_data.get('pe_ratio', 999)
if pe_ratio < 10:
    advantages.append(f"💎 低本益比 {pe_ratio:.1f}倍")
elif pe_ratio < 15:
    advantages.append(f"🔍 合理本益比 {pe_ratio:.1f}倍")

# 營收成長
revenue_growth = analysis_data.get('revenue_growth', 0)
if revenue_growth > 20:
    advantages.append(f"🏢 營收高成長 {revenue_growth:.1f}%")
elif revenue_growth > 10:
    advantages.append(f"📈 營收成長 {revenue_growth:.1f}%")

# 連續配息
dividend_years = analysis_data.get('dividend_consecutive_years', 0)
if dividend_years > 10:
    advantages.append(f"🏆 連續配息 {dividend_years}年")
elif dividend_years > 5:
    advantages.append(f"🎯 穩定配息 {dividend_years}年")

return advantages
```

def extract_institutional_flows_detailed(analysis_data):
“”“提取詳細法人動向（修復版）”””
flows = []

```
# 外資買賣
foreign_net = analysis_data.get('foreign_net_buy', 0)
if foreign_net != 0:
    foreign_億 = foreign_net / 10000
    consecutive_days = analysis_data.get('consecutive_buy_days', 0)
    
    if foreign_net > 50000:  # 5億以上
        if consecutive_days > 3:
            flows.append(f"🔥 外資連{consecutive_days}日大買 {foreign_億:.1f}億")
        else:
            flows.append(f"🟢 外資大幅買超 {foreign_億:.1f}億")
    elif foreign_net > 10000:  # 1億以上
        flows.append(f"📈 外資買超 {foreign_億:.1f}億")
    elif foreign_net > 0:
        flows.append(f"🟡 外資小買 {foreign_億:.1f}億")
    elif foreign_net < -50000:  # 大量賣出
        flows.append(f"🔴 外資大賣 {abs(foreign_億):.1f}億")
    elif foreign_net < -10000:
        flows.append(f"📉 外資賣超 {abs(foreign_億):.1f}億")
    elif foreign_net < 0:
        flows.append(f"🟠 外資小賣 {abs(foreign_億):.1f}億")

# 投信買賣
trust_net = analysis_data.get('trust_net_buy', 0)
if trust_net != 0:
    trust_億 = trust_net / 10000
    if trust_net > 20000:  # 2億以上
        flows.append(f"🏦 投信大買 {trust_億:.1f}億")
    elif trust_net > 5000:
        flows.append(f"📊 投信買超 {trust_億:.1f}億")
    elif trust_net > 0:
        flows.append(f"💼 投信小買 {trust_億:.1f}億")
    elif trust_net < -20000:
        flows.append(f"🔻 投信大賣 {abs(trust_億):.1f}億")
    elif trust_net < 0:
        flows.append(f"📉 投信賣超 {abs(trust_億):.1f}億")

# 自營商
dealer_net = analysis_data.get('dealer_net_buy', 0)
if dealer_net != 0:
    dealer_億 = dealer_net / 10000
    if abs(dealer_net) > 10000:  # 1億以上才顯示
        if dealer_net > 0:
            flows.append(f"🏪 自營買超 {dealer_億:.1f}億")
        else:
            flows.append(f"🏪 自營賣超 {abs(dealer_億):.1f}億")

# 三大法人合計
total_institutional = analysis_data.get('total_institutional', 0)
if abs(total_institutional) > 50000:  # 5億以上才顯示合計
    total_億 = total_institutional / 10000
    if total_institutional > 0:
        flows.append(f"🏛️ 三大法人合計買超 {total_億:.1f}億")
    else:
        flows.append(f"🏛️ 三大法人合計賣超 {abs(total_億):.1f}億")

return flows
```

def generate_enhanced_html_content(strategies_data, time_slot, date):
“”“生成增強版HTML內容（修復版）”””

```
html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>📊 {time_slot} 股票分析報告 - {date}</title>
    <style>
        body {{
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f6fa;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .section {{
            padding: 30px;
        }}
        .stock-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 5px solid #3498db;
            transition: transform 0.3s ease;
        }}
        .stock-card:hover {{
            transform: translateY(-5px);
        }}
        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}
        .stock-title {{
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stock-price {{
            font-size: 18px;
            font-weight: bold;
        }}
        .price-up {{ color: #e74c3c; }}
        .price-down {{ color: #27ae60; }}
        .indicators-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .indicator-section {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        }}
        .indicator-title {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .indicator-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .indicator-list li {{
            padding: 5px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        .indicator-list li:last-child {{
            border-bottom: none;
        }}
        .recommendation-reason {{
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            font-weight: bold;
        }}
        .price-targets {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        .price-target {{
            background: #e8f5e8;
            border: 2px solid #27ae60;
            border-radius: 8px;
            padding: 10px 15px;
            text-align: center;
            flex: 1;
            min-width: 120px;
        }}
        .price-target.stop-loss {{
            background: #ffeaa7;
            border-color: #fdcb6e;
        }}
        .weak-stock-card {{
            border-left-color: #e74c3c;
            background: #fef9f9;
        }}
        .long-term-card {{
            border-left-color: #f39c12;
        }}
        .no-data {{
            text-align: center;
            color: #7f8c8d;
            padding: 40px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {time_slot} 股票分析報告</h1>
            <p>📅 {date} | 🤖 AI智能分析</p>
        </div>
"""

# 短線推薦
if strategies_data.get('short_term'):
    html += '<div class="section"><h2>🔥 短線推薦</h2>'
    
    for stock in strategies_data['short_term']:
        analysis = stock.get('analysis', {})
        change_class = 'price-up' if analysis.get('change_percent', 0) >= 0 else 'price-down'
        change_symbol = '+' if analysis.get('change_percent', 0) >= 0 else ''
        
        # 提取詳細指標
        technical_indicators = extract_technical_indicators_detailed(analysis)
        fundamental_advantages = extract_fundamental_advantages_detailed(analysis)
        institutional_flows = extract_institutional_flows_detailed(analysis)
        
        html += f'''
        <div class="stock-card">
            <div class="stock-header">
                <div class="stock-title">{stock['code']} {stock['name']}</div>
                <div class="stock-price {change_class}">
                    {stock['current_price']:.1f} ({change_symbol}{analysis.get('change_percent', 0):.1f}%)
                </div>
            </div>
            
            <div class="recommendation-reason">
                📋 推薦理由: {stock.get('reason', '技術面分析看好')}
            </div>
            
            <div class="indicators-grid">
        '''
        
        # 技術指標區塊
        if technical_indicators:
            html += f'''
                <div class="indicator-section">
                    <div class="indicator-title">📊 技術指標</div>
                    <ul class="indicator-list">
            '''
            for indicator in technical_indicators:
                html += f'<li>{indicator}</li>'
            html += '</ul></div>'
        
        # 基本面區塊
        if fundamental_advantages:
            html += f'''
                <div class="indicator-section">
                    <div class="indicator-title">💎 基本面優勢</div>
                    <ul class="indicator-list">
            '''
            for advantage in fundamental_advantages:
                html += f'<li>{advantage}</li>'
            html += '</ul></div>'
        
        # 法人動向區塊
        if institutional_flows:
            html += f'''
                <div class="indicator-section">
                    <div class="indicator-title">🏛️ 法人動向</div>
                    <ul class="indicator-list">
            '''
            for flow in institutional_flows:
                html += f'<li>{flow}</li>'
            html += '</ul></div>'
        
        html += '</div>'  # 結束 indicators-grid
        
        # 價格目標
        if stock.get('target_price') or stock.get('stop_loss'):
            html += '<div class="price-targets">'
            if stock.get('target_price'):
                upside = ((stock['target_price'] - stock['current_price']) / stock['current_price'] * 100)
                html += f'''
                    <div class="price-target">
                        <div style="font-weight: bold;">🎯 目標價</div>
                        <div>{stock['target_price']:.1f} 元</div>
                        <div style="font-size: 12px;">上漲空間 {upside:.1f}%</div>
                    </div>
                '''
            if stock.get('stop_loss'):
                html += f'''
                    <div class="price-target stop-loss">
                        <div style="font-weight: bold;">🛑 停損價</div>
                        <div>{stock['stop_loss']:.1f} 元</div>
                    </div>
                '''
            html += '</div>'
        
        html += '</div>'  # 結束 stock-card
    
    html += '</div>'  # 結束 section

# 長線推薦
if strategies_data.get('long_term'):
    html += '<div class="section"><h2>💎 長線推薦</h2>'
    
    for stock in strategies_data['long_term']:
        analysis = stock.get('analysis', {})
        change_class = 'price-up' if analysis.get('change_percent', 0) >= 0 else 'price-down'
        change_symbol = '+' if analysis.get('change_percent', 0) >= 0 else ''
        
        # 提取詳細指標
        fundamental_advantages = extract_fundamental_advantages_detailed(analysis)
        institutional_flows = extract_institutional_flows_detailed(analysis)
        
        html += f'''
        <div class="stock-card long-term-card">
            <div class="stock-header">
                <div class="stock-title">{stock['code']} {stock['name']}</div>
                <div class="stock-price {change_class}">
                    {stock['current_price']:.1f} ({change_symbol}{analysis.get('change_percent', 0):.1f}%)
                </div>
            </div>
            
            <div class="recommendation-reason">
                📋 投資理由: {stock.get('reason', '基本面穩健，適合長期投資')}
            </div>
            
            <div class="indicators-grid">
        '''
        
        # 基本面區塊（長線重點）
        if fundamental_advantages:
            html += f'''
                <div class="indicator-section">
                    <div class="indicator-title">💎 基本面優勢</div>
                    <ul class="indicator-list">
            '''
            for advantage in fundamental_advantages:
                html += f'<li>{advantage}</li>'
            html += '</ul></div>'
        
        # 法人動向區塊
        if institutional_flows:
            html += f'''
                <div class="indicator-section">
                    <div class="indicator-title">🏛️ 法人動向</div>
                    <ul class="indicator-list">
            '''
            for flow in institutional_flows:
                html += f'<li>{flow}</li>'
            html += '</ul></div>'
        
        html += '</div>'  # 結束 indicators-grid
        html += '</div>'  # 結束 stock-card
    
    html += '</div>'  # 結束 section

# 風險警示
if strategies_data.get('weak_stocks'):
    html += '<div class="section"><h2>⚠️ 風險警示</h2>'
    
    for stock in strategies_data['weak_stocks']:
        analysis = stock.get('analysis', {})
        change_class = 'price-down'
        
        html += f'''
        <div class="stock-card weak-stock-card">
            <div class="stock-header">
                <div class="stock-title">{stock['code']} {stock['name']}</div>
                <div class="stock-price {change_class}">
                    {stock['current_price']:.1f} ({analysis.get('change_percent', 0):.1f}%)
                </div>
            </div>
            
            <div class="recommendation-reason" style="background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);">
                ⚠️ 警示原因: {stock.get('alert_reason', '技術面轉弱')}
            </div>
        </div>
        '''
    
    html += '</div>'  # 結束 section

# 結尾
html += '''
        <div class="section" style="text-align: center; background: #f8f9fa; color: #7f8c8d;">
            <p>⚠️ 本報告僅供參考，不構成投資建議</p>
            <p>💡 投資有風險，請審慎評估</p>
            <p>🤖 由AI智能分析系統生成</p>
        </div>
    </div>
</body>
</html>
'''

return html
```

def send_enhanced_combined_recommendations(strategies_data, time_slot_name):
“”“發送增強版組合推薦（修復版）”””

```
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    
    # 生成HTML內容
    date_str = datetime.now().strftime('%Y/%m/%d')
    html_content = generate_enhanced_html_content(strategies_data, time_slot_name, date_str)
    
    # 創建郵件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📊 {time_slot_name} 股票分析報告 - {date_str}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    
    # 添加HTML內容
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)
    
    # 發送郵件
    server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
    server.starttls()
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
    
    print(f"✅ 增強版推薦報告已發送: {time_slot_name}")
    return True
    
except Exception as e:
    print(f"❌ 發送增強版報告失敗: {e}")
    return False
```

‘’’

```
    # 寫入修復文件
    with open('enhanced_display_functions.py', 'w', encoding='utf-8') as f:
        f.write("# 增強版顯示功能（修復版）\n")
        f.write(enhanced_notifier_code)
    
    print("✅ 增強版顯示函數已創建")

def create_optimized_filter_logic(self):
    """創建優化的篩選邏輯"""
    
    optimized_filter_code = '''
```

def generate_optimized_recommendations_v2(self, analyses: List[Dict[str, Any]], time_slot: str) -> Dict[str, List[Dict[str, Any]]]:
“”“生成優化推薦V2（更智能的篩選邏輯）”””
if not analyses:
return {“short_term”: [], “long_term”: [], “weak_stocks”: []}

```
config = self.time_slot_config[time_slot]
limits = config['recommendation_limits']

# 過濾有效分析
valid_analyses = [a for a in analyses if a.get('data_quality') != 'limited']

# 🔥 短線推薦邏輯（更精準）
short_term_candidates = []
for analysis in valid_analyses:
    score = analysis.get('weighted_score', 0)
    change_percent = analysis.get('change_percent', 0)
    volume_ratio = analysis.get('volume_ratio', 1)
    rsi = analysis.get('rsi', 50)
    
    # 多條件篩選
    conditions_met = 0
    
    # 條件1: 基本評分
    if score >= 3:
        conditions_met += 2
    elif score >= 1:
        conditions_met += 1
    
    # 條件2: 技術指標強勢
    technical_signals = analysis.get('technical_signals', {})
    if technical_signals.get('macd_golden_cross'):
        conditions_met += 3
    elif technical_signals.get('macd_bullish'):
        conditions_met += 2
    
    if technical_signals.get('ma20_bullish'):
        conditions_met += 2
    if technical_signals.get('ma_golden_cross'):
        conditions_met += 2
    
    # 條件3: RSI適中且有動能
    if 40 <= rsi <= 70:
        conditions_met += 1
    elif rsi < 30:  # 超賣反彈
        conditions_met += 2
    elif rsi > 80:  # 過熱扣分
        conditions_met -= 2
    
    # 條件4: 成交量放大
    if volume_ratio > 2.5:
        conditions_met += 3
    elif volume_ratio > 1.8:
        conditions_met += 2
    elif volume_ratio > 1.3:
        conditions_met += 1
    
    # 條件5: 價格表現
    if change_percent > 5:
        conditions_met += 3
    elif change_percent > 3:
        conditions_met += 2
    elif change_percent > 1:
        conditions_met += 1
    elif change_percent < -3:
        conditions_met -= 2
    
    # 條件6: 法人支持
    foreign_net = analysis.get('foreign_net_buy', 0)
    if foreign_net > 20000:
        conditions_met += 2
    elif foreign_net > 5000:
        conditions_met += 1
    elif foreign_net < -20000:
        conditions_met -= 2
    
    # 短線推薦門檻：需要至少6個條件點數
    if conditions_met >= 6:
        analysis['short_term_conditions'] = conditions_met
        short_term_candidates.append(analysis)

# 按條件點數排序
short_term_candidates.sort(key=lambda x: x.get('short_term_conditions', 0), reverse=True)

# 🏆 長線推薦邏輯（重視基本面和穩定性）
long_term_candidates = []
for analysis in valid_analyses:
    score = analysis.get('weighted_score', 0)
    
    conditions_met = 0
    stability_score = 0
    
    # 條件1: 基本評分（門檻較低）
    if score >= 0:
        conditions_met += 1
    
    # 條件2: 基本面優勢
    dividend_yield = analysis.get('dividend_yield', 0)
    eps_growth = analysis.get('eps_growth', 0)
    roe = analysis.get('roe', 0)
    pe_ratio = analysis.get('pe_ratio', 999)
    
    if dividend_yield > 5:
        conditions_met += 4
        stability_score += 3
    elif dividend_yield > 3:
        conditions_met += 3
        stability_score += 2
    elif dividend_yield > 1.5:
        conditions_met += 2
        stability_score += 1
    
    if eps_growth > 20:
        conditions_met += 4
    elif eps_growth > 10:
        conditions_met += 3
    elif eps_growth > 5:
        conditions_met += 2
    elif eps_growth < -5:
        conditions_met -= 2
    
    if roe > 15:
        conditions_met += 3
        stability_score += 2
    elif roe > 10:
        conditions_met += 2
        stability_score += 1
    elif roe < 5:
        conditions_met -= 1
    
    if pe_ratio < 12:
        conditions_met += 2
        stability_score += 2
    elif pe_ratio < 18:
        conditions_met += 1
        stability_score += 1
    elif pe_ratio > 30:
        conditions_met -= 2
    
    # 條件3: 法人持續支持
    foreign_net = analysis.get('foreign_net_buy', 0)
    trust_net = analysis.get('trust_net_buy', 0)
    consecutive_days = analysis.get('consecutive_buy_days', 0)
    
    if foreign_net > 30000:
        conditions_met += 3
        stability_score += 2
    elif foreign_net > 10000:
        conditions_met += 2
        stability_score += 1
    elif foreign_net > 0:
        conditions_met += 1
    
    if trust_net > 10000:
        conditions_met += 2
    elif trust_net > 0:
        conditions_met += 1
    
    if consecutive_days > 5:
        conditions_met += 2
        stability_score += 2
    elif consecutive_days > 3:
        conditions_met += 1
        stability_score += 1
    
    # 條件4: 財務穩定性
    debt_ratio = analysis.get('debt_ratio', 50)
    dividend_years = analysis.get('dividend_consecutive_years', 0)
    
    if debt_ratio < 30:
        stability_score += 2
        conditions_met += 1
    elif debt_ratio > 70:
        stability_score -= 1
        conditions_met -= 1
    
    if dividend_years > 10:
        stability_score += 3
        conditions_met += 2
    elif dividend_years > 5:
        stability_score += 2
        conditions_met += 1
    
    # 條件5: 成交量穩定性
    trade_value = analysis.get('trade_value', 0)
    if trade_value > 100000000:  # 1億以上
        stability_score += 1
        conditions_met += 1
    
    # 長線推薦門檻：需要至少8個條件點數且穩定性分數>=3
    if conditions_met >= 8 and stability_score >= 3:
        analysis['long_term_conditions'] = conditions_met
        analysis['stability_score'] = stability_score
        long_term_candidates.append(analysis)

# 按穩定性分數和條件點數排序
long_term_candidates.sort(
    key=lambda x: (x.get('stability_score', 0), x.get('long_term_conditions', 0)), 
    reverse=True
)

# ⚠️ 風險股票邏輯（多重警示）
weak_candidates = []
for analysis in valid_analyses:
    score = analysis.get('weighted_score', 0)
    change_percent = analysis.get('change_percent', 0)
    
    risk_flags = 0
    risk_reasons = []
    
    # 風險1: 評分極低
    if score <= -3:
        risk_flags += 3
        risk_reasons.append("綜合評分極低")
    elif score <= -1:
        risk_flags += 1
        risk_reasons.append("評分偏低")
    
    # 風險2: 價格大跌
    if change_percent <= -5:
        risk_flags += 3
        risk_reasons.append(f"大跌{abs(change_percent):.1f}%")
    elif change_percent <= -3:
        risk_flags += 2
        risk_reasons.append(f"下跌{abs(change_percent):.1f}%")
    
    # 風險3: 法人大量賣出
    foreign_net = analysis.get('foreign_net_buy', 0)
    if foreign_net < -30000:
        risk_flags += 3
        risk_reasons.append("外資大量賣出")
    elif foreign_net < -10000:
        risk_flags += 2
        risk_reasons.append("外資賣超")
    
    # 風險4: 技術指標轉弱
    technical_signals = analysis.get('technical_signals', {})
    if technical_signals.get('macd_death_cross'):
        risk_flags += 2
        risk_reasons.append("MACD死叉")
    if technical_signals.get('ma_death_cross'):
        risk_flags += 2
        risk_reasons.append("均線轉空")
    
    # 風險5: RSI過熱
    rsi = analysis.get('rsi', 50)
    if rsi > 85:
        risk_flags += 2
        risk_reasons.append("RSI嚴重超買")
    
    # 風險6: 基本面惡化
    eps_growth = analysis.get('eps_growth', 0)
    if eps_growth < -15:
        risk_flags += 2
        risk_reasons.append("EPS大幅衰退")
    
    # 風險門檻：需要至少4個風險點數
    if risk_flags >= 4:
        analysis['risk_flags'] = risk_flags
        analysis['risk_reasons'] = risk_reasons
        weak_candidates.append(analysis)

# 按風險程度排序
weak_candidates.sort(key=lambda x: x.get('risk_flags', 0), reverse=True)

# 🎯 生成最終推薦
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
        "analysis": analysis,
        "confidence_level": "高" if analysis.get('short_term_conditions', 0) >= 10 else "中"
    })

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
        "analysis": analysis,
        "stability_rating": "A" if analysis.get('stability_score', 0) >= 6 else "B"
    })

weak_stocks = []
for analysis in weak_candidates[:limits['weak_stocks']]:
    main_reason = "、".join(analysis.get('risk_reasons', [])[:2])
    weak_stocks.append({
        "code": analysis["code"],
        "name": analysis["name"],
        "current_price": analysis["current_price"],
        "alert_reason": main_reason,
        "trade_value": analysis["trade_value"],
        "analysis": analysis,
        "risk_level": "高" if analysis.get('risk_flags', 0) >= 7 else "中"
    })

return {
    "short_term": short_term,
    "long_term": long_term,
    "weak_stocks": weak_stocks
}
```

‘’’

```
    # 寫入篩選邏輯文件
    with open('optimized_filter_logic.py', 'w', encoding='utf-8') as f:
        f.write("# 優化篩選邏輯V2\n")
        f.write("# 請將此方法替換到 enhanced_stock_bot.py 中\n\n")
        f.write(optimized_filter_code)
    
    print("✅ 優化篩選邏輯已創建")

def create_integration_guide(self):
    """創建整合指南"""
    
    guide_content = f"""
```

# 顯示問題修復和篩選優化整合指南

## 修復時間

{datetime.now().strftime(’%Y-%m-%d %H:%M:%S’)}

## 修復內容

### 1. 技術指標顯示修復

- 修復 RSI、MACD、均線、成交量指標不顯示問題
- 加入詳細的技術指標標籤和數值顯示
- 使用顏色標示不同指標狀態

### 2. 基本面優勢顯示修復

- 修復殖利率、EPS成長、ROE等不顯示問題
- 加入具體數值和優勢級別標示
- 突出顯示高殖利率、高成長等優勢

### 3. 法人動向顯示修復

- 修復外資、投信、自營商買賣不顯示問題
- 加入具體金額和連續買賣天數
- 使用圖示區分不同程度的買賣超

### 4. 篩選邏輯優化

- 短線推薦：採用多條件計分制（技術+量能+法人）
- 長線推薦：重視基本面穩定性和成長性
- 風險警示：多重風險因子識別

## 整合步驟

### 步驟1: 備份現有文件

已完成備份到: {self.backup_dir}

### 步驟2: 更新 notifier.py

將 enhanced_display_functions.py 中的函數加入到 notifier.py：

```python
# 在 notifier.py 中加入以下函數
{open('enhanced_display_functions.py', 'r', encoding='utf-8').read() if os.path.exists('enhanced_display_functions.py') else ''}
```

### 步驟3: 更新 enhanced_stock_bot.py

將 optimized_filter_logic.py 中的篩選邏輯替換現有的 generate_recommendations_optimized 方法

### 步驟4: 測試驗證

執行測試確認修復效果：

```bash
python enhanced_stock_bot.py afternoon_scan
```

## 預期效果

### 顯示修復效果

- ✅ 技術指標完整顯示（RSI、MACD、均線、成交量）
- ✅ 基本面優勢詳細展示（殖利率、EPS、ROE等）
- ✅ 法人動向具體顯示（買賣金額、天數）

### 篩選優化效果

- 🎯 短線推薦更精準（多條件計分）
- 💎 長線推薦更穩健（重視基本面）
- ⚠️ 風險識別更準確（多重因子）

## 注意事項

1. 建議先在測試環境驗證修復效果
1. 如有問題可隨時使用備份文件回滾
1. 新的篩選邏輯可能會改變推薦結果數量

## 技術支援

如有問題請檢查：

1. 函數名稱是否正確
1. 數據欄位是否存在
1. 郵件配置是否正確
   “””
   
   ```
    with open('integration_guide.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ 整合指南已創建")
   ```
   
   def run_complete_fix(self):
   “”“執行完整修復”””
   print(“🔧 開始修復技術指標、基本面、法人動向顯示問題”)
   print(“🎯 同時優化篩選邏輯”)
   print(”=” * 70)
   
   ```
    # 1. 備份文件
    self.backup_files()
    
    # 2. 創建修復功能
    self.create_enhanced_display_functions()
    
    # 3. 創建優化篩選邏輯
    self.create_optimized_filter_logic()
    
    # 4. 創建整合指南
    self.create_integration_guide()
    
    print("\n" + "=" * 70)
    print("🎉 修復文件生成完成！")
    print("=" * 70)
    
    print("\n📁 生成的文件:")
    print("  ✅ enhanced_display_functions.py - 增強顯示功能")
    print("  ✅ optimized_filter_logic.py - 優化篩選邏輯")
    print("  ✅ integration_guide.md - 整合指南")
    
    print(f"\n💾 備份位置: {self.backup_dir}")
    
    print("\n📋 下一步操作:")
    print("1. 查看 integration_guide.md 了解詳細整合步驟")
    print("2. 將修復代碼整合到現有文件中")
    print("3. 執行測試驗證修復效果")
    
    print("\n🎯 修復效果:")
    print("  📊 技術指標: RSI、MACD、均線詳細顯示")
    print("  💎 基本面: 殖利率、EPS、ROE具體數值")
    print("  🏛️ 法人動向: 買賣金額、連續天數")
    print("  🔍 篩選邏輯: 多條件智能篩選")
   ```

def main():
“”“主函數”””
print(“🔧 技術指標、基本面、法人動向顯示修復工具”)
print(“🎯 同時優化股票篩選邏輯”)

```
response = input("\n是否開始修復？(y/N): ")
if response.lower() not in ['y', 'yes']:
    print("❌ 修復已取消")
    return

fixer = DisplayAndFilterFixer()
fixer.run_complete_fix()
```

if **name** == “**main**”:
main()
