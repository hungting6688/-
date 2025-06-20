"""
immediate_credibility_fix.py - 立即修復可信度問題
針對法人買超錯誤和技術指標缺乏佐證的緊急修復
"""
import os
import json
import shutil
from datetime import datetime

class ImmediateCredibilityFix:
    """立即可信度修復器"""
    
    def __init__(self):
        self.backup_dir = f"credibility_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.fixes_applied = []
        
    def apply_emergency_fixes(self):
        """應用緊急修復"""
        print("🚨 應用緊急可信度修復...")
        print("=" * 50)
        
        # 1. 備份現有文件
        self._backup_files()
        
        # 2. 修復法人數據問題
        self._fix_institutional_data_issues()
        
        # 3. 修復技術指標佐證問題
        self._fix_technical_indicator_issues()
        
        # 4. 加入可信度標示
        self._add_credibility_labels()
        
        # 5. 生成修復報告
        self._generate_fix_report()
        
        print("✅ 緊急修復完成！")
    
    def _backup_files(self):
        """備份現有文件"""
        print("📁 備份現有文件...")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        files_to_backup = [
            'enhanced_stock_bot.py',
            'twse_data_fetcher.py', 
            'notifier.py'
        ]
        
        for filename in files_to_backup:
            if os.path.exists(filename):
                backup_path = os.path.join(self.backup_dir, filename)
                shutil.copy2(filename, backup_path)
                print(f"  ✅ 已備份: {filename}")
    
    def _fix_institutional_data_issues(self):
        """修復法人數據問題"""
        print("\n🔧 修復法人數據問題...")
        
        # 修復 enhanced_stock_bot.py 中的法人數據處理
        institutional_fix_code = '''
def _fetch_enhanced_institutional_data(self, stock_code: str) -> Optional[Dict]:
    """獲取增強版法人買賣數據（修復版）"""
    try:
        # ⚠️ 修復：停用模擬數據，使用實際數據或標記為不確定
        # 原有的隨機生成邏輯已被停用
        
        # 嘗試從多個來源獲取真實法人數據
        real_institutional_data = self._get_real_institutional_data(stock_code)
        
        if real_institutional_data and real_institutional_data.get('confidence', 0) > 0.7:
            # 有可信的實際數據
            return {
                'foreign_net_buy': real_institutional_data['foreign_net_buy'],
                'trust_net_buy': real_institutional_data['trust_net_buy'],
                'dealer_net_buy': real_institutional_data['dealer_net_buy'],
                'consecutive_buy_days': real_institutional_data.get('consecutive_days', 0),
                'data_source': 'verified',
                'confidence': real_institutional_data['confidence']
            }
        else:
            # 無法獲取可信數據，誠實標記
            return {
                'foreign_net_buy': 0,
                'trust_net_buy': 0, 
                'dealer_net_buy': 0,
                'consecutive_buy_days': 0,
                'data_source': 'unavailable',
                'confidence': 0.0,
                'warning': '法人數據暫時無法驗證'
            }
            
    except Exception as e:
        log_event(f"⚠️ 法人數據獲取失敗: {stock_code}", level='warning')
        return {
            'foreign_net_buy': 0,
            'trust_net_buy': 0,
            'dealer_net_buy': 0,
            'data_source': 'error', 
            'confidence': 0.0,
            'warning': '法人數據獲取異常'
        }

def _get_real_institutional_data(self, stock_code: str) -> Optional[Dict]:
    """嘗試獲取真實法人數據"""
    try:
        # 方法1: 從證交所API獲取（需要實現）
        # 這裡應該實現真實的API調用
        
        # 方法2: 從可信的第三方數據源
        # 可以整合Yahoo Finance、鉅亨網等數據
        
        # 方法3: 暫時返回None，誠實面對數據限制
        return None
        
    except Exception:
        return None

def _generate_institutional_reason(self, analysis: Dict, analysis_type: str) -> str:
    """生成法人動向推薦理由（修復版）"""
    reasons = []
    
    # 檢查法人數據的可信度
    institutional_confidence = analysis.get('institutional_confidence', 0)
    
    if institutional_confidence > 0.8:
        # 高可信度法人數據
        foreign_net = analysis.get('foreign_net_buy', 0)
        trust_net = analysis.get('trust_net_buy', 0)
        
        if foreign_net > 20000:
            reasons.append(f"外資買超 {foreign_net//10000:.1f}億元 ✅驗證")
        elif foreign_net < -20000:
            reasons.append(f"外資賣超 {abs(foreign_net)//10000:.1f}億元 ⚠️注意")
        
        if trust_net > 10000:
            reasons.append(f"投信買超 {trust_net//10000:.1f}億元 ✅支撐")
            
    elif institutional_confidence > 0.5:
        # 中等可信度，謹慎表述
        reasons.append("法人動向待進一步確認 ⚠️")
        
    else:
        # 低可信度，不使用法人數據作為推薦理由
        reasons.append("基於技術面和基本面分析")
    
    return "，".join(reasons) if reasons else "綜合指標分析"
'''
        
        # 寫入修復文件
        fix_file = 'institutional_data_fix.py'
        with open(fix_file, 'w', encoding='utf-8') as f:
            f.write("# 法人數據修復代碼\n")
            f.write("# 請將以下代碼整合到 enhanced_stock_bot.py 中\n\n")
            f.write(institutional_fix_code)
        
        self.fixes_applied.append("法人數據可信度修復")
        print("  ✅ 法人數據修復代碼已生成")
    
    def _fix_technical_indicator_issues(self):
        """修復技術指標佐證問題"""
        print("\n🔧 修復技術指標佐證問題...")
        
        technical_fix_code = '''
def _get_verified_technical_analysis(self, stock_code: str, stock_info: Dict[str, Any]) -> Dict[str, Any]:
    """獲取經過驗證的技術分析（修復版）"""
    try:
        # 檢查是否有足夠的歷史數據
        historical_data = self._attempt_get_historical_data(stock_code)
        
        if historical_data is None or len(historical_data) < 20:
            # 沒有足夠數據，誠實標記
            return {
                'available': False,
                'confidence': 0.0,
                'warning': '歷史數據不足，技術指標無法驗證',
                'fallback_reason': '僅基於當日價格和成交量分析'
            }
        
        # 有足夠數據，進行真實計算
        verified_indicators = self._calculate_real_technical_indicators(historical_data)
        evidence_data = self._generate_technical_evidence(historical_data, verified_indicators)
        
        return {
            'available': True,
            'confidence': 0.9,
            'indicators': verified_indicators,
            'evidence': evidence_data,
            'data_points': len(historical_data),
            'verification_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        log_event(f"⚠️ 技術指標驗證失敗: {stock_code} - {e}", level='warning')
        return {
            'available': False,
            'confidence': 0.0,
            'warning': '技術指標驗證失敗',
            'fallback_reason': '僅基於基本價量關係分析'
        }

def _generate_technical_reason_with_evidence(self, analysis: Dict, analysis_type: str) -> str:
    """生成有佐證的技術分析理由（修復版）"""
    reasons = []
    
    # 檢查技術指標的可信度
    technical_confidence = analysis.get('technical_confidence', 0)
    
    if technical_confidence > 0.8:
        # 高可信度技術指標，提供具體數值佐證
        technical_signals = analysis.get('technical_signals', {})
        
        if technical_signals.get('macd_golden_cross'):
            macd_val = analysis.get('macd_value', 0)
            signal_val = analysis.get('macd_signal_value', 0)
            reasons.append(f"MACD金叉 ({macd_val:.3f} > {signal_val:.3f}) ✅驗證")
        
        if technical_signals.get('ma20_bullish'):
            ma20_val = analysis.get('ma20_value', 0)
            current_price = analysis.get('current_price', 0)
            reasons.append(f"站穩20MA ({current_price:.1f} > {ma20_val:.1f}) ✅確認")
        
        if technical_signals.get('rsi_healthy'):
            rsi_val = analysis.get('rsi_value', 50)
            reasons.append(f"RSI健康 ({rsi_val:.0f}) ✅動能良好")
            
    elif technical_confidence > 0.5:
        # 中等可信度，謹慎表述
        change_percent = analysis.get('change_percent', 0)
        if abs(change_percent) > 2:
            reasons.append(f"價格表現{'強勢' if change_percent > 0 else '弱勢'} ({change_percent:+.1f}%)")
        reasons.append("技術面需進一步觀察 ⚠️")
        
    else:
        # 低可信度，專注於可驗證的基本數據
        change_percent = analysis.get('change_percent', 0)
        trade_value = analysis.get('trade_value', 0)
        
        reasons.append(f"今日{'上漲' if change_percent > 0 else '下跌'} {abs(change_percent):.1f}%")
        
        if trade_value > 1000000000:
            reasons.append(f"成交金額 {trade_value/100000000:.1f}億元，交投活躍")
    
    return "，".join(reasons) if reasons else "基於當日價量表現"

def _attempt_get_historical_data(self, stock_code: str, days: int = 30) -> Optional[pd.DataFrame]:
    """嘗試獲取歷史數據"""
    try:
        # 方法1: 從證交所API獲取歷史數據
        # 這裡應該實現真實的歷史數據獲取
        
        # 方法2: 從第三方數據源獲取
        # 可以整合Yahoo Finance等
        
        # 方法3: 暫時返回None，誠實面對數據限制
        return None
        
    except Exception:
        return None

def _calculate_real_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
    """計算真實的技術指標"""
    try:
        # 確保有足夠的數據點
        if len(df) < 26:
            return {}
        
        # 計算移動平均線
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA20'] = df['close'].rolling(20).mean()
        
        # 計算MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        # 計算RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 獲取最新值
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        
        return {
            'current_price': latest['close'],
            'ma20_value': latest['MA20'],
            'macd_value': latest['MACD'],
            'macd_signal_value': latest['MACD_Signal'],
            'rsi_value': latest['RSI'],
            
            # 技術信號
            'macd_golden_cross': (latest['MACD'] > latest['MACD_Signal'] and 
                                 previous['MACD'] <= previous['MACD_Signal']),
            'ma20_bullish': latest['close'] > latest['MA20'],
            'rsi_healthy': 30 <= latest['RSI'] <= 70,
            
            'calculation_confidence': 0.95
        }
        
    except Exception as e:
        log_event(f"技術指標計算失敗: {e}", level='error')
        return {}
'''
        
        # 寫入修復文件
        fix_file = 'technical_indicator_fix.py'
        with open(fix_file, 'w', encoding='utf-8') as f:
            f.write("# 技術指標佐證修復代碼\n")
            f.write("# 請將以下代碼整合到 enhanced_stock_bot.py 中\n\n")
            f.write(technical_fix_code)
        
        self.fixes_applied.append("技術指標佐證修復")
        print("  ✅ 技術指標修復代碼已生成")
    
    def _add_credibility_labels(self):
        """加入可信度標示"""
        print("\n🏷️ 加入可信度標示...")
        
        credibility_code = '''
def generate_credibility_enhanced_notifications(self, recommendations: Dict, time_slot: str):
    """生成包含可信度標示的通知（修復版）"""
    
    message = f"📊 {time_slot} 股票分析（可信度增強版）\\n\\n"
    
    # 處理短線推薦
    if recommendations.get('short_term'):
        message += "【🔥 短線推薦】\\n\\n"
        
        for i, stock in enumerate(recommendations['short_term'], 1):
            analysis = stock.get('analysis', {})
            
            # 計算整體可信度
            credibility = self._calculate_overall_credibility(analysis)
            credibility_label = self._get_credibility_label(credibility)
            
            message += f"{credibility_label} {i}. {stock['code']} {stock['name']}\\n"
            message += f"💰 現價: {stock['current_price']} 元\\n"
            
            # 顯示經過驗證的資訊
            verified_facts = self._extract_verified_facts(analysis)
            for fact in verified_facts:
                message += f"  {fact}\\n"
            
            # 顯示數據警告（如果有）
            warnings = self._extract_data_warnings(analysis)
            for warning in warnings:
                message += f"  ⚠️ {warning}\\n"
            
            message += f"📊 數據可信度: {credibility:.0%}\\n"
            message += f"📋 推薦理由: {stock['reason']}\\n\\n"
    
    # 處理長線推薦
    if recommendations.get('long_term'):
        message += "【💎 長線推薦】\\n\\n"
        
        for i, stock in enumerate(recommendations['long_term'], 1):
            analysis = stock.get('analysis', {})
            credibility = self._calculate_overall_credibility(analysis)
            credibility_label = self._get_credibility_label(credibility)
            
            message += f"{credibility_label} {i}. {stock['code']} {stock['name']}\\n"
            message += f"💰 現價: {stock['current_price']} 元\\n"
            
            # 基本面驗證資訊
            fundamental_facts = self._extract_fundamental_facts(analysis)
            for fact in fundamental_facts:
                message += f"  {fact}\\n"
            
            message += f"📊 數據可信度: {credibility:.0%}\\n"
            message += f"💡 投資亮點: {stock['reason']}\\n\\n"
    
    # 加入數據透明度說明
    message += "\\n📋 數據透明度說明:\\n"
    message += "✅ 高可信度：官方數據驗證\\n"
    message += "⚠️ 中等可信度：部分數據待確認\\n" 
    message += "❌ 低可信度：數據不足，謹慎參考\\n"
    message += "\\n⚠️ 投資有風險，決策請謹慎\\n"
    
    return message

def _calculate_overall_credibility(self, analysis: Dict) -> float:
    """計算整體可信度"""
    factors = []
    
    # 基本數據可信度（總是高）
    factors.append(0.9)
    
    # 法人數據可信度
    institutional_confidence = analysis.get('institutional_confidence', 0)
    factors.append(institutional_confidence)
    
    # 技術數據可信度
    technical_confidence = analysis.get('technical_confidence', 0)
    factors.append(technical_confidence)
    
    return sum(factors) / len(factors) if factors else 0.0

def _get_credibility_label(self, credibility: float) -> str:
    """獲取可信度標籤"""
    if credibility >= 0.8:
        return "✅"
    elif credibility >= 0.6:
        return "⚠️"
    else:
        return "❌"

def _extract_verified_facts(self, analysis: Dict) -> List[str]:
    """提取已驗證的事實"""
    facts = []
    
    # 價格和成交量（總是可信）
    change_percent = analysis.get('change_percent', 0)
    if change_percent != 0:
        direction = "上漲" if change_percent > 0 else "下跌"
        facts.append(f"今日{direction} {abs(change_percent):.1f}% ✅確認")
    
    trade_value = analysis.get('trade_value', 0)
    if trade_value > 0:
        facts.append(f"成交金額 {trade_value/100000000:.1f}億元 ✅確認")
    
    # 經過驗證的技術指標
    if analysis.get('technical_confidence', 0) > 0.8:
        if analysis.get('macd_golden_cross'):
            macd_val = analysis.get('macd_value', 0)
            facts.append(f"MACD金叉 {macd_val:.3f} ✅驗證")
        
        if analysis.get('ma20_bullish'):
            ma20_val = analysis.get('ma20_value', 0)
            facts.append(f"站穩20MA {ma20_val:.1f} ✅驗證")
    
    # 經過驗證的法人數據
    if analysis.get('institutional_confidence', 0) > 0.8:
        foreign_net = analysis.get('foreign_net_buy', 0)
        if abs(foreign_net) > 5000:
            direction = "買超" if foreign_net > 0 else "賣超"
            facts.append(f"外資{direction} {abs(foreign_net)//10000:.1f}億 ✅驗證")
    
    return facts

def _extract_data_warnings(self, analysis: Dict) -> List[str]:
    """提取數據警告"""
    warnings = []
    
    # 法人數據警告
    if analysis.get('institutional_confidence', 0) < 0.6:
        warnings.append("法人數據待進一步確認")
    
    # 技術指標警告
    if analysis.get('technical_confidence', 0) < 0.6:
        warnings.append("技術指標缺乏充分歷史數據佐證")
    
    return warnings
'''
        
        # 寫入修復文件
        fix_file = 'credibility_labels_fix.py'
        with open(fix_file, 'w', encoding='utf-8') as f:
            f.write("# 可信度標示修復代碼\n")
            f.write("# 請將以下代碼整合到 notifier.py 中\n\n")
            f.write(credibility_code)
        
        self.fixes_applied.append("可信度標示系統")
        print("  ✅ 可信度標示代碼已生成")
    
    def _generate_fix_report(self):
        """生成修復報告"""
        print("\n📋 生成修復報告...")
        
        report = {
            "fix_time": datetime.now().isoformat(),
            "backup_location": self.backup_dir,
            "fixes_applied": self.fixes_applied,
            "problems_addressed": [
                {
                    "problem": "法人買超數據錯誤",
                    "solution": "停用模擬數據，加入可信度驗證機制",
                    "impact": "避免誤導性的法人買超報告"
                },
                {
                    "problem": "技術指標缺乏佐證",
                    "solution": "要求實際歷史數據計算，無數據時誠實標記",
                    "impact": "提供有根據的技術分析或明確標示限制"
                },
                {
                    "problem": "推薦說服力不足",
                    "solution": "加入可信度分級和透明度說明",
                    "impact": "用戶可以根據可信度做出更好的決策"
                }
            ],
            "next_steps": [
                "整合修復代碼到現有系統",
                "測試可信度評分準確性",
                "觀察用戶對透明度改進的反饋",
                "逐步實現真實數據源接入"
            ],
            "expected_improvements": {
                "data_accuracy": "大幅提升",
                "user_trust": "顯著改善", 
                "recommendation_quality": "更加可靠",
                "transparency": "完全透明"
            }
        }
        
        # 寫入報告
        with open('credibility_fix_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("  ✅ 修復報告已生成: credibility_fix_report.json")
    
    def show_fix_summary(self):
        """顯示修復摘要"""
        print("\n" + "=" * 60)
        print("🎉 可信度問題修復完成！")
        print("=" * 60)
        
        print(f"📁 備份位置: {self.backup_dir}")
        
        print("\n🔧 已生成修復文件:")
        print("  📄 institutional_data_fix.py - 法人數據修復")
        print("  📄 technical_indicator_fix.py - 技術指標佐證修復")
        print("  📄 credibility_labels_fix.py - 可信度標示修復")
        print("  📄 credibility_fix_report.json - 修復報告")
        
        print("\n📝 下一步操作:")
        print("1. 將修復代碼整合到對應的原始文件中")
        print("2. 測試修復後的系統運行")
        print("3. 驗證可信度標示是否正確顯示")
        print("4. 觀察推薦品質的改善效果")
        
        print("\n✅ 修復重點:")
        print("• 停用不準確的模擬法人數據")
        print("• 要求技術指標提供實際計算佐證")
        print("• 加入明確的可信度分級標示")
        print("• 提升數據透明度和用戶信任")
        
        print("\n🎯 預期效果:")
        print("• 消除法人買超錯誤報告")
        print("• 提供技術指標實際數值佐證")
        print("• 用戶可以根據可信度做決策")
        print("• 大幅提升推薦說服力")
        
        print("\n💡 使用建議:")
        print("優先推薦 ✅ 高可信度的股票")
        print("謹慎考慮 ⚠️ 中等可信度的股票")
        print("避免推薦 ❌ 低可信度的股票")

def main():
    """主函數"""
    print("🚨 股票推薦可信度緊急修復工具")
    print("針對法人買超錯誤和技術指標缺乏佐證問題")
    
    response = input("\n是否開始緊急修復？(y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ 修復已取消")
        return
    
    fixer = ImmediateCredibilityFix()
    fixer.apply_emergency_fixes()
    fixer.show_fix_summary()

if __name__ == "__main__":
    main()
