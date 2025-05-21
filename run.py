"""
run.py - 股市機器人啟動腳本
提供命令行界面，便於啟動、測試和配置股市機器人
"""
import os
import sys
import time
import argparse
import logging
import importlib
from datetime import datetime

def setup_logging():
    """設置日誌"""
    from config import LOG_DIR, LOG_CONFIG
    
    # 確保日誌目錄存在
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 配置日誌
    logging.basicConfig(
        filename=LOG_CONFIG['filename'],
        level=getattr(logging, LOG_CONFIG['level']),
        format=LOG_CONFIG['format']
    )
    
    # 同時輸出到控制台
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, LOG_CONFIG['level']))
    console.setFormatter(logging.Formatter(LOG_CONFIG['format']))
    logging.getLogger().addHandler(console)

def check_environment():
    """檢查環境是否配置正確"""
    try:
        # 嘗試導入必要的模塊
        import requests
        import pandas
        import schedule
        import numpy
        from dotenv import load_dotenv
        
        # 檢查配置文件
        from config import EMAIL_CONFIG
        if EMAIL_CONFIG['enabled']:
            if not all([EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'], EMAIL_CONFIG['receiver']]):
                # 檢查是否在GitHub Actions或CI環境中運行
                if 'GITHUB_ACTIONS' in os.environ or 'CI' in os.environ:
                    print("⚠️ 警告: 在CI環境中檢測到電子郵件設定不完整，請檢查GitHub Secrets是否正確配置")
                    print(f"目前環境變數: EMAIL_SENDER={'已設置' if os.getenv('EMAIL_SENDER') else '未設置'}")
                    print(f"             EMAIL_RECEIVER={'已設置' if os.getenv('EMAIL_RECEIVER') else '未設置'}")
                    print(f"             EMAIL_PASSWORD={'已設置' if os.getenv('EMAIL_PASSWORD') else '未設置'}")
                else:
                    print("⚠️ 警告: 電子郵件設定不完整，請檢查.env文件")
                return False
        
        # 檢查目錄結構
        from config import LOG_DIR, CACHE_DIR, DATA_DIR
        for directory in [LOG_DIR, CACHE_DIR, DATA_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"已創建目錄: {directory}")
        
        # 檢查是否在CI環境中運行
        if 'GITHUB_ACTIONS' in os.environ or 'CI' in os.environ:
            print("檢測到CI環境，正在使用GitHub Secrets作為配置來源")
        
        return True
        
    except ImportError as e:
        print(f"❌ 錯誤: 缺少必要的套件: {e}")
        print("請執行 pip install -r requirements.txt 安裝必要的套件")
        return False
    
    except Exception as e:
        print(f"❌ 錯誤: 環境檢查失敗: {e}")
        return False

def run_analysis(time_slot):
    """執行特定時段的分析"""
    print(f"執行 {time_slot} 分析...")
    import stock_bot
    stock_bot.run_analysis(time_slot)
    print(f"{time_slot} 分析完成")

def run_bot(daemon=False):
    """運行股市機器人"""
    import stock_bot
    
    if daemon:
        # 後台運行
        print("股市機器人已在後台啟動")
        print(f"日誌將寫入到 {stock_bot.LOG_CONFIG['filename']}")
        stock_bot.main()
    else:
        # 前台運行
        print("股市機器人已啟動 (按Ctrl+C退出)")
        try:
            stock_bot.main()
        except KeyboardInterrupt:
            print("\n使用者中斷，股市機器人已停止")

def test_notification(test_type='all'):
    """測試通知系統"""
    print(f"執行通知系統測試: {test_type}")
    
    # 直接調用測試腳本
    sys.argv = ['test_notification.py', '--test', test_type]
    import test_notification
    importlib.reload(test_notification)  # 確保重新加載
    test_notification.main()

def check_status():
    """檢查系統狀態"""
    import stock_bot
    import notifier
    from config import EMAIL_CONFIG, FILE_BACKUP, NOTIFICATION_SCHEDULE
    
    print("=" * 50)
    print("股市機器人狀態報告")
    print("=" * 50)
    print(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # 檢查配置
    print("配置狀態:")
    print(f"電子郵件通知: {'啟用' if EMAIL_CONFIG['enabled'] else '停用'}")
    if EMAIL_CONFIG['enabled']:
        print(f"  寄件者: {EMAIL_CONFIG['sender']}")
        print(f"  收件者: {EMAIL_CONFIG['receiver']}")
        print(f"  SMTP伺服器: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
    
    print(f"文件備份: {'啟用' if FILE_BACKUP['enabled'] else '停用'}")
    if FILE_BACKUP['enabled']:
        print(f"  備份目錄: {FILE_BACKUP['directory']}")
    
    # 排程狀態
    print("\n排程狀態:")
    print(f"盤前分析: 每個工作日 {NOTIFICATION_SCHEDULE['pre_market']}")
    print(f"午間分析: 每個工作日 {NOTIFICATION_SCHEDULE['mid_day']}")
    print(f"盤後分析: 每個工作日 {NOTIFICATION_SCHEDULE['post_market']}")
    print(f"週末總結: 每週五 {NOTIFICATION_SCHEDULE['weekly_summary']}")
    
    # 通知狀態
    print("\n通知系統狀態:")
    try:
        email_status = notifier.STATUS['email']
        last_success = "從未成功" if not email_status['last_success'] else \
            f"{(datetime.now() - datetime.fromisoformat(email_status['last_success'])).total_seconds() / 60:.1f}分鐘前"
        print(f"電子郵件: {'可用' if email_status['available'] else '不可用'}, 上次成功: {last_success}, 失敗次數: {email_status['failure_count']}")
        
        # 檢查未送達的通知
        print(f"未送達通知數: {notifier.STATUS['undelivered_count']}")
        
        # 檢查心跳
        if notifier.STATUS['last_heartbeat']:
            last_hb = datetime.fromisoformat(notifier.STATUS['last_heartbeat'])
            hours_ago = (datetime.now() - last_hb).total_seconds() / 3600
            print(f"上次心跳: {hours_ago:.1f}小時前 ({last_hb.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("上次心跳: 從未發送")
    except Exception as e:
        print(f"獲取通知狀態失敗: {e}")
    
    print("\n系統檢查完成")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='台股分析機器人')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 啟動命令
    start_parser = subparsers.add_parser('start', help='啟動股市機器人')
    start_parser.add_argument('--daemon', '-d', action='store_true', help='後台運行')
    
    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='執行特定時段的分析')
    analyze_parser.add_argument('time_slot', choices=['pre_market', 'mid_day', 'post_market', 'weekly_summary'], 
                              help='分析時段')
    
    # 測試命令
    test_parser = subparsers.add_parser('test', help='測試通知系統')
    test_parser.add_argument('--type', '-t', choices=['all', 'simple', 'html', 'urgent', 'stock', 'combined', 'heartbeat'], 
                           default='all', help='測試類型')
    
    # 狀態命令
    subparsers.add_parser('status', help='檢查系統狀態')
    
    # 解析命令行參數
    args = parser.parse_args()
    
    # 檢查環境
    if not check_environment():
        print("環境檢查失敗，請修復上述問題再嘗試")
        return
    
    # 設置日誌
    setup_logging()
    
    # 執行相應的命令
    if args.command == 'start':
        run_bot(args.daemon)
    elif args.command == 'analyze':
        run_analysis(args.time_slot)
    elif args.command == 'test':
        test_notification(args.type)
    elif args.command == 'status':
        check_status()
    else:
        # 如果沒有提供命令，顯示幫助
        parser.print_help()

if __name__ == "__main__":
    main()
