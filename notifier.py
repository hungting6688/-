"""
unified_stock_notifier.py - 統整版股票分析通知系統
整合EMAIL、LINE和文件備份三種通知方式
修復技術指標顯示和長線文字清晰度問題
"""
import os
import time
import json
import logging
import traceback
import smtplib
import socket
import ssl
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from typing import Dict, List, Any, Optional

# 導入配置
try:
    from config import EMAIL_CONFIG, LINE_CONFIG, FILE_BACKUP, RETRY_CONFIG, LOG_DIR, CACHE_DIR
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
    CACHE_DIR = 'cache'
    FILE_BACKUP = {'enabled': True, 'directory': os.path.join(LOG_DIR, 'notifications')}
    RETRY_CONFIG = {'max_attempts': 3, 'base_delay': 2.0, 'backoff_factor': 1.5, 'max_delay': 60}

# 確保目錄存在
for directory in [LOG_DIR, CACHE_DIR, FILE_BACKUP['directory']]:
    os.makedirs(directory, exist_ok=True)

# 配置日誌
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'unified_stock_notifier.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 狀態追踪
STATUS = {
    'email': {'last_success': None, 'failure_count': 0, 'available': True},
    'line': {'last_success': None, 'failure_count': 0, 'available': False},
    'file': {'last_success': None, 'failure_count': 0, 'available': True},
    'last_notification': None,
    'undelivered_count': 0,
    'last_heartbeat': None,
}

