"""
line_notifier.py - LINE推播通知模組
實現LINE Bot API推播股票分析結果
"""
import os
import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 設置日誌
logger = logging.getLogger(__name__)

class LineNotifier:
    """LINE推播通知器"""
    
    def __init__(self):
        """初始化LINE通知器"""
        self.channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        self.user_id = os.getenv('LINE_USER_ID')
        self.group_id = os.getenv('LINE_GROUP_ID')
        self.api_url = 'https://api.line.me/v2/bot/message/push'
        
        # 驗證配置
        self.enabled = self._validate_config()
        
    def _validate_config(self) -> bool:
        """驗證LINE配置是否完整"""
        if not self.channel_access_token:
            logger.warning("LINE_CHANNEL_ACCESS_TOKEN 未設置")
            return False
        
        if not self.user_id and not self.group_id:
            logger.warning("LINE_USER_ID 或 LINE_GROUP_ID 至少要設置一個")
            return False
        
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """獲取API請求標頭"""
        return {
            'Authorization': f'Bearer {self.channel_access_token}',
            'Content-Type': 'application/json'
        }
    
    def _send_message(self, to: str, message: Dict[str, Any]) -> bool:
        """
        發送訊息到LINE
        
        參數:
        - to: 接收者ID（用戶ID或群組ID）
        - message: 訊息內容
        
        返回:
        - 是否發送成功
        """
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
                logger.info(f"LINE訊息發送成功到 {to}")
                return True
            else:
                logger.error(f"LINE訊息發送失敗: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"LINE訊息發送異常: {e}")
            return False
    
    def send_text_message(self, text: str, target_type: str = 'user') -> bool:
        """
        發送純文字訊息
        
        參數:
        - text: 訊息文字
        - target_type: 目標類型 ('user' 或 'group')
        
        返回:
        - 是否發送成功
        """
        # 選擇發送目標
        if target_type == 'group' and self.group_id:
            to = self.group_id
        elif target_type == 'user' and self.user_id:
            to = self.user_id
        else:
            # 默認優先發送給個人
            to = self.user_id or self.group_id
        
        if not to:
            logger.error("沒有有效的LINE發送目標")
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
        """
        發送Flex訊息（結構化訊息）
        
        參數:
        - alt_text: 替代文字
        - flex_content: Flex訊息內容
        - target_type: 目標類型 ('user' 或 'group')
        
        返回:
        - 是否發送成功
        """
        # 選擇發送目標
        if target_type == 'group' and self.group_id:
            to = self.group_id
        elif target_type == 'user' and self.user_id:
            to = self.user_id
        else:
            to = self.user_id or self.group_id
        
        if not to:
            logger.error("沒有有效的LINE發送目標")
            return False
        
        message = {
            'type': 'flex',
            'altText': alt_text,
            'contents': flex_content
        }
        
        return self._send_message(to, message)
    
    def generate_stock_flex_message(self, recommendations: Dict[str, List[Dict]], time_slot: str) -> Dict[str, Any]:
        """
        生成股票推薦的Flex訊息格式
        
        參數:
        - recommendations: 推薦數據
        - time_slot: 時段名稱
        
        返回:
        - Flex訊息內容
        """
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
        """
        發送股票推薦通知
        
        參數:
        - recommendations: 推薦數據
        - time_slot: 時段名稱
        
        返回:
        - 是否發送成功
        """
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
                logger.info(f"LINE股票推薦通知發送成功: {time_slot}")
            else:
                logger.error(f"LINE股票推薦通知發送失敗: {time_slot}")
            
            return success
            
        except Exception as e:
            logger.error(f"生成LINE股票推薦訊息失敗: {e}")
            return False
    
    def send_heartbeat(self) -> bool:
        """
        發送心跳檢測訊息
        
        返回:
        - 是否發送成功
        """
        current_time = datetime.now().strftime('%H:%M:%S')
        message = f"💓 股票分析系統心跳檢測\n⏰ 檢測時間: {current_time}\n✅ 系統運行正常"
        
        return self.send_text_message(message)

def test_line_notification():
    """測試LINE通知功能"""
    print("🧪 測試LINE通知功能...")
    
    # 創建LINE通知器
    line_notifier = LineNotifier()
    
    if not line_notifier.enabled:
        print("❌ LINE通知未啟用或配置不完整")
        print("請檢查以下環境變數:")
        print("- LINE_CHANNEL_ACCESS_TOKEN")
        print("- LINE_USER_ID 或 LINE_GROUP_ID")
        return False
    
    # 測試心跳通知
    print("📧 發送心跳測試...")
    heartbeat_success = line_notifier.send_heartbeat()
    
    if heartbeat_success:
        print("✅ 心跳通知發送成功")
    else:
        print("❌ 心跳通知發送失敗")
        return False
    
    # 測試股票推薦通知
    print("📊 發送股票推薦測試...")
    
    test_recommendations = {
        "short_term": [
            {
                "code": "2330",
                "name": "台積電",
                "current_price": 638.5,
                "analysis": {"change_percent": 2.35}
            }
        ],
        "long_term": [
            {
                "code": "2609",
                "name": "陽明",
                "current_price": 91.2,
                "analysis": {
                    "change_percent": 1.8,
                    "dividend_yield": 7.2,
                    "eps_growth": 35.6
                }
            }
        ],
        "weak_stocks": [
            {
                "code": "1234",
                "name": "測試股",
                "current_price": 25.8
            }
        ]
    }
    
    stock_success = line_notifier.send_stock_recommendations(test_recommendations, "測試分析")
    
    if stock_success:
        print("✅ 股票推薦通知發送成功")
        print("📱 請檢查您的LINE是否收到測試訊息")
        return True
    else:
        print("❌ 股票推薦通知發送失敗")
        return False

if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 執行測試
    test_line_notification()
