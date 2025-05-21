"""
config.py - 股市機器人的配置文件
包含所有應用程序的設置和參數
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
        'morning_scan': 100,       # 9:00掃描股票數量
        'mid_morning_scan': 150,   # 10:30掃描股票數量
        'mid_day_scan': 150,       # 12:30掃描股票數量
        'afternoon_scan': 450,     # 15:00掃描股票數量
    },
    'recommendation_limits': {  # 不同時段推薦的股票數量
        'morning_scan': {           # 9:00
            'long_term': 2,
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
    }
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

# 分析與通知時間
NOTIFICATION_SCHEDULE = {
    'morning_scan': '09:00',       # 早盤掃描
    'mid_morning_scan': '10:30',   # 盤中掃描
    'mid_day_scan': '12:30',       # 午間掃描
    'afternoon_scan': '15:00',     # 盤後掃描
    'weekly_summary': 'Friday 17:00',  # 週末總結
    'heartbeat': '08:30',   # 心跳檢測
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
    
    return missing

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
    print(f"文件備份: {'啟用' if FILE_BACKUP['enabled'] else '停用'}")