class LineNotifier:
    """LINE推播通知器"""
    
    def __init__(self):
        """初始化LINE通知器"""
        self.channel_access_token = LINE_CONFIG.get('channel_access_token')
        self.user_id = LINE_CONFIG.get('user_id')
        self.group_id = LINE_CONFIG.get('group_id')
        self.api_url = 'https://api.line.me/v2/bot/message/push'
        
        # 驗證配置
        self.enabled = self._validate_config()
        if self.enabled:
            STATUS['line']['available'] = True
        
    def _validate_config(self) -> bool:
        """驗證LINE配置是否完整"""
        if not LINE_CONFIG.get('enabled', False):
            return False
            
        if not self.channel_access_token:
            log_event("LINE_CHANNEL_ACCESS_TOKEN 未設置", 'warning')
            return False
        
        if not self.user_id and not self.group_id:
            log_event("LINE_USER_ID 或 LINE_GROUP_ID 至少要設置一個", 'warning')
            return False
        
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """獲取API請求標頭"""
        return {
            'Authorization': f'Bearer {self.channel_access_token}',
            'Content-Type': 'application/json'
        }
    
    def _send_message(self, to: str, message: Dict[str, Any]) -> bool:
        """發送訊息到LINE"""
        if not self.enabled:
            return False
        
        payload = {
            'to': to,
            'messages': [message]
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self._get_headers(),
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                log_event(f"LINE訊息發送成功到 {to}")
                return True
            else:
                log_event(f"LINE訊息發送失敗: {response.status_code} - {response.text}", 'error')
                return False
                
        except Exception as e:
            log_event(f"LINE訊息發送異常: {e}", 'error')
            return False
    
    def send_text_message(self, text: str, target_type: str = 'user') -> bool:
        """發送純文字訊息"""
        # 選擇發送目標
        if target_type == 'group' and self.group_id:
            to = self.group_id
        elif target_type == 'user' and self.user_id:
            to = self.user_id
        else:
            to = self.user_id or self.group_id
        
        if not to:
            log_event("沒有有效的LINE發送目標", 'error')
            return False
        
        # LINE文字訊息限制2000字元
        if len(text) > 2000:
            text = text[:1990] + "...(內容過長已截取)"
        
        message = {
            'type': 'text',
            'text': text
        }
        
        return self._send_message(to, message)
    
    def send_flex_message(self, alt_text: str, flex_content: Dict[str, Any], target_type: str = 'user') -> bool:
        """發送Flex訊息（結構化訊息）"""
        # 選擇發送目標
        if target_type == 'group' and self.group_id:
            to = self.group_id
        elif target_type == 'user' and self.user_id:
            to = self.user_id
        else:
            to = self.user_id or self.group_id
        
        if not to:
            log_event("沒有有效的LINE發送目標", 'error')
            return False
        
        message = {
            'type': 'flex',
            'altText': alt_text,
            'contents': flex_content
        }
        
        return self._send_message(to, message)
    
    def generate_stock_flex_message(self, recommendations: Dict[str, List[Dict]], time_slot: str) -> Dict[str, Any]:
        """生成股票推薦的Flex訊息格式"""
        # 時段中文對應
        time_slot_names = {
            'morning_scan': '🌅 早盤掃描',
            'mid_morning_scan': '☀️ 盤中掃描',
            'mid_day_scan': '🌞 午間掃描',
            'afternoon_scan': '🌇 盤後掃描',
            'weekly_summary': '📈 週末總結'
        }
        
        title = time_slot_names.get(time_slot, '📊 股票分析')
        
        # 創建Flex訊息結構
        flex_content = {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "weight": "bold",
                        "size": "xl",
                        "color": "#1DB446"
                    },
                    {
                        "type": "text",
                        "text": datetime.now().strftime('%Y/%m/%d %H:%M'),
                        "size": "sm",
                        "color": "#aaaaaa"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": []
            }
        }
        
        # 添加短線推薦
        if recommendations.get('short_term'):
            short_section = {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "🔥 短線推薦",
                        "weight": "bold",
                        "size": "md",
                        "color": "#FF5551"
                    }
                ]
            }
            
            for i, stock in enumerate(recommendations['short_term'][:3]):  # 最多顯示3支
                change_percent = stock.get('analysis', {}).get('change_percent', 0)
                change_color = "#FF5551" if change_percent > 0 else "#00C851" if change_percent < 0 else "#757575"
                change_text = f"+{change_percent:.1f}%" if change_percent > 0 else f"{change_percent:.1f}%"
                
                stock_box = {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"{stock['code']} {stock['name']}",
                            "size": "sm",
                            "flex": 3
                        },
                        {
                            "type": "text",
                            "text": f"{stock['current_price']}",
                            "size": "sm",
                            "align": "end",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": change_text,
                            "size": "sm",
                            "align": "end",
                            "color": change_color,
                            "flex": 1
                        }
                    ]
                }
                short_section["contents"].append(stock_box)
            
            flex_content["body"]["contents"].append(short_section)
        
        # 添加長線推薦
        if recommendations.get('long_term'):
            long_section = {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "💎 長線推薦",
                        "weight": "bold",
                        "size": "md",
                        "color": "#FFB000",
                        "margin": "md"
                    }
                ]
            }
            
            for stock in recommendations['long_term'][:3]:  # 最多顯示3支
                analysis = stock.get('analysis', {})
                dividend_yield = analysis.get('dividend_yield', 0)
                eps_growth = analysis.get('eps_growth', 0)
                
                # 基本面標籤
                tags = []
                if dividend_yield > 4:
                    tags.append(f"殖利率{dividend_yield:.1f}%")
                if eps_growth > 10:
                    tags.append(f"EPS成長{eps_growth:.1f}%")
                
                tags_text = " | ".join(tags) if tags else "基本面穩健"
                
                stock_box = {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": f"{stock['code']} {stock['name']}",
                                    "size": "sm",
                                    "weight": "bold",
                                    "flex": 2
                                },
                                {
                                    "type": "text",
                                    "text": f"{stock['current_price']}元",
                                    "size": "sm",
                                    "align": "end",
                                    "flex": 1
                                }
                            ]
                        },
                        {
                            "type": "text",
                            "text": tags_text,
                            "size": "xs",
                            "color": "#888888",
                            "margin": "xs"
                        }
                    ]
                }
                long_section["contents"].append(stock_box)
            
            flex_content["body"]["contents"].append(long_section)
        
        # 添加風險警示
        if recommendations.get('weak_stocks'):
            weak_section = {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "⚠️ 風險警示",
                        "weight": "bold",
                        "size": "md",
                        "color": "#FF8A00",
                        "margin": "md"
                    }
                ]
            }
            
            for stock in recommendations['weak_stocks'][:2]:  # 最多顯示2支
                stock_box = {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"{stock['code']} {stock['name']}",
                            "size": "sm",
                            "flex": 2
                        },
                        {
                            "type": "text",
                            "text": "謹慎操作",
                            "size": "sm",
                            "align": "end",
                            "color": "#FF8A00",
                            "flex": 1
                        }
                    ]
                }
                weak_section["contents"].append(stock_box)
            
            flex_content["body"]["contents"].append(weak_section)
        
        # 添加免責聲明
        disclaimer = {
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "contents": [
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "⚠️ 本報告僅供參考，不構成投資建議\n股市有風險，投資需謹慎",
                    "size": "xs",
                    "color": "#888888",
                    "margin": "md",
                    "wrap": True
                }
            ]
        }
        
        flex_content["body"]["contents"].append(disclaimer)
        
        return flex_content
    
    def send_stock_recommendations(self, recommendations: Dict[str, List[Dict]], time_slot: str) -> bool:
        """發送股票推薦通知"""
        try:
            # 生成Flex訊息
            flex_content = self.generate_stock_flex_message(recommendations, time_slot)
            
            # 生成替代文字
            short_count = len(recommendations.get('short_term', []))
            long_count = len(recommendations.get('long_term', []))
            weak_count = len(recommendations.get('weak_stocks', []))
            
            alt_text = f"📊 {time_slot}分析報告\n短線推薦: {short_count}支\n長線推薦: {long_count}支\n風險警示: {weak_count}支"
            
            # 發送Flex訊息
            success = self.send_flex_message(alt_text, flex_content)
            
            if success:
                log_event(f"LINE股票推薦通知發送成功: {time_slot}")
            else:
                log_event(f"LINE股票推薦通知發送失敗: {time_slot}", 'error')
            
            return success
            
        except Exception as e:
            log_event(f"生成LINE股票推薦訊息失敗: {e}", 'error')
            return False

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

