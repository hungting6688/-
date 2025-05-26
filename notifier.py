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

def generate_enhanced_html_report(strategies_data, time_slot, date):
    """生成增強版HTML報告（重點顯示長線基本面資訊）"""
    
    short_term_stocks = strategies_data.get("short_term", [])
    long_term_stocks = strategies_data.get("long_term", [])
    weak_stocks = strategies_data.get("weak_stocks", [])
