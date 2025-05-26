"""
enhanced_notifier_fixed.py - 修復版通知系統
解決Gmail認證問題並增加現價和漲跌百分比顯示
增強長線推薦：重點顯示EPS、法人買超、殖利率資訊
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

def format_foreign_net_buy(foreign_net):
    """格式化外資買賣超顯示"""
    if abs(foreign_net) < 1000:  # 小於1000萬不顯示
        return ""
    
    amount_yi = abs(foreign_net) / 10000  # 轉換為億
    if foreign_net > 0:
        if amount_yi >= 1:
            return f"🏦 外資買超: {amount_yi:.1f}億"
        else:
            return f"🏦 外資買超: {abs(foreign_net)/1000:.0f}千萬"
    else:
        if amount_yi >= 1:
            return f"🏦 外資賣超: {amount_yi:.1f}億"
        else:
            return f"🏦 外資賣超: {abs(foreign_net)/1000:.0f}千萬"

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

def generate_enhanced_html_report(strategies_data, time_slot, date):
    """生成增強版HTML報告（重點顯示長線基本面資訊）"""
    
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
                padding: 25px;
                border-radius: 12px;
                margin-bottom: 25px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .section {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 25px;
                box-shadow: 0 3px 15px rgba(0,0,0,0.08);
            }}
            .section-title {{
                color: #2c3e50;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 20px;
                border-bottom: 3px solid #3498db;
                padding-bottom: 8px;
                display: flex;
                align-items: center;
            }}
            .section-title.short-term {{
                border-bottom-color: #e74c3c;
            }}
            .section-title.long-term {{
                border-bottom-color: #27ae60;
            }}
            .section-title.weak {{
                border-bottom-color: #f39c12;
            }}
            .stock-card {{
                border: 1px solid #e1e5e9;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                background: #fafbfc;
                transition: transform 0.2s ease;
            }}
            .stock-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .stock-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }}
            .stock-name {{
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .stock-price {{
                font-size: 16px;
                font-weight: bold;
            }}
            .price-up {{ color: #e74c3c; }}
            .price-down {{ color: #27ae60; }}
            .price-flat {{ color: #95a5a6; }}
            .stock-info {{
                margin-top: 15px;
                font-size: 14px;
            }}
            .info-row {{
                margin: 8px 0;
                display: flex;
                align-items: center;
                flex-wrap: wrap;
            }}
            .info-label {{
                color: #7f8c8d;
                margin-right: 8px;
                min-width: 80px;
                font-weight: 500;
            }}
            .info-value {{
                color: #2c3e50;
                font-weight: 500;
            }}
            .fundamental-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
                margin: 10px 0;
                padding: 15px;
                background: #f8f9ff;
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }}
            .fundamental-item {{
                text-align: center;
                padding: 8px;
                background: white;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .fundamental-label {{
                font-size: 12px;
                color: #7f8c8d;
                margin-bottom: 4px;
            }}
            .fundamental-value {{
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .fundamental-value.positive {{
                color: #27ae60;
            }}
            .fundamental-value.negative {{
                color: #e74c3c;
            }}
            .institutional-info {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 12px;
                margin: 10px 0;
            }}
            .institutional-item {{
                display: inline-block;
                margin: 4px 8px;
                padding: 4px 8px;
                background: #fff;
                border-radius: 4px;
                font-size: 13px;
                border: 1px solid #ddd;
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
                padding: 4px 10px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: 500;
            }}
            .indicator-tag.technical {{
                background-color: #9b59b6;
            }}
            .indicator-tag.fundamental {{
                background-color: #27ae60;
            }}
            .indicator-tag.institutional {{
                background-color: #f39c12;
            }}
            .weak-stock {{
                border-left: 5px solid #e74c3c;
                background: #fdf2f2;
            }}
            .short-term {{
                border-left: 5px solid #f39c12;
                background: #fff8f3;
            }}
            .long-term {{
                border-left: 5px solid #27ae60;
                background: #f8fff8;
            }}
            .score-badge {{
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .score-badge.high {{
                background: #27ae60;
            }}
            .score-badge.medium {{
                background: #f39c12;
            }}
            .score-badge.low {{
                background: #95a5a6;
            }}
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 20px;
                margin: 25px 0;
                border-radius: 8px;
            }}
            .footer {{
                text-align: center;
                color: #7f8c8d;
                font-size: 12px;
                margin-top: 40px;
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
            <div class="section-title short-term">🔥 短線推薦（技術面主導）</div>
        """
        for stock in short_term_stocks:
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            price_class = "price-up" if change_percent > 0 else "price-down" if change_percent < 0 else "price-flat"
            change_symbol = "+" if change_percent > 0 else ""
            
            # 計算評分等級
            score = analysis.get('weighted_score', 0)
            if score >= 6:
                score_class = "high"
            elif score >= 3:
                score_class = "medium"
            else:
                score_class = "low"
            
            html += f"""
            <div class="stock-card short-term">
                <div class="stock-header">
                    <div class="stock-name">📈 {stock['code']} {stock['name']}
                        <span class="score-badge {score_class}">評分: {score:.1f}</span>
                    </div>
                    <div class="stock-price {price_class}">
                        現價: {current_price} 元 ({change_symbol}{change_percent:.2f}%)
                    </div>
                </div>
                <div class="stock-info">
                    <div class="info-row">
                        <span class="info-label">💵 成交金額:</span>
                        <span class="info-value">{format_number(stock.get('trade_value', 0))}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">📊 推薦理由:</span>
                        <span class="info-value">{stock['reason']}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">🎯 目標價:</span>
                        <span class="info-value">{stock.get('target_price', 'N/A')} 元</span>
                        <span class="info-label" style="margin-left: 20px;">🛡️ 止損價:</span>
                        <span class="info-value">{stock.get('stop_loss', 'N/A')} 元</span>
                    </div>
            """
            
            # 法人買超資訊
            foreign_net = analysis.get('foreign_net_buy', 0)
            if abs(foreign_net) >= 1000:
                foreign_info = format_foreign_net_buy(foreign_net)
                if foreign_info:
                    html += f"""
                    <div class="info-row">
                        <span class="info-label">🏦 法人動向:</span>
                        <span class="info-value">{foreign_info.replace('🏦 ', '')}</span>
                    </div>
                    """
            
            # 技術指標
            if 'technical_signals' in analysis:
                signals = analysis['technical_signals']
                html += '<div class="indicators">'
                if signals.get('rsi_healthy'):
                    html += '<span class="indicator-tag technical">RSI健康</span>'
                if signals.get('macd_bullish'):
                    html += '<span class="indicator-tag technical">MACD轉強</span>'
                if signals.get('ma20_bullish'):
                    html += '<span class="indicator-tag technical">站穩均線</span>'
                html += '</div>'
            
            html += """
                </div>
            </div>
            """
        
        html += "</div>"
    
    # 長線推薦 - 重點增強
    if long_term_stocks:
        html += """
        <div class="section">
            <div class="section-title long-term">💎 長線潛力（基本面主導）</div>
        """
        for stock in long_term_stocks:
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            price_class = "price-up" if change_percent > 0 else "price-down" if change_percent < 0 else "price-flat"
            change_symbol = "+" if change_percent > 0 else ""
            
            # 長線評分
            long_term_score = stock.get('long_term_score', 0)
            if long_term_score >= 4:
                score_class = "high"
            elif long_term_score >= 2:
                score_class = "medium"
            else:
                score_class = "low"
            
            html += f"""
            <div class="stock-card long-term">
                <div class="stock-header">
                    <div class="stock-name">💎 {stock['code']} {stock['name']}
                        <span class="score-badge {score_class}">長線評分: {long_term_score:.1f}</span>
                    </div>
                    <div class="stock-price {price_class}">
                        現價: {current_price} 元 ({change_symbol}{change_percent:.2f}%)
                    </div>
                </div>
                <div class="stock-info">
                    <div class="info-row">
                        <span class="info-label">💵 成交金額:</span>
                        <span class="info-value">{format_number(stock.get('trade_value', 0))}</span>
                    </div>
            """
            
            # 基本面資訊網格
            dividend_yield = analysis.get('dividend_yield', 0)
            eps_growth = analysis.get('eps_growth', 0)
            roe = analysis.get('roe', 0)
            pe_ratio = analysis.get('pe_ratio', 0)
            
            if dividend_yield > 0 or eps_growth > 0 or roe > 0 or pe_ratio > 0:
                html += '<div class="fundamental-grid">'
                
                if dividend_yield > 0:
                    dividend_class = "positive" if dividend_yield > 4 else ""
                    html += f"""
                    <div class="fundamental-item">
                        <div class="fundamental-label">殖利率</div>
                        <div class="fundamental-value {dividend_class}">{dividend_yield:.1f}%</div>
                    </div>
                    """
                
                if eps_growth != 0:
                    eps_class = "positive" if eps_growth > 0 else "negative"
                    html += f"""
                    <div class="fundamental-item">
                        <div class="fundamental-label">EPS成長</div>
                        <div class="fundamental-value {eps_class}">{eps_growth:.1f}%</div>
                    </div>
                    """
                
                if roe > 0:
                    roe_class = "positive" if roe > 15 else ""
                    html += f"""
                    <div class="fundamental-item">
                        <div class="fundamental-label">ROE</div>
                        <div class="fundamental-value {roe_class}">{roe:.1f}%</div>
                    </div>
                    """
                
                if pe_ratio > 0:
                    pe_class = "positive" if pe_ratio < 15 else ""
                    html += f"""
                    <div class="fundamental-item">
                        <div class="fundamental-label">本益比</div>
                        <div class="fundamental-value {pe_class}">{pe_ratio:.1f}倍</div>
                    </div>
                    """
                
                html += '</div>'
            
            # 法人買賣資訊
            foreign_net = analysis.get('foreign_net_buy', 0)
            trust_net = analysis.get('trust_net_buy', 0)
            consecutive_days = analysis.get('consecutive_buy_days', 0)
            
            institutional_items = []
            
            if abs(foreign_net) >= 1000:
                foreign_info = format_foreign_net_buy(foreign_net)
                if foreign_info:
                    institutional_items.append(foreign_info.replace('🏦 ', ''))
            
            if abs(trust_net) >= 1000:
                if trust_net > 0:
                    trust_amount = trust_net / 10000
                    if trust_amount >= 1:
                        institutional_items.append(f"投信買超: {trust_amount:.1f}億")
                    else:
                        institutional_items.append(f"投信買超: {trust_net/1000:.0f}千萬")
                else:
                    trust_amount = abs(trust_net) / 10000
                    if trust_amount >= 1:
                        institutional_items.append(f"投信賣超: {trust_amount:.1f}億")
                    else:
                        institutional_items.append(f"投信賣超: {abs(trust_net)/1000:.0f}千萬")
            
            if abs(consecutive_days) >= 3:
                if consecutive_days > 0:
                    institutional_items.append(f"連續買超{consecutive_days}天")
                else:
                    institutional_items.append(f"連續賣超{abs(consecutive_days)}天")
            
            if institutional_items:
                html += '<div class="institutional-info">🏦 <strong>法人動向:</strong>'
                for item in institutional_items:
                    html += f'<span class="institutional-item">{item}</span>'
                html += '</div>'
            
            html += f"""
                    <div class="info-row">
                        <span class="info-label">📋 推薦理由:</span>
                        <span class="info-value">{stock['reason']}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">🎯 目標價:</span>
                        <span class="info-value">{stock.get('target_price', 'N/A')} 元</span>
                        <span class="info-label" style="margin-left: 20px;">🛡️ 止損價:</span>
                        <span class="info-value">{stock.get('stop_loss', 'N/A')} 元</span>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # 風險警示
    if weak_stocks:
        html += """
        <div class="section">
            <div class="section-title weak">⚠️ 風險警示</div>
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
                        <span class="info-value">{format_number(stock.get('trade_value', 0))}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">🚨 警報原因:</span>
                        <span class="info-value">{stock['alert_reason']}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">⚠️ 風險提示:</span>
                        <span class="info-value">建議謹慎操作，嚴設停損</span>
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
            <p>• <strong>長線投資重視基本面</strong>：關注殖利率、EPS成長、ROE等指標</p>
            <p>• <strong>短線操作注重技術面</strong>：關注均線、MACD、RSI等指標</p>
            <p>• <strong>法人動向是重要參考</strong>：外資和投信的買賣行為具指標意義</p>
            <p>• 建議設定停損點，控制投資風險</p>
        </div>
        
        <div class="footer">
            <p>此電子郵件由台股分析系統自動產生於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>💎 長線投資著重基本面 | 🔥 短線操作關注技術面 | 🏦 法人動向具參考價值</p>
            <p>祝您投資順利！💰</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_combined_recommendations(strategies_data, time_slot):
    """
    發送包含三種策略的股票推薦通知（增強版 - 重點顯示長線基本面資訊）
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
    
    # 短線推薦部分（技術面為主）
    message += "【短線推薦】（技術面主導）\n\n"
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
            foreign_info = format_foreign_net_buy(analysis.get('foreign_net_buy', 0))
            if foreign_info:
                message += f"{foreign_info}\n"
            
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
    
    # 長線推薦部分（基本面為主） - 重點增強
    message += "【長線潛力】（基本面主導）\n\n"
    if long_term_stocks:
        for i, stock in enumerate(long_term_stocks, 1):
            message += f"💎 {i}. {stock['code']} {stock['name']}\n"
            
            # 現價和漲跌幅
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            
            # 成交量
            trade_value = stock.get('trade_value', 0)
            message += f"💵 成交金額: {format_number(trade_value)}\n"
            
            # 重點：基本面資訊
            fundamental_info = []
            
            # 殖利率資訊
            dividend_yield = analysis.get('dividend_yield', 0)
            if dividend_yield > 0:
                if dividend_yield > 5:
                    fundamental_info.append(f"💰 高殖利率: {dividend_yield:.1f}%")
                elif dividend_yield > 3:
                    fundamental_info.append(f"💰 殖利率: {dividend_yield:.1f}%")
                else:
                    fundamental_info.append(f"💰 殖利率: {dividend_yield:.1f}%")
            
            # EPS成長資訊
            eps_growth = analysis.get('eps_growth', 0)
            if eps_growth > 0:
                if eps_growth > 15:
                    fundamental_info.append(f"📈 EPS高成長: {eps_growth:.1f}%")
                elif eps_growth > 10:
                    fundamental_info.append(f"📈 EPS成長: {eps_growth:.1f}%")
                elif eps_growth > 5:
                    fundamental_info.append(f"📈 EPS穩定成長: {eps_growth:.1f}%")
            
            # ROE資訊
            roe = analysis.get('roe', 0)
            if roe > 15:
                fundamental_info.append(f"🏆 ROE優異: {roe:.1f}%")
            elif roe > 10:
                fundamental_info.append(f"🏆 ROE良好: {roe:.1f}%")
            
            # 本益比資訊
            pe_ratio = analysis.get('pe_ratio', 0)
            if 0 < pe_ratio < 15:
                fundamental_info.append(f"📊 本益比合理: {pe_ratio:.1f}倍")
            elif pe_ratio > 0:
                fundamental_info.append(f"📊 本益比: {pe_ratio:.1f}倍")
            
            # 顯示基本面資訊
            if fundamental_info:
                message += f"📋 基本面: {' | '.join(fundamental_info)}\n"
            
            # 法人買超資訊 - 加強顯示
            foreign_net = analysis.get('foreign_net_buy', 0)
            trust_net = analysis.get('trust_net_buy', 0)
            consecutive_days = analysis.get('consecutive_buy_days', 0)
            
            institutional_info = []
            
            # 外資買超
            if abs(foreign_net) >= 1000:  # 大於1000萬才顯示
                foreign_info = format_foreign_net_buy(foreign_net)
                if foreign_info:
                    institutional_info.append(foreign_info.replace('🏦 ', ''))
            
            # 投信買超
            if trust_net > 5000:  # 5000萬以上
                trust_amount = trust_net / 10000
                if trust_amount >= 1:
                    institutional_info.append(f"投信買超: {trust_amount:.1f}億")
                else:
                    institutional_info.append(f"投信買超: {trust_net/1000:.0f}千萬")
            elif trust_net < -5000:
                trust_amount = abs(trust_net) / 10000
                if trust_amount >= 1:
                    institutional_info.append(f"投信賣超: {trust_amount:.1f}億")
                else:
                    institutional_info.append(f"投信賣超: {abs(trust_net)/1000:.0f}千萬")
            
            # 連續買超天數
            if consecutive_days >= 3:
                institutional_info.append(f"連續買超{consecutive_days}天")
            elif consecutive_days <= -3:
                institutional_info.append(f"連續賣超{abs(consecutive_days)}天")
            
            if institutional_info:
                message += f"🏦 法人動向: {' | '.join(institutional_info)}\n"
            
            # 長線評分（如果有的話）
            long_term_score = stock.get('long_term_score', 0)
            if long_term_score > 0:
                message += f"⭐ 長線評分: {long_term_score:.1f}分\n"
            
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
            
            # 法人賣超資訊
            foreign_info = format_foreign_net_buy(analysis.get('foreign_net_buy', 0))
            if foreign_info and '賣超' in foreign_info:
                message += f"{foreign_info}\n"
            
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
    message += "⚠️ 長線投資重視基本面，短線操作注重技術面\n"
    message += "⚠️ 建議設定停損點，控制投資風險\n\n"
    message += "祝您投資順利！💰"
    
    # 生成HTML格式（增強版）
    html_body = generate_enhanced_html_report(strategies_data, time_slot, today)
    
    subject = f"【{time_slot}分析報告】- {today}"
    send_notification(message, subject, html_body)

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
    message = f"🔔 增強系統心跳檢測通知\n\n"
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
    
    # 系統功能說明
    message += "💎 系統增強功能:\n"
    message += "  • 長線推薦重視基本面（EPS、殖利率、ROE）\n"
    message += "  • 法人買超資訊詳細顯示\n"
    message += "  • 短線推薦著重技術指標\n"
    message += "  • HTML郵件格式美化\n\n"
    
    message += "💡 如果您收到此訊息，表示增強版通知系統運作正常！"
    
    # 發送心跳通知
    success = send_notification(message, "🔔 增強系統心跳檢測")
    
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
    log_event("初始化增強版通知系統")
    
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
    
    log_event("增強版通知系統初始化完成")
    log_event("✨ 新功能: 長線推薦加強基本面顯示")

# 測試函數
def test_notification():
    """測試通知功能"""
    log_event("開始測試增強版通知功能")
    
    # 測試基本通知
    test_message = f"""📧 增強版通知系統測試

⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 如果您收到此郵件，表示通知系統運作正常！

🆕 增強功能:
• 長線推薦重視基本面指標
• EPS成長率、殖利率、ROE詳細顯示
• 法人買賣超資訊加強
• HTML郵件美化升級

🔧 系統資訊:
• 郵件服務器: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}
• TLS加密: {'是' if EMAIL_CONFIG['use_tls'] else '否'}
• 發件人: {EMAIL_CONFIG['sender']}
• 收件人: {EMAIL_CONFIG['receiver']}

💡 這是測試郵件，請忽略投資建議內容。
"""

    success = send_notification(
        message=test_message,
        subject="📧 台股分析系統 - 增強版通知測試",
        urgent=False
    )

    if success:
        log_event("✅ 增強版通知測試成功！請檢查您的郵箱")
    else:
        log_event("❌ 增強版通知測試失敗，請檢查配置", 'error')

    return success

if __name__ == "__main__":
    # 初始化
    init()

    # 執行測試
    print("=" * 50)
    print("增強版通知系統測試")
    print("=" * 50)

    test_notification()

    print("\n" + "=" * 50)
    print("增強功能說明:")
    print("=" * 50)
    print("1. 長線推薦加強基本面顯示")
    print("2. EPS成長率、殖利率、ROE等關鍵指標")
    print("3. 法人買賣超資訊詳細顯示")
    print("4. HTML郵件格式全面升級")
    print("5. 區分短線技術面和長線基本面重點")
    print("=" * 50)
