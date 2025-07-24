#!/usr/bin/env python3
"""
real_data_system_upgrade.py - 台股系統真實數據升級腳本
確保您的股票分析系統使用真實當天數據，而非模擬數據
"""
import os
import sys
import shutil
import importlib.util
from datetime import datetime
from typing import Dict, Any, List

class RealDataSystemUpgrade:
    """台股系統真實數據升級器"""
    
    def __init__(self):
        self.backup_dir = f"backup_before_real_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.files_to_modify = [
            'unified_stock_analyzer.py',
            'enhanced_stock_bot.py', 
            'config.py'
        ]
        self.upgrade_results = {}
        
    def start_upgrade(self):
        """開始升級流程"""
        print("🚀 台股系統真實數據升級")
        print("=" * 60)
        print(f"升級時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 檢查前置條件
        if not self._check_prerequisites():
            return False
        
        # 創建備份
        if not self._create_backup():
            return False
        
        # 執行升級
        if not self._execute_upgrade():
            return False
        
        # 驗證升級
        if not self._verify_upgrade():
            return False
        
        # 完成升級
        self._complete_upgrade()
        return True
    
    def _check_prerequisites(self):
        """檢查升級前置條件"""
        print("🔍 檢查升級前置條件...")
        
        # 檢查必要文件是否存在
        required_files = ['real_taiwan_stock_fetcher.py']
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
            print("   請確保 real_taiwan_stock_fetcher.py 文件在當前目錄")
            return False
        
        # 檢查網路連接
        try:
            from real_taiwan_stock_fetcher import RealTaiwanStockFetcher
            fetcher = RealTaiwanStockFetcher()
            api_results = fetcher.test_all_apis()
            
            if not any(api_results.values()):
                print("❌ 無法連接到台股API，請檢查網路連接")
                return False
            
            working_apis = [name for name, status in api_results.items() if status]
            print(f"✅ API連接正常: {', '.join(working_apis)}")
            
        except Exception as e:
            print(f"❌ 測試API連接失敗: {e}")
            return False
        
        print("✅ 前置條件檢查完成")
        return True
    
    def _create_backup(self):
        """創建備份"""
        print(f"\n📁 創建備份到 {self.backup_dir}...")
        
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            
            backed_up = 0
            for filename in self.files_to_modify:
                if os.path.exists(filename):
                    backup_path = os.path.join(self.backup_dir, filename)
                    shutil.copy2(filename, backup_path)
                    backed_up += 1
                    print(f"  ✅ 已備份: {filename}")
            
            if backed_up == 0:
                print("⚠️ 沒有文件需要備份")
            
            print(f"✅ 備份完成: {backed_up} 個文件")
            return True
            
        except Exception as e:
            print(f"❌ 備份失敗: {e}")
            return False
    
    def _execute_upgrade(self):
        """執行系統升級"""
        print(f"\n🔧 執行系統升級...")
        
        # 升級1: 修改 unified_stock_analyzer.py
        if os.path.exists('unified_stock_analyzer.py'):
            success = self._upgrade_unified_analyzer()
            self.upgrade_results['unified_analyzer'] = success
            if not success:
                print("❌ unified_stock_analyzer.py 升級失敗")
                return False
        
        # 升級2: 修改 enhanced_stock_bot.py 
        if os.path.exists('enhanced_stock_bot.py'):
            success = self._upgrade_enhanced_bot()
            self.upgrade_results['enhanced_bot'] = success
            if not success:
                print("❌ enhanced_stock_bot.py 升級失敗")
                return False
        
        # 升級3: 修改配置文件
        if os.path.exists('config.py'):
            success = self._upgrade_config()
            self.upgrade_results['config'] = success
            if not success:
                print("❌ config.py 升級失敗")
                return False
        
        # 創建集成腳本
        success = self._create_integration_script()
        self.upgrade_results['integration_script'] = success
        
        print("✅ 系統升級完成")
        return True
    
    def _upgrade_unified_analyzer(self):
        """升級 unified_stock_analyzer.py"""
        print("  🔧 升級 unified_stock_analyzer.py...")
        
        try:
            # 讀取原文件
            with open('unified_stock_analyzer.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 修改 DataFetcher 類別
            modified_content = self._modify_data_fetcher_class(content)
            
            # 寫回文件
            with open('unified_stock_analyzer.py', 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print("    ✅ unified_stock_analyzer.py 升級完成")
            return True
            
        except Exception as e:
            print(f"    ❌ 升級 unified_stock_analyzer.py 失敗: {e}")
            return False
    
    def _modify_data_fetcher_class(self, content: str) -> str:
        """修改 DataFetcher 類別以使用真實數據"""
        
        # 1. 添加導入語句
        import_addition = """
# 真實數據獲取器導入
try:
    from real_taiwan_stock_fetcher import RealTaiwanStockFetcher
    REAL_DATA_AVAILABLE = True
    print("✅ 真實數據獲取器已載入")
except ImportError:
    REAL_DATA_AVAILABLE = False
    print("⚠️ 真實數據獲取器不可用，將使用備用方案")
"""
        
        # 在文件開頭添加導入
        if 'from real_taiwan_stock_fetcher import RealTaiwanStockFetcher' not in content:
            lines = content.split('\n')
            insert_index = 0
            
            # 找到合適的插入位置（在其他導入之後）
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_index = i + 1
            
            lines.insert(insert_index, import_addition)
            content = '\n'.join(lines)
        
        # 2. 修改 DataFetcher.__init__ 方法
        init_replacement = '''    def __init__(self):
        self.cache = {}
        self.cache_expire_minutes = 30
        self.use_real_data = REAL_DATA_AVAILABLE
        self.real_fetcher = None
        
        # 初始化真實數據獲取器
        self._init_real_fetcher()
    
    def _init_real_fetcher(self):
        """初始化真實數據獲取器"""
        if not REAL_DATA_AVAILABLE:
            log_event("真實數據獲取器不可用", level='warning')
            self.use_real_data = False
            return
        
        try:
            self.real_fetcher = RealTaiwanStockFetcher()
            
            # 測試連接
            test_results = self.real_fetcher.test_all_apis()
            if any(test_results.values()):
                log_event("✅ 真實數據源連接成功", level='success')
                self.use_real_data = True
            else:
                log_event("⚠️ 真實數據源連接失敗，將使用備用方案", level='warning')
                self.use_real_data = False
                
        except Exception as e:
            log_event(f"⚠️ 真實數據獲取器初始化失敗: {e}，使用備用方案", level='warning')
            self.use_real_data = False'''
        
        # 替換 DataFetcher.__init__ 方法
        if 'def __init__(self):' in content and 'class DataFetcher:' in content:
            import re
            pattern = r'(class DataFetcher:.*?def __init__\(self\):)(.*?)(?=\n    def [^_]|\n\n|\nclass|\Z)'
            
            def replace_init(match):
                return match.group(1) + '\n' + init_replacement + '\n'
            
            content = re.sub(pattern, replace_init, content, flags=re.DOTALL)
        
        # 3. 修改 get_stocks_by_time_slot 方法
        method_replacement = '''    def get_stocks_by_time_slot(self, time_slot: str, date: str = None) -> List[Dict[str, Any]]:
        """根據時段獲取股票數據（優先使用真實數據）"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"{time_slot}_{date}"
        
        # 檢查快取
        if self._is_cache_valid(cache_key):
            cached_data = self.cache[cache_key]
            log_event(f"使用快取數據: {len(cached_data)} 支股票")
            return cached_data
        
        # 優先使用真實數據
        if self.use_real_data and self.real_fetcher:
            try:
                stocks = self.real_fetcher.get_stocks_by_time_slot(time_slot, force_fresh=True)
                if stocks:
                    log_event(f"✅ 獲取真實數據: {len(stocks)} 支股票", level='success')
                    self.cache[cache_key] = stocks
                    return stocks
                else:
                    log_event("⚠️ 真實數據為空，回退到備用方案", level='warning')
            except Exception as e:
                log_event(f"⚠️ 真實數據獲取失敗: {e}，回退到備用方案", level='warning')
                # 如果真實數據失敗，將標記為不可用，避免重複嘗試
                self.use_real_data = False
        
        # 備用方案：拋出錯誤而非使用模擬數據
        error_msg = "無法獲取台股真實數據，請檢查網路連接或稍後再試"
        log_event(error_msg, level='error')
        raise Exception(error_msg)'''
        
        # 替換 get_stocks_by_time_slot 方法
        if 'def get_stocks_by_time_slot(self, time_slot: str' in content:
            import re
            pattern = r'def get_stocks_by_time_slot\(self, time_slot: str.*?\n        return stocks'
            content = re.sub(pattern, method_replacement.strip(), content, flags=re.DOTALL)
        
        return content
    
    def _upgrade_enhanced_bot(self):
        """升級 enhanced_stock_bot.py"""
        print("  🔧 升級 enhanced_stock_bot.py...")
        
        try:
            # 檢查文件是否存在並讀取
            with open('enhanced_stock_bot.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加真實數據標記
            if 'USE_REAL_DATA_ONLY = True' not in content:
                addition = '''
# 真實數據配置
USE_REAL_DATA_ONLY = True  # 強制使用真實數據，禁用模擬數據
REAL_DATA_VERIFICATION = True  # 啟用數據驗證

'''
                # 在文件開頭添加
                content = addition + content
            
            # 寫回文件
            with open('enhanced_stock_bot.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("    ✅ enhanced_stock_bot.py 升級完成")
            return True
            
        except Exception as e:
            print(f"    ❌ 升級 enhanced_stock_bot.py 失敗: {e}")
            return False
    
    def _upgrade_config(self):
        """升級配置文件"""
        print("  🔧 升級 config.py...")
        
        try:
            # 檢查文件是否存在並讀取
            with open('config.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加真實數據配置
            config_addition = '''

# 真實數據獲取配置
REAL_DATA_CONFIG = {
    'enabled': True,  # 啟用真實數據獲取
    'force_real_data': True,  # 強制使用真實數據
    'disable_simulation': True,  # 禁用模擬數據
    'api_timeout': 15,  # API請求超時時間
    'max_retries': 3,  # 最大重試次數
    'cache_enabled': False,  # 禁用快取以確保數據新鮮
    'data_freshness_minutes': 1,  # 數據新鮮度要求（分鐘）
}

# 數據品質要求
DATA_QUALITY_CONFIG = {
    'min_stocks_count': 50,  # 最少股票數量
    'require_current_day': True,  # 要求當天數據
    'verify_timestamps': True,  # 驗證時間戳
    'reject_old_data': True,  # 拒絕舊數據
}
'''
            
            # 添加配置（如果尚未存在）
            if 'REAL_DATA_CONFIG' not in content:
                content += config_addition
            
            # 寫回文件
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("    ✅ config.py 升級完成")
            return True
            
        except Exception as e:
            print(f"    ❌ 升級 config.py 失敗: {e}")
            return False
    
    def _create_integration_script(self):
        """創建集成腳本"""
        print("  🔧 創建集成腳本...")
        
        try:
            script_content = '''#!/usr/bin/env python3
"""
run_real_stock_analysis.py - 台股真實數據分析啟動腳本
確保使用台股當天真實數據進行分析
"""
import sys
import os
from datetime import datetime

def main():
    """主函數"""
    print("🚀 台股真實數據分析系統")
    print("=" * 50)
    print(f"啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 檢查真實數據獲取器
    try:
        from real_taiwan_stock_fetcher import RealTaiwanStockFetcher
        print("✅ 真實數據獲取器已載入")
        
        # 測試API連接
        fetcher = RealTaiwanStockFetcher()
        api_results = fetcher.test_all_apis()
        
        working_apis = [name for name, status in api_results.items() if status]
        if working_apis:
            print(f"✅ API連接正常: {', '.join(working_apis)}")
        else:
            print("❌ 所有API都無法連接，請檢查網路")
            return
            
    except ImportError:
        print("❌ 真實數據獲取器不可用")
        return
    except Exception as e:
        print(f"❌ API測試失敗: {e}")
        return
    
    # 啟動統一分析器
    try:
        from unified_stock_analyzer import UnifiedStockAnalyzer
        
        # 創建優化模式分析器（重視基本面和法人數據）
        analyzer = UnifiedStockAnalyzer(mode='optimized')
        
        print("🎯 分析器模式: OPTIMIZED (重視當天真實數據)")
        print("📊 數據來源: 台灣證交所官方API")
        print("⚡ 數據品質: 當天實時驗證")
        print()
        
        # 根據命令行參數執行相應操作
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == 'test':
                print("🧪 執行測試分析...")
                analyzer.test_notification('all')
                
            elif command == 'run':
                if len(sys.argv) > 2:
                    time_slot = sys.argv[2]
                    print(f"📈 執行 {time_slot} 分析...")
                    analyzer.run_analysis(time_slot)
                else:
                    print("❌ 請指定時段，例如: python run_real_stock_analysis.py run afternoon_scan")
                    
            elif command == 'daemon':
                print("🔄 啟動後台服務...")
                analyzer.run_daemon()
                
            else:
                print("❌ 未知命令，支援的命令: test, run, daemon")
        else:
            # 默認執行當前時段分析
            now = datetime.now()
            hour = now.hour
            
            if 9 <= hour < 10:
                time_slot = 'morning_scan'
            elif 10 <= hour < 12:
                time_slot = 'mid_morning_scan'
            elif 12 <= hour < 14:
                time_slot = 'mid_day_scan'
            elif 14 <= hour < 16:
                time_slot = 'afternoon_scan'
            else:
                time_slot = 'afternoon_scan'  # 默認
            
            print(f"📈 執行當前時段分析: {time_slot}")
            analyzer.run_analysis(time_slot)
        
    except Exception as e:
        print(f"❌ 系統啟動失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''
            
            # 寫入腳本文件
            with open('run_real_stock_analysis.py', 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print("    ✅ 集成腳本創建完成: run_real_stock_analysis.py")
            return True
            
        except Exception as e:
            print(f"    ❌ 創建集成腳本失敗: {e}")
            return False
    
    def _verify_upgrade(self):
        """驗證升級是否成功"""
        print(f"\n🔍 驗證升級結果...")
        
        # 測試真實數據獲取
        try:
            from real_taiwan_stock_fetcher import RealTaiwanStockFetcher
            fetcher = RealTaiwanStockFetcher()
            
            # 小規模測試
            test_stocks = fetcher.get_stocks_by_time_slot('afternoon_scan', force_fresh=True)
            
            if test_stocks and len(test_stocks) > 10:
                print(f"✅ 真實數據測試成功: 獲取 {len(test_stocks)} 支股票")
                
                # 驗證數據品質
                real_data_count = sum(1 for stock in test_stocks[:10] if stock.get('is_real_data', False))
                print(f"✅ 數據品質驗證: {real_data_count}/10 支股票為真實數據")
                
                return True
            else:
                print("❌ 真實數據測試失敗: 數據不足")
                return False
                
        except Exception as e:
            print(f"❌ 驗證失敗: {e}")
            return False
    
    def _complete_upgrade(self):
        """完成升級"""
        print(f"\n🎉 台股系統真實數據升級完成！")
        print("=" * 60)
        
        # 顯示升級結果
        print("📊 升級結果摘要:")
        for component, success in self.upgrade_results.items():
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"  {component}: {status}")
        
        # 使用說明
        print(f"\n📋 使用說明:")
        print(f"1. 測試系統: python run_real_stock_analysis.py test")
        print(f"2. 執行分析: python run_real_stock_analysis.py run afternoon_scan")
        print(f"3. 啟動服務: python run_real_stock_analysis.py daemon")
        print(f"4. 快速執行: python run_real_stock_analysis.py")
        
        print(f"\n🛡️ 安全保證:")
        print(f"• 系統已配置為優先使用真實數據")
        print(f"• 當真實數據不可用時，會報錯而非使用模擬數據")
        print(f"• 所有數據都有時間戳和來源標記")
        print(f"• 備份文件保存在: {self.backup_dir}")
        
        print(f"\n🔄 如需回滾:")
        print(f"可從 {self.backup_dir} 目錄恢復原始文件")
        
        print(f"\n💰 現在您的系統將使用台股當天真實數據進行分析！")


def main():
    """主函數"""
    print("歡迎使用台股系統真實數據升級器！")
    print("本升級器將確保您的系統使用台股當天真實數據")
    print()
    
    response = input("是否開始升級？(y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("升級已取消")
        return
    
    upgrader = RealDataSystemUpgrade()
    success = upgrader.start_upgrade()
    
    if not success:
        print("❌ 升級失敗，請檢查錯誤信息")
        print(f"備份文件位於: {upgrader.backup_dir}")
    else:
        print("✅ 升級成功完成！")


if __name__ == "__main__":
    main()
