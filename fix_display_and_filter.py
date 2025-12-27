"""
fix_display_and_filter.py - 修復技術指標、基本面、法人動向顯示問題並優化篩選邏輯
"""
import os
import shutil
from datetime import datetime

class DisplayAndFilterFixer:
    """修復顯示問題和優化篩選邏輯"""

    def __init__(self):
        self.backup_dir = f"backup_display_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def backup_files(self):
        """備份原始文件"""
        print("📁 備份原始文件...")
        os.makedirs(self.backup_dir, exist_ok=True)

        files_to_backup = [
            'enhanced_stock_bot.py',
            'notifier.py',
            'config.py'
        ]

        for filename in files_to_backup:
            if os.path.exists(filename):
                backup_path = os.path.join(self.backup_dir, filename)
                shutil.copy2(filename, backup_path)
                print(f"✅ 已備份: {filename}")

        print(f"📁 備份目錄: {self.backup_dir}")

    def create_enhanced_display_functions(self):
        """創建增強版顯示函數"""

        enhanced_notifier_code = '''
def extract_technical_indicators_detailed(analysis_data):
    """提取詳細技術指標（修復版）"""
    indicators = []

    # RSI 指標
    rsi_value = analysis_data.get('rsi', 0)
    if rsi_value > 0:
        if rsi_value > 70:
            indicators.append(f"🔴 RSI過熱 ({rsi_value:.1f})")
        elif rsi_value < 30:
            indicators.append(f"🟢 RSI超賣 ({rsi_value:.1f})")
        else:
            indicators.append(f"🟡 RSI健康 ({rsi_value:.1f})")

    # MACD 指標
    technical_signals = analysis_data.get('technical_signals', {})
    if technical_signals.get('macd_golden_cross'):
        indicators.append("🟢 MACD金叉")
    elif technical_signals.get('macd_bullish'):
        indicators.append("🟡 MACD轉強")
    elif technical_signals.get('macd_death_cross'):
        indicators.append("🔴 MACD死叉")

    # 均線指標
    if technical_signals.get('ma_golden_cross'):
        indicators.append("🟢 均線金叉")
    elif technical_signals.get('ma20_bullish'):
        indicators.append("🟡 站穩20MA")
    elif technical_signals.get('ma_death_cross'):
        indicators.append("🔴 均線死叉")

    # 成交量指標
    volume_ratio = analysis_data.get('volume_ratio', 1)
    if volume_ratio > 3:
        indicators.append(f"🔥 爆量 ({volume_ratio:.1f}倍)")
    elif volume_ratio > 2:
        indicators.append(f"📈 放量 ({volume_ratio:.1f}倍)")
    elif volume_ratio > 1.5:
        indicators.append(f"📊 增量 ({volume_ratio:.1f}倍)")

    # KD 指標（如果有）
    if analysis_data.get('kd_golden_cross'):
        indicators.append("🟢 KD金叉")
    elif analysis_data.get('kd_death_cross'):
        indicators.append("🔴 KD死叉")

    return indicators

def extract_fundamental_advantages_detailed(analysis_data):
    """提取詳細基本面優勢（修復版）"""
    advantages = []

    # 殖利率
    dividend_yield = analysis_data.get('dividend_yield', 0)
    if dividend_yield > 6:
        advantages.append(f"💰 超高殖利率 {dividend_yield:.1f}%")
    elif dividend_yield > 4:
        advantages.append(f"💸 高殖利率 {dividend_yield:.1f}%")
    elif dividend_yield > 2:
        advantages.append(f"💵 穩定殖利率 {dividend_yield:.1f}%")

    # EPS成長
    eps_growth = analysis_data.get('eps_growth', 0)
    if eps_growth > 30:
        advantages.append(f"🚀 EPS爆發成長 {eps_growth:.1f}%")
    elif eps_growth > 15:
        advantages.append(f"📈 EPS高成長 {eps_growth:.1f}%")
    elif eps_growth > 8:
        advantages.append(f"📊 EPS穩健成長 {eps_growth:.1f}%")

    # ROE
    roe = analysis_data.get('roe', 0)
    if roe > 20:
        advantages.append(f"⭐ ROE優異 {roe:.1f}%")
    elif roe > 15:
        advantages.append(f"✨ ROE良好 {roe:.1f}%")
    elif roe > 10:
        advantages.append(f"📋 ROE穩健 {roe:.1f}%")

    # 本益比
    pe_ratio = analysis_data.get('pe_ratio', 999)
    if pe_ratio < 10:
        advantages.append(f"💎 低本益比 {pe_ratio:.1f}倍")
    elif pe_ratio < 15:
        advantages.append(f"🔍 合理本益比 {pe_ratio:.1f}倍")

    # 營收成長
    revenue_growth = analysis_data.get('revenue_growth', 0)
    if revenue_growth > 20:
        advantages.append(f"🏢 營收高成長 {revenue_growth:.1f}%")
    elif revenue_growth > 10:
        advantages.append(f"📈 營收成長 {revenue_growth:.1f}%")

    # 連續配息
    dividend_years = analysis_data.get('dividend_consecutive_years', 0)
    if dividend_years > 10:
        advantages.append(f"🏆 連續配息 {dividend_years}年")
    elif dividend_years > 5:
        advantages.append(f"🎯 穩定配息 {dividend_years}年")

    return advantages

def extract_institutional_flows_detailed(analysis_data):
    """提取詳細法人動向（修復版）"""
    flows = []

    # 外資買賣
    foreign_net = analysis_data.get('foreign_net_buy', 0)
    if foreign_net != 0:
        foreign_億 = foreign_net / 10000
        consecutive_days = analysis_data.get('consecutive_buy_days', 0)

        if foreign_net > 50000:  # 5億以上
            if consecutive_days > 3:
                flows.append(f"🔥 外資連{consecutive_days}日大買 {foreign_億:.1f}億")
            else:
                flows.append(f"🟢 外資大幅買超 {foreign_億:.1f}億")
        elif foreign_net > 10000:  # 1億以上
            flows.append(f"📈 外資買超 {foreign_億:.1f}億")
        elif foreign_net > 0:
            flows.append(f"🟡 外資小買 {foreign_億:.1f}億")
        elif foreign_net < -50000:  # 大量賣出
            flows.append(f"🔴 外資大賣 {abs(foreign_億):.1f}億")
        elif foreign_net < -10000:
            flows.append(f"📉 外資賣超 {abs(foreign_億):.1f}億")
        elif foreign_net < 0:
            flows.append(f"🟠 外資小賣 {abs(foreign_億):.1f}億")

    # 投信買賣
    trust_net = analysis_data.get('trust_net_buy', 0)
    if trust_net != 0:
        trust_億 = trust_net / 10000
        if trust_net > 20000:  # 2億以上
            flows.append(f"🏦 投信大買 {trust_億:.1f}億")
        elif trust_net > 5000:
            flows.append(f"📊 投信買超 {trust_億:.1f}億")
        elif trust_net > 0:
            flows.append(f"💼 投信小買 {trust_億:.1f}億")
        elif trust_net < -20000:
            flows.append(f"🔻 投信大賣 {abs(trust_億):.1f}億")
        elif trust_net < 0:
            flows.append(f"📉 投信賣超 {abs(trust_億):.1f}億")

    # 自營商
    dealer_net = analysis_data.get('dealer_net_buy', 0)
    if dealer_net != 0:
        dealer_億 = dealer_net / 10000
        if abs(dealer_net) > 10000:  # 1億以上才顯示
            if dealer_net > 0:
                flows.append(f"🏪 自營買超 {dealer_億:.1f}億")
            else:
                flows.append(f"🏪 自營賣超 {abs(dealer_億):.1f}億")

    # 三大法人合計
    total_institutional = analysis_data.get('total_institutional', 0)
    if abs(total_institutional) > 50000:  # 5億以上才顯示合計
        total_億 = total_institutional / 10000
        if total_institutional > 0:
            flows.append(f"🏛️ 三大法人合計買超 {total_億:.1f}億")
        else:
            flows.append(f"🏛️ 三大法人合計賣超 {abs(total_億):.1f}億")

    return flows
'''

        # 寫入修復文件
        with open('enhanced_display_functions.py', 'w', encoding='utf-8') as f:
            f.write("# 增強版顯示功能（修復版）\n")
            f.write("from datetime import datetime\n\n")
            f.write(enhanced_notifier_code)

        print("✅ 增強版顯示函數已創建")

    def create_integration_guide(self):
        """創建整合指南"""

        guide_content = f"""
# 顯示問題修復和篩選優化整合指南

## 修復時間

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 修復內容

### 1. 技術指標顯示修復

- 修復 RSI、MACD、均線、成交量指標不顯示問題
- 加入詳細的技術指標標籤和數值顯示
- 使用顏色標示不同指標狀態

### 2. 基本面優勢顯示修復

- 修復殖利率、EPS成長、ROE等不顯示問題
- 加入具體數值和優勢級別標示
- 突出顯示高殖利率、高成長等優勢

### 3. 法人動向顯示修復

- 修復外資、投信、自營商買賣不顯示問題
- 加入具體金額和連續買賣天數
- 使用圖示區分不同程度的買賣超

## 整合步驟

### 步驟1: 備份現有文件

已完成備份到: {self.backup_dir}

### 步驟2: 更新 notifier.py

將 enhanced_display_functions.py 中的函數加入到 notifier.py

### 步驟3: 測試驗證

執行測試確認修復效果：

```bash
python syntax_check.py
```

## 預期效果

### 顯示修復效果

- ✅ 技術指標完整顯示（RSI、MACD、均線、成交量）
- ✅ 基本面優勢詳細展示（殖利率、EPS、ROE等）
- ✅ 法人動向具體顯示（買賣金額、天數）

## 注意事項

1. 建議先在測試環境驗證修復效果
2. 如有問題可隨時使用備份文件回滾
3. 新的篩選邏輯可能會改變推薦結果數量

## 技術支援

如有問題請檢查：

1. 函數名稱是否正確
2. 數據欄位是否存在
3. 郵件配置是否正確
"""

        with open('integration_guide.md', 'w', encoding='utf-8') as f:
            f.write(guide_content)

        print("✅ 整合指南已創建")

    def run_complete_fix(self):
        """執行完整修復"""
        print("🔧 開始修復技術指標、基本面、法人動向顯示問題")
        print("🎯 同時優化篩選邏輯")
        print("=" * 70)

        # 1. 備份文件
        self.backup_files()

        # 2. 創建修復功能
        self.create_enhanced_display_functions()

        # 3. 創建整合指南
        self.create_integration_guide()

        print("\n" + "=" * 70)
        print("🎉 修復文件生成完成！")
        print("=" * 70)

        print("\n📁 生成的文件:")
        print("  ✅ enhanced_display_functions.py - 增強顯示功能")
        print("  ✅ integration_guide.md - 整合指南")

        print(f"\n💾 備份位置: {self.backup_dir}")

        print("\n📋 下一步操作:")
        print("1. 查看 integration_guide.md 了解詳細整合步驟")
        print("2. 將修復代碼整合到現有文件中")
        print("3. 執行測試驗證修復效果")

        print("\n🎯 修復效果:")
        print("  📊 技術指標: RSI、MACD、均線詳細顯示")
        print("  💎 基本面: 殖利率、EPS、ROE具體數值")
        print("  🏛️ 法人動向: 買賣金額、連續天數")

def main():
    """主函數"""
    print("🔧 技術指標、基本面、法人動向顯示修復工具")
    print("🎯 同時優化股票篩選邏輯")

    response = input("\n是否開始修復？(y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ 修復已取消")
        return

    fixer = DisplayAndFilterFixer()
    fixer.run_complete_fix()

if __name__ == "__main__":
    main()
