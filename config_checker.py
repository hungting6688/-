#!/usr/bin/env python3
"""
config_checker.py - 配置檢查工具
檢查GitHub Actions和本地環境配置是否正確

使用方法:
python config_checker.py --check-all
python config_checker.py --check-env
python config_checker.py --check-files
python config_checker.py --test-notification
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Tuple

def check_color_print(message: str, status: str = "info"):
    """帶顏色的打印"""
    colors = {
        "success": "\033[92m✅",
        "warning": "\033[93m⚠️",
        "error": "\033[91m❌",
        "info": "\033[94mℹ️",
        "reset": "\033[0m"
    }
    
    color = colors.get(status, colors["info"])
    reset = colors["reset"]
    print(f"{color} {message}{reset}")

class ConfigChecker:
    """配置檢查器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_items = []
    
    def check_python_environment(self) -> bool:
        """檢查Python環境"""
        check_color_print("=== Python環境檢查 ===", "info")
        
        # 檢查Python版本
        python_version = sys.version_info
        if python_version >= (3, 8):
            check_color_print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}", "success")
            self.success_items.append("Python版本符合要求")
        else:
            check_color_print(f"Python版本過舊: {python_version.major}.{python_version.minor}.{python_version.micro} (需要 >= 3.8)", "error")
            self.errors.append("Python版本不符合要求")
            return False
        
        # 檢查必要套件
        required_packages = [
            'pandas', 'numpy', 'requests', 'schedule', 
            'python-dotenv', 'email-validator'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                check_color_print(f"套件 {package}: 已安裝", "success")
            except ImportError:
                check_color_print(f"套件 {package}: 未安裝", "error")
                missing_packages.append(package)
        
        if missing_packages:
            self.errors.append(f"缺少套件: {', '.join(missing_packages)}")
            check_color_print(f"安裝命令: pip install {' '.join(missing_packages)}", "info")
            return False
        
        self.success_items.append("所有必要套件已安裝")
        return True
    
    def check_environment_variables(self) -> bool:
        """檢查環境變數"""
        check_color_print("=== 環境變數檢查 ===", "info")
        
        # 檢查.env文件
        env_file_exists = os.path.exists('.env')
        if env_file_exists:
            check_color_print(".env文件: 存在", "success")
            self.success_items.append(".env文件存在")
            
            # 讀取.env文件內容
            try:
                from dotenv import load_dotenv
                load_dotenv()
                check_color_print(".env文件載入: 成功", "success")
            except Exception as e:
                check_color_print(f".env文件載入失敗: {e}", "error")
                self.errors.append(".env文件載入失敗")
        else:
            check_color_print(".env文件: 不存在，將使用系統環境變數", "warning")
            self.warnings.append(".env文件不存在")
        
        # 檢查必要的環境變數
        required_env_vars = {
            'EMAIL_SENDER': '發送郵件地址',
            'EMAIL_RECEIVER': '接收郵件地址', 
            'EMAIL_PASSWORD': '郵件應用程式密碼'
        }
        
        optional_env_vars = {
            'LINE_NOTIFY_TOKEN': 'LINE推播Token'
        }
        
        all_good = True
        
        for var, description in required_env_vars.items():
            value = os.getenv(var)
            if value:
                # 隱藏敏感資訊
                display_value = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '***'
                check_color_print(f"{var} ({description}): {display_value}", "success")
                self.success_items.append(f"{description}已設置")
            else:
                check_color_print(f"{var} ({description}): 未設置", "error")
                self.errors.append(f"{description}未設置")
                all_good = False
        
        for var, description in optional_env_vars.items():
            value = os.getenv(var)
            if value:
                display_value = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '***'
                check_color_print(f"{var} ({description}): {display_value}", "success")
                self.success_items.append(f"{description}已設置")
            else:
                check_color_print(f"{var} ({description}): 未設置 (可選)", "warning")
                self.warnings.append(f"{description}未設置")
        
        return all_good
    
    def check_file_structure(self) -> bool:
        """檢查文件結構"""
        check_color_print("=== 文件結構檢查 ===", "info")
        
        # 檢查主要程式文件
        main_files = [
            ('unified_stock_analyzer.py', '統一股票分析器'),
            ('enhanced_stock_bot.py', '增強版分析器'),
            ('integrated_stock_bot.py', '整合版分析器'),
            ('notifier.py', '通知系統'),
            ('config.py', '配置文件')
        ]
        
        has_analyzer = False
        for file_path, description in main_files:
            if os.path.exists(file_path):
                check_color_print(f"{file_path} ({description}): 存在", "success")
                if 'analyzer' in file_path or 'bot' in file_path:
                    has_analyzer = True
                self.success_items.append(f"{description}文件存在")
            else:
                if file_path == 'config.py':
                    check_color_print(f"{file_path} ({description}): 不存在 (可選)", "warning")
                    self.warnings.append(f"{description}不存在")
                else:
                    check_color_print(f"{file_path} ({description}): 不存在", "error")
                    self.errors.append(f"{description}不存在")
        
        if not has_analyzer:
            check_color_print("未找到任何分析器文件", "error")
            self.errors.append("缺少分析器文件")
            return False
        
        # 檢查必要目錄
        required_dirs = ['data', 'logs', '.github/workflows']
        for dir_path in required_dirs:
            if os.path.exists(dir_path):
                check_color_print(f"目錄 {dir_path}: 存在", "success")
                self.success_items.append(f"{dir_path}目錄存在")
            else:
                check_color_print(f"目錄 {dir_path}: 不存在，將自動創建", "warning")
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    check_color_print(f"目錄 {dir_path}: 創建成功", "success")
                    self.success_items.append(f"{dir_path}目錄已創建")
                except Exception as e:
                    check_color_print(f"創建目錄 {dir_path} 失敗: {e}", "error")
                    self.errors.append(f"無法創建{dir_path}目錄")
        
        # 檢查GitHub Actions工作流程
        workflow_file = '.github/workflows/stock_analysis.yml'
        if os.path.exists(workflow_file):
            check_color_print("GitHub Actions工作流程: 存在", "success")
            self.success_items.append("GitHub Actions工作流程已配置")
        else:
            check_color_print("GitHub Actions工作流程: 不存在", "warning")
            self.warnings.append("GitHub Actions工作流程未配置")
        
        return True
    
    def check_github_secrets(self) -> bool:
        """檢查GitHub Secrets配置指南"""
        check_color_print("=== GitHub Secrets配置檢查 ===", "info")
        
        secrets_info = {
            'EMAIL_SENDER': '發送郵件的Gmail地址',
            'EMAIL_RECEIVER': '接收通知的郵件地址', 
            'EMAIL_PASSWORD': 'Gmail應用程式密碼（非一般密碼）'
        }
        
        check_color_print("請確保在GitHub Repository Settings > Secrets and variables > Actions 中設置以下Secrets:", "info")
        
        for secret, description in secrets_info.items():
            check_color_print(f"  {secret}: {description}", "info")
        
        check_color_print("\n📧 Gmail應用程式密碼設置步驟:", "info")
        check_color_print("  1. 登入Gmail > 管理您的Google帳戶", "info")
        check_color_print("  2. 安全性 > 兩步驗驗證 (必須先啟用)", "info")
        check_color_print("  3. 應用程式密碼 > 選擇應用程式 (郵件) > 生成", "info")
        check_color_print("  4. 複製生成的16位密碼到GitHub Secrets", "info")
        
        return True
    
    def test_notification_system(self) -> bool:
        """測試通知系統"""
        check_color_print("=== 通知系統測試 ===", "info")
        
        try:
            # 嘗試導入通知模組
            sys.path.append('.')
            import notifier
            
            check_color_print("通知模組導入: 成功", "success")
            
            # 初始化通知系統
            notifier.init()
            check_color_print("通知系統初始化: 成功", "success")
            
            # 檢查通知系統可用性
            if hasattr(notifier, 'is_notification_available'):
                if notifier.is_notification_available():
                    check_color_print("通知系統狀態: 可用", "success")
                    self.success_items.append("通知系統可用")
                else:
                    check_color_print("通知系統狀態: 不可用", "error")
                    self.errors.append("通知系統不可用")
                    return False
            
            # 發送測試通知
            test_message = f"""🧪 配置檢查測試通知

⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 測試目的: 驗證通知系統配置
✅ 如果您收到這封郵件，表示通知系統配置正確！

📋 下一步:
1. 檢查GitHub Secrets配置
2. 測試GitHub Actions工作流程
3. 設置自動排程

祝您使用愉快！🚀"""
            
            notifier.send_notification(test_message, "🧪 通知系統測試")
            check_color_print("測試通知發送: 成功", "success")
            check_color_print("📧 請檢查您的郵箱確認是否收到測試通知", "info")
            self.success_items.append("測試通知發送成功")
            
            return True
            
        except ImportError:
            check_color_print("通知模組導入: 失敗 (notifier.py不存在)", "error")
            self.errors.append("通知模組不存在")
            return False
        except Exception as e:
            check_color_print(f"通知系統測試失敗: {e}", "error")
            self.errors.append(f"通知系統測試失敗: {e}")
            return False
    
    def generate_report(self) -> None:
        """生成檢查報告"""
        check_color_print("\n" + "="*50, "info")
        check_color_print("📊 配置檢查報告", "info")
        check_color_print("="*50, "info")
        
        if self.success_items:
            check_color_print(f"\n✅ 成功項目 ({len(self.success_items)}):", "success")
            for item in self.success_items:
                check_color_print(f"  • {item}", "success")
        
        if self.warnings:
            check_color_print(f"\n⚠️  警告項目 ({len(self.warnings)}):", "warning")
            for item in self.warnings:
                check_color_print(f"  • {item}", "warning")
        
        if self.errors:
            check_color_print(f"\n❌ 錯誤項目 ({len(self.errors)}):", "error")
            for item in self.errors:
                check_color_print(f"  • {item}", "error")
        
        # 總體評估
        total_checks = len(self.success_items) + len(self.warnings) + len(self.errors)
        success_rate = len(self.success_items) / total_checks * 100 if total_checks > 0 else 0
        
        check_color_print(f"\n📈 檢查結果:", "info")
        check_color_print(f"  總計檢查項目: {total_checks}", "info")
        check_color_print(f"  成功率: {success_rate:.1f}%", "info")
        
        if len(self.errors) == 0:
            if len(self.warnings) == 0:
                check_color_print("🎉 所有檢查項目都通過！系統配置完美！", "success")
            else:
                check_color_print("✅ 基本配置正確，有一些小警告需要注意", "success")
        else:
            check_color_print("❌ 發現配置問題，請修復後再試", "error")
            
        check_color_print("\n📋 建議後續步驟:", "info")
        check_color_print("  1. 修復所有錯誤項目", "info")
        check_color_print("  2. 確認GitHub Secrets設置", "info")
        check_color_print("  3. 測試GitHub Actions工作流程", "info")
        check_color_print("  4. 設置自動排程執行", "info")
    
    def run_all_checks(self) -> bool:
        """執行所有檢查"""
        check_color_print("🚀 開始執行配置檢查...\n", "info")
        
        # 執行各項檢查
        python_ok = self.check_python_environment()
        env_ok = self.check_environment_variables()
        files_ok = self.check_file_structure()
        self.check_github_secrets()  # 這個只是顯示資訊
        
        # 生成報告
        self.generate_report()
        
        return python_ok and env_ok and files_ok

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='台股分析系統配置檢查工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python config_checker.py --check-all          # 執行所有檢查
  python config_checker.py --check-env          # 只檢查環境變數
  python config_checker.py --check-files        # 只檢查文件結構
  python config_checker.py --test-notification  # 測試通知系統
        """
    )
    
    parser.add_argument('--check-all', action='store_true', help='執行所有檢查')
    parser.add_argument('--check-env', action='store_true', help='檢查環境變數')
    parser.add_argument('--check-files', action='store_true', help='檢查文件結構')
    parser.add_argument('--test-notification', action='store_true', help='測試通知系統')
    
    args = parser.parse_args()
    
    # 創建檢查器
    checker = ConfigChecker()
    
    # 如果沒有指定參數，默認執行所有檢查
    if not any([args.check_all, args.check_env, args.check_files, args.test_notification]):
        args.check_all = True
    
    try:
        if args.check_all:
            success = checker.run_all_checks()
            if args.test_notification:
                checker.test_notification_system()
        else:
            if args.check_env:
                checker.check_python_environment()
                checker.check_environment_variables()
            
            if args.check_files:
                checker.check_file_structure()
            
            if args.test_notification:
                checker.test_notification_system()
            
            checker.generate_report()
            success = len(checker.errors) == 0
        
        # 設置退出碼
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        check_color_print("\n⚠️ 用戶中斷檢查", "warning")
        sys.exit(1)
    except Exception as e:
        check_color_print(f"\n❌ 檢查過程中發生錯誤: {e}", "error")
        sys.exit(1)

if __name__ == '__main__':
    main()
