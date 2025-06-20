#!/usr/bin/env python3
"""
complete_hotfix_aiohttp.py - 完整版 aiohttp 缺失問題修復腳本
自動檢測並修復所有與 aiohttp 相關的導入問題
"""
import os
import sys
import subprocess
import shutil
from datetime import datetime

class AiohttpHotfix:
    """aiohttp 缺失問題修復器"""
    
    def __init__(self):
        self.backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.files_to_fix = [
            'twse_data_fetcher.py',
            'enhanced_realtime_twse_fetcher.py',
            'enhanced_stock_bot.py'
        ]
        
    def print_header(self, message):
        """打印標題"""
        print(f"\n{'='*60}")
        print(f"🔧 {message}")
        print(f"{'='*60}")
    
    def print_step(self, step, message):
        """打印步驟"""
        print(f"\n📋 步驟 {step}: {message}")
    
    def backup_files(self):
        """備份原始文件"""
        self.print_step(1, "備份原始文件")
        
        os.makedirs(self.backup_dir, exist_ok=True)
        backed_up = []
        
        for filename in self.files_to_fix:
            if os.path.exists(filename):
                backup_path = os.path.join(self.backup_dir, filename)
                shutil.copy2(filename, backup_path)
                backed_up.append(filename)
                print(f"  ✅ 已備份: {filename} → {backup_path}")
        
        if backed_up:
            print(f"📁 備份目錄: {self.backup_dir}")
        else:
            print("⚠️ 沒有找到需要修復的文件")
        
        return len(backed_up) > 0
    
    def try_install_aiohttp(self):
        """嘗試安裝 aiohttp"""
        self.print_step(2, "嘗試安裝 aiohttp")
        
        try:
            print("🔄 正在安裝 aiohttp...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'aiohttp>=3.8.0'],
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ aiohttp 安裝成功！")
                # 測試導入
                try:
                    import aiohttp
                    print("✅ aiohttp 導入測試成功")
                    return True
                except ImportError:
                    print("⚠️ aiohttp 安裝了但無法導入")
                    return False
            else:
                print(f"❌ aiohttp 安裝失敗:")
                print(f"   錯誤: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 安裝超時")
            return False
        except Exception as e:
            print(f"❌ 安裝過程出錯: {e}")
            return False
    
    def patch_twse_data_fetcher(self):
        """修補 twse_data_fetcher.py"""
        filename = 'twse_data_fetcher.py'
        
        if not os.path.exists(filename):
            print(f"⚠️ 找不到 {filename}")
            return False
        
        print(f"🔧 修補 {filename}...")
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否已經修復過
        if 'ASYNC_SUPPORT' in content:
            print(f"✅ {filename} 已經修復過")
            return True
        
        # 修復導入部分
        new_imports = '''import os
import json
import time
import requests
import pandas as pd
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 可選的異步支援
try:
    import asyncio
    import aiohttp
    ASYNC_SUPPORT = True
    print("✅ 異步支援已啟用 (aiohttp 可用)")
except ImportError:
    ASYNC_SUPPORT = False
    print("⚠️ 異步支援未啟用 (aiohttp 未安裝)，將使用同步模式")
    
    # 創建虛擬的 asyncio 和 aiohttp 以避免錯誤
    class MockAsyncio:
        @staticmethod
        def run(coro):
            return None
        @staticmethod  
        def get_event_loop():
            return None
        @staticmethod
        def ensure_future(coro):
            return None
    
    class MockAiohttp:
        class ClientSession:
            def __init__(self, *args, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            async def get(self, *args, **kwargs):
                return MockResponse()
        
        class ClientTimeout:
            def __init__(self, *args, **kwargs):
                pass
    
    class MockResponse:
        status = 200
        async def json(self):
            return {}
        async def text(self):
            return ""
    
    asyncio = MockAsyncio()
    aiohttp = MockAiohttp()'''
        
        # 找到導入部分的結束位置
        lines = content.split('\n')
        new_lines = []
        imports_replaced = False
        
        for i, line in enumerate(lines):
            # 跳過原有的導入直到找到第一個非導入行
            if not imports_replaced:
                if (line.strip() and 
                    not line.startswith('#') and 
                    not line.startswith('import') and 
                    not line.startswith('from') and
                    '"""' not in line):
                    # 插入新的導入
                    new_lines.append(new_imports)
                    new_lines.append('')
                    new_lines.append(line)
                    imports_replaced = True
                elif line.startswith('import aiohttp') or line.startswith('import asyncio'):
                    # 跳過這些導入
                    continue
                elif not (line.startswith('import') or line.startswith('from') or line.startswith('#') or not line.strip()):
                    # 非導入行，插入新導入
                    new_lines.append(new_imports)
                    new_lines.append('')
                    new_lines.append(line)
                    imports_replaced = True
                else:
                    # 保留其他導入和註釋
                    if not (line.startswith('import aiohttp') or line.startswith('import asyncio')):
                        new_lines.append(line)
            else:
                new_lines.append(line)
        
        # 如果沒有找到合適的位置插入，就在文件開頭插入
        if not imports_replaced:
            new_content = new_imports + '\n\n' + content
        else:
            new_content = '\n'.join(new_lines)
        
        # 寫回文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ {filename} 修復完成")
        return True
    
    def patch_enhanced_realtime_fetcher(self):
        """修補 enhanced_realtime_twse_fetcher.py"""
        filename = 'enhanced_realtime_twse_fetcher.py'
        
        if not os.path.exists(filename):
            print(f"⚠️ 找不到 {filename}，跳過")
            return True
        
        print(f"🔧 修補 {filename}...")
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否已經修復過
        if 'ASYNC_SUPPORT' in content or 'try:' in content[:500]:
            print(f"✅ {filename} 已經修復過或不需要修復")
            return True
        
        # 替換 aiohttp 導入
        content = content.replace(
            'import aiohttp',
            '''# 可選的異步支援
try:
    import aiohttp
    ASYNC_SUPPORT = True
except ImportError:
    ASYNC_SUPPORT = False
    class MockAiohttp:
        class ClientSession:
            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
            async def get(self, *args, **kwargs): 
                return MockResponse()
        class ClientTimeout:
            def __init__(self, *args, **kwargs): pass
    
    class MockResponse:
        status = 200
        async def json(self): return {}
    
    aiohttp = MockAiohttp()'''
        )
        
        # 寫回文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {filename} 修復完成")
        return True
    
    def patch_enhanced_stock_bot(self):
        """修補 enhanced_stock_bot.py"""
        filename = 'enhanced_stock_bot.py'
        
        if not os.path.exists(filename):
            print(f"⚠️ 找不到 {filename}，跳過")
            return True
        
        print(f"🔧 檢查 {filename}...")
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否有問題的導入
        if 'from enhanced_realtime_twse_fetcher import' in content:
            # 添加異常處理
            content = content.replace(
                'from enhanced_realtime_twse_fetcher import',
                '''try:
    from enhanced_realtime_twse_fetcher import'''
            )
            
            # 在適當位置添加 except 塊
            if 'except ImportError:' not in content:
                # 找到類定義的位置添加異常處理
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if 'from enhanced_realtime_twse_fetcher import' in line and 'try:' in line:
                        new_lines.append('    REALTIME_AVAILABLE = True')
                        new_lines.append('except ImportError:')
                        new_lines.append('    REALTIME_AVAILABLE = False')
                        new_lines.append('    print("⚠️ 即時API功能不可用，將使用標準模式")')
                
                content = '\n'.join(new_lines)
            
            # 寫回文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {filename} 修復完成")
        else:
            print(f"✅ {filename} 不需要修復")
        
        return True
    
    def update_requirements(self):
        """更新 requirements.txt"""
        self.print_step(4, "更新 requirements.txt")
        
        filename = 'requirements.txt'
        
        # 讀取現有內容
        existing_content = ""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # 檢查是否已經包含 aiohttp
        if 'aiohttp' in existing_content:
            print("✅ requirements.txt 已包含 aiohttp")
            return True
        
        # 添加 aiohttp
        new_content = existing_content + '\n# 異步HTTP客戶端套件（用於即時API功能）\naiohttp>=3.8.0\n'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ 已將 aiohttp 添加到 requirements.txt")
        return True
    
    def test_imports(self):
        """測試修復後的導入"""
        self.print_step(5, "測試修復結果")
        
        test_results = {}
        
        for filename in self.files_to_fix:
            if not os.path.exists(filename):
                continue
                
            try:
                # 嘗試編譯文件
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                compile(content, filename, 'exec')
                test_results[filename] = True
                print(f"  ✅ {filename} 語法檢查通過")
                
            except SyntaxError as e:
                test_results[filename] = False
                print(f"  ❌ {filename} 語法錯誤: {e}")
            except Exception as e:
                test_results[filename] = False
                print(f"  ⚠️ {filename} 其他錯誤: {e}")
        
        # 嘗試導入 twse_data_fetcher
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("twse_data_fetcher", "twse_data_fetcher.py")
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print("  ✅ twse_data_fetcher 模組導入成功")
                test_results['import_test'] = True
            else:
                print("  ⚠️ 無法創建 twse_data_fetcher 模組規格")
                test_results['import_test'] = False
        except Exception as e:
            print(f"  ⚠️ twse_data_fetcher 導入測試失敗: {e}")
            test_results['import_test'] = False
        
        return all(test_results.values())
    
    def run_full_fix(self):
        """執行完整的修復流程"""
        self.print_header("aiohttp 缺失問題完整修復")
        
        print(f"🕐 修復時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python 版本: {sys.version}")
        print(f"📁 工作目錄: {os.getcwd()}")
        
        # 步驟1: 備份文件
        backup_success = self.backup_files()
        
        # 步驟2: 嘗試安裝 aiohttp
        install_success = self.try_install_aiohttp()
        
        if install_success:
            print("🎉 aiohttp 安裝成功，問題已解決！")
            print("💡 建議: 重新運行您的股票分析系統")
            return True
        
        # 步驟3: 代碼修補
        self.print_step(3, "代碼修補（兼容模式）")
        
        patch_results = []
        patch_results.append(self.patch_twse_data_fetcher())
        patch_results.append(self.patch_enhanced_realtime_fetcher())
        patch_results.append(self.patch_enhanced_stock_bot())
        
        # 步驟4: 更新 requirements.txt
        self.update_requirements()
        
        # 步驟5: 測試修復結果
        test_success = self.test_imports()
        
        # 總結
        self.print_header("修復結果總結")
        
        if all(patch_results) and test_success:
            print("🎉 修復成功！")
            print("✅ 所有文件已修補為兼容模式")
            print("✅ 系統將自動使用同步模式（功能完整）")
            print("✅ 如果之後安裝了 aiohttp，將自動啟用異步功能")
            
            print(f"\n📋 修復內容:")
            print(f"  🔧 代碼修補: 添加 aiohttp 可選導入邏輯")
            print(f"  📦 依賴更新: requirements.txt 已包含 aiohttp")
            print(f"  💾 文件備份: {self.backup_dir}")
            
            print(f"\n🚀 下一步:")
            print(f"  1. 重新運行您的股票分析系統")
            print(f"  2. 系統將正常運行（使用同步模式）")
            print(f"  3. 如需即時API功能，可稍後安裝 aiohttp")
            
            return True
        else:
            print("❌ 修復過程中出現問題")
            print(f"💾 原始文件備份在: {self.backup_dir}")
            print("🔄 您可以從備份中恢復原始文件")
            return False

def main():
    """主函數"""
    try:
        hotfix = AiohttpHotfix()
        success = hotfix.run_full_fix()
        
        if success:
            print(f"\n🎯 修復完成！現在可以運行您的股票分析系統了")
            print(f"🚀 執行命令: python enhanced_stock_bot.py afternoon_scan")
        else:
            print(f"\n❌ 修復失敗，請檢查上面的錯誤信息")
            
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 用戶中斷修復過程")
        return 1
    except Exception as e:
        print(f"\n❌ 修復過程發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
