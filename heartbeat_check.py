#!/usr/bin/env python3
"""
heartbeat_check.py - 心跳檢測腳本
用於 GitHub Actions 中的心跳檢測，避免 YAML 中嵌入複雜 Python 代碼
"""
import sys
import os

def main():
    """執行心跳檢測"""
    print("🔔 開始心跳檢測...")
    
    # 優先嘗試優化版通知系統
    try:
        import optimized_notifier as notifier
        print("✅ 使用優化版通知系統")
        notifier.init()
        result = notifier.send_heartbeat()
        
        if result:
            print("💓 優化版心跳檢測成功")
            return True
        else:
            print("⚠️ 優化版心跳檢測失敗，嘗試標準版")
    except ImportError:
        print("⚠️ 優化版通知系統不可用，使用標準版")
    except Exception as e:
        print(f"⚠️ 優化版心跳檢測異常: {e}")
    
    # 回退到標準版通知系統
    try:
        import notifier
        print("✅ 使用標準版通知系統")
        notifier.init()
        result = notifier.send_heartbeat()
        
        if result:
            print("💓 標準版心跳檢測成功")
            return True
        else:
            print("❌ 標準版心跳檢測失敗")
            return False
    except ImportError:
        print("❌ 標準版通知系統也不可用")
        return False
    except Exception as e:
        print(f"❌ 標準版心跳檢測異常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("❌ 心跳檢測失敗")
        sys.exit(1)
    else:
        print("✅ 心跳檢測完成")
        sys.exit(0)