def get_technical_indicators_text(analysis):
    """獲取技術指標文字"""
    indicators = []
    
    # RSI 指標
    if 'rsi' in analysis:
        rsi_value = analysis['rsi']
        if rsi_value < 30:
            indicators.append("RSI超賣")
        elif rsi_value > 70:
            indicators.append("RSI超買") 
        else:
            indicators.append(f"RSI {rsi_value:.0f}")
    
    # MACD 指標
    technical_signals = analysis.get('technical_signals', {})
    if technical_signals.get('macd_golden_cross'):
        indicators.append("MACD金叉")
    elif technical_signals.get('macd_bullish'):
        indicators.append("MACD轉強")
    
    # 均線指標
    if technical_signals.get('ma20_bullish'):
        indicators.append("站穩20MA")
    if technical_signals.get('ma_golden_cross'):
        indicators.append("均線多頭")
    
    # 成交量
    if 'volume_ratio' in analysis:
        vol_ratio = analysis['volume_ratio']
        if vol_ratio > 2:
            indicators.append(f"爆量{vol_ratio:.1f}倍")
        elif vol_ratio > 1.5:
            indicators.append(f"放量{vol_ratio:.1f}倍")
    
    # 法人買超（短線也顯示）
    if 'foreign_net_buy' in analysis and analysis['foreign_net_buy'] > 10000:
        indicators.append("外資買超")
    
    return indicators

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

