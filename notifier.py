"""
enhanced_notifier_fixed.py - 修復版通知系統
解決Gmail認證問題並增加現價和漲跌百分比顯示
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
    filename=os.path.join(LOG_DIR, 'notifier.log'),
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

def check_gmail_app_password():
    """檢查Gmail應用程式密碼設定"""
    password = EMAIL_CONFIG.get('password', '')
    if not password:
        log_event("未設定EMAIL_PASSWORD環境變數", 'error')
        return False
    
    # Gmail應用程式密碼通常是16位數
    if len(password) == 16 and password.replace(' ', '').isalnum():
        log_event("檢測到Gmail應用程式密碼格式")
        return True
    elif '@gmail.com' in EMAIL_CONFIG.get('sender', '') and len(password) < 16:
        log_event("Gmail帳戶需要使用應用程式密碼，請參考以下步驟：", 'warning')
        log_event("1. 登入 Google 帳戶設定", 'warning')
        log_event("2. 啟用兩步驟驗證", 'warning')
        log_event("3. 生成應用程式密碼", 'warning')
        log_event("4. 將16位密碼設定為EMAIL_PASSWORD", 'warning')
        return False
    
    return True

def send_email_notification_fixed(message, subject, html_body=None, urgent=False):
    """
    修復版Gmail通知發送
    解決認證問題並支援應用程式密碼
    """
    sender = EMAIL_CONFIG['sender']
    password = EMAIL_CONFIG['password']
    receiver = EMAIL_CONFIG['receiver']
    smtp_server = EMAIL_CONFIG['smtp_server']
    smtp_port = EMAIL_CONFIG['smtp_port']
    
    if not sender or not password or not receiver:
        log_event("缺少電子郵件通知配置", 'warning')
        return False
    
    # 檢查Gmail應用程式密碼
    if 'gmail.com' in smtp_server and not check_gmail_app_password():
        return False
    
    max_attempts = RETRY_CONFIG['max_attempts']
    
    for attempt in range(max_attempts):
        try:
            log_event(f"嘗試發送郵件 (第 {attempt + 1} 次)")
            
            # 創建安全的SSL上下文
            context = ssl.create_default_context()
            
            # 建立SMTP連接
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()  # 可能需要額外的ehlo命令
            server.starttls(context=context)
            server.ehlo()  # TLS後再次ehlo
            
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
            
        except smtplib.SMTPAuthenticationError as e:
            log_event(f"郵件認證失敗: {e}", 'error')
            if 'gmail.com' in smtp_server:
                log_event("Gmail認證失敗，請檢查：", 'error')
                log_event("1. 是否啟用了兩步驟驗證", 'error')
                log_event("2. 是否使用應用程式密碼而非一般密碼", 'error')
                log_event("3. 應用程式密碼是否正確（16位數）", 'error')
            break  # 認證錯誤不需要重試
            
        except Exception as e:
            log_event(f"郵件發送失敗 (嘗試 {attempt + 1}/{max_attempts}): {e}", 'error')
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)  # 指數退避
            
    return False

def send_notification(message, subject='系統通知', html_body=None, urgent=False):
    """
    發送通知，優先郵件，失敗後備份到檔案
    """
    log_event(f"發送通知: {subject}")
    
    # 更新上次通知時間
    STATUS['last_notification'] = datetime.now().isoformat()
    
    # 嘗試發送郵件
    success = False
    try:
        if EMAIL_CONFIG['enabled'] and STATUS['email']['available']:
            if send_email_notification_fixed(message, subject, html_body, urgent):
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

def send_combined_recommendations(strategies_data, time_slot):
    """
    發送包含三種策略的股票推薦通知（增強版 - 包含現價和漲跌百分比）
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
    
    # 短線推薦部分（增強版 - 包含現價和漲跌百分比）
    message += "【短線推薦】\n\n"
    if short_term_stocks:
        for i, stock in enumerate(short_term_stocks, 1):
            message += f"📈 {i}. {stock['code']} {stock['name']}\n"
            
            # 現價和漲跌幅（重點增強）
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
                if abs(foreign_net) > 1000:  # 超過1000萬才顯示
                    if foreign_net > 0:
                        message += f"🏦 外資買超: {format_number(foreign_net*10000)} 元\n"
                    else:
                        message += f"🏦 外資賣超: {format_number(abs(foreign_net)*10000)} 元\n"
            
            # 推薦理由
            message += f"📊 推薦理由: {stock['reason']}\n"
            
            # 目標價和止損價
            target_price = stock.get('target_price')
            stop_loss = stock.get('stop_loss')
            if target_price:
                message += f"🎯 目標價: {target_price} 元"
            if stop_loss:
                message += f" | 🛡️ 止損價: {stop_loss} 元"
            message += "\n"
            
            # 技術指標（如果有）
            if 'technical_signals' in analysis:
                signals = analysis['technical_signals']
                indicators = []
                if signals.get('rsi_healthy'):
                    indicators.append("RSI健康")
                if signals.get('macd_bullish'):
                    indicators.append("MACD轉強")
                if signals.get('ma20_bullish'):
                    indicators.append("站穩均線")
                if indicators:
                    message += f"📊 技術指標: {' | '.join(indicators)}\n"
            
            message += "\n"
    else:
        message += "今日無短線推薦股票\n\n"
    
    # 長線推薦部分（增強版）
    message += "【長線潛力】\n\n"
    if long_term_stocks:
        for i, stock in enumerate(long_term_stocks, 1):
            message += f"📊 {i}. {stock['code']} {stock['name']}\n"
            
            # 現價和漲跌幅
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            
            # 成交量
            trade_value = stock.get('trade_value', 0)
            message += f"💵 成交金額: {format_number(trade_value)}\n"
            
            # 基本面資訊
            if 'dividend_yield' in analysis and analysis['dividend_yield'] > 0:
                message += f"💸 殖利率: {analysis['dividend_yield']:.1f}%\n"
            if 'pe_ratio' in analysis and analysis['pe_ratio'] > 0:
                message += f"📊 本益比: {analysis['pe_ratio']:.1f}\n"
            if 'eps_growth' in analysis and analysis['eps_growth'] > 0:
                message += f"📈 EPS成長: {analysis['eps_growth']:.1f}%\n"
            
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
    
    # 極弱股警示部分（增強版）
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
    
    # 風險提示
    message += "【投資提醒】\n"
    message += "⚠️ 本報告僅供參考，不構成投資建議\n"
    message += "⚠️ 股市有風險，投資需謹慎\n"
    message += "⚠️ 建議設定停損點，控制投資風險\n\n"
    message += "祝您投資順利！💰"
    
    # 生成HTML格式（增強版）
    html_body = generate_enhanced_html_report(strategies_data, time_slot, today)
    
    subject = f"【{time_slot}分析報告】- {today}"
    send_notification(message, subject, html_body)

