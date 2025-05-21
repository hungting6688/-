"""
notifier.py - 股市機器人的通知系統
專注於Email作為主要通知渠道，並具備檔案備份功能
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

# 配置日誌
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'notifier.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 確保通知備份目錄存在
if FILE_BACKUP['enabled']:
    os.makedirs(FILE_BACKUP['directory'], exist_ok=True)

# 狀態追踪
STATUS = {
    'email': {'last_success': None, 'failure_count': 0, 'available': True},
    'file': {'last_success': None, 'failure_count': 0, 'available': True},
    'last_notification': None,
    'undelivered_count': 0,
    'last_heartbeat': None,
}

# 載入狀態 (如果存在)
STATUS_FILE = os.path.join(CACHE_DIR, 'notifier_status.json')
try:
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            stored_status = json.load(f)
            # 更新除了 'available' 以外的狀態
            for channel in STATUS:
                if channel in stored_status and isinstance(stored_status[channel], dict):
                    for key in STATUS[channel]:
                        if key != 'available' and key in stored_status[channel]:
                            STATUS[channel][key] = stored_status[channel][key]
            
            # 更新全局狀態
            for key in ['last_notification', 'undelivered_count', 'last_heartbeat']:
                if key in stored_status:
                    STATUS[key] = stored_status[key]
                    
            logging.info("已載入通知狀態")
except Exception as e:
    logging.error(f"載入狀態失敗: {e}")

def save_status():
    """保存狀態到文件"""
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(STATUS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存狀態失敗: {e}")

def log_event(message, level='info'):
    """記錄通知事件"""
    if level == 'error':
        logging.error(message)
        print(f"❌ {message}")
    elif level == 'warning':
        logging.warning(message)
        print(f"⚠️ {message}")
    else:
        logging.info(message)
        print(f"ℹ️ {message}")

def send_notification(message, subject='系統通知', html_body=None, urgent=False):
    """
    發送通知，嘗試Email，失敗後備份到檔案
    
    參數:
    - message: 通知內容
    - subject: 通知標題
    - html_body: HTML格式內容(可選)
    - urgent: 是否緊急通知
    
    返回:
    - bool: 是否成功發送
    """
    # 記錄通知
    log_event(f"發送通知: {subject}")
    
    # 更新上次通知時間
    STATUS['last_notification'] = datetime.now().isoformat()
    
    # 嘗試發送郵件
    success = False
    try:
        if EMAIL_CONFIG['enabled'] and STATUS['email']['available']:
            log_event(f"嘗試通過 Email 發送通知")
            if send_email_notification(message, subject, html_body, urgent):
                success = True
                
                # 更新渠道狀態
                STATUS['email']['last_success'] = datetime.now().isoformat()
                STATUS['email']['failure_count'] = 0
                save_status()
                
                log_event(f"通過 Email 發送通知成功")
    except Exception as e:
        # 更新失敗次數
        STATUS['email']['failure_count'] += 1
        save_status()
        
        log_event(f"通過 Email 發送通知失敗: {e}", 'error')
        log_event(traceback.format_exc(), 'error')
    
    # 如果郵件失敗且檔案備份啟用，則保存到文件
    if not success and FILE_BACKUP['enabled']:
        try:
            log_event(f"嘗試將通知保存到檔案")
            if save_notification_to_file(message, subject, html_body, urgent):
                # 文件備份成功仍算部分成功
                STATUS['file']['last_success'] = datetime.now().isoformat()
                STATUS['file']['failure_count'] = 0
                save_status()
                
                log_event(f"已將通知保存到檔案")
            else:
                STATUS['file']['failure_count'] += 1
                save_status()
                log_event(f"保存通知到檔案失敗", 'error')
        except Exception as e:
            STATUS['file']['failure_count'] += 1
            save_status()
            
            log_event(f"保存通知到檔案發生異常: {e}", 'error')
            log_event(traceback.format_exc(), 'error')
    
    # 如果所有渠道都失敗
    if not success and not (FILE_BACKUP['enabled'] and STATUS['file']['failure_count'] == 0):
        STATUS['undelivered_count'] += 1
        save_status()
        
        # 保存未發送的通知
        save_undelivered_notification(message, subject, html_body, urgent)
        log_event(f"所有通知渠道都失敗，已保存為未發送通知", 'error')
    
    return success

def send_email_notification(message, subject, html_body=None, urgent=False):
    """
    使用電子郵件發送通知
    
    返回:
    - bool: 是否成功
    """
    sender = EMAIL_CONFIG['sender']
    password = EMAIL_CONFIG['password']
    receiver = EMAIL_CONFIG['receiver']
    smtp_server = EMAIL_CONFIG['smtp_server']
    smtp_port = EMAIL_CONFIG['smtp_port']
    use_tls = EMAIL_CONFIG['use_tls']
    
    if not sender or not password or not receiver:
        log_event("缺少電子郵件通知配置", 'warning')
        return False
    
    # 嘗試重試
    max_attempts = RETRY_CONFIG['max_attempts']
    base_delay = RETRY_CONFIG['base_delay']
    backoff_factor = RETRY_CONFIG['backoff_factor']
    
    for attempt in range(max_attempts):
        try:
            # 隨機添加延遲
            if attempt > 0:
                delay = base_delay * (backoff_factor ** (attempt - 1))
                delay = delay * (1 + random.uniform(-0.2, 0.2))
                time.sleep(delay)
            
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
            
            # 添加郵件頭
            msg['Subject'] = f"{'[緊急] ' if urgent else ''}{subject}"
            msg['From'] = sender
            msg['To'] = receiver
            msg['Date'] = formatdate(localtime=True)
            
            # 嘗試通過不同方式發送
            if attempt == 0:
                # 第一次嘗試：使用標準配置
                if use_tls:
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                else:
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                # 後續嘗試：嘗試其他常見配置
                try:
                    if attempt == 1:
                        # 嘗試SSL
                        server = smtplib.SMTP_SSL(smtp_server, 465)
                    else:
                        # 嘗試多個常見SMTP服務器
                        alternate_servers = [
                            ('smtp.gmail.com', 587, True),
                            ('smtp-mail.outlook.com', 587, True),
                            ('smtp.mail.yahoo.com', 587, True),
                            ('smtp.gmail.com', 465, False)
                        ]
                        
                        for alt_server, alt_port, use_starttls in alternate_servers:
                            try:
                                if use_starttls:
                                    server = smtplib.SMTP(alt_server, alt_port)
                                    server.starttls()
                                else:
                                    server = smtplib.SMTP_SSL(alt_server, alt_port)
                                break
                            except:
                                continue
                except:
                    # 如果這些都失敗了，嘗試一次最後的嘗試
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    try:
                        server.starttls()
                    except:
                        pass
            
            # 登錄並發送
            server.login(sender, password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            log_event(f"電子郵件身份驗證失敗", 'error')
            break  # 不需要重試認證錯誤
            
        except socket.gaierror:
            log_event(f"無法連接到郵件服務器，網絡問題", 'warning')
            
        except Exception as e:
            log_event(f"電子郵件通知失敗 (嘗試 {attempt+1}/{max_attempts}): {e}", 'warning')
    
    return False

def save_notification_to_file(message, subject, html_body=None, urgent=False):
    """
    將通知保存到本地文件
    
    返回:
    - bool: 是否成功
    """
    if not FILE_BACKUP['enabled']:
        return False
        
    try:
        notifications_dir = FILE_BACKUP['directory']
        os.makedirs(notifications_dir, exist_ok=True)
        
        # 創建文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        urgency = "URGENT_" if urgent else ""
        safe_subject = "".join([c if c.isalnum() else "_" for c in subject])
        filename = f"{urgency}{timestamp}_{safe_subject[:30]}.txt"
        filepath = os.path.join(notifications_dir, filename)
        
        # 寫入文件
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

def save_undelivered_notification(message, subject, html_body=None, urgent=False):
    """保存未發送的通知以便稍後重試"""
    try:
        undelivered_dir = os.path.join(LOG_DIR, 'undelivered')
        os.makedirs(undelivered_dir, exist_ok=True)
        
        # 創建文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"undelivered_{timestamp}.json"
        filepath = os.path.join(undelivered_dir, filename)
        
        # 保存通知數據
        with open(filepath, 'w', encoding='utf-8') as f:
            data = {
                'timestamp': datetime.now().isoformat(),
                'subject': subject,
                'message': message,
                'html_body': html_body,
                'urgent': urgent,
                'retry_count': 0
            }
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        log_event(f"已保存未發送的通知: {filepath}")
        return True
    
    except Exception as e:
        log_event(f"保存未發送通知失敗: {e}", 'error')
        return False

def retry_undelivered_notifications(max_retries=3):
    """重試未發送的通知"""
    undelivered_dir = os.path.join(LOG_DIR, 'undelivered')
    if not os.path.exists(undelivered_dir):
        return 0, 0
    
    # 獲取所有未發送的通知
    files = [f for f in os.listdir(undelivered_dir) if f.startswith('undelivered_') and f.endswith('.json')]
    if not files:
        return 0, 0
    
    log_event(f"開始重試 {len(files)} 個未發送的通知")
    
    success_count = 0
    for filename in files:
        try:
            filepath = os.path.join(undelivered_dir, filename)
            
            # 讀取通知數據
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查重試次數
            retry_count = data.get('retry_count', 0)
            if retry_count >= max_retries:
                log_event(f"通知 {filename} 已達最大重試次數 ({max_retries}), 跳過", 'warning')
                continue
            
            # 重試發送
            message = data.get('message', '')
            subject = data.get('subject', '系統通知')
            html_body = data.get('html_body')
            urgent = data.get('urgent', False)
            
            # 添加重試信息
            retry_subject = f"{subject} [重試 {retry_count+1}/{max_retries}]"
            
            if send_notification(message, retry_subject, html_body, urgent):
                # 成功發送，刪除文件
                os.remove(filepath)
                success_count += 1
                log_event(f"成功重試發送通知: {filename}")
            else:
                # 更新重試次數
                data['retry_count'] = retry_count + 1
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                log_event(f"重試發送通知失敗: {filename}", 'warning')
            
            # 避免發送過於頻繁
            time.sleep(5)
            
        except Exception as e:
            log_event(f"處理未發送通知 {filename} 時出錯: {e}", 'error')
    
    return len(files), success_count

def send_heartbeat():
    """發送心跳檢測，確認通知系統正常運作"""
    now = datetime.now()
    
    # 檢查上次心跳時間
    if STATUS['last_heartbeat']:
        last_heartbeat = datetime.fromisoformat(STATUS['last_heartbeat'])
        # 如果距離上次心跳不足1小時，跳過
        if (now - last_heartbeat).total_seconds() < 3600:  # 1小時
            return False
    
    # 發送心跳通知
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    message = f"此為系統心跳檢測通知，時間: {timestamp}\n"
    
    # 添加系統狀態
    message += "\n系統狀態:\n"
    
    # 通知渠道狀態
    for channel in ['email', 'file']:
        status = STATUS[channel]
        if status['last_success']:
            last_time = datetime.fromisoformat(status['last_success'])
            time_ago = (now - last_time).total_seconds() / 60  # 分鐘
            if time_ago < 60:
                time_str = f"{int(time_ago)} 分鐘前"
            else:
                time_str = f"{int(time_ago/60)} 小時前"
        else:
            time_str = "從未成功"
        
        emoji = "✅" if status['available'] and status['failure_count'] < 3 else "⚠️"
        message += f"  {emoji} {channel}: 上次成功 {time_str}, 失敗次數 {status['failure_count']}\n"
    
    # 未送達統計
    message += f"\n未送達通知數: {STATUS['undelivered_count']}\n"
    
    # 發送心跳通知
    success = send_notification(message, "系統心跳檢測")
    
    # 更新心跳時間
    if success:
        STATUS['last_heartbeat'] = now.isoformat()
        save_status()
    
    return success

def is_notification_available():
    """檢查通知系統是否可用"""
    # 如果Email可用或檔案備份可用，則通知系統可用
    return (EMAIL_CONFIG['enabled'] and STATUS['email']['available']) or \
           (FILE_BACKUP['enabled'] and STATUS['file']['available'])

def send_stock_recommendations(stocks, time_slot):
    """
    發送股票推薦通知
    
    參數:
    - stocks: 推薦股票列表
    - time_slot: 時段名稱
    """
    if not stocks:
        message = f"【{time_slot}推薦】\n\n沒有符合條件的推薦股票"
        subject = f"【{time_slot}推薦】- 無推薦"
        send_notification(message, subject)
        return
    
    # 生成通知消息
    today = datetime.now().strftime("%Y/%m/%d")
    message = f"📈 {today} {time_slot}推薦股票\n\n"
    
    for stock in stocks:
        message += f"📊 {stock['code']} {stock['name']}\n"
        message += f"推薦理由: {stock['reason']}\n"
        message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_parts = []
    html_parts.append("""
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { color: #0066cc; font-size: 20px; font-weight: bold; margin-bottom: 20px; }
            .stock { margin-bottom: 20px; border-left: 4px solid #0066cc; padding-left: 15px; }
            .stock-name { font-weight: bold; font-size: 16px; }
            .label { color: #666; }
            .price { color: #009900; font-weight: bold; }
            .stop-loss { color: #cc0000; font-weight: bold; }
            .reason { color: #333; }
            .footer { color: #666; font-size: 12px; margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="header">""" + f"📈 {today} {time_slot}推薦股票" + """</div>
    """)
    
    for stock in stocks:
        stock_html = """
        <div class="stock">
            <div class="stock-name">📊 """ + stock['code'] + " " + stock['name'] + """</div>
            <div><span class="label">推薦理由:</span> <span class="reason">""" + stock['reason'] + """</span></div>
            <div><span class="label">目標價:</span> <span class="price">""" + str(stock['target_price']) + """</span> | <span class="label">止損價:</span> <span class="stop-loss">""" + str(stock['stop_loss']) + """</span></div>
        </div>
        """
        html_parts.append(stock_html)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_parts.append("""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 """ + timestamp + """
        </div>
    </body>
    </html>
    """)
    
    html_body = "".join(html_parts)
    subject = f"【{time_slot}推薦】- {today}"
    send_notification(message, subject, html_body)

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
    message = f"📈 {today} {time_slot}分析報告\n\n"
    
    # 短線推薦部分
    message += "【短線推薦】\n\n"
    if short_term_stocks:
        for stock in short_term_stocks:
            message += f"📈 {stock['code']} {stock['name']}\n"
            message += f"推薦理由: {stock['reason']}\n"
            message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
    else:
        message += "今日無短線推薦股票\n\n"
    
    # 長線推薦部分
    message += "【長線潛力】\n\n"
    if long_term_stocks:
        for stock in long_term_stocks:
            message += f"📊 {stock['code']} {stock['name']}\n"
            message += f"推薦理由: {stock['reason']}\n"
            message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
    else:
        message += "今日無長線推薦股票\n\n"
    
    # 極弱股警示部分
    message += "【極弱股】\n\n"
    if weak_stocks:
        for stock in weak_stocks:
            message += f"⚠️ {stock['code']} {stock['name']}\n"
            message += f"當前價格: {stock['current_price']}\n"
            message += f"警報原因: {stock['alert_reason']}\n\n"
    else:
        message += "今日無極弱股警示\n\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_parts = []
    html_parts.append("""
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { color: #0066cc; font-size: 20px; font-weight: bold; margin-bottom: 20px; }
            .section { margin-bottom: 30px; }
            .section-title { color: #333; font-size: 18px; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
            .stock { margin-bottom: 20px; border-left: 4px solid #0066cc; padding-left: 15px; }
            .stock.long-term { border-left-color: #009900; }
            .stock.weak { border-left-color: #cc0000; }
            .stock-name { font-weight: bold; font-size: 16px; }
            .label { color: #666; }
            .price { color: #009900; font-weight: bold; }
            .stop-loss { color: #cc0000; font-weight: bold; }
            .current-price { font-weight: bold; }
            .reason { color: #333; }
            .footer { color: #666; font-size: 12px; margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="header">""" + f"📈 {today} {time_slot}分析報告" + """</div>
    """)
    
    # 短線推薦 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【短線推薦】</div>
    """)
    
    if short_term_stocks:
        for stock in short_term_stocks:
            stock_html = """
            <div class="stock">
                <div class="stock-name">📈 """ + stock['code'] + " " + stock['name'] + """</div>
                <div><span class="label">推薦理由:</span> <span class="reason">""" + stock['reason'] + """</span></div>
                <div><span class="label">目標價:</span> <span class="price">""" + str(stock['target_price']) + """</span> | <span class="label">止損價:</span> <span class="stop-loss">""" + str(stock['stop_loss']) + """</span></div>
                <div><span class="label">當前價格:</span> <span class="current-price">""" + str(stock.get('current_price', '無資料')) + """</span></div>
            </div>
            """
            html_parts.append(stock_html)
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
            stock_html = """
            <div class="stock long-term">
                <div class="stock-name">📊 """ + stock['code'] + " " + stock['name'] + """</div>
                <div><span class="label">推薦理由:</span> <span class="reason">""" + stock['reason'] + """</span></div>
                <div><span class="label">目標價:</span> <span class="price">""" + str(stock['target_price']) + """</span> | <span class="label">止損價:</span> <span class="stop-loss">""" + str(stock['stop_loss']) + """</span></div>
                <div><span class="label">當前價格:</span> <span class="current-price">""" + str(stock.get('current_price', '無資料')) + """</span></div>
            </div>
            """
            html_parts.append(stock_html)
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
            stock_html = """
            <div class="stock weak">
                <div class="stock-name">⚠️ """ + stock['code'] + " " + stock['name'] + """</div>
                <div><span class="label">當前價格:</span> <span class="current-price">""" + str(stock['current_price']) + """</span></div>
                <div><span class="label">警報原因:</span> <span class="reason">""" + stock['alert_reason'] + """</span></div>
            </div>
            """
            html_parts.append(stock_html)
    else:
        html_parts.append("""<div>今日無極弱股警示</div>""")
    
    html_parts.append("""</div>""")  # 關閉極弱股警示區段
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_parts.append("""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 """ + timestamp + """
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
