"""
optimized_notifier.py - 優化版通知系統
針對長線推薦加強 EPS、法人買超、殖利率等基本面資訊顯示
"""
import os
import time
import json
import logging
import traceback
import smtplib
import socket
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

# 導入配置
try:
    from config import EMAIL_CONFIG, FILE_BACKUP, RETRY_CONFIG, LOG_DIR, CACHE_DIR
except ImportError:
    # 如果沒有config文件，使用環境變數
    EMAIL_CONFIG = {
        'enabled': True,
        'sender': os.getenv('EMAIL_SENDER'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'receiver': os.getenv('EMAIL_RECEIVER'),
        'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
        'use_tls': os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    }
    
    LOG_DIR = 'logs'
    CACHE_DIR = 'cache'
    FILE_BACKUP = {'enabled': True, 'directory': os.path.join(LOG_DIR, 'notifications')}
    RETRY_CONFIG = {'max_attempts': 3, 'base_delay': 2.0, 'backoff_factor': 1.5, 'max_delay': 60}

# 確保目錄存在
for directory in [LOG_DIR, CACHE_DIR, FILE_BACKUP['directory']]:
    os.makedirs(directory, exist_ok=True)

# 配置日誌
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'optimized_notifier.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 狀態追踪
STATUS = {
    'email': {'last_success': None, 'failure_count': 0, 'available': True},
    'file': {'last_success': None, 'failure_count': 0, 'available': True},
    'last_notification': None,
    'undelivered_count': 0,
    'last_heartbeat': None,
}

def log_event(message, level='info'):
    """記錄通知事件"""
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

def format_institutional_flow(amount_in_wan):
    """格式化法人買賣金額"""
    if amount_in_wan == 0:
        return "0"
    
    amount_yuan = amount_in_wan * 10000
    
    if abs(amount_yuan) >= 100000000:  # 億
        return f"{amount_yuan/100000000:.1f}億"
    elif abs(amount_yuan) >= 10000000:  # 千萬
        return f"{amount_yuan/10000000:.0f}千萬"
    else:
        return f"{amount_yuan/10000:.0f}萬"

def send_email_notification_optimized(message, subject, html_body=None, urgent=False):
    """優化版Gmail通知發送"""
    sender = EMAIL_CONFIG['sender']
    password = EMAIL_CONFIG['password']
    receiver = EMAIL_CONFIG['receiver']
    smtp_server = EMAIL_CONFIG['smtp_server']
    smtp_port = EMAIL_CONFIG['smtp_port']
    
    if not sender or not password or not receiver:
        log_event("缺少電子郵件通知配置", 'warning')
        return False
    
    max_attempts = RETRY_CONFIG['max_attempts']
    
    for attempt in range(max_attempts):
        try:
            log_event(f"嘗試發送郵件 (第 {attempt + 1} 次)")
            
            # 創建安全的SSL上下文
            context = ssl.create_default_context()
            
            # 建立SMTP連接
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            
            # 登入
            server.login(sender, password)
            
            # 創建郵件
            if html_body:
                msg = MIMEMultipart('alternative')
                text_part = MIMEText(message, 'plain', 'utf-8')
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(text_part)
                msg.attach(html_part)
            else:
                msg = MIMEMultipart()
                msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # 設定郵件標題
            msg['Subject'] = f"{'[緊急] ' if urgent else ''}{subject}"
            msg['From'] = sender
            msg['To'] = receiver
            msg['Date'] = formatdate(localtime=True)
            
            # 發送郵件
            server.send_message(msg)
            server.quit()
            
            log_event("郵件發送成功！")
            return True
            
        except Exception as e:
            log_event(f"郵件發送失敗 (嘗試 {attempt + 1}/{max_attempts}): {e}", 'error')
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
            
    return False

def send_notification(message, subject='系統通知', html_body=None, urgent=False):
    """發送通知"""
    log_event(f"發送通知: {subject}")
    
    # 更新上次通知時間
    STATUS['last_notification'] = datetime.now().isoformat()
    
    # 嘗試發送郵件
    success = False
    try:
        if EMAIL_CONFIG['enabled'] and STATUS['email']['available']:
            if send_email_notification_optimized(message, subject, html_body, urgent):
                success = True
                STATUS['email']['last_success'] = datetime.now().isoformat()
                STATUS['email']['failure_count'] = 0
                log_event("通知發送成功")
    except Exception as e:
        STATUS['email']['failure_count'] += 1
        log_event(f"通知發送失敗: {e}", 'error')
        log_event(traceback.format_exc(), 'error')
    
    # 如果郵件失敗，保存到文件
    if not success and FILE_BACKUP['enabled']:
        try:
            if save_notification_to_file(message, subject, html_body, urgent):
                STATUS['file']['last_success'] = datetime.now().isoformat()
                STATUS['file']['failure_count'] = 0
                log_event("已將通知保存到檔案")
            else:
                STATUS['file']['failure_count'] += 1
        except Exception as e:
            STATUS['file']['failure_count'] += 1
            log_event(f"保存通知到檔案失敗: {e}", 'error')
    
    # 如果都失敗
    if not success:
        STATUS['undelivered_count'] += 1
        log_event("所有通知渠道都失敗", 'error')
    
    return success

def save_notification_to_file(message, subject, html_body=None, urgent=False):
    """將通知保存到本地文件"""
    try:
        notifications_dir = FILE_BACKUP['directory']
        os.makedirs(notifications_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        urgency = "URGENT_" if urgent else ""
        safe_subject = "".join([c if c.isalnum() else "_" for c in subject])
        filename = f"{urgency}{timestamp}_{safe_subject[:30]}.txt"
        filepath = os.path.join(notifications_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"主題: {subject}\n")
            f.write(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"緊急: {'是' if urgent else '否'}\n")
            f.write("-" * 50 + "\n\n")
            f.write(message)
            f.write("\n\n")
            
            if html_body:
                f.write("-" * 50 + "\n")
                f.write("HTML內容:\n")
                f.write(html_body)
        
        log_event(f"已將通知保存到文件: {filepath}")
        return True
    
    except Exception as e:
        log_event(f"保存通知到文件失敗: {e}", 'error')
        return False

def send_optimized_combined_recommendations(strategies_data, time_slot):
    """
    發送優化版股票推薦通知（強化長線基本面資訊顯示）
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
    message = f"📈 {today} {time_slot}分析報告\n\n"
    
    # 短線推薦部分
    message += "【短線推薦】\n\n"
    if short_term_stocks:
        for i, stock in enumerate(short_term_stocks, 1):
            message += f"📈 {i}. {stock['code']} {stock['name']}\n"
            
            # 現價和漲跌幅
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            
            # 成交量和資金流向
            trade_value = stock.get('trade_value', 0)
            message += f"💵 成交金額: {format_number(trade_value)}\n"
            
            # 法人買超資訊
            if 'foreign_net_buy' in analysis:
                foreign_net = analysis['foreign_net_buy']
                if abs(foreign_net) > 1000:
                    if foreign_net > 0:
                        message += f"🏦 外資買超: {format_institutional_flow(foreign_net)}\n"
                    else:
                        message += f"🏦 外資賣超: {format_institutional_flow(abs(foreign_net))}\n"
            
            # 推薦理由
            message += f"📊 推薦理由: {stock['reason']}\n"
            
            # 目標價和止損價
            target_price = stock.get('target_price')
            stop_loss = stock.get('stop_loss')
            if target_price:
                message += f"🎯 目標價: {target_price} 元"
            if stop_loss:
                message += f" | 🛡️ 止損價: {stop_loss} 元"
            message += "\n\n"
    else:
        message += "今日無短線推薦股票\n\n"
    
    # 長線推薦部分（重點優化）
    message += "【💎 長線潛力 - 基本面優質股】\n\n"
    if long_term_stocks:
        for i, stock in enumerate(long_term_stocks, 1):
            message += f"💎 {i}. {stock['code']} {stock['name']}\n"
            
            # 現價和漲跌幅
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            
            # === 基本面資訊區塊（重點顯示）===
            message += "📊 基本面分析:\n"
            
            # 殖利率（重點）
            if 'dividend_yield' in analysis and analysis['dividend_yield'] > 0:
                dividend_yield = analysis['dividend_yield']
                dividend_years = analysis.get('dividend_consecutive_years', 0)
                if dividend_yield > 5:
                    message += f"   💸 高殖利率: {dividend_yield:.1f}%"
                elif dividend_yield > 3:
                    message += f"   💸 殖利率: {dividend_yield:.1f}%"
                else:
                    message += f"   💸 殖利率: {dividend_yield:.1f}%"
                
                if dividend_years > 5:
                    message += f" (連續{dividend_years}年配息)\n"
                else:
                    message += "\n"
            
            # EPS成長（重點）
            if 'eps_growth' in analysis and analysis['eps_growth'] > 0:
                eps_growth = analysis['eps_growth']
                if eps_growth > 20:
                    message += f"   📈 EPS高成長: {eps_growth:.1f}% (獲利大幅提升)\n"
                elif eps_growth > 10:
                    message += f"   📈 EPS穩健成長: {eps_growth:.1f}%\n"
                else:
                    message += f"   📈 EPS成長: {eps_growth:.1f}%\n"
            
            # ROE和本益比
            if 'roe' in analysis and analysis['roe'] > 0:
                roe = analysis['roe']
                pe_ratio = analysis.get('pe_ratio', 0)
                if roe > 15:
                    message += f"   🏆 ROE: {roe:.1f}% (獲利能力優秀)"
                else:
                    message += f"   🏆 ROE: {roe:.1f}%"
                
                if pe_ratio > 0 and pe_ratio < 20:
                    message += f" | 本益比: {pe_ratio:.1f}倍 (估值合理)\n"
                else:
                    message += f" | 本益比: {pe_ratio:.1f}倍\n"
            
            # 營收成長
            if 'revenue_growth' in analysis and analysis['revenue_growth'] > 8:
                revenue_growth = analysis['revenue_growth']
                message += f"   📊 營收成長: {revenue_growth:.1f}% (業務擴張)\n"
            
            # === 法人買賣區塊（重點顯示）===
            message += "🏦 法人動向:\n"
            
            foreign_net = analysis.get('foreign_net_buy', 0)
            trust_net = analysis.get('trust_net_buy', 0)
            total_institutional = analysis.get('total_institutional', 0)
            consecutive_days = analysis.get('consecutive_buy_days', 0)
            
            if total_institutional > 50000:
                message += f"   🔥 三大法人大幅買超: {format_institutional_flow(total_institutional)}\n"
            elif foreign_net > 10000:
                message += f"   🌍 外資買超: {format_institutional_flow(foreign_net)}"
                if trust_net > 5000:
                    message += f" | 投信買超: {format_institutional_flow(trust_net)}\n"
                else:
                    message += "\n"
            elif trust_net > 5000:
                message += f"   🏢 投信買超: {format_institutional_flow(trust_net)}\n"
            elif foreign_net > 0 or trust_net > 0:
                if foreign_net > 0:
                    message += f"   🌍 外資買超: {format_institutional_flow(foreign_net)}"
                if trust_net > 0:
                    message += f" | 投信買超: {format_institutional_flow(trust_net)}"
                message += "\n"
            else:
                message += f"   ➖ 法人中性\n"
            
            if consecutive_days > 3:
                message += f"   ⏰ 持續買超: {consecutive_days}天\n"
            
            # 成交量
            trade_value = stock.get('trade_value', 0)
            message += f"💵 成交金額: {format_number(trade_value)}\n"
            
            # 推薦理由
            message += f"📋 推薦理由: {stock['reason']}\n"
            
            # 目標價和止損價
            target_price = stock.get('target_price')
            stop_loss = stock.get('stop_loss')
            if target_price:
                message += f"🎯 目標價: {target_price} 元"
            if stop_loss:
                message += f" | 🛡️ 止損價: {stop_loss} 元"
            message += "\n\n"
    else:
        message += "今日無長線推薦股票\n\n"
    
    # 極弱股警示部分
    message += "【風險警示】\n\n"
    if weak_stocks:
        for i, stock in enumerate(weak_stocks, 1):
            message += f"⚠️ {i}. {stock['code']} {stock['name']}\n"
            
            # 現價和跌幅
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            
            # 成交量
            trade_value = stock.get('trade_value', 0)
            message += f"💵 成交金額: {format_number(trade_value)}\n"
            
            # 警報原因
            message += f"🚨 警報原因: {stock['alert_reason']}\n"
            
            # 風險提示
            message += f"⚠️ 風險提示: 建議謹慎操作，嚴設停損\n\n"
    else:
        message += "今日無極弱股警示\n\n"
    
    # 投資提醒（優化版）
    message += "【💡 投資提醒】\n"
    message += "💎 長線推薦重點關注基本面：殖利率、EPS成長、法人動向\n"
    message += "📊 建議長線投資者重視公司獲利能力和股息政策\n"
    message += "⚠️ 本報告僅供參考，不構成投資建議\n"
    message += "⚠️ 股市有風險，投資需謹慎\n"
    message += "⚠️ 建議設定停損點，控制投資風險\n\n"
    message += "祝您投資順利！💰"
    
    # 生成HTML格式（針對長線優化）
    html_body = generate_optimized_html_report(strategies_data, time_slot, today)
    
    subject = f"【{time_slot}分析報告】💎 長線基本面優化版 - {today}"
    send_notification(message, subject, html_body)

def generate_optimized_html_report(strategies_data, time_slot, date):
    """生成優化版HTML報告（強化長線基本面顯示）"""
    
    short_term_stocks = strategies_data.get("short_term", [])
    long_term_stocks = strategies_data.get("long_term", [])
    weak_stocks = strategies_data.get("weak_stocks", [])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{time_slot}分析報告 - {date}</title>
        <style>
            body {{
                font-family: 'Microsoft JhengHei', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .section {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .section-title {{
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
            }}
            .longterm-title {{
                border-bottom: 2px solid #f39c12;
                background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
            }}
            .stock-card {{
                border: 1px solid #e1e5e9;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                background: #fafbfc;
            }}
            .longterm-card {{
                border: 2px solid #f39c12;
                background: linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%);
                box-shadow: 0 4px 15px rgba(243, 156, 18, 0.2);
            }}
            .stock-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }}
            .stock-name {{
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .stock-price {{
                font-size: 14px;
                font-weight: bold;
            }}
            .price-up {{ color: #e74c3c; }}
            .price-down {{ color: #27ae60; }}
            .price-flat {{ color: #95a5a6; }}
            .fundamental-section {{
                background: #e8f5e8;
                border-left: 4px solid #27ae60;
                padding: 10px;
                margin: 10px 0;
                border-radius: 0 5px 5px 0;
            }}
            .institutional-section {{
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 10px;
                margin: 10px 0;
                border-radius: 0 5px 5px 0;
            }}
            .info-row {{
                margin: 5px 0;
                display: flex;
                align-items: center;
            }}
            .info-label {{
                color: #7f8c8d;
                margin-right: 8px;
                min-width: 80px;
                font-weight: bold;
            }}
            .highlight-metric {{
                background: #fff3cd;
                padding: 2px 6px;
                border-radius: 3px;
                font-weight: bold;
                color: #856404;
            }}
            .excellent-metric {{
                background: #d4edda;
                padding: 2px 6px;
                border-radius: 3px;
                font-weight: bold;
                color: #155724;
            }}
            .weak-stock {{
                border-left: 4px solid #e74c3c;
            }}
            .short-term {{
                border-left: 4px solid #f39c12;
            }}
            .warning {{
                background-color: #ffeaa7;
                border-left: 4px solid #fdcb6e;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .footer {{
                text-align: center;
                color: #7f8c8d;
                font-size: 12px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ecf0f1;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📈 {time_slot}分析報告</h1>
            <p>{date} - 💎 長線基本面優化版</p>
        </div>
    """
    
    # 短線推薦
    if short_term_stocks:
        html += """
        <div class="section">
            <div class="section-title">🔥 短線推薦</div>
        """
        for stock in short_term_stocks:
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            price_class = "price-up" if change_percent > 0 else "price-down" if change_percent < 0 else "price-flat"
            change_symbol = "+" if change_percent > 0 else ""
            
            html += f"""
            <div class="stock-card short-term">
                <div class="stock-header">
                    <div class="stock-name">📈 {stock['code']} {stock['name']}</div>
                    <div class="stock-price {price_class}">
                        現價: {current_price} 元 ({change_symbol}{change_percent:.2f}%)
                    </div>
                </div>
                <div class="stock-info">
                    <div class="info-row">
                        <span class="info-label">💵 成交金額:</span>
                        {format_number(stock.get('trade_value', 0))}
                    </div>
                    <div class="info-row">
                        <span class="info-label">📊 推薦理由:</span>
                        {stock['reason']}
                    </div>
                    <div class="info-row">
                        <span class="info-label">🎯 目標價:</span>
                        {stock.get('target_price', 'N/A')} 元
                        <span class="info-label" style="margin-left: 20px;">🛡️ 止損價:</span>
                        {stock.get('stop_loss', 'N/A')} 元
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # 長線推薦（重點優化）
    if long_term_stocks:
        html += """
        <div class="section">
            <div class="longterm-title">💎 長線潛力 - 基本面優質股</div>
        """
        for stock in long_term_stocks:
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            price_class = "price-up" if change_percent > 0 else "price-down" if change_percent < 0 else "price-flat"
            change_symbol = "+" if change_percent > 0 else ""
            
            html += f"""
            <div class="stock-card longterm-card">
                <div class="stock-header">
                    <div class="stock-name">💎 {stock['code']} {stock['name']}</div>
                    <div class="stock-price {price_class}">
                        現價: {current_price} 元 ({change_symbol}{change_percent:.2f}%)
                    </div>
                </div>
                
                <!-- 基本面分析區塊 -->
                <div class="fundamental-section">
                    <h4 style="margin: 0 0 10px 0; color: #27ae60;">📊 基本面分析</h4>
            """
            
            # 殖利率顯示
            if 'dividend_yield' in analysis and analysis['dividend_yield'] > 0:
                dividend_yield = analysis['dividend_yield']
                dividend_years = analysis.get('dividend_consecutive_years', 0)
                
                if dividend_yield > 5:
                    yield_class = "excellent-metric"
                elif dividend_yield > 3:
                    yield_class = "highlight-metric"
                else:
                    yield_class = ""
                
                html += f"""
                    <div class="info-row">
                        <span class="info-label">💸 殖利率:</span>
                        <span class="{yield_class}">{dividend_yield:.1f}%</span>
                """
                
                if dividend_years > 5:
                    html += f' <small>(連續{dividend_years}年配息)</small>'
                
                html += "</div>"
            
            # EPS成長顯示
            if 'eps_growth' in analysis and analysis['eps_growth'] > 0:
                eps_growth = analysis['eps_growth']
                
                if eps_growth > 20:
                    eps_class = "excellent-metric"
                elif eps_growth > 10:
                    eps_class = "highlight-metric"
                else:
                    eps_class = ""
                
                html += f"""
                    <div class="info-row">
                        <span class="info-label">📈 EPS成長:</span>
                        <span class="{eps_class}">{eps_growth:.1f}%</span>
                """
                
                if eps_growth > 20:
                    html += ' <small>(高速成長)</small>'
                elif eps_growth > 10:
                    html += ' <small>(穩健成長)</small>'
                
                html += "</div>"
            
            # ROE和本益比
            if 'roe' in analysis and analysis['roe'] > 0:
                roe = analysis['roe']
                pe_ratio = analysis.get('pe_ratio', 0)
                
                roe_class = "excellent-metric" if roe > 15 else "highlight-metric" if roe > 10 else ""
                pe_class = "excellent-metric" if pe_ratio < 15 else "highlight-metric" if pe_ratio < 20 else ""
                
                html += f"""
                    <div class="info-row">
                        <span class="info-label">🏆 ROE:</span>
                        <span class="{roe_class}">{roe:.1f}%</span>
                        <span class="info-label" style="margin-left: 20px;">📊 本益比:</span>
                        <span class="{pe_class}">{pe_ratio:.1f}倍</span>
                    </div>
                """
            
            # 營收成長
            if 'revenue_growth' in analysis and analysis['revenue_growth'] > 8:
                revenue_growth = analysis['revenue_growth']
                revenue_class = "excellent-metric" if revenue_growth > 15 else "highlight-metric"
                
                html += f"""
                    <div class="info-row">
                        <span class="info-label">📊 營收成長:</span>
                        <span class="{revenue_class}">{revenue_growth:.1f}%</span>
                        <small>(業務擴張)</small>
                    </div>
                """
            
            html += "</div>"  # 結束基本面區塊
            
            # 法人動向區塊
            html += """
                <div class="institutional-section">
                    <h4 style="margin: 0 0 10px 0; color: #2196f3;">🏦 法人動向</h4>
            """
            
            foreign_net = analysis.get('foreign_net_buy', 0)
            trust_net = analysis.get('trust_net_buy', 0)
            total_institutional = analysis.get('total_institutional', 0)
            consecutive_days = analysis.get('consecutive_buy_days', 0)
            
            if total_institutional > 50000:
                html += f"""
                    <div class="info-row">
                        <span class="info-label">🔥 三大法人:</span>
                        <span class="excellent-metric">大幅買超 {format_institutional_flow(total_institutional)}</span>
                    </div>
                """
            else:
                if foreign_net > 5000:
                    foreign_class = "excellent-metric" if foreign_net > 20000 else "highlight-metric"
                    html += f"""
                        <div class="info-row">
                            <span class="info-label">🌍 外資:</span>
                            <span class="{foreign_class}">買超 {format_institutional_flow(foreign_net)}</span>
                        </div>
                    """
                elif foreign_net < -5000:
                    html += f"""
                        <div class="info-row">
                            <span class="info-label">🌍 外資:</span>
                            <span style="color: #e74c3c;">賣超 {format_institutional_flow(abs(foreign_net))}</span>
                        </div>
                    """
                
                if trust_net > 3000:
                    trust_class = "excellent-metric" if trust_net > 10000 else "highlight-metric"
                    html += f"""
                        <div class="info-row">
                            <span class="info-label">🏢 投信:</span>
                            <span class="{trust_class}">買超 {format_institutional_flow(trust_net)}</span>
                        </div>
                    """
                elif trust_net < -3000:
                    html += f"""
                        <div class="info-row">
                            <span class="info-label">🏢 投信:</span>
                            <span style="color: #e74c3c;">賣超 {format_institutional_flow(abs(trust_net))}</span>
                        </div>
                    """
            
            if consecutive_days > 3:
                html += f"""
                    <div class="info-row">
                        <span class="info-label">⏰ 持續買超:</span>
                        <span class="highlight-metric">{consecutive_days}天</span>
                    </div>
                """
            
            html += "</div>"  # 結束法人動向區塊
            
            # 其他資訊
            html += f"""
                <div class="stock-info">
                    <div class="info-row">
                        <span class="info-label">💵 成交金額:</span>
                        {format_number(stock.get('trade_value', 0))}
                    </div>
                    <div class="info-row">
                        <span class="info-label">📋 推薦理由:</span>
                        {stock['reason']}
                    </div>
                    <div class="info-row">
                        <span class="info-label">🎯 目標價:</span>
                        {stock.get('target_price', 'N/A')} 元
                        <span class="info-label" style="margin-left: 20px;">🛡️ 止損價:</span>
                        {stock.get('stop_loss', 'N/A')} 元
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # 風險警示
    if weak_stocks:
        html += """
        <div class="section">
            <div class="section-title">⚠️ 風險警示</div>
        """
        for stock in weak_stocks:
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            html += f"""
            <div class="stock-card weak-stock">
                <div class="stock-header">
                    <div class="stock-name">⚠️ {stock['code']} {stock['name']}</div>
                    <div class="stock-price price-down">
                        現價: {current_price} 元 ({change_percent:.2f}%)
                    </div>
                </div>
                <div class="stock-info">
                    <div class="info-row">
                        <span class="info-label">💵 成交金額:</span>
                        {format_number(stock.get('trade_value', 0))}
                    </div>
                    <div class="info-row">
                        <span class="info-label">🚨 警報原因:</span>
                        {stock['alert_reason']}
                    </div>
                    <div class="info-row">
                        <span class="info-label">⚠️ 風險提示:</span>
                        建議謹慎操作，嚴設停損
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # 投資提醒（優化版）
    html += """
        <div class="warning">
            <h3>💡 投資提醒</h3>
            <p><strong>💎 長線投資重點：</strong></p>
            <ul>
                <li>📊 殖利率 > 3% 提供穩定現金流</li>
                <li>📈 EPS成長 > 10% 代表獲利持續改善</li>
                <li>🏦 法人買超顯示專業投資人看好</li>
                <li>🏆 ROE > 15% 表示獲利能力優秀</li>
                <li>⏰ 連續配息年數反映股息政策穩定</li>
            </ul>
            <p><strong>⚠️ 風險提醒：</strong></p>
            <ul>
                <li>本報告僅供參考，不構成投資建議</li>
                <li>股市有風險，投資需謹慎</li>
                <li>建議設定停損點，控制投資風險</li>
                <li>長線投資應定期檢視基本面變化</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>此電子郵件由台股分析系統自動產生於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>💎 長線基本面優化版 - 專注殖利率、EPS成長、法人動向</p>
            <p>祝您投資順利！💰</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_heartbeat():
    """發送心跳檢測"""
    now = datetime.now()
    
    # 檢查上次心跳時間
    if STATUS['last_heartbeat']:
        try:
            last_heartbeat = datetime.fromisoformat(STATUS['last_heartbeat'])
            if (now - last_heartbeat).total_seconds() < 3600:  # 1小時內不重複發送
                return False
        except:
            pass
    
    # 發送心跳通知
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    message = f"🔔 優化版系統心跳檢測通知\n\n"
    message += f"⏰ 檢測時間: {timestamp}\n\n"
    
    # 系統狀態
    message += "📊 系統狀態:\n"
    
    email_status = STATUS['email']
    if email_status['last_success']:
        try:
            last_time = datetime.fromisoformat(email_status['last_success'])
            hours_ago = (now - last_time).total_seconds() / 3600
            time_str = f"{hours_ago:.1f} 小時前" if hours_ago >= 1 else f"{int((now - last_time).total_seconds() / 60)} 分鐘前"
        except:
            time_str = "時間解析錯誤"
    else:
        time_str = "從未成功"
    
    emoji = "✅" if email_status['available'] and email_status['failure_count'] < 3 else "⚠️"
    message += f"  {emoji} 郵件通知: 上次成功 {time_str}, 失敗次數 {email_status['failure_count']}\n"
    
    # 未送達統計
    message += f"\n📈 統計資訊:\n"
    message += f"  • 未送達通知數: {STATUS['undelivered_count']}\n"
    message += f"  • 系統運行正常: {'是' if email_status['failure_count'] < 5 else '否'}\n\n"
    
    message += "💎 優化版功能:\n"
    message += "  • 長線推薦強化基本面分析\n"
    message += "  • 重視殖利率、EPS成長、法人動向\n"
    message += "  • 提供更詳細的投資參考資訊\n\n"
    
    message += "💡 如果您收到此訊息，表示優化版通知系統運作正常！"
    
    # 發送心跳通知
    success = send_notification(message, "🔔 優化版系統心跳檢測")
    
    # 更新心跳時間
    if success:
        STATUS['last_heartbeat'] = now.isoformat()
    
    return success

def is_notification_available():
    """檢查通知系統是否可用"""
    return (EMAIL_CONFIG['enabled'] and STATUS['email']['available']) or \
           (FILE_BACKUP['enabled'] and STATUS['file']['available'])

def init():
    """初始化優化版通知系統"""
    log_event("初始化優化版通知系統")
    
    # 檢查郵件配置
    if EMAIL_CONFIG['enabled']:
        missing = []
        for key in ['sender', 'password', 'receiver']:
            if not EMAIL_CONFIG[key]:
                missing.append(f'EMAIL_{key.upper()}')
        
        if missing:
            log_event(f"警告: 缺少以下郵件配置: {', '.join(missing)}", 'warning')
            log_event("請設置相應的環境變數", 'warning')
            STATUS['email']['available'] = False
        else:
            log_event("郵件配置檢查通過")
    
    # 檢查文件備份
    if FILE_BACKUP['enabled']:
        try:
            os.makedirs(FILE_BACKUP['directory'], exist_ok=True)
            log_event(f"文件備份目錄準備完成: {FILE_BACKUP['directory']}")
        except Exception as e:
            log_event(f"文件備份目錄創建失敗: {e}", 'error')
            STATUS['file']['available'] = False
    
    log_event("優化版通知系統初始化完成")
    log_event("💎 長線推薦將重點顯示：殖利率、EPS成長、法人買超資訊")

# 向下相容的函數別名
send_combined_recommendations = send_optimized_combined_recommendations

if __name__ == "__main__":
    # 初始化
    init()
    
    # 執行測試
    print("=" * 60)
    print("💎 優化版通知系統測試 - 強化長線基本面顯示")
    print("=" * 60)
    
    # 創建測試數據
    test_data = {
        "short_term": [
            {
                "code": "2330",
                "name": "台積電",
                "current_price": 638.5,
                "reason": "技術面轉強，MACD金叉，外資買超支撐",
                "target_price": 670.0,
                "stop_loss": 620.0,
                "trade_value": 14730000000,
                "analysis": {
                    "change_percent": 2.35,
                    "foreign_net_buy": 25000,
                    "technical_signals": {
                        "rsi_healthy": True,
                        "macd_bullish": True
                    }
                }
            }
        ],
        "long_term": [
            {
                "code": "2609",
                "name": "陽明",
                "current_price": 91.2,
                "reason": "高殖利率7.2%，EPS高成長35.6%，三大法人大幅買超，連續配息5年",
                "target_price": 110.0,
                "stop_loss": 85.0,
                "trade_value": 4560000000,
                "analysis": {
                    "change_percent": 1.8,
                    "dividend_yield": 7.2,
                    "eps_growth": 35.6,
                    "pe_ratio": 8.9,
                    "roe": 18.4,
                    "revenue_growth": 28.9,
                    "dividend_consecutive_years": 5,
                    "foreign_net_buy": 45000,
                    "trust_net_buy": 15000,
                    "total_institutional": 62000,
                    "consecutive_buy_days": 6
                }
            },
            {
                "code": "2882",
                "name": "國泰金",
                "current_price": 58.3,
                "reason": "穩定殖利率6.2%，連續配息18年，外資持續買超",
                "target_price": 65.0,
                "stop_loss": 55.0,
                "trade_value": 2100000000,
                "analysis": {
                    "change_percent": 0.5,
                    "dividend_yield": 6.2,
                    "eps_growth": 8.5,
                    "pe_ratio": 11.3,
                    "roe": 13.8,
                    "revenue_growth": 6.7,
                    "dividend_consecutive_years": 18,
                    "foreign_net_buy": 12000,
                    "trust_net_buy": 3000,
                    "total_institutional": 16000,
                    "consecutive_buy_days": 4
                }
            }
        ],
        "weak_stocks": []
    }
    
    # 發送測試通知
    send_optimized_combined_recommendations(test_data, "測試分析")
    
    print("\n💎 優化版通知已發送！")
    print("\n📋 請檢查您的郵箱，確認以下長線基本面資訊:")
    print("1. ✅ 殖利率顯示是否突出（>5%會特別標示）")
    print("2. 📈 EPS成長率是否清楚標示（>20%會特別標示）")
    print("3. 🏦 法人買賣超金額是否詳細顯示")
    print("4. 🏆 ROE和本益比是否清楚標示")
    print("5. ⏰ 連續配息年數是否顯示")
    print("6. 📊 營收成長是否顯示")
    print("7. 🎨 HTML格式的基本面區塊是否美觀")
    print("8. 💎 長線推薦標題是否突出顯示")
    
    print("\n=" * 60)
    print("💡 使用說明:")
    print("1. 將此模組匯入到 optimized_stock_bot 中")
    print("2. 替換原有的 notifier 模組")
    print("3. 享受更詳細的長線基本面分析報告")
    print("=" * 60)
