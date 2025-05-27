"""
enhanced_config.py - 台股分析機器人的優化配置檔案
包含多種市場環境與行業分析配置
更新：早盤延後到9:30、啟用LINE推播、週末總結改到週六12:00
"""
import os
import sys
from dotenv import load_dotenv

# 首先嘗試從.env文件加載環境變量（若存在）
# 但如果變量已經在系統環境中存在，則優先使用系統環境中的變量（如GitHub Secrets）
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"已從 {dotenv_path} 加載環境變量配置")
else:
    print("未找到.env文件，將使用系統環境變量")

# 日誌和緩存目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 確保必要的目錄存在
for directory in [LOG_DIR, CACHE_DIR, DATA_DIR]:
    os.makedirs(directory, exist_ok=True)

# 通知配置
EMAIL_CONFIG = {
    'enabled': True,
    'sender': os.getenv('EMAIL_SENDER'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'receiver': os.getenv('EMAIL_RECEIVER'),
    'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
    'use_tls': os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
}

# LINE通知配置
LINE_CONFIG = {
    'enabled': os.getenv('LINE_ENABLED', 'True').lower() in ('true', '1', 't'),  # 默認啟用
    'channel_access_token': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
    'user_id': os.getenv('LINE_USER_ID'),
    'group_id': os.getenv('LINE_GROUP_ID'),  # 支援群組推播
    'api_url': 'https://api.line.me/v2/bot/message/push'
}

# 通知渠道配置（啟用LINE）
NOTIFICATION_CHANNELS = {
    'email': {
        'priority': 1,  # 優先級，數字越小優先級越高
        'enabled': True,
        'config': EMAIL_CONFIG
    },
    'line': {
        'priority': 2,  # LINE為第二優先級
        'enabled': LINE_CONFIG['enabled'],
        'config': LINE_CONFIG
    },
    'telegram': {
        'priority': 3,
        'enabled': os.getenv('TELEGRAM_ENABLED', 'False').lower() in ('true', '1', 't'),
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'chat_id': os.getenv('TELEGRAM_CHAT_ID')
    }
}

# 檔案通知備份設置
FILE_BACKUP = {
    'enabled': True,
    'directory': os.path.join(LOG_DIR, 'notifications')
}

# 通知重試策略
RETRY_CONFIG = {
    'max_attempts': 3,
    'base_delay': 2.0,
    'backoff_factor': 1.5,
    'max_delay': 60,
}

# 市場環境配置
MARKET_ENVIRONMENTS = {
    'bullish': {  # 牛市配置
        'weight_configs': {
            'short_term': {  # 短線分析權重
                'technical': 0.8,     # 技術面權重
                'fundamental': 0.1,   # 基本面權重
                'quantitative': 0.1,  # 量化指標權重
            },
            'long_term': {   # 長線分析權重
                'technical': 0.4,     # 技術面權重
                'fundamental': 0.5,   # 基本面權重
                'quantitative': 0.1,  # 量化指標權重
            }
        },
        'recommendation_limits': {  # 不同時段推薦的股票數量
            'morning_scan': {      # 9:30（延後）
                'long_term': 2,
                'short_term': 4,   # 牛市加大短線推薦數量
                'weak_stocks': 1   # 減少弱勢股數量
            },
            'afternoon_scan': {    # 15:00
                'long_term': 3,
                'short_term': 4,
                'weak_stocks': 0
            }
        }
    },
    'bearish': {  # 熊市配置
        'weight_configs': {
            'short_term': {
                'technical': 0.5,
                'fundamental': 0.3,
                'quantitative': 0.2,
            },
            'long_term': {
                'technical': 0.2,
                'fundamental': 0.7,
                'quantitative': 0.1,
            }
        },
        'recommendation_limits': {  # 不同時段推薦的股票數量
            'morning_scan': {      # 9:30（延後）
                'long_term': 3,    # 熊市增加長線推薦
                'short_term': 2,   # 減少短線推薦
                'weak_stocks': 3   # 增加弱勢股警示
            },
            'afternoon_scan': {    # 15:00
                'long_term': 4,
                'short_term': 2,
                'weak_stocks': 3
            }
        }
    }
}

# 行業特定配置
INDUSTRY_CONFIGS = {
    'electronics': {  # 電子業
        'price_change_threshold': 5.0,    # 更高的價格變動閾值
        'volume_change_threshold': 150.0, # 更高的成交量變動閾值
        'scan_limits': {                 # 掃描數量調整
            'morning_scan': 150,         # 增加電子股掃描數量
            'afternoon_scan': 500
        }
    },
    'finance': {  # 金融業
        'price_change_threshold': 2.0,   # 較低的價格變動閾值
        'volume_change_threshold': 80.0, # 較低的成交量變動閾值
        'scan_limits': {                 # 掃描數量調整
            'morning_scan': 50,          # 減少金融股掃描數量
            'afternoon_scan': 100
        }
    },
    'traditional': {  # 傳統產業
        'price_change_threshold': 3.0,
        'volume_change_threshold': 100.0,
        'scan_limits': {
            'morning_scan': 80,
            'afternoon_scan': 120
        }
    }
}

# 特殊時段配置（例如除權息期間，財報季）
SEASONAL_CONFIGS = {
    'earnings_season': {  # 財報季
        'scan_limits': {
            'morning_scan': 150,    # 增加掃描數量
            'afternoon_scan': 500
        },
        'weight_configs': {
            'short_term': {
                'technical': 0.5,   # 減少技術面權重
                'fundamental': 0.4, # 提高基本面權重
                'quantitative': 0.1
            }
        }
    },
    'dividend_season': {  # 除權息期間
        'scan_limits': {
            'morning_scan': 150,
            'mid_morning_scan': 200
        },
        'recommendation_limits': {
            'morning_scan': {
                'long_term': 5,     # 增加長線推薦數量
                'short_term': 3,
                'weak_stocks': 2
            }
        }
    }
}

# 股票分析配置
STOCK_ANALYSIS = {
    'data_source': os.getenv('STOCK_DATA_SOURCE', 'twse'),  # 台灣證券交易所
    'api_key': os.getenv('STOCK_API_KEY', ''),
    'max_stocks_per_category': 5,  # 每類最多推薦數量
    'price_change_threshold': 3.0,  # 價格變動閾值(百分比)
    'volume_change_threshold': 100.0,  # 成交量變動閾值(百分比)
    'short_term_days': 5,  # 短線考慮天數
    'long_term_days': 30,  # 長線考慮天數
    'scan_limits': {  # 不同時段掃描的股票數量
        'morning_scan': 200,       # 9:30掃描股票數量（延後後可增加數量）
        'mid_morning_scan': 150,   # 10:30掃描股票數量
        'mid_day_scan': 150,       # 12:30掃描股票數量
        'afternoon_scan': 450,     # 15:00掃描股票數量
    },
    'recommendation_limits': {  # 不同時段推薦的股票數量
        'morning_scan': {           # 9:30（延後後使用當日數據）
            'long_term': 3,         # 增加長線推薦（當日數據品質更好）
            'short_term': 3,
            'weak_stocks': 2
        },
        'mid_morning_scan': {       # 10:30
            'long_term': 3,
            'short_term': 2,
            'weak_stocks': 0
        },
        'mid_day_scan': {           # 12:30
            'long_term': 3,
            'short_term': 2,
            'weak_stocks': 0
        },
        'afternoon_scan': {         # 15:00
            'long_term': 3,
            'short_term': 3,
            'weak_stocks': 0
        }
    },
    # 增加的多維度分析權重配置
    'weight_configs': {
        'short_term': {
            'technical': 0.7,     # 技術面權重
            'fundamental': 0.1,   # 基本面權重
            'quantitative': 0.2,  # 量化指標權重
        },
        'long_term': {
            'technical': 0.3,     # 技術面權重
            'fundamental': 0.5,   # 基本面權重
            'quantitative': 0.2,  # 量化指標權重
        }
    },
    # 增加超級股名單 - 這些股票會被優先分析
    'priority_stocks': [
        '2330',  # 台積電
        '2317',  # 鴻海
        '2454',  # 聯發科
        '2412',  # 中華電
        '2308',  # 台達電
    ],
    # 增加黑名單 - 這些股票會被排除在分析之外
    'blacklist_stocks': [
        # 例如，可以放入暫停交易或特殊處理的股票
    ],
    # 增加使用白話文的設定
    'use_white_text': True,
}

# 股市交易時間
MARKET_HOURS = {
    'morning_start': '09:00',
    'morning_end': '13:30',
    'pre_market_hour': '08:30',
    'post_market_hour': '14:30',
    'lunch_break_start': '12:00',
    'lunch_break_end': '13:00',
}

# 分析與通知時間（更新排程）
NOTIFICATION_SCHEDULE = {
    'morning_scan': '09:30',       # 早盤掃描（延後到9:30）
    'mid_morning_scan': '10:30',   # 盤中掃描
    'mid_day_scan': '12:30',       # 午間掃描
    'afternoon_scan': '15:00',     # 盤後掃描
    'weekly_summary': '12:00',     # 週末總結改到週六中午12:00
    'heartbeat': '08:30',          # 心跳檢測
}

# 日誌配置
LOG_CONFIG = {
    'filename': os.path.join(LOG_DIR, 'stock_bot.log'),
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
}

# 檢查必要的配置是否存在
def validate_config():
    """驗證配置是否完整，返回缺失配置的列表"""
    missing = []
    
    # 檢查郵件配置
    if EMAIL_CONFIG['enabled']:
        for key in ['sender', 'password', 'receiver']:
            if not EMAIL_CONFIG[key]:
                missing.append(f'EMAIL_{key.upper()}')
    
    # 檢查LINE配置
    if LINE_CONFIG['enabled']:
        if not LINE_CONFIG['channel_access_token']:
            missing.append('LINE_CHANNEL_ACCESS_TOKEN')
        if not LINE_CONFIG['user_id'] and not LINE_CONFIG['group_id']:
            missing.append('LINE_USER_ID or LINE_GROUP_ID')
    
    return missing

# 獲取當前市場環境的配置
def get_current_market_environment():
    """
    根據環境變量或預設值獲取當前市場環境配置
    
    返回: 
    - 市場環境配置字典
    """
    # 從環境變量獲取市場環境，默認為中性
    market_env = os.getenv('MARKET_ENVIRONMENT', 'neutral')
    
    # 如果指定的環境存在於配置中，返回對應配置
    if market_env in MARKET_ENVIRONMENTS:
        return MARKET_ENVIRONMENTS[market_env]
    
    # 否則返回默認配置
    return {
        'weight_configs': STOCK_ANALYSIS['weight_configs'],
        'recommendation_limits': STOCK_ANALYSIS['recommendation_limits']
    }

# 獲取行業特定配置
def get_industry_config(industry_code):
    """
    獲取特定行業的配置
    
    參數:
    - industry_code: 行業代碼
    
    返回:
    - 行業特定配置
    """
    # 建立行業代碼與配置類型的映射
    industry_mapping = {
        'technology': 'electronics',  # 技術業映射到電子業
        'semiconductor': 'electronics',  # 半導體業映射到電子業
        'hardware': 'electronics',  # 硬體業映射到電子業
        'bank': 'finance',  # 銀行業映射到金融業
        'insurance': 'finance',  # 保險業映射到金融業
        'manufacturing': 'traditional',  # 製造業映射到傳統產業
        'retail': 'traditional',  # 零售業映射到傳統產業
    }
    
    # 將行業代碼轉換為配置類型
    config_type = industry_mapping.get(industry_code, 'traditional')
    
    # 返回對應的行業配置，如果不存在則返回默認配置
    return INDUSTRY_CONFIGS.get(config_type, {})

# 獲取當前季節特定配置
def get_seasonal_config():
    """
    獲取當前季節的特定配置
    
    返回:
    - 季節特定配置
    """
    # 從環境變量獲取當前季節，默認為普通季節
    current_season = os.getenv('CURRENT_SEASON', 'normal')
    
    # 如果指定的季節存在於配置中，返回對應配置
    if current_season in SEASONAL_CONFIGS:
        return SEASONAL_CONFIGS[current_season]
    
    # 否則返回空配置
    return {}

# 如果此文件被直接執行，則驗證並顯示配置
if __name__ == '__main__':
    missing_config = validate_config()
    if missing_config:
        print(f"警告: 缺少以下配置項: {', '.join(missing_config)}")
        print("請在.env文件中設置這些變量")
    else:
        print("配置驗證通過!")
        
    # 顯示當前配置
    print("\n當前配置:")
    print(f"日誌目錄: {LOG_DIR}")
    print(f"緩存目錄: {CACHE_DIR}")
    print(f"數據目錄: {DATA_DIR}")
    print(f"郵件通知: {'啟用' if EMAIL_CONFIG['enabled'] else '停用'}")
    print(f"LINE通知: {'啟用' if LINE_CONFIG['enabled'] else '停用'}")
    print(f"文件備份: {'啟用' if FILE_BACKUP['enabled'] else '停用'}")
    
    # 顯示更新的排程時間
    print(f"\n更新的排程時間:")
    print(f"早盤掃描: {NOTIFICATION_SCHEDULE['morning_scan']} (使用當日數據)")
    print(f"盤中掃描: {NOTIFICATION_SCHEDULE['mid_morning_scan']}")
    print(f"午間掃描: {NOTIFICATION_SCHEDULE['mid_day_scan']}")
    print(f"盤後掃描: {NOTIFICATION_SCHEDULE['afternoon_scan']}")
    print(f"週末總結: 週六 {NOTIFICATION_SCHEDULE['weekly_summary']}")
    
    # 顯示當前市場環境
    market_env = os.getenv('MARKET_ENVIRONMENT', 'neutral')
    print(f"\n當前市場環境: {market_env}")
    if market_env in MARKET_ENVIRONMENTS:
        print(f"正在使用 {market_env} 市場環境的特定配置")
