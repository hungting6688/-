"""
integrated_notifier.py - 整合版通知系統
同時支援EMAIL和LINE推播，確保訊息送達率
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
from typing import Dict, List, Any, Optional

# 導入LINE推播模組
try:
    from line_notifier import LineNotifier
    LINE_AVAILABLE = True
except ImportError:
    LINE_AVAILABLE = False
    print("⚠️ LINE推播模組未找到，僅使用EMAIL推播")

# 導入配置
try:
    from config import EMAIL_CONFIG, LINE_CONFIG, NOTIFICATION_CHANNELS, FILE_BACKUP, RETRY_CONFIG, LOG_DIR
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
    
    LINE_CONFIG = {
        'enabled': os.getenv('LINE_ENABLED', 'True').lower() in ('true', '1', 't'),
        'channel_access_token': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
        'user_id': os.getenv('LINE_USER_ID'),
        'group_id': os.getenv('LINE_GROUP_ID')
    }
    
    LOG_DIR = 'logs'
    FILE_BACKUP = {'enabled': True, 'directory': os.path.join(LOG_DIR, 'notifications')}
    RETRY_CONFIG = {'max_attempts': 3, 'base_delay': 2.0, 'backoff_factor': 1.5, 'max_delay': 60}

# 確保目錄存在
for directory in [LOG_DIR, FILE_BACKUP['directory']]:
    os.makedirs(directory, exist_ok=True)

# 配置日誌
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'integrated_notifier.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 狀態追踪
STATUS = {
    'email': {'last_success': None, 'failure_count': 0, 'available': True},
    'line': {'last_success': None, 'failure_count': 0, 'available': LINE_AVAILABLE and LINE_CONFIG.get('enabled', False)},
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

# 初始化LINE推播器
if LINE_AVAILABLE and STATUS['line']['available']:
    line_notifier = LineNotifier()
    if not line_notifier.enabled:
        STATUS['line']['available'] = False
        log_event("LINE推播配置不完整，已停用", 'warning')
else:
    line_notifier = None

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

def send_email_notification(message, subject, html_body=None, urgent=False):
    """發送EMAIL通知"""
    if not EMAIL_CONFIG['enabled'] or not STATUS['email']['available']:
        return False
    
    sender = EMAIL_CONFIG['sender']
    password = EMAIL_CONFIG['password']
    receiver = EMAIL_CONFIG['receiver']
    smtp_server = EMAIL_CONFIG['smtp_server']
    smtp_port = EMAIL_CONFIG['smtp_port']
    
    if not sender or not password or not receiver:
        log_event("EMAIL配置不完整", 'warning')
        STATUS['email']['available'] = False
        return False
    
    max_attempts = RETRY_CONFIG['max_attempts']
    
    for attempt in range(max_attempts):
        try:
            log_event(f"嘗試發送EMAIL (第 {attempt + 1} 次)")
            
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
            
            log_event("EMAIL發送成功！")
            STATUS['email']['last_success'] = datetime.now().isoformat()
            STATUS['email']['failure_count'] = 0
            return True
            
        except Exception as e:
            log_event(f"EMAIL發送失敗 (嘗試 {attempt + 1}/{max_attempts}): {e}", 'error')
            STATUS['email']['failure_count'] += 1
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
    
    STATUS['email']['available'] = False
    return False

def send_line_notification(message, data=None, time_slot=None):
    """發送LINE通知"""
    if not STATUS['line']['available'] or not line_notifier:
        return False
    
    try:
        success = False
        
        # 如果有推薦數據，發送結構化訊息
        if data and time_slot:
            success = line_notifier.send_stock_recommendations(data, time_slot)
        else:
            # 發送純文字訊息
            success = line_notifier.send_text_message(message)
        
        if success:
            log_event("LINE推播發送成功！")
            STATUS['line']['last_success'] = datetime.now().isoformat()
            STATUS['line']['failure_count'] = 0
            return True
        else:
            log_event("LINE推播發送失敗", 'error')
            STATUS['line']['failure_count'] += 1
            return False
            
    except Exception as e:
        log_event(f"LINE推播異常: {e}", 'error')
        STATUS['line']['failure_count'] += 1
        return False

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
        
        log_event(f"通知已保存到文件: {filepath}")
        STATUS['file']['last_success'] = datetime.now().isoformat()
        STATUS['file']['failure_count'] = 0
        return True
    
    except Exception as e:
        log_event(f"保存通知到文件失敗: {e}", 'error')
        STATUS['file']['failure_count'] += 1
        return False

def send_integrated_notification(message, subject='系統通知', html_body=None, urgent=False, 
                                recommendations_data=None, time_slot=None):
    """
    發送整合通知（EMAIL + LINE）
    
    參數:
    - message: 純文字訊息
    - subject: 郵件主題
    - html_body: HTML郵件內容
    - urgent: 是否緊急
    - recommendations_data: 股票推薦數據（用於LINE結構化訊息）
    - time_slot: 時段名稱（用於LINE訊息）
    
    返回:
    - 通知是否成功送達（至少一個渠道成功）
    """
    log_event(f"發送整合通知: {subject}")
    
    # 更新上次通知時間
    STATUS['last_notification'] = datetime.now().isoformat()
    
    success_count = 0
    total_channels = 0
    
    # 嘗試EMAIL通知
    if EMAIL_CONFIG['enabled'] and STATUS['email']['available']:
        total_channels += 1
        if send_email_notification(message, subject, html_body, urgent):
            success_count += 1
            log_event("✅ EMAIL通知發送成功")
        else:
            log_event("❌ EMAIL通知發送失敗", 'error')
    
    # 嘗試LINE通知（支援結構化訊息）
    if STATUS['line']['available']:
        total_channels += 1
        if send_line_notification(message, recommendations_data, time_slot):
            success_count += 1
            log_event("✅ LINE推播發送成功")
        else:
            log_event("❌ LINE推播發送失敗", 'error')
    
    # 如果所有主要渠道都失敗，保存到文件
    if success_count == 0 and FILE_BACKUP['enabled']:
        if save_notification_to_file(message, subject, html_body, urgent):
            log_event("✅ 通知已保存到備份文件")
        else:
            STATUS['undelivered_count'] += 1
            log_event("❌ 所有通知渠道都失敗", 'error')
    
    # 記錄通知結果
    if success_count > 0:
        log_event(f"📊 通知發送結果: {success_count}/{total_channels} 個渠道成功")
        return True
    else:
        STATUS['undelivered_count'] += 1
        log_event("💥 所有通知渠道都失敗", 'error')
        return False

def send_combined_recommendations(strategies_data, time_slot):
    """
    發送股票推薦通知（EMAIL + LINE雙推播）
    
    參數:
    - strategies_data: 推薦策略數據
    - time_slot: 時段名稱
    """
    short_term_stocks = strategies_data.get("short_term", [])
    long_term_stocks = strategies_data.get("long_term", [])
    weak_stocks = strategies_data.get("weak_stocks", [])
    
    if not short_term_stocks and not long_term_stocks and not weak_stocks:
        message = f"【{time_slot}分析報告】\n\n沒有符合條件的推薦股票和警示"
        subject = f"【{time_slot}分析報告】- 無推薦"
        send_integrated_notification(message, subject)
        return
    
    # 生成EMAIL用的詳細報告
    today = datetime.now().strftime("%Y/%m/%d")
    message = f"📈 {today} {time_slot}分析報告\n\n"
    
    # 時段中文對應
    time_slot_names = {
        'morning_scan': '🌅 早盤掃描 (9:30)',
        'mid_morning_scan': '☀️ 盤中掃描 (10:30)',
        'mid_day_scan': '🌞 午間掃描 (12:30)',
        'afternoon_scan': '🌇 盤後掃描 (15:00)',
        'weekly_summary': '📈 週末總結 (週六12:00)'
    }
    
    display_name = time_slot_names.get(time_slot, time_slot)
    
    # 短線推薦部分
    message += f"【🔥 短線推薦】\n\n"
    if short_term_stocks:
        for i, stock in enumerate(short_term_stocks, 1):
            message += f"🔥 {i}. {stock['code']} {stock['name']}\n"
            
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            message += f"💵 成交金額: {format_number(stock.get('trade_value', 0))}\n"
            message += f"📋 推薦理由: {stock['reason']}\n"
            
            target_price = stock.get('target_price')
            stop_loss = stock.get('stop_loss')
            if target_price:
                message += f"🎯 目標價: {target_price} 元"
            if stop_loss:
                message += f" | 🛡️ 止損價: {stop_loss} 元"
            message += "\n\n"
    else:
        message += "今日無短線推薦股票\n\n"
    
    # 長線推薦部分
    message += f"【💎 長線潛力股】\n\n"
    if long_term_stocks:
        for i, stock in enumerate(long_term_stocks, 1):
            message += f"💎 {i}. {stock['code']} {stock['name']}\n"
            
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            message += f"💵 成交金額: {format_number(stock.get('trade_value', 0))}\n"
            
            # 基本面資訊
            if 'dividend_yield' in analysis:
                dividend_yield = analysis['dividend_yield']
                if dividend_yield > 0:
                    message += f"💸 殖利率: {dividend_yield:.1f}%\n"
            
            if 'eps_growth' in analysis:
                eps_growth = analysis['eps_growth']
                if eps_growth > 0:
                    message += f"📈 EPS成長: {eps_growth:.1f}%\n"
            
            # 法人買超資訊
            if 'foreign_net_buy' in analysis:
                foreign_net = analysis['foreign_net_buy']
                if foreign_net > 5000:
                    message += f"🏦 外資買超: {format_number(foreign_net * 10000)}\n"
            
            message += f"📋 投資亮點: {stock['reason']}\n"
            
            target_price = stock.get('target_price')
            stop_loss = stock.get('stop_loss')
            if target_price:
                message += f"🎯 目標價: {target_price} 元"
            if stop_loss:
                message += f" | 🛡️ 止損價: {stop_loss} 元"
            message += "\n\n"
    else:
        message += "今日無長線推薦股票\n\n"
    
    # 風險警示部分
    if weak_stocks:
        message += f"【⚠️ 風險警示】\n\n"
        for i, stock in enumerate(weak_stocks, 1):
            message += f"⚠️ {i}. {stock['code']} {stock['name']}\n"
            
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            message += f"💵 成交金額: {format_number(stock.get('trade_value', 0))}\n"
            message += f"🚨 風險因子: {stock['alert_reason']}\n"
            message += f"⚠️ 操作建議: 謹慎操作，嚴設停損\n\n"
    
    # 投資提醒
    message += f"【💡 投資提醒】\n"
    message += f"📧 本報告透過EMAIL + LINE雙重推播確保送達\n"
    if time_slot == 'morning_scan':
        message += f"🌅 早盤分析已延後到9:30，使用當日即時數據提升準確度\n"
    if time_slot == 'weekly_summary':
        message += f"📊 週末總結改到週六中午12:00，給您更充裕的週末規劃時間\n"
    message += f"⚠️ 本報告僅供參考，不構成投資建議\n"
    message += f"⚠️ 股市有風險，投資需謹慎\n\n"
    message += f"祝您投資順利！💰"
    
    # 生成HTML版本（可選）
    html_body = None  # 可以後續實現HTML版本
    
    # 發送整合通知（EMAIL + LINE）
    subject = f"【{display_name}】💎 雙推播股票分析 - {today}"
    send_integrated_notification(
        message=message, 
        subject=subject, 
        html_body=html_body,
        recommendations_data=strategies_data,
        time_slot=time_slot
    )

def send_heartbeat():
    """發送心跳檢測（EMAIL + LINE）"""
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
    message = f"🔔 雙推播系統心跳檢測通知\n\n"
    message += f"⏰ 檢測時間: {timestamp}\n\n"
    
    # 系統狀態
    message += f"📊 系統狀態:\n"
    
    # EMAIL狀態
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
    message += f"  {emoji} EMAIL通知: 上次成功 {time_str}, 失敗次數 {email_status['failure_count']}\n"
    
    # LINE狀態
    line_status = STATUS['line']
    if line_status['available']:
        if line_status['last_success']:
            try:
                last_time = datetime.fromisoformat(line_status['last_success'])
                hours_ago = (now - last_time).total_seconds() / 3600
                time_str = f"{hours_ago:.1f} 小時前" if hours_ago >= 1 else f"{int((now - last_time).total_seconds() / 60)} 分鐘前"
            except:
                time_str = "時間解析錯誤"
        else:
            time_str = "從未成功"
        
        emoji = "✅" if line_status['failure_count'] < 3 else "⚠️"
        message += f"  {emoji} LINE推播: 上次成功 {time_str}, 失敗次數 {line_status['failure_count']}\n"
    else:
        message += f"  ❌ LINE推播: 未啟用或配置錯誤\n"
    
    # 未送達統計
    message += f"\n📈 統計資訊:\n"
    message += f"  • 未送達通知數: {STATUS['undelivered_count']}\n"
    message += f"  • 系統運行正常: {'是' if email_status['failure_count'] < 5 and line_status['failure_count'] < 5 else '否'}\n\n"
    
    message += f"🆕 系統更新:\n"
    message += f"  • ✅ 啟用EMAIL + LINE雙推播功能\n"
    message += f"  • ✅ 早盤分析延後到9:30，使用當日數據\n"
    message += f"  • ✅ 週末總結改到週六中午12:00\n"
    message += f"  • 📱 LINE推播支援結構化股票訊息顯示\n\n"
    
    message += f"💡 如果您收到此訊息，表示雙推播通知系統運作正常！"
    
    # 發送心跳通知
    success = send_integrated_notification(message, "🔔 雙推播系統心跳檢測")
    
    # 更新心跳時間
    if success:
        STATUS['last_heartbeat'] = now.isoformat()
    
    return success

def is_notification_available():
    """檢查通知系統是否可用"""
    return (EMAIL_CONFIG['enabled'] and STATUS['email']['available']) or STATUS['line']['available']

def init():
    """初始化整合通知系統"""
    log_event("初始化整合通知系統（EMAIL + LINE）")
    
    # 檢查EMAIL配置
    if EMAIL_CONFIG['enabled']:
        missing = []
        for key in ['sender', 'password', 'receiver']:
            if not EMAIL_CONFIG[key]:
                missing.append(f'EMAIL_{key.upper()}')
        
        if missing:
            log_event(f"警告: 缺少EMAIL配置: {', '.join(missing)}", 'warning')
            STATUS['email']['available'] = False
        else:
            log_event("✅ EMAIL配置檢查通過")
    
    # 檢查LINE配置
    if LINE_CONFIG['enabled'] and LINE_AVAILABLE:
        if line_notifier and line_notifier.enabled:
            log_event("✅ LINE推播配置檢查通過")
            STATUS['line']['available'] = True
        else:
            log_event("⚠️ LINE推播配置不完整", 'warning')
            STATUS['line']['available'] = False
    elif not LINE_AVAILABLE:
        log_event("⚠️ LINE推播模組未安裝", 'warning')
        STATUS['line']['available'] = False
    
    # 檢查文件備份
    if FILE_BACKUP['enabled']:
        try:
            os.makedirs(FILE_BACKUP['directory'], exist_ok=True)
            log_event(f"✅ 文件備份目錄準備完成: {FILE_BACKUP['directory']}")
        except Exception as e:
            log_event(f"文件備份目錄創建失敗: {e}", 'error')
            STATUS['file']['available'] = False
    
    available_channels = []
    if STATUS['email']['available']:
        available_channels.append("EMAIL")
    if STATUS['line']['available']:
        available_channels.append("LINE")
    
    log_event(f"🎯 整合通知系統初始化完成，可用渠道: {', '.join(available_channels) if available_channels else '無'}")
    
    if not available_channels:
        log_event("❌ 警告: 沒有可用的通知渠道！", 'error')

# 向下相容的函數別名
send_notification = send_integrated_notification

if __name__ == "__main__":
    # 初始化
    init()
    
    # 執行測試
    print("=" * 60)
    print("🔧 整合通知系統測試（EMAIL + LINE）")
    print("=" * 60)
    
    # 測試心跳
    print("💓 測試心跳通知...")
    if send_heartbeat():
        print("✅ 心跳通知發送成功")
    else:
        print("❌ 心跳通知發送失敗")
    
    print("\n📊 測試股票推薦通知...")
    
    # 創建測試數據
    test_data = {
        "short_term": [
            {
                "code": "2330",
                "name": "台積電",
                "current_price": 638.5,
                "reason": "技術面轉強，MACD金叉",
                "target_price": 670.0,
                "stop_loss": 620.0,
                "trade_value": 14730000000,
                "analysis": {"change_percent": 2.35}
            }
        ],
        "long_term": [
            {
                "code": "2609",
                "name": "陽明",
                "current_price": 91.2,
                "reason": "高殖利率7.2%，EPS高成長35.6%",
                "target_price": 110.0,
                "stop_loss": 85.0,
                "trade_value": 4560000000,
                "analysis": {
                    "change_percent": 1.8,
                    "dividend_yield": 7.2,
                    "eps_growth": 35.6,
                    "foreign_net_buy": 45000
                }
            }
        ],
        "weak_stocks": []
    }
    
    # 發送測試通知
    send_combined_recommendations(test_data, "雙推播測試")
    
    print("\n✅ 整合通知系統測試完成！")
    print("📧 請檢查您的EMAIL和LINE是否都收到測試訊息")
    print("💡 如果只收到其中一種，請檢查另一種的配置")
