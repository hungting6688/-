"""
enhanced_notifier.py - 增強型通知系統（加入現價和資金流向）
支援顯示現價、漲跌百分比、資金買超等資訊
"""
import os
import time
import json
import random
import logging
import traceback
import smtplib
import socket
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

# 導入配置
from config import EMAIL_CONFIG, FILE_BACKUP, RETRY_CONFIG, LOG_DIR, CACHE_DIR

# 嘗試導入白話文轉換模組
try:
    import text_formatter
    WHITE_TEXT_AVAILABLE = True
except ImportError:
    WHITE_TEXT_AVAILABLE = False

# 配置日誌
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'notifier.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def format_number(num):
    """格式化數字顯示"""
    if num >= 100000000:  # 億
        return f"{num/100000000:.1f}億"
    elif num >= 10000:  # 萬
        return f"{num/10000:.0f}萬"
    else:
        return f"{num:,.0f}"

def format_price_change(change_percent):
    """格式化漲跌幅顯示"""
    if change_percent > 0:
        return f"📈 +{change_percent:.2f}%"
    elif change_percent < 0:
        return f"📉 {change_percent:.2f}%"
    else:
        return "➖ 0.00%"

def send_combined_recommendations(strategies_data, time_slot):
    """
    發送包含三種策略的股票推薦通知（增強版）
    
    參數:
    - strategies_data: 包含三種策略的字典 {"short_term": [...], "long_term": [...], "weak_stocks": [...]}
    - time_slot: 時段名稱
    """
    short_term_stocks = strategies_data.get("short_term", [])
    long_term_stocks = strategies_data.get("long_term", [])
    weak_stocks = strategies_data.get("weak_stocks", [])
    
    if not short_term_stocks and not long_term_stocks and not weak_stocks:
        message = f"【{time_slot}分析報告】\n\n沒有符合條件的推薦股票和警示"
        subject = f"【{time_slot}分析報告】- 無推薦"
        send_notification(message, subject)
        return
    
    # 生成通知消息
    today = datetime.now().strftime("%Y/%m/%d")
    
    # 嘗試使用白話文生成介紹
    try:
        if WHITE_TEXT_AVAILABLE:
            import text_formatter
            intro_text = text_formatter.generate_intro_text(time_slot.lower().replace(' ', '_'))
            message = f"📈 {today} {time_slot}分析報告\n\n{intro_text}\n\n"
        else:
            message = f"📈 {today} {time_slot}分析報告\n\n"
    except Exception as e:
        message = f"📈 {today} {time_slot}分析報告\n\n"
        logging.error(f"生成引言失敗: {e}")
    
    # 短線推薦部分
    message += "【短線推薦】\n\n"
    if short_term_stocks:
        for stock in short_term_stocks:
            # 基本資訊
            message += f"📈 {stock['code']} {stock['name']}\n"
            
            # 現價和漲跌幅
            current_price = stock.get('current_price', 0)
            change_percent = stock.get('analysis', {}).get('change_percent', 0) if 'analysis' in stock else 0
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            
            # 成交量和資金流向
            trade_value = stock.get('trade_value', 0)
            message += f"💵 成交金額: {format_number(trade_value)}\n"
            
            # 法人買超資訊（如果有）
            if 'analysis' in stock:
                analysis = stock['analysis']
                if 'foreign_net_buy' in analysis:
                    foreign_net = analysis['foreign_net_buy']
                    if foreign_net > 0:
                        message += f"🏦 外資買超: {format_number(foreign_net*10000)} 元\n"
                    elif foreign_net < 0:
                        message += f"🏦 外資賣超: {format_number(abs(foreign_net)*10000)} 元\n"
                
                if 'trust_net_buy' in analysis:
                    trust_net = analysis['trust_net_buy']
                    if trust_net > 0:
                        message += f"🏢 投信買超: {format_number(trust_net*10000)} 元\n"
                    elif trust_net < 0:
                        message += f"🏢 投信賣超: {format_number(abs(trust_net)*10000)} 元\n"
            
            # 推薦理由
            message += f"📊 推薦理由: {stock['reason']}\n"
            
            # 目標價和止損價
            message += f"🎯 目標價: {stock['target_price']} | 🛡️ 止損價: {stock['stop_loss']}\n"
            
            # 技術指標（如果有）
            if 'analysis' in stock:
                analysis = stock['analysis']
                if 'rsi' in analysis:
                    message += f"📉 RSI: {analysis['rsi']:.1f}"
                if 'volume_ratio' in analysis:
                    message += f" | 量比: {analysis.get('volume_ratio', 0):.1f}倍"
                message += "\n"
            
            message += "\n"
    else:
        message += "今日無短線推薦股票\n\n"
    
    # 長線推薦部分
    message += "【長線潛力】\n\n"
    if long_term_stocks:
        for stock in long_term_stocks:
            # 基本資訊
            message += f"📊 {stock['code']} {stock['name']}\n"
            
            # 現價和漲跌幅
            current_price = stock.get('current_price', 0)
            change_percent = stock.get('analysis', {}).get('change_percent', 0) if 'analysis' in stock else 0
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            
            # 成交量
            trade_value = stock.get('trade_value', 0)
            message += f"💵 成交金額: {format_number(trade_value)}\n"
            
            # 基本面資訊（如果有）
            if 'analysis' in stock:
                analysis = stock['analysis']
                if 'dividend_yield' in analysis and analysis['dividend_yield'] > 0:
                    message += f"💸 殖利率: {analysis['dividend_yield']:.1f}%\n"
                if 'pe_ratio' in analysis and analysis['pe_ratio'] > 0:
                    message += f"📊 本益比: {analysis['pe_ratio']:.1f}\n"
                if 'eps_growth' in analysis and analysis['eps_growth'] != 0:
                    message += f"📈 EPS成長率: {analysis['eps_growth']:.1f}%\n"
            
            # 推薦理由
            message += f"📊 推薦理由: {stock['reason']}\n"
            
            # 目標價和止損價
            message += f"🎯 目標價: {stock['target_price']} | 🛡️ 止損價: {stock['stop_loss']}\n\n"
    else:
        message += "今日無長線推薦股票\n\n"
    
    # 極弱股警示部分
    message += "【極弱股警示】\n\n"
    if weak_stocks:
        for stock in weak_stocks:
            # 基本資訊
            message += f"⚠️ {stock['code']} {stock['name']}\n"
            
            # 現價和跌幅
            current_price = stock.get('current_price', 0)
            change_percent = stock.get('analysis', {}).get('change_percent', 0) if 'analysis' in stock else 0
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            
            # 成交量
            trade_value = stock.get('trade_value', 0)
            message += f"💵 成交金額: {format_number(trade_value)}\n"
            
            # 法人賣超資訊（如果有）
            if 'analysis' in stock:
                analysis = stock['analysis']
                if 'foreign_net_buy' in analysis and analysis['foreign_net_buy'] < -10000:
                    message += f"🏦 外資賣超: {format_number(abs(analysis['foreign_net_buy'])*10000)} 元\n"
            
            # 警示原因
            message += f"⚠️ 警示原因: {stock['alert_reason']}\n\n"
    else:
        message += "今日無極弱股警示\n\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_parts = []
    html_parts.append("""
    <html>
    <head>
        <style>
            body { font-family: 'Microsoft JhengHei', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; }
            .header { color: #0066cc; font-size: 24px; font-weight: bold; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; }
            .intro { margin-bottom: 20px; background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #0066cc; }
            .section { margin-bottom: 30px; }
            .section-title { color: #333; font-size: 18px; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
            .stock { margin-bottom: 20px; border-left: 4px solid #0066cc; padding-left: 15px; background-color: #fafafa; padding: 15px; border-radius: 3px; }
            .stock.long-term { border-left-color: #009900; }
            .stock.weak { border-left-color: #cc0000; }
            .stock-name { font-weight: bold; font-size: 16px; margin-bottom: 8px; }
            .stock-code { font-size: 14px; color: #666; margin-left: 8px; }
            .price-info { margin: 10px 0; font-size: 16px; }
            .price { font-weight: bold; color: #0066cc; }
            .change-positive { color: #cc0000; font-weight: bold; }
            .change-negative { color: #009900; font-weight: bold; }
            .change-neutral { color: #666; }
            .trade-info { margin: 8px 0; color: #666; }
            .institutional { background-color: #e8f4f8; padding: 8px; border-radius: 3px; margin: 8px 0; }
            .buy-excess { color: #cc0000; }
            .sell-excess { color: #009900; }
            .indicators { margin: 10px 0; font-size: 14px; color: #666; }
            .target-info { margin: 10px 0; background-color: #fff3cd; padding: 8px; border-radius: 3px; }
            .reason { margin: 10px 0; font-style: italic; color: #555; }
            .footer { color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px; }
        </style>
    </head>
    <body>
        <div class="header">""" + f"📈 {today} {time_slot}分析報告" + """</div>
    """)
    
    # 添加引言段落
    try:
        if WHITE_TEXT_AVAILABLE:
            intro_text = text_formatter.generate_intro_text(time_slot.lower().replace(' ', '_'))
            html_parts.append(f"""<div class="intro">{intro_text.replace(chr(10), '<br>')}</div>""")
    except Exception:
        pass
    
    # 短線推薦 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【短線推薦】</div>
    """)
    
    if short_term_stocks:
        for stock in short_term_stocks:
            current_price = stock.get('current_price', 0)
            change_percent = stock.get('analysis', {}).get('change_percent', 0) if 'analysis' in stock else 0
            change_class = "change-positive" if change_percent > 0 else "change-negative" if change_percent < 0 else "change-neutral"
            change_symbol = "+" if change_percent > 0 else ""
            
            html_parts.append(f"""
            <div class="stock">
                <div class="stock-name">📈 {stock['code']} {stock['name']}</div>
                <div class="price-info">
                    <span class="price">現價: {current_price} 元</span>
                    <span class="{change_class}"> {change_symbol}{change_percent:.2f}%</span>
                </div>
                <div class="trade-info">成交金額: {format_number(stock.get('trade_value', 0))}</div>
            """)
            
            # 法人買賣資訊
            if 'analysis' in stock and 'foreign_net_buy' in stock['analysis']:
                foreign_net = stock['analysis']['foreign_net_buy']
                trust_net = stock['analysis'].get('trust_net_buy', 0)
                
                html_parts.append("""<div class="institutional">""")
                if foreign_net > 0:
                    html_parts.append(f"""<span class="buy-excess">外資買超: {format_number(foreign_net*10000)} 元</span>""")
                elif foreign_net < 0:
                    html_parts.append(f"""<span class="sell-excess">外資賣超: {format_number(abs(foreign_net)*10000)} 元</span>""")
                
                if trust_net > 0:
                    html_parts.append(f""" | <span class="buy-excess">投信買超: {format_number(trust_net*10000)} 元</span>""")
                elif trust_net < 0:
                    html_parts.append(f""" | <span class="sell-excess">投信賣超: {format_number(abs(trust_net)*10000)} 元</span>""")
                html_parts.append("""</div>""")
            
            # 技術指標
            if 'analysis' in stock:
                indicators_text = []
                if 'rsi' in stock['analysis']:
                    indicators_text.append(f"RSI: {stock['analysis']['rsi']:.1f}")
                if 'volume_ratio' in stock['analysis']:
                    indicators_text.append(f"量比: {stock['analysis'].get('volume_ratio', 0):.1f}倍")
                if indicators_text:
                    html_parts.append(f"""<div class="indicators">{' | '.join(indicators_text)}</div>""")
            
            html_parts.append(f"""
                <div class="reason">推薦理由: {stock['reason']}</div>
                <div class="target-info">
                    🎯 目標價: <strong>{stock['target_price']}</strong> | 
                    🛡️ 止損價: <strong>{stock['stop_loss']}</strong>
                </div>
            </div>
            """)
    else:
        html_parts.append("""<div style="color: #666;">今日無短線推薦股票</div>""")
    
    html_parts.append("""</div>""")
    
    # 長線推薦 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【長線潛力】</div>
    """)
    
    if long_term_stocks:
        for stock in long_term_stocks:
            current_price = stock.get('current_price', 0)
            change_percent = stock.get('analysis', {}).get('change_percent', 0) if 'analysis' in stock else 0
            change_class = "change-positive" if change_percent > 0 else "change-negative" if change_percent < 0 else "change-neutral"
            change_symbol = "+" if change_percent > 0 else ""
            
            html_parts.append(f"""
            <div class="stock long-term">
                <div class="stock-name">📊 {stock['code']} {stock['name']}</div>
                <div class="price-info">
                    <span class="price">現價: {current_price} 元</span>
                    <span class="{change_class}"> {change_symbol}{change_percent:.2f}%</span>
                </div>
                <div class="trade-info">成交金額: {format_number(stock.get('trade_value', 0))}</div>
            """)
            
            # 基本面資訊
            if 'analysis' in stock:
                fundamental_info = []
                if 'dividend_yield' in stock['analysis'] and stock['analysis']['dividend_yield'] > 0:
                    fundamental_info.append(f"殖利率: {stock['analysis']['dividend_yield']:.1f}%")
                if 'pe_ratio' in stock['analysis'] and stock['analysis']['pe_ratio'] > 0:
                    fundamental_info.append(f"本益比: {stock['analysis']['pe_ratio']:.1f}")
                if 'eps_growth' in stock['analysis'] and stock['analysis']['eps_growth'] != 0:
                    fundamental_info.append(f"EPS成長: {stock['analysis']['eps_growth']:.1f}%")
                
                if fundamental_info:
                    html_parts.append(f"""<div class="indicators">{' | '.join(fundamental_info)}</div>""")
            
            html_parts.append(f"""
                <div class="reason">推薦理由: {stock['reason']}</div>
                <div class="target-info">
                    🎯 目標價: <strong>{stock['target_price']}</strong> | 
                    🛡️ 止損價: <strong>{stock['stop_loss']}</strong>
                </div>
            </div>
            """)
    else:
        html_parts.append("""<div style="color: #666;">今日無長線推薦股票</div>""")
    
    html_parts.append("""</div>""")
    
    # 極弱股警示 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【極弱股警示】</div>
    """)
    
    if weak_stocks:
        for stock in weak_stocks:
            current_price = stock.get('current_price', 0)
            change_percent = stock.get('analysis', {}).get('change_percent', 0) if 'analysis' in stock else 0
            change_symbol = "+" if change_percent > 0 else ""
            
            html_parts.append(f"""
            <div class="stock weak">
                <div class="stock-name">⚠️ {stock['code']} {stock['name']}</div>
                <div class="price-info">
                    <span class="price">現價: {current_price} 元</span>
                    <span class="change-negative"> {change_symbol}{change_percent:.2f}%</span>
                </div>
                <div class="trade-info">成交金額: {format_number(stock.get('trade_value', 0))}</div>
            """)
            
            # 法人賣超資訊
            if 'analysis' in stock and 'foreign_net_buy' in stock['analysis'] and stock['analysis']['foreign_net_buy'] < -10000:
                html_parts.append(f"""
                <div class="institutional">
                    <span class="sell-excess">外資賣超: {format_number(abs(stock['analysis']['foreign_net_buy'])*10000)} 元</span>
                </div>
                """)
            
            html_parts.append(f"""
                <div class="reason" style="color: #cc0000;">警示原因: {stock['alert_reason']}</div>
            </div>
            """)
    else:
        html_parts.append("""<div style="color: #666;">今日無極弱股警示</div>""")
    
    html_parts.append("""</div>""")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_parts.append("""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 """ + timestamp + """<br>
            本分析結果僅供參考，不構成投資建議，投資決策請自行承擔風險。
        </div>
    </body>
    </html>
    """)
    
    html_body = "".join(html_parts)
    subject = f"【{time_slot}分析報告】- {today}"
    send_notification(message, subject, html_body)

# 保留原有的 send_notification 和其他函數...
# （這裡省略其他未修改的函數）

def send_combined_recommendations(strategies_data, time_slot):
    """
    發送包含三種策略的股票推薦通知
    
    參數:
    - strategies_data: 包含三種策略的字典 {"short_term": [...], "long_term": [...], "weak_stocks": [...]}
    - time_slot: 時段名稱
    """
    short_term_stocks = strategies_data.get("short_term", [])
    long_term_stocks = strategies_data.get("long_term", [])
    weak_stocks = strategies_data.get("weak_stocks", [])
    
    if not short_term_stocks and not long_term_stocks and not weak_stocks:
        message = f"【{time_slot}分析報告】\n\n沒有符合條件的推薦股票和警示"
        subject = f"【{time_slot}分析報告】- 無推薦"
        send_notification(message, subject)
        return
    
    # 生成通知消息
    today = datetime.now().strftime("%Y/%m/%d")
    
    # 嘗試使用白話文生成介紹
    try:
        if WHITE_TEXT_AVAILABLE:
            import text_formatter
            intro_text = text_formatter.generate_intro_text(time_slot.lower().replace(' ', '_'))
            message = f"📈 {today} {time_slot}分析報告\n\n{intro_text}\n\n"
        else:
            message = f"📈 {today} {time_slot}分析報告\n\n"
    except Exception as e:
        message = f"📈 {today} {time_slot}分析報告\n\n"
        logging.error(f"生成引言失敗: {e}")
    
    # 短線推薦部分
    message += "【短線推薦】\n\n"
    if short_term_stocks:
        for stock in short_term_stocks:
            message += f"📈 {stock['code']} {stock['name']}\n"
            
            # 嘗試使用白話文生成建議
            try:
                if WHITE_TEXT_AVAILABLE and 'analysis' in stock:  # 如果有完整分析資料
                    plain_text = text_formatter.generate_plain_text(stock['analysis'], "short_term")
                    message += f"{plain_text['description']}\n"
                    message += f"📍 {plain_text['suggestion']}\n\n"
                else:
                    message += f"推薦理由: {stock['reason']}\n"
                    message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
            except Exception as e:
                message += f"推薦理由: {stock['reason']}\n"
                message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
                logging.error(f"生成短線白話文失敗: {e}")
    else:
        message += "今日無短線推薦股票\n\n"
    
    # 長線推薦部分
    message += "【長線潛力】\n\n"
    if long_term_stocks:
        for stock in long_term_stocks:
            message += f"📊 {stock['code']} {stock['name']}\n"
            
            # 嘗試使用白話文生成建議
            try:
                if WHITE_TEXT_AVAILABLE and 'analysis' in stock:  # 如果有完整分析資料
                    plain_text = text_formatter.generate_plain_text(stock['analysis'], "long_term")
                    message += f"{plain_text['description']}\n"
                    message += f"📍 {plain_text['suggestion']}\n\n"
                else:
                    message += f"推薦理由: {stock['reason']}\n"
                    message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
            except Exception as e:
                message += f"推薦理由: {stock['reason']}\n"
                message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
                logging.error(f"生成長線白話文失敗: {e}")
    else:
        message += "今日無長線推薦股票\n\n"
    
    # 極弱股警示部分
    message += "【極弱股】\n\n"
    if weak_stocks:
        for stock in weak_stocks:
            message += f"⚠️ {stock['code']} {stock['name']}\n"
            
            # 嘗試使用白話文生成建議
            try:
                if WHITE_TEXT_AVAILABLE and 'analysis' in stock:  # 如果有完整分析資料
                    plain_text = text_formatter.generate_plain_text(stock['analysis'], "weak_stock")
                    message += f"{plain_text['description']}\n"
                    message += f"📍 {plain_text['suggestion']}\n\n"
                else:
                    message += f"當前價格: {stock['current_price']}\n"
                    message += f"警報原因: {stock['alert_reason']}\n\n"
            except Exception as e:
                message += f"當前價格: {stock['current_price']}\n"
                message += f"警報原因: {stock['alert_reason']}\n\n"
                logging.error(f"生成弱勢股白話文失敗: {e}")
    else:
        message += "今日無極弱股警示\n\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_parts = []
    html_parts.append("""
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; }
            .header { color: #0066cc; font-size: 24px; font-weight: bold; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; }
            .intro { margin-bottom: 20px; background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #0066cc; }
            .section { margin-bottom: 30px; }
            .section-title { color: #333; font-size: 18px; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
            .stock { margin-bottom: 20px; border-left: 4px solid #0066cc; padding-left: 15px; background-color: #fafafa; padding: 10px 15px; border-radius: 3px; }
            .stock.long-term { border-left-color: #009900; }
            .stock.weak { border-left-color: #cc0000; }
            .stock-name { font-weight: bold; font-size: 16px; }
            .stock-code { font-size: 14px; color: #666; margin-left: 8px; }
            .stock-description { margin: 10px 0; color: #333; }
            .suggestion { margin: 10px 0; color: #0066cc; font-weight: bold; background-color: #f0f7ff; padding: 5px 10px; border-radius: 3px; display: inline-block; }
            .price-info { margin: 8px 0; font-size: 14px; }
            .label { color: #666; }
            .price { color: #009900; font-weight: bold; }
            .stop-loss { color: #cc0000; font-weight: bold; }
            .current-price { font-weight: bold; color: #0066cc; }
            .reason { color: #333; font-style: italic; margin: 5px 0; }
            .footer { color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px; }
            .tech-badge { display: inline-block; font-size: 12px; padding: 2px 8px; margin-right: 5px; border-radius: 10px; background-color: #e1f5fe; color: #0288d1; }
            .fundamental-badge { display: inline-block; font-size: 12px; padding: 2px 8px; margin-right: 5px; border-radius: 10px; background-color: #e8f5e9; color: #388e3c; }
            .volume-badge { display: inline-block; font-size: 12px; padding: 2px 8px; margin-right: 5px; border-radius: 10px; background-color: #fff3e0; color: #f57c00; }
        </style>
    </head>
    <body>
        <div class="header">""" + f"📈 {today} {time_slot}分析報告" + """</div>
    """)
    
    # 添加引言段落
    try:
        if WHITE_TEXT_AVAILABLE:
            intro_text = text_formatter.generate_intro_text(time_slot.lower().replace(' ', '_'))
            html_parts.append(f"""<div class="intro">{intro_text.replace(chr(10), '<br>')}</div>""")
    except Exception:
        pass
    
    # 短線推薦 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【短線推薦】</div>
    """)
    
    if short_term_stocks:
        for stock in short_term_stocks:
            html_parts.append(f"""
            <div class="stock">
                <div class="stock-name">📈 {stock['code']} {stock['name']}</div>
            """)
            
            # 添加技術指標標籤
            if 'analysis' in stock and 'signals' in stock['analysis']:
                signals = stock['analysis']['signals']
                if signals.get('ma5_crosses_above_ma20') or signals.get('macd_crosses_above_signal'):
                    html_parts.append(f"""<div class="tech-badge">均線{'金叉' if signals.get('ma5_crosses_above_ma20') else '多頭'}</div>""")
                if signals.get('volume_spike') and signals.get('price_up'):
                    html_parts.append(f"""<div class="volume-badge">成交放大</div>""")
                if signals.get('rsi_bullish'):
                    html_parts.append(f"""<div class="tech-badge">RSI回升</div>""")
            
            # 嘗試使用白話文生成建議
            try:
                if WHITE_TEXT_AVAILABLE and 'analysis' in stock:  # 如果有完整分析資料
                    plain_text = text_formatter.generate_plain_text(stock['analysis'], "short_term")
                    html_parts.append(f"""<div class="stock-description">{plain_text['description']}</div>""")
                    html_parts.append(f"""<div class="suggestion">📍 {plain_text['suggestion']}</div>""")
                else:
                    html_parts.append(f"""<div><span class="label">推薦理由:</span> <span class="reason">{stock['reason']}</span></div>""")
                    html_parts.append(f"""<div><span class="label">目標價:</span> <span class="price">{stock['target_price']}</span> | <span class="label">止損價:</span> <span class="stop-loss">{stock['stop_loss']}</span></div>""")
                    html_parts.append(f"""<div><span class="label">當前價格:</span> <span class="current-price">{stock.get('current_price', '無資料')}</span></div>""")
            except Exception:
                html_parts.append(f"""<div><span class="label">推薦理由:</span> <span class="reason">{stock['reason']}</span></div>""")
                html_parts.append(f"""<div><span class="label">目標價:</span> <span class="price">{stock['target_price']}</span> | <span class="label">止損價:</span> <span class="stop-loss">{stock['stop_loss']}</span></div>""")
                html_parts.append(f"""<div><span class="label">當前價格:</span> <span class="current-price">{stock.get('current_price', '無資料')}</span></div>""")
            
            # 添加綜合評分 (如果有)
            if 'analysis' in stock and 'comprehensive_score' in stock['analysis']:
                html_parts.append(f"""<div><span class="label">綜合評分:</span> <span class="current-price">{stock['analysis']['comprehensive_score']}</span></div>""")
            
            html_parts.append("""</div>""")  # 關閉單支股票區塊
    else:
        html_parts.append("""<div>今日無短線推薦股票</div>""")
    
    html_parts.append("""</div>""")  # 關閉短線推薦區段
    
    # 長線推薦 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【長線潛力】</div>
    """)
    
    if long_term_stocks:
        for stock in long_term_stocks:
            html_parts.append(f"""
            <div class="stock long-term">
                <div class="stock-name">📊 {stock['code']} {stock['name']}</div>
            """)
            
            # 添加基本面指標標籤
            if 'analysis' in stock:
                # 檢查基本面數據
                if stock['analysis'].get('eps_growth', 0) > 5:
                    html_parts.append(f"""<div class="fundamental-badge">獲利成長</div>""")
                if stock['analysis'].get('dividend_yield', 0) > 3:
                    html_parts.append(f"""<div class="fundamental-badge">高股息</div>""")
                if stock['analysis'].get('roe', 0) > 15:
                    html_parts.append(f"""<div class="fundamental-badge">高ROE</div>""")
                
                # 檢查技術面數據
                signals = stock['analysis'].get('signals', {})
                if signals.get('ma5_above_ma20') and signals.get('ma10_above_ma20'):
                    html_parts.append(f"""<div class="tech-badge">均線多頭</div>""")
            
            # 嘗試使用白話文生成建議
            try:
                if WHITE_TEXT_AVAILABLE and 'analysis' in stock:  # 如果有完整分析資料
                    plain_text = text_formatter.generate_plain_text(stock['analysis'], "long_term")
                    html_parts.append(f"""<div class="stock-description">{plain_text['description']}</div>""")
                    html_parts.append(f"""<div class="suggestion">📍 {plain_text['suggestion']}</div>""")
                else:
                    html_parts.append(f"""<div><span class="label">推薦理由:</span> <span class="reason">{stock['reason']}</span></div>""")
                    html_parts.append(f"""<div><span class="label">目標價:</span> <span class="price">{stock['target_price']}</span> | <span class="label">止損價:</span> <span class="stop-loss">{stock['stop_loss']}</span></div>""")
                    html_parts.append(f"""<div><span class="label">當前價格:</span> <span class="current-price">{stock.get('current_price', '無資料')}</span></div>""")
            except Exception:
                html_parts.append(f"""<div><span class="label">推薦理由:</span> <span class="reason">{stock['reason']}</span></div>""")
                html_parts.append(f"""<div><span class="label">目標價:</span> <span class="price">{stock['target_price']}</span> | <span class="label">止損價:</span> <span class="stop-loss">{stock['stop_loss']}</span></div>""")
                html_parts.append(f"""<div><span class="label">當前價格:</span> <span class="current-price">{stock.get('current_price', '無資料')}</span></div>""")
            
            # 添加綜合評分 (如果有)
            if 'analysis' in stock and 'comprehensive_score' in stock['analysis']:
                html_parts.append(f"""<div><span class="label">綜合評分:</span> <span class="current-price">{stock['analysis']['comprehensive_score']}</span></div>""")
            
            html_parts.append("""</div>""")  # 關閉單支股票區塊
    else:
        html_parts.append("""<div>今日無長線推薦股票</div>""")
    
    html_parts.append("""</div>""")  # 關閉長線推薦區段
    
    # 極弱股警示 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【極弱股】</div>
    """)
    
    if weak_stocks:
        for stock in weak_stocks:
            html_parts.append(f"""
            <div class="stock weak">
                <div class="stock-name">⚠️ {stock['code']} {stock['name']}</div>
            """)
            
            # 添加技術指標標籤
            if 'analysis' in stock and 'signals' in stock['analysis']:
                signals = stock['analysis']['signals']
                if signals.get('ma5_crosses_below_ma20'):
                    html_parts.append(f"""<div class="tech-badge">均線死叉</div>""")
                if signals.get('macd_crosses_below_signal'):
                    html_parts.append(f"""<div class="tech-badge">MACD死叉</div>""")
                if signals.get('volume_spike') and signals.get('price_down'):
                    html_parts.append(f"""<div class="volume-badge">放量下跌</div>""")
            
            # 嘗試使用白話文生成建議
            try:
                if WHITE_TEXT_AVAILABLE and 'analysis' in stock:  # 如果有完整分析資料
                    plain_text = text_formatter.generate_plain_text(stock['analysis'], "weak_stock")
                    html_parts.append(f"""<div class="stock-description">{plain_text['description']}</div>""")
                    html_parts.append(f"""<div class="suggestion">📍 {plain_text['suggestion']}</div>""")
                else:
                    html_parts.append(f"""<div><span class="label">當前價格:</span> <span class="current-price">{stock['current_price']}</span></div>""")
                    html_parts.append(f"""<div><span class="label">警報原因:</span> <span class="reason">{stock['alert_reason']}</span></div>""")
            except Exception:
                html_parts.append(f"""<div><span class="label">當前價格:</span> <span class="current-price">{stock['current_price']}</span></div>""")
                html_parts.append(f"""<div><span class="label">警報原因:</span> <span class="reason">{stock['alert_reason']}</span></div>""")
            
            # 添加綜合評分 (如果有)
            if 'analysis' in stock and 'comprehensive_score' in stock['analysis']:
                html_parts.append(f"""<div><span class="label">綜合評分:</span> <span class="stop-loss">{stock['analysis']['comprehensive_score']}</span></div>""")
            
            html_parts.append("""</div>""")  # 關閉單支股票區塊
    else:
        html_parts.append("""<div>今日無極弱股警示</div>""")
    
    html_parts.append("""</div>""")  # 關閉極弱股警示區段
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_parts.append("""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 """ + timestamp + """<br>
            本分析結果僅供參考，不構成投資建議，投資決策請自行承擔風險。
        </div>
    </body>
    </html>
    """)
    
    html_body = "".join(html_parts)
    subject = f"【{time_slot}分析報告】- {today}"
    send_notification(message, subject, html_body)

# 初始化
def init():
    """初始化通知系統"""
    try:
        # 檢查必要目錄
        os.makedirs(LOG_DIR, exist_ok=True)
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # 發送心跳通知
        last_heartbeat = STATUS.get('last_heartbeat')
        if not last_heartbeat or (datetime.now() - datetime.fromisoformat(last_heartbeat)).total_seconds() > 86400:  # 24小時
            send_heartbeat()
        
        # 重試未發送的通知
        retry_undelivered_notifications()
        
        log_event("通知系統已初始化")
        return True
    except Exception as e:
        log_event(f"通知系統初始化失敗: {e}", 'error')
        return False

# 如果直接運行此文件，則初始化
if __name__ == "__main__":
    init()