def send_unified_notification(message, subject='系統通知', html_body=None, urgent=False, 
                            recommendations_data=None, time_slot=None):
    """
    發送統一通知（EMAIL + LINE + 文件備份）
    
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
    log_event(f"發送統一通知: {subject}")
    
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

def generate_unified_html_report(strategies_data, time_slot, date):
    """生成統一版HTML報告"""
    
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
                font-family: 'Microsoft JhengHei', 'Segoe UI', Arial, sans-serif;
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
            .shortterm-title {{
                border-bottom: 2px solid #e74c3c;
                background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
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
            .shortterm-card {{
                border: 2px solid #e74c3c;
                background: linear-gradient(135deg, #ffeaea 0%, #ffebee 100%);
                box-shadow: 0 4px 15px rgba(231, 76, 60, 0.2);
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
            
            .technical-indicators {{
                background: #e8f4fd;
                border-left: 4px solid #3498db;
                padding: 10px;
                margin: 10px 0;
                border-radius: 0 5px 5px 0;
            }}
            .indicator-tag {{
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 12px;
                margin: 2px 4px 2px 0;
                font-weight: bold;
            }}
            .rsi-tag {{ background: #9b59b6; }}
            .macd-tag {{ background: #e67e22; }}
            .ma-tag {{ background: #16a085; }}
            .volume-tag {{ background: #f39c12; }}
            .institutional-tag {{ background: #2ecc71; }}
            
            .fundamental-section {{
                background: #e8f5e8;
                border-left: 4px solid #27ae60;
                padding: 12px;
                margin: 10px 0;
                border-radius: 0 5px 5px 0;
            }}
            .fundamental-title {{
                font-weight: bold;
                color: #27ae60;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            .fundamental-item {{
                margin: 6px 0;
                display: flex;
                align-items: center;
                font-size: 13px;
                line-height: 1.4;
            }}
            
            .institutional-section {{
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 12px;
                margin: 10px 0;
                border-radius: 0 5px 5px 0;
            }}
            .institutional-title {{
                font-weight: bold;
                color: #2196f3;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            .institutional-item {{
                margin: 6px 0;
                display: flex;
                align-items: center;
                font-size: 13px;
                line-height: 1.4;
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
            <p>{date} - 📊 統一版股票通知系統</p>
        </div>
    """
    
    # 短線推薦區塊
    if short_term_stocks:
        html += """
        <div class="section">
            <div class="shortterm-title">🔥 短線推薦</div>
        """
        for stock in short_term_stocks:
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            price_class = "price-up" if change_percent > 0 else "price-down" if change_percent < 0 else "price-flat"
            change_symbol = "+" if change_percent > 0 else ""
            
            html += f"""
            <div class="stock-card shortterm-card">
                <div class="stock-header">
                    <div class="stock-name">🔥 {stock['code']} {stock['name']}</div>
                    <div class="stock-price {price_class}">
                        現價: {current_price} 元 ({change_symbol}{change_percent:.2f}%)
                    </div>
                </div>
                
                <div class="technical-indicators">
                    <div class="fundamental-title">📊 技術指標</div>
                    <div>
            """
            
            # 獲取技術指標標籤
            technical_indicators = get_technical_indicators_text(analysis)
            for indicator in technical_indicators:
                # 根據指標類型設定不同樣式
                tag_class = "indicator-tag"
                if "RSI" in indicator:
                    tag_class += " rsi-tag"
                elif "MACD" in indicator:
                    tag_class += " macd-tag"
                elif "MA" in indicator or "均線" in indicator:
                    tag_class += " ma-tag"
                elif "量" in indicator:
                    tag_class += " volume-tag"
                elif "外資" in indicator:
                    tag_class += " institutional-tag"
                
                html += f'<span class="{tag_class}">{indicator}</span>'
            
            html += f"""
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
    
    # 長線推薦區塊
    if long_term_stocks:
        html += """
        <div class="section">
            <div class="longterm-title">💎 長線潛力股 - 基本面優質</div>
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
                
                <div class="fundamental-section">
                    <div class="fundamental-title">📊 基本面優勢</div>
            """
            
            # 殖利率顯示
            if 'dividend_yield' in analysis and analysis['dividend_yield'] > 0:
                dividend_yield = analysis['dividend_yield']
                dividend_years = analysis.get('dividend_consecutive_years', 0)
                
                yield_class = "excellent-metric" if dividend_yield > 5 else "highlight-metric" if dividend_yield > 3 else ""
                
                html += f"""
                    <div class="fundamental-item">
                        <span>💸 殖利率:</span>
                        <span class="{yield_class}" style="margin-left: 8px;">{dividend_yield:.1f}%</span>
                """
                
                if dividend_years > 5:
                    html += f' <small style="margin-left: 8px; color: #27ae60;">(連續{dividend_years}年配息)</small>'
                
                html += "</div>"
            
            # EPS成長顯示
            if 'eps_growth' in analysis and analysis['eps_growth'] > 0:
                eps_growth = analysis['eps_growth']
                
                eps_class = "excellent-metric" if eps_growth > 20 else "highlight-metric" if eps_growth > 10 else ""
                growth_desc = "高速成長" if eps_growth > 20 else "穩健成長" if eps_growth > 10 else "成長"
                
                html += f"""
                    <div class="fundamental-item">
                        <span>📈 EPS{growth_desc}:</span>
                        <span class="{eps_class}" style="margin-left: 8px;">{eps_growth:.1f}%</span>
                    </div>
                """
            
            # ROE和本益比
            if 'roe' in analysis and analysis['roe'] > 0:
                roe = analysis['roe']
                pe_ratio = analysis.get('pe_ratio', 0)
                
                roe_class = "excellent-metric" if roe > 15 else "highlight-metric" if roe > 10 else ""
                pe_class = "excellent-metric" if pe_ratio < 15 else "highlight-metric" if pe_ratio < 20 else ""
                
                html += f"""
                    <div class="fundamental-item">
                        <span>🏆 ROE:</span>
                        <span class="{roe_class}" style="margin-left: 8px;">{roe:.1f}%</span>
                        <span style="margin-left: 15px;">📊 本益比:</span>
                        <span class="{pe_class}" style="margin-left: 8px;">{pe_ratio:.1f}倍</span>
                    </div>
                """
            
            html += "</div>"  # 結束基本面區塊
            
            # 法人動向區塊
            html += """
                <div class="institutional-section">
                    <div class="institutional-title">🏦 法人動向</div>
            """
            
            foreign_net = analysis.get('foreign_net_buy', 0)
            trust_net = analysis.get('trust_net_buy', 0)
            total_institutional = analysis.get('total_institutional', 0)
            consecutive_days = analysis.get('consecutive_buy_days', 0)
            
            if total_institutional > 50000:
                html += f"""
                    <div class="institutional-item">
                        <span>🔥 三大法人大幅買超:</span>
                        <span class="excellent-metric" style="margin-left: 8px;">{format_institutional_flow(total_institutional)}</span>
                    </div>
                """
            else:
                if foreign_net > 5000:
                    foreign_class = "excellent-metric" if foreign_net > 20000 else "highlight-metric"
                    html += f"""
                        <div class="institutional-item">
                            <span>🌍 外資買超:</span>
                            <span class="{foreign_class}" style="margin-left: 8px;">{format_institutional_flow(foreign_net)}</span>
                        </div>
                    """
                
                if trust_net > 3000:
                    trust_class = "excellent-metric" if trust_net > 10000 else "highlight-metric"
                    html += f"""
                        <div class="institutional-item">
                            <span>🏢 投信買超:</span>
                            <span class="{trust_class}" style="margin-left: 8px;">{format_institutional_flow(trust_net)}</span>
                        </div>
                    """
            
            if consecutive_days > 3:
                html += f"""
                    <div class="institutional-item">
                        <span>⏰ 持續買超:</span>
                        <span class="highlight-metric" style="margin-left: 8px;">{consecutive_days}天</span>
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
                        <span class="info-label">📋 投資亮點:</span>
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
    
    # 風險警示區塊
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
                        <span class="info-label">🚨 風險因子:</span>
                        {stock['alert_reason']}
                    </div>
                    <div class="info-row">
                        <span class="info-label">⚠️ 操作建議:</span>
                        謹慎操作，嚴設停損
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # 投資提醒
    html += """
        <div class="warning">
            <h3>💡 投資提醒</h3>
            <p><strong>🔥 短線推薦重點：</strong></p>
            <ul>
                <li>📊 重視技術指標轉強（RSI、MACD、均線）</li>
                <li>📈 關注成交量放大配合價格上漲</li>
                <li>🏦 法人買超提供資金動能支撐</li>
                <li>⏰ 適合短期操作，嚴設停損</li>
            </ul>
            <p><strong>💎 長線推薦重點：</strong></p>
            <ul>
                <li>💸 殖利率 > 3% 提供穩定現金流</li>
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
            <p>此電子郵件由統一版股票分析系統自動產生於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>📊 整合EMAIL、LINE和文件備份三種通知方式</p>
            <p>祝您投資順利！💰</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_unified_stock_recommendations(strategies_data, time_slot):
    """發送統一版股票推薦通知"""
    short_term_stocks = strategies_data.get("short_term", [])
    long_term_stocks = strategies_data.get("long_term", [])
    weak_stocks = strategies_data.get("weak_stocks", [])
    
    if not short_term_stocks and not long_term_stocks and not weak_stocks:
        message = f"【{time_slot}分析報告】\n\n沒有符合條件的推薦股票和警示"
        subject = f"【{time_slot}分析報告】- 無推薦"
        send_unified_notification(message, subject)
        return
    
    # 生成通知消息
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
            
            # 現價和漲跌幅
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            message += f"💵 成交金額: {format_number(stock.get('trade_value', 0))}\n"
            
            # 技術指標
            technical_indicators = get_technical_indicators_text(analysis)
            if technical_indicators:
                message += f"📊 技術指標: {' | '.join(technical_indicators)}\n"
            
            # 法人買超資訊
            if 'foreign_net_buy' in analysis:
                foreign_net = analysis['foreign_net_buy']
                if abs(foreign_net) > 1000:
                    if foreign_net > 0:
                        message += f"🏦 外資買超: {format_institutional_flow(foreign_net)}\n"
                    else:
                        message += f"🏦 外資賣超: {format_institutional_flow(abs(foreign_net))}\n"
            
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
        message += "今日無短線推薦股票\n\n"
    
    # 長線推薦部分
    message += f"【💎 長線潛力股】\n\n"
    if long_term_stocks:
        for i, stock in enumerate(long_term_stocks, 1):
            message += f"💎 {i}. {stock['code']} {stock['name']}\n"
            
            # 現價和漲跌幅
            current_price = stock.get('current_price', 0)
            analysis = stock.get('analysis', {})
            change_percent = analysis.get('change_percent', 0)
            
            message += f"💰 現價: {current_price} 元 {format_price_change(change_percent)}\n"
            
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
                    message += f"🏦 外資買超: {format_institutional_flow(foreign_net)}\n"
            
            message += f"📋 投資亮點: {stock['reason']}\n"
            
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
    message += f"📧 本報告透過EMAIL + LINE + 文件備份三重保障確保送達\n"
    message += f"🔥 短線推薦：重視技術指標轉強、成交量放大\n"
    message += f"💎 長線推薦：重視殖利率、EPS成長、法人動向\n"
    message += f"⚠️ 本報告僅供參考，不構成投資建議\n"
    message += f"⚠️ 股市有風險，投資需謹慎\n\n"
    message += f"祝您投資順利！💰"
    
    # 生成HTML版本
    html_body = generate_unified_html_report(strategies_data, time_slot, today)
    
    # 發送統一通知（EMAIL + LINE + 文件備份）
    subject = f"【{display_name}】📊 統一版股票分析 - {today}"
    send_unified_notification(
        message=message, 
        subject=subject, 
        html_body=html_body,
        recommendations_data=strategies_data,
        time_slot=time_slot
    )

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
    message = f"🔔 統一版股票通知系統心跳檢測\n\n"
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
    
    # 文件備份狀態
    file_status = STATUS['file']
    if file_status['last_success']:
        try:
            last_time = datetime.fromisoformat(file_status['last_success'])
            hours_ago = (now - last_time).total_seconds() / 3600
            time_str = f"{hours_ago:.1f} 小時前" if hours_ago >= 1 else f"{int((now - last_time).total_seconds() / 60)} 分鐘前"
        except:
            time_str = "時間解析錯誤"
    else:
        time_str = "從未使用"
    
    emoji = "✅" if file_status['available'] else "❌"
    message += f"  {emoji} 文件備份: 上次使用 {time_str}, 失敗次數 {file_status['failure_count']}\n"
    
    # 未送達統計
    message += f"\n📈 統計資訊:\n"
    message += f"  • 未送達通知數: {STATUS['undelivered_count']}\n"
    
    # 系統運行狀態
    all_good = (email_status['failure_count'] < 5 and 
                line_status['failure_count'] < 5 and 
                file_status['failure_count'] < 5)
    message += f"  • 系統運行正常: {'是' if all_good else '否'}\n\n"
    
    message += f"🚀 統一版系統功能:\n"
    message += f"  • ✅ EMAIL通知 - 詳細HTML格式報告\n"
    message += f"  • 📱 LINE推播 - 結構化Flex訊息\n"
    message += f"  • 💾 文件備份 - 確保通知不遺失\n"
    message += f"  • 🔧 技術指標標籤完整顯示修復\n"
    message += f"  • 💎 長線基本面文字清晰度優化\n"
    message += f"  • 📊 三重通知保障機制\n\n"
    
    message += f"💡 如果您收到此訊息，表示統一版通知系統運作正常！"
    
    # 發送心跳通知
    success = send_unified_notification(message, "🔔 統一版系統心跳檢測")
    
    # 更新心跳時間
    if success:
        STATUS['last_heartbeat'] = now.isoformat()
    
    return success

def is_notification_available():
    """檢查通知系統是否可用"""
    return (EMAIL_CONFIG['enabled'] and STATUS['email']['available']) or \
           STATUS['line']['available'] or \
           (FILE_BACKUP['enabled'] and STATUS['file']['available'])

def init():
    """初始化統一版通知系統"""
    log_event("初始化統一版股票通知系統（EMAIL + LINE + 文件備份）")
    
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
    
    # 初始化LINE通知器
    global line_notifier
    line_notifier = LineNotifier()
    if line_notifier.enabled:
        log_event("✅ LINE推播配置檢查通過")
    else:
        log_event("⚠️ LINE推播配置不完整或未啟用", 'warning')
    
    # 檢查文件備份
    if FILE_BACKUP['enabled']:
        try:
            os.makedirs(FILE_BACKUP['directory'], exist_ok=True)
            log_event(f"✅ 文件備份目錄準備完成: {FILE_BACKUP['directory']}")
        except Exception as e:
            log_event(f"文件備份目錄創建失敗: {e}", 'error')
            STATUS['file']['available'] = False
    
    # 統計可用渠道
    available_channels = []
    if STATUS['email']['available']:
        available_channels.append("EMAIL")
    if STATUS['line']['available']:
        available_channels.append("LINE")
    if STATUS['file']['available']:
        available_channels.append("文件備份")
    
    log_event(f"🎯 統一版通知系統初始化完成，可用渠道: {', '.join(available_channels) if available_channels else '無'}")
    
    if not available_channels:
        log_event("❌ 警告: 沒有可用的通知渠道！", 'error')
    else:
        log_event("📊 系統特色:")
        log_event("  ✅ 三重通知保障 - EMAIL + LINE + 文件備份")
        log_event("  🔧 技術指標標籤顯示修復")
        log_event("  💎 長線基本面文字清晰度優化")
        log_event("  📱 LINE結構化Flex訊息支援")

# 向下相容的函數別名
send_notification = send_unified_notification
send_combined_recommendations = send_unified_stock_recommendations

# 初始化LINE通知器（全域變數）
line_notifier = None

if __name__ == "__main__":
    # 初始化
    init()
    
    # 執行測試
    print("=" * 70)
    print("📊 統一版股票通知系統測試（EMAIL + LINE + 文件備份）")
    print("=" * 70)
    
    # 測試心跳
    print("💓 測試心跳通知...")
    if send_heartbeat():
        print("✅ 心跳通知發送成功")
    else:
        print("❌ 心跳通知發送失敗")
    
    print("\n📊 測試股票推薦通知...")
    
    # 創建豐富的測試數據
    test_data = {
        "short_term": [
            {
                "code": "2330",
                "name": "台積電",
                "current_price": 638.5,
                "reason": "技術面轉強，MACD金叉，RSI健康回升，外資買超支撐",
                "target_price": 670.0,
                "stop_loss": 620.0,
                "trade_value": 14730000000,
                "analysis": {
                    "change_percent": 2.35,
                    "rsi": 58.5,
                    "volume_ratio": 2.3,
                    "foreign_net_buy": 25000,
                    "technical_signals": {
                        "rsi_healthy": True,
                        "macd_bullish": True,
                        "macd_golden_cross": True,
                        "ma20_bullish": True,
                        "ma_golden_cross": True
                    }
                }
            },
            {
                "code": "2454",
                "name": "聯發科",
                "current_price": 825.0,
                "reason": "放量突破，RSI超賣回升，MACD轉強",
                "target_price": 880.0,
                "stop_loss": 800.0,
                "trade_value": 8950000000,
                "analysis": {
                    "change_percent": 4.12,
                    "rsi": 45.2,
                    "volume_ratio": 3.1,
                    "foreign_net_buy": 15000,
                    "technical_signals": {
                        "rsi_healthy": True,
                        "macd_bullish": True,
                        "ma20_bullish": True
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
                "reason": "穩定殖利率6.2%，連續配息18年，ROE良好13.8%，外資持續買超",
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
                    "foreign_net_buy": 16000,
                    "trust_net_buy": 3000,
                    "total_institutional": 20000,
                    "consecutive_buy_days": 4
                }
            }
        ],
        "weak_stocks": [
            {
                "code": "1234",
                "name": "測試弱股",
                "current_price": 25.8,
                "alert_reason": "技術面走弱，跌破重要支撐，成交量萎縮",
                "trade_value": 150000000,
                "analysis": {
                    "change_percent": -5.2
                }
            }
        ]
    }
    
    # 發送測試通知
    send_unified_stock_recommendations(test_data, "統一版系統測試")
    
    print("\n✅ 統一版通知系統測試完成！")
    print("\n📋 請檢查以下通知渠道:")
    print("📧 EMAIL:")
    print("  ✅ 是否收到詳細的HTML格式股票分析報告")
    print("  🔧 短線推薦技術指標標籤是否完整顯示")
    print("  💎 長線推薦基本面資訊是否清晰易讀")
    print("  🎨 HTML排版是否美觀")
    print("📱 LINE:")
    print("  ✅ 是否收到結構化的Flex訊息")
    print("  📊 股票資訊顯示是否清楚")
    print("  🏷️ 基本面標籤是否正確顯示")
    print("💾 文件備份:")
    print(f"  ✅ 檢查 {FILE_BACKUP['directory']} 目錄")
    print("  📄 確認通知內容是否完整保存")
    
    print("\n🎯 統一版系統特色:")
    print("1. 📊 三重通知保障 - EMAIL + LINE + 文件備份")
    print("2. 🔧 技術指標標籤顯示修復")
    print("3. 💎 長線基本面文字清晰度優化")
    print("4. 📱 LINE結構化Flex訊息支援")
    print("5. 🌐 美觀的HTML格式郵件")
    print("6. 💾 可靠的文件備份機制")
    
    print("\n💡 配置提醒:")
    print("請確保已設置以下環境變數:")
    print("📧 EMAIL配置:")
    print("  - EMAIL_SENDER")
    print("  - EMAIL_PASSWORD") 
    print("  - EMAIL_RECEIVER")
    print("📱 LINE配置:")
    print("  - LINE_ENABLED=True")
    print("  - LINE_CHANNEL_ACCESS_TOKEN")
    print("  - LINE_USER_ID 或 LINE_GROUP_ID")