def generate_enhanced_html_report(strategies_data, time_slot, date):
    """生成增強版HTML報告（包含現價和漲跌百分比）"""
    
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
                max-width: 800px;
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
            .stock-card {{
                border: 1px solid #e1e5e9;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                background: #fafbfc;
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
            .stock-info {{
                margin-top: 10px;
                font-size: 14px;
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
            }}
            .indicators {{
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin-top: 10px;
            }}
            .indicator-tag {{
                background-color: #3498db;
                color: white;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            .weak-stock {{
                border-left: 4px solid #e74c3c;
            }}
            .short-term {{
                border-left: 4px solid #f39c12;
            }}
            .long-term {{
                border-left: 4px solid #27ae60;
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
            <p>{date}</p>
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
            """
            
            # 技術指標
            if 'technical_signals' in analysis:
                signals = analysis['technical_signals']
                html += '<div class="indicators">'
                if signals.get('rsi_healthy'):
                    html += '<span class="indicator-tag">RSI健康</span>'
                if signals.get('macd_bullish'):
                    html += '<span class="indicator-tag">MACD轉強</span>'
                if signals.get('ma20_bullish'):
                    html += '<span class="indicator-tag">站穩均線</span>'
                html += '</div>'
            
            html += """
                </div>
            </div>
            """
        
        html += "</div>"
    
    # 長線推薦
    if long_term_stocks:
        html += """
        <div class="section">
            <div class="section-title">📊 長線潛力</div>
        """
        for stock in long_term_stocks:
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            price_class = "price-up" if change_percent > 0 else "price-down" if change_percent < 0 else "price-flat"
            change_symbol = "+" if change_percent > 0 else ""
            
            html += f"""
            <div class="stock-card long-term">
                <div class="stock-header">
                    <div class="stock-name">📊 {stock['code']} {stock['name']}</div>
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
                        <span class="info-label">📋 推薦理由:</span>
                        {stock['reason']}
                    </div>
            """
            
            # 基本面資訊
            if 'dividend_yield' in analysis and analysis['dividend_yield'] > 0:
                html += f"""
                    <div class="info-row">
                        <span class="info-label">💸 殖利率:</span>
                        {analysis['dividend_yield']:.1f}%
                    </div>
                """
            
            html += f"""
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
    
    # 風險提示
    html += """
        <div class="warning">
            <h3>⚠️ 投資提醒</h3>
            <p>• 本報告僅供參考，不構成投資建議</p>
            <p>• 股市有風險，投資需謹慎</p>
            <p>• 建議設定停損點，控制投資風險</p>
        </div>
        
        <div class="footer">
            <p>此電子郵件由台股分析系統自動產生於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
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
    message = f"🔔 系統心跳檢測通知\n\n"
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
    
    message += "💡 如果您收到此訊息，表示通知系統運作正常！"
    
    # 發送心跳通知
    success = send_notification(message, "🔔 系統心跳檢測")
    
    # 更新心跳時間
    if success:
        STATUS['last_heartbeat'] = now.isoformat()
    
    return success

def is_notification_available():
    """檢查通知系統是否可用"""
    return (EMAIL_CONFIG['enabled'] and STATUS['email']['available']) or \
           (FILE_BACKUP['enabled'] and STATUS['file']['available'])

def init():
    """初始化通知系統"""
    log_event("初始化通知系統")
    
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
            if 'gmail.com' in EMAIL_CONFIG['smtp_server']:
                check_gmail_app_password()
    
    # 檢查文件備份
    if FILE_BACKUP['enabled']:
        try:
            os.makedirs(FILE_BACKUP['directory'], exist_ok=True)
            log_event(f"文件備份目錄準備完成: {FILE_BACKUP['directory']}")
        except Exception as e:
            log_event(f"文件備份目錄創建失敗: {e}", 'error')
            STATUS['file']['available'] = False
    
    log_event("通知系統初始化完成")

# 測試函數
def test_notification():
    """測試通知功能"""
    log_event("開始測試通知功能")
    
    # 測試基本通知
    test_message = f"""📧 通知系統測試
    
⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 如果您收到此郵件，表示通知系統運作正常！

🔧 系統資訊:
• 郵件服務器: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}
• TLS加密: {'是' if EMAIL_CONFIG['use_tls'] else '否'}
• 發件人: {EMAIL_CONFIG['sender']}
• 收件人: {EMAIL_CONFIG['receiver']}

📊 測試股票推薦格式:
現價: 100.50 元 📈 +2.5%
成交金額: 1.2億
推薦理由: 技術面轉強，MACD金叉
目標價: 110 元 | 止損價: 95 元

💡 這是測試郵件，請忽略投資建議內容。
"""
    
    success = send_notification(
        message=test_message,
        subject="📧 台股分析系統 - 通知測試",
        urgent=False
    )
    
    if success:
        log_event("✅ 通知測試成功！請檢查您的郵箱")
    else:
        log_event("❌ 通知測試失敗，請檢查配置", 'error')
    
    return success

if __name__ == "__main__":
    # 初始化
    init()
    
    # 執行測試
    print("=" * 50)
    print("修復版通知系統測試")
    print("=" * 50)
    
    test_notification()
    
    print("\n" + "=" * 50)
    print("Gmail設定指南:")
    print("=" * 50)
    print("1. 登入 Google 帳戶設定")
    print("2. 啟用「兩步驟驗證」")
    print("3. 生成「應用程式密碼」")
    print("4. 將16位密碼設定為 EMAIL_PASSWORD 環境變數")
    print("5. 重新執行測試")
    print("=" * 50)
