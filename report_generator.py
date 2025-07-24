"""
report_generator.py - 股票分析報告生成器（增強版）
加入現價和漲跌百分比顯示功能
"""
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

# 配置日誌
logger = logging.getLogger(__name__)

class ReportGenerator:
    """報告生成器"""
    
    def __init__(self, output_dir: str = 'reports'):
        """
        初始化報告生成器
        
        參數:
        - output_dir: 報告輸出目錄
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 報告模板
        self.time_slot_templates = {
            'morning_scan': {
                'title': '早盤分析分析報告',
                'intro': '今日開盤前分析已完成，以下是最具潛力的投資標的：\n\n市場觀望氣氛濃厚，建議以價值投資思維布局。'
            },
            'mid_morning_scan': {
                'title': '盤中掃描分析報告',
                'intro': '盤中分析已完成，以下是值得關注的個股：\n\n大盤走勢偏多，留意強勢股表現。'
            },
            'mid_day_scan': {
                'title': '午間掃描分析報告',
                'intro': '午間分析已完成，以下是午後值得留意的標的：\n\n午後行情波動加大，注意風險控制。'
            },
            'afternoon_scan': {
                'title': '盤後掃描分析報告',
                'intro': '早安！今天市場開盤前，這些股票值得您特別關注：\n\n今日大盤呈現盤整格局，可選擇性布局強勢個股。'
            },
            'weekly_summary': {
                'title': '週末總結報告',
                'intro': '本週市場總結已完成，以下是下週值得關注的投資機會：\n\n經過本週震盪，市場醞釀新的方向。'
            }
        }
    
    def generate_email_report(self, 
                            time_slot: str,
                            analysis_results: List[Dict],
                            criteria: Dict = None,
                            max_stocks: int = 10) -> str:
        """
        生成電子郵件格式的報告
        
        參數:
        - time_slot: 時段名稱
        - analysis_results: 分析結果列表
        - criteria: 篩選條件（可選）
        - max_stocks: 最多顯示的股票數量
        
        返回:
        - 報告內容字符串
        """
        # 獲取模板
        template = self.time_slot_templates.get(time_slot, self.time_slot_templates['morning_scan'])
        
        # 生成報告標題
        date_str = datetime.now().strftime('%Y/%m/%d')
        report_title = f"📊 {date_str} {template['title']}"
        
        # 篩選和排序股票
        selected_stocks = self._select_top_stocks(analysis_results, criteria, max_stocks)
        
        # 生成報告內容
        report = f"{report_title}\n\n"
        report += f"{template['intro']}\n\n"
        
        # 生成短線推薦部分
        report += self._generate_recommendations_section(selected_stocks)
        
        # 生成市場觀察部分
        report += self._generate_market_observation(analysis_results)
        
        # 生成風險提示
        report += self._generate_risk_warning()
        
        return report
    
    def _select_top_stocks(self, 
                         analysis_results: List[Dict], 
                         criteria: Dict = None,
                         max_stocks: int = 10) -> List[Dict]:
        """選擇最優股票"""
        # 先根據評分排序
        sorted_stocks = sorted(analysis_results, key=lambda x: x['score'], reverse=True)
        
        # 如果有額外條件，進行篩選
        if criteria:
            filtered = []
            for stock in sorted_stocks:
                # 檢查是否有必要的信號或形態
                if criteria.get('required_signals'):
                    if any(signal in stock['signals'] for signal in criteria['required_signals']):
                        filtered.append(stock)
                elif criteria.get('required_patterns'):
                    if any(pattern in stock['patterns'] for pattern in criteria['required_patterns']):
                        filtered.append(stock)
                else:
                    filtered.append(stock)
            
            sorted_stocks = filtered
        
        # 返回前N支
        return sorted_stocks[:max_stocks]
    
    def _generate_recommendations_section(self, stocks: List[Dict]) -> str:
        """生成推薦股票部分"""
        if not stocks:
            return "【短線推薦】\n\n目前暫無符合條件的推薦標的。\n\n"
        
        section = "【短線推薦】\n\n"
        
        for stock in stocks:
            # 股票基本信息（加入現價和漲跌幅）
            section += f"📈 {stock['code']} {stock['name']}\n"
            
            # 顯示現價和漲跌幅
            change_symbol = "📈" if stock['change'] >= 0 else "📉"
            change_prefix = "+" if stock['change'] >= 0 else ""
            section += f"現價: {stock['close']:.1f} | 漲跌: {change_prefix}{stock['change_percent']:.1f}%\n"
            
            # 推薦理由
            section += f"推薦理由: "
            reasons = []
            
            # 根據形態生成理由
            if '突破20日均線' in stock['patterns']:
                reasons.append("突破關鍵均線")
            if '成交量突破' in stock['patterns']:
                reasons.append("成交量放大")
            if 'MACD金叉' in stock['patterns']:
                reasons.append("技術面轉佳")
            if 'RSI超賣' in stock['patterns']:
                reasons.append("超賣反彈")
            
            # 根據信號生成理由
            if '強勢突破信號' in stock['signals']:
                reasons.append("表現強勢")
            if '買入信號' in stock['signals']:
                reasons.append("技術面買點")
            
            # 如果沒有特定理由，根據技術指標生成
            if not reasons:
                if stock['indicators'].get('volume_ratio', 0) > 1.5:
                    reasons.append("成交活躍")
                if stock['score'] > 70:
                    reasons.append("綜合評分優異")
            
            section += "、".join(reasons) if reasons else "技術面向好"
            section += "\n"
            
            # 關鍵指標
            if stock['indicators']:
                indicators_text = []
                
                # RSI
                if 'rsi' in stock['indicators']:
                    rsi_value = stock['indicators']['rsi']
                    if rsi_value < 30:
                        indicators_text.append(f"超賣區(RSI:{rsi_value:.1f})")
                    elif rsi_value > 70:
                        indicators_text.append(f"超買區(RSI:{rsi_value:.1f})")
                
                # 成交量比率
                if 'volume_ratio' in stock['indicators']:
                    vol_ratio = stock['indicators']['volume_ratio']
                    if vol_ratio > 2:
                        indicators_text.append(f"爆量({vol_ratio:.1f}倍)")
                    elif vol_ratio > 1.5:
                        indicators_text.append(f"放量({vol_ratio:.1f}倍)")
                
                # 均線位置
                if all(k in stock['indicators'] for k in ['ma5', 'ma20']):
                    current_price = stock['close']
                    ma5 = stock['indicators']['ma5']
                    ma20 = stock['indicators']['ma20']
                    
                    if current_price > ma5 > ma20:
                        indicators_text.append("多頭排列")
                    elif current_price < ma5 < ma20:
                        indicators_text.append("空頭排列")
                
                if indicators_text:
                    section += f"📍 {' | '.join(indicators_text)}\n"
            
            section += "\n"
        
        return section
    
    def _generate_market_observation(self, all_results: List[Dict]) -> str:
        """生成市場觀察部分"""
        section = "【市場觀察】\n\n"
        
        # 統計上漲下跌家數
        up_count = sum(1 for s in all_results if s.get('change_percent', 0) > 0)
        down_count = sum(1 for s in all_results if s.get('change_percent', 0) < 0)
        unchanged_count = len(all_results) - up_count - down_count
        
        section += f"📊 今日統計：上漲 {up_count} 家 | 下跌 {down_count} 家 | 平盤 {unchanged_count} 家\n\n"
        
        # 找出漲幅前三
        top_gainers = sorted(all_results, key=lambda x: x.get('change_percent', 0), reverse=True)[:3]
        if top_gainers:
            section += "🔥 漲幅前三：\n"
            for stock in top_gainers:
                section += f"   {stock['code']} {stock['name']} +{stock['change_percent']:.1f}%\n"
            section += "\n"
        
        # 找出跌幅前三
        top_losers = sorted(all_results, key=lambda x: x.get('change_percent', 0))[:3]
        if top_losers and top_losers[0].get('change_percent', 0) < 0:
            section += "💧 跌幅前三：\n"
            for stock in top_losers[:3]:
                if stock.get('change_percent', 0) < 0:
                    section += f"   {stock['code']} {stock['name']} {stock['change_percent']:.1f}%\n"
            section += "\n"
        
        # 成交量異常股票
        high_volume_stocks = [s for s in all_results if s['indicators'].get('volume_ratio', 0) > 3]
        if high_volume_stocks:
            section += "📢 成交量異常放大：\n"
            for stock in high_volume_stocks[:5]:
                vol_ratio = stock['indicators']['volume_ratio']
                section += f"   {stock['code']} {stock['name']} (成交量 {vol_ratio:.1f} 倍)\n"
            section += "\n"
        
        return section
    
    def _generate_risk_warning(self) -> str:
        """生成風險提示"""
        warning = "\n【風險提示】\n\n"
        warning += "⚠️ 本報告僅供參考，不構成投資建議\n"
        warning += "⚠️ 股市有風險，投資需謹慎\n"
        warning += "⚠️ 建議設定停損點，控制投資風險\n\n"
        warning += "祝您投資順利！💰\n"
        
        return warning
    
    def save_report(self, report_content: str, time_slot: str) -> str:
        """
        保存報告到文件
        
        參數:
        - report_content: 報告內容
        - time_slot: 時段名稱
        
        返回:
        - 報告文件路徑
        """
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{time_slot}_report_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        # 保存報告
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"報告已保存至: {filepath}")
        
        return filepath
    
    def generate_html_report(self, 
                           time_slot: str,
                           analysis_results: List[Dict],
                           criteria: Dict = None,
                           max_stocks: int = 10) -> str:
        """
        生成HTML格式的報告
        
        參數:
        - time_slot: 時段名稱
        - analysis_results: 分析結果列表
        - criteria: 篩選條件（可選）
        - max_stocks: 最多顯示的股票數量
        
        返回:
        - HTML報告內容
        """
        # 獲取模板
        template = self.time_slot_templates.get(time_slot, self.time_slot_templates['morning_scan'])
        
        # 篩選股票
        selected_stocks = self._select_top_stocks(analysis_results, criteria, max_stocks)
        
        # 生成HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{template['title']} - {datetime.now().strftime('%Y/%m/%d')}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }}
                .stock-card {{
                    background-color: white;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .stock-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                }}
                .stock-name {{
                    font-size: 18px;
                    font-weight: bold;
                }}
                .stock-price {{
                    font-size: 16px;
                }}
                .positive {{
                    color: #e74c3c;
                }}
                .negative {{
                    color: #27ae60;
                }}
                .indicators {{
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                    margin-top: 10px;
                }}
                .indicator-tag {{
                    background-color: #ecf0f1;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 12px;
                }}
                .section {{
                    margin-bottom: 30px;
                }}
                .warning {{
                    background-color: #f39c12;
                    color: white;
                    padding: 15px;
                    border-radius: 10px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{template['title']}</h1>
                <p>{datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
            </div>
            
            <div class="section">
                <p>{template['intro']}</p>
            </div>
            
            <div class="section">
                <h2>📊 推薦標的</h2>
        """
        
        # 加入推薦股票
        for stock in selected_stocks:
            change_class = "positive" if stock['change_percent'] >= 0 else "negative"
            change_symbol = "+" if stock['change_percent'] >= 0 else ""
            
            html += f"""
                <div class="stock-card">
                    <div class="stock-header">
                        <div class="stock-name">{stock['code']} {stock['name']}</div>
                        <div class="stock-price">
                            <span>現價: {stock['close']:.1f}</span>
                            <span class="{change_class}"> {change_symbol}{stock['change_percent']:.1f}%</span>
                        </div>
                    </div>
                    <div class="stock-info">
                        <p><strong>推薦理由:</strong> {self._get_recommendation_reason(stock)}</p>
                        <div class="indicators">
            """
            
            # 加入技術指標標籤
            if stock['indicators'].get('rsi'):
                html += f'<span class="indicator-tag">RSI: {stock["indicators"]["rsi"]:.1f}</span>'
            
            if stock['indicators'].get('volume_ratio', 0) > 1.5:
                html += f'<span class="indicator-tag">成交量: {stock["indicators"]["volume_ratio"]:.1f}倍</span>'
            
            for pattern in stock['patterns'][:3]:  # 最多顯示3個形態
                html += f'<span class="indicator-tag">{pattern}</span>'
            
            html += """
                        </div>
                    </div>
                </div>
            """
        
        # 加入市場統計
        up_count = sum(1 for s in analysis_results if s.get('change_percent', 0) > 0)
        down_count = sum(1 for s in analysis_results if s.get('change_percent', 0) < 0)
        
        html += f"""
            </div>
            
            <div class="section">
                <h2>📈 市場概況</h2>
                <p>今日統計：上漲 {up_count} 家 | 下跌 {down_count} 家</p>
            </div>
            
            <div class="warning">
                <h3>⚠️ 風險提示</h3>
                <p>本報告僅供參考，不構成投資建議。股市有風險，投資需謹慎。</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_recommendation_reason(self, stock: Dict) -> str:
        """獲取推薦理由"""
        reasons = []
        
        # 根據形態
        if '突破20日均線' in stock['patterns']:
            reasons.append("突破關鍵均線")
        if '成交量突破' in stock['patterns']:
            reasons.append("成交量放大")
        if 'MACD金叉' in stock['patterns']:
            reasons.append("技術面轉佳")
        
        # 根據信號
        if '強勢突破信號' in stock['signals']:
            reasons.append("表現強勢")
        if '買入信號' in stock['signals']:
            reasons.append("技術買點")
        
        # 如果沒有特定理由
        if not reasons:
            if stock['score'] > 70:
                reasons.append("綜合評分優異")
            else:
                reasons.append("技術面向好")
        
        return "、".join(reasons)

# 測試代碼
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 創建報告生成器
    generator = ReportGenerator()
    
    # 測試數據
    test_results = [
        {
            'code': '2609',
            'name': '陽明',
            'close': 91.2,
            'change': 3.5,
            'change_percent': 4.1,
            'volume': 50000000,
            'trade_value': 4560000000,
            'signals': ['強勢突破信號'],
            'patterns': ['突破20日均線', '成交量突破'],
            'indicators': {
                'rsi': 65.5,
                'volume_ratio': 2.3,
                'ma5': 88.5,
                'ma20': 85.2
            },
            'score': 78
        },
        {
            'code': '2615',
            'name': '萬海',
            'close': 132.8,
            'change': 11.2,
            'change_percent': 9.1,
            'volume': 30000000,
            'trade_value': 3984000000,
            'signals': ['強勢上漲信號'],
            'patterns': ['成交量突破', 'MACD金叉'],
            'indicators': {
                'rsi': 72.3,
                'volume_ratio': 3.5,
                'ma5': 125.6,
                'ma20': 118.9
            },
            'score': 85
        },
        {
            'code': '2368',
            'name': '金像電',
            'close': 262.5,
            'change': 6.0,
            'change_percent': 2.4,
            'volume': 15000000,
            'trade_value': 3937500000,
            'signals': [],
            'patterns': ['突破60日均線'],
            'indicators': {
                'rsi': 58.7,
                'volume_ratio': 1.8,
                'ma5': 258.3,
                'ma20': 252.1
            },
            'score': 65
        }
    ]
    
    # 生成早盤報告
    report = generator.generate_email_report('morning_scan', test_results, max_stocks=3)
    print(report)
    
    # 保存報告
    filepath = generator.save_report(report, 'morning_scan')
    print(f"\n報告已保存至: {filepath}")
    
    # 生成HTML報告
    html_report = generator.generate_html_report('morning_scan', test_results, max_stocks=3)
    html_path = filepath.replace('.txt', '.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    print(f"HTML報告已保存至: {html_path}")
