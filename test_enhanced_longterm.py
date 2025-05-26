"""
test_enhanced_longterm.py - 测试增强版长线推荐功能
验证EPS、法人买超、殖利率高者是否正确纳入长线推荐
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入增强版股票机器人
from enhanced_stock_bot import EnhancedStockBot
import notifier

def create_test_stocks():
    """创建测试股票数据，包含不同基本面特征的股票"""
    return [
        # 高殖利率股票
        {
            'code': '2882',
            'name': '國泰金',
            'close': 45.8,
            'change_percent': 0.5,
            'volume': 15000000,
            'trade_value': 687000000
        },
        # 高EPS成长股票
        {
            'code': '2454',
            'name': '聯發科',
            'close': 825.0,
            'change_percent': 1.2,
            'volume': 8000000,
            'trade_value': 6600000000
        },
        # 法人大买超股票
        {
            'code': '2330',
            'name': '台積電',
            'close': 638.0,
            'change_percent': -0.3,
            'volume': 25000000,
            'trade_value': 15950000000
        },
        # 综合基本面优异
        {
            'code': '2609',
            'name': '陽明',
            'close': 91.2,
            'change_percent': 2.1,
            'volume': 35000000,
            'trade_value': 3192000000
        },
        # 基本面一般的股票
        {
            'code': '6666',
            'name': '測試股A',
            'close': 50.0,
            'change_percent': 4.5,  # 短线技术面不错
            'volume': 10000000,
            'trade_value': 500000000
        },
        # 基本面较差的股票
        {
            'code': '7777',
            'name': '測試股B',
            'close': 30.0,
            'change_percent': -2.8,
            'volume': 5000000,
            'trade_value': 150000000
        },
        # 高ROE股票
        {
            'code': '1301',
            'name': '台塑',
            'close': 88.5,
            'change_percent': 0.8,
            'volume': 12000000,
            'trade_value': 1062000000
        },
        # 低本益比高殖利率
        {
            'code': '2615',
            'name': '萬海',
            'close': 132.8,
            'change_percent': 1.5,
            'volume': 20000000,
            'trade_value': 2656000000
        }
    ]

def test_enhanced_analysis():
    """测试增强分析功能"""
    print("=" * 60)
    print("测试增强版长线推荐功能")
    print("=" * 60)
    
    # 创建机器人实例
    bot = EnhancedStockBot()
    
    # 获取测试股票
    test_stocks = create_test_stocks()
    
    print(f"测试股票数量: {len(test_stocks)}")
    print("\n1. 单支股票分析测试:")
    print("-" * 40)
    
    all_analyses = []
    
    for stock in test_stocks:
        print(f"\n分析股票: {stock['code']} {stock['name']}")
        
        # 进行增强分析
        analysis = bot.analyze_stock_enhanced(stock, 'long_term')
        all_analyses.append(analysis)
        
        # 显示分析结果
        print(f"  基础评分: {analysis.get('base_score', 0):.1f}")
        print(f"  加权评分: {analysis.get('weighted_score', 0):.1f}")
        
        # 显示基本面信息
        if analysis.get('analysis_components', {}).get('fundamental'):
            print(f"  殖利率: {analysis.get('dividend_yield', 0):.1f}%")
            print(f"  EPS成长: {analysis.get('eps_growth', 0):.1f}%")
            print(f"  ROE: {analysis.get('roe', 0):.1f}%")
            print(f"  本益比: {analysis.get('pe_ratio', 0):.1f}倍")
            print(f"  基本面评分: {analysis.get('fundamental_score', 0):.1f}")
        
        # 显示法人资讯
        if analysis.get('analysis_components', {}).get('institutional'):
            foreign_net = analysis.get('foreign_net_buy', 0)
            trust_net = analysis.get('trust_net_buy', 0)
            consecutive = analysis.get('consecutive_buy_days', 0)
            print(f"  外资买卖: {foreign_net/10000:.1f}亿")
            print(f"  投信买卖: {trust_net/10000:.1f}亿")
            print(f"  连续买超: {consecutive}天")
            print(f"  法人评分: {analysis.get('institutional_score', 0):.1f}")
        
        print(f"  趋势判断: {analysis.get('trend', 'N/A')}")
        print(f"  操作建议: {analysis.get('suggestion', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("2. 推荐生成测试:")
    print("-" * 40)
    
    # 生成推荐
    recommendations = bot.generate_recommendations(all_analyses, 'afternoon_scan')
    
    # 显示短线推荐
    print(f"\n短线推荐 ({len(recommendations['short_term'])} 支):")
    for i, stock in enumerate(recommendations['short_term'], 1):
        analysis = stock['analysis']
        print(f"  {i}. {stock['code']} {stock['name']}")
        print(f"     评分: {analysis.get('weighted_score', 0):.1f}")
        print(f"     现价: {stock['current_price']} 元")
        print(f"     理由: {stock['reason'][:60]}...")
    
    # 显示长线推荐 - 重点检查
    print(f"\n💎 长线推荐 ({len(recommendations['long_term'])} 支):")
    for i, stock in enumerate(recommendations['long_term'], 1):
        analysis = stock['analysis']
        long_score = stock.get('long_term_score', 0)
        
        print(f"  {i}. {stock['code']} {stock['name']}")
        print(f"     基础评分: {analysis.get('weighted_score', 0):.1f}")
        print(f"     长线评分: {long_score:.1f}")
        print(f"     现价: {stock['current_price']} 元")
        
        # 显示基本面优势
        advantages = []
        dividend_yield = analysis.get('dividend_yield', 0)
        eps_growth = analysis.get('eps_growth', 0)
        roe = analysis.get('roe', 0)
        foreign_net = analysis.get('foreign_net_buy', 0)
        
        if dividend_yield > 4:
            advantages.append(f"高殖利率{dividend_yield:.1f}%")
        elif dividend_yield > 3:
            advantages.append(f"殖利率{dividend_yield:.1f}%")
        
        if eps_growth > 15:
            advantages.append(f"EPS高成长{eps_growth:.1f}%")
        elif eps_growth > 10:
            advantages.append(f"EPS成长{eps_growth:.1f}%")
        
        if roe > 15:
            advantages.append(f"ROE优异{roe:.1f}%")
        elif roe > 10:
            advantages.append(f"ROE良好{roe:.1f}%")
        
        if foreign_net > 20000:
            advantages.append(f"外资大买超{foreign_net/10000:.1f}亿")
        elif foreign_net > 10000:
            advantages.append(f"外资买超{foreign_net/10000:.1f}亿")
        
        if advantages:
            print(f"     优势: {' | '.join(advantages)}")
        
        print(f"     理由: {stock['reason'][:80]}...")
        print()
    
    # 显示弱势股
    print(f"\n⚠️ 风险警示 ({len(recommendations['weak_stocks'])} 支):")
    for i, stock in enumerate(recommendations['weak_stocks'], 1):
        analysis = stock['analysis']
        print(f"  {i}. {stock['code']} {stock['name']}")
        print(f"     评分: {analysis.get('weighted_score', 0):.1f}")
        print(f"     现价: {stock['current_price']} 元")
        print(f"     警示: {stock['alert_reason'][:60]}...")
    
    return recommendations

def test_notification_display():
    """测试通知显示效果"""
    print("\n" + "=" * 60)
    print("3. 通知显示测试:")
    print("-" * 40)
    
    # 创建测试数据
    test_recommendations = {
        "short_term": [
            {
                "code": "6666",
                "name": "測試股A",
                "current_price": 50.0,
                "reason": "今日大涨 4.5%，现价 50.0 元，MACD指标转强，站稳20日均线",
                "target_price": 53.0,
                "stop_loss": 48.5,
                "trade_value": 500000000,
                "analysis": {
                    "change_percent": 4.5,
                    "weighted_score": 5.2,
                    "technical_signals": {
                        "macd_bullish": True,
                        "ma20_bullish": True
                    },
                    "foreign_net_buy": 15000,
                    "analysis_components": {
                        "technical": True,
                        "institutional": True
                    }
                }
            }
        ],
        "long_term": [
            {
                "code": "2882",
                "name": "國泰金",
                "current_price": 45.8,
                "reason": "今日微涨 0.5%，现价 45.8 元，高殖利率达 5.8%，ROE良好 13.5%，外资买超",
                "target_price": 49.5,
                "stop_loss": 43.5,
                "trade_value": 687000000,
                "long_term_score": 4.2,
                "analysis": {
                    "change_percent": 0.5,
                    "weighted_score": 2.1,
                    "dividend_yield": 5.8,
                    "eps_growth": 6.2,
                    "roe": 13.5,
                    "pe_ratio": 11.3,
                    "foreign_net_buy": 25000,
                    "trust_net_buy": 8000,
                    "consecutive_buy_days": 4,
                    "fundamental_score": 6.8,
                    "institutional_score": 3.2,
                    "analysis_components": {
                        "fundamental": True,
                        "institutional": True
                    }
                }
            },
            {
                "code": "2454",
                "name": "聯發科",
                "current_price": 825.0,
                "reason": "今日上涨 1.2%，现价 825.0 元，EPS高成长 15.2%，ROE优异 19.3%，法人连续买超",
                "target_price": 890.0,
                "stop_loss": 783.8,
                "trade_value": 6600000000,
                "long_term_score": 3.8,
                "analysis": {
                    "change_percent": 1.2,
                    "weighted_score": 3.2,
                    "dividend_yield": 2.8,
                    "eps_growth": 15.2,
                    "roe": 19.3,
                    "pe_ratio": 16.8,
                    "foreign_net_buy": 45000,
                    "trust_net_buy": 12000,
                    "consecutive_buy_days": 6,
                    "fundamental_score": 8.1,
                    "institutional_score": 4.5,
                    "analysis_components": {
                        "fundamental": True,
                        "institutional": True
                    }
                }
            },
            {
                "code": "2609",
                "name": "陽明",
                "current_price": 91.2,
                "reason": "今日上涨 2.1%，现价 91.2 元，高殖利率达 6.8%，EPS高成长 25.6%，外资大幅买超",
                "target_price": 98.5,
                "stop_loss": 86.6,
                "trade_value": 3192000000,
                "long_term_score": 5.5,
                "analysis": {
                    "change_percent": 2.1,
                    "weighted_score": 4.8,
                    "dividend_yield": 6.8,
                    "eps_growth": 25.6,
                    "roe": 18.4,
                    "pe_ratio": 8.9,
                    "foreign_net_buy": 85000,
                    "trust_net_buy": 15000,
                    "consecutive_buy_days": 8,
                    "fundamental_score": 9.2,
                    "institutional_score": 5.8,
                    "analysis_components": {
                        "fundamental": True,
                        "institutional": True
                    }
                }
            }
        ],
        "weak_stocks": [
            {
                "code": "7777",
                "name": "測試股B",
                "current_price": 30.0,
                "alert_reason": "今日下跌 2.8%，现价 30.0 元，外资大幅卖超，技术面转弱",
                "trade_value": 150000000,
                "analysis": {
                    "change_percent": -2.8,
                    "foreign_net_buy": -35000
                }
            }
        ]
    }
    
    print("发送测试通知...")
    
    # 初始化通知系统
    notifier.init()
    
    # 发送测试通知
    notifier.send_combined_recommendations(test_recommendations, "增强长线推荐测试")
    
    print("✅ 测试通知已发送！")
    print("\n请检查您的邮箱，确认以下内容：")
    print("1. 长线推荐部分是否重点显示基本面信息")
    print("2. EPS成长率、殖利率、ROE是否正确显示")
    print("3. 法人买超信息是否详细显示")
    print("4. HTML格式是否美观易读")
    print("5. 短线和长线推荐是否有明确区分")

def analyze_longterm_criteria():
    """分析长线推荐的筛选标准"""
    print("\n" + "=" * 60)
    print("4. 长线推荐标准分析:")
    print("-" * 40)
    
    print("增强后的长线推荐标准：")
    print("基础条件：")
    print("  • 加权评分在 -1 到 5 之间")
    print("  • 成交金额 > 5000万")
    
    print("\n加分项目：")
    print("  • 殖利率 > 4%：+2分")
    print("  • 殖利率 > 3%：+1分")
    print("  • EPS成长 > 15%：+2分")
    print("  • EPS成长 > 10%：+1分")
    print("  • EPS成长 > 5%：+0.5分")
    print("  • ROE > 15%：+1.5分")
    print("  • ROE > 10%：+1分")
    print("  • 本益比 < 15：+1分")
    print("  • 外资买超 > 5亿：+2分")
    print("  • 外资买超 > 2亿：+1.5分")
    print("  • 外资买超 > 1亿：+1分")
    print("  • 投信买超 > 1亿：+1分")
    print("  • 投信买超 > 5000万：+0.5分")
    print("  • 连续买超 >= 3天：+1分")
    
    print("\n最终筛选：")
    print("  • 长线评分 >= 1分的股票进入长线推荐")
    print("  • 按长线评分排序，取前N名")
    
    print("\n权重配置（长线分析）：")
    print("  • 基础分数权重：0.4（降低）")
    print("  • 技术面权重：0.3（降低）")
    print("  • 基本面权重：1.2（大幅提高）")
    print("  • 法人买卖权重：0.8（提高）")

def main():
    """主函数"""
    print("增强版长线推荐功能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 测试增强分析
        recommendations = test_enhanced_analysis()
        
        # 2. 分析筛选标准
        analyze_longterm_criteria()
        
        # 3. 测试通知显示
        test_notification_display()
        
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        short_count = len(recommendations['short_term'])
        long_count = len(recommendations['long_term'])
        weak_count = len(recommendations['weak_stocks'])
        
        print(f"推荐结果统计:")
        print(f"  短线推荐: {short_count} 支")
        print(f"  长线推荐: {long_count} 支")
        print(f"  风险警示: {weak_count} 支")
        
        print(f"\n增强功能验证:")
        
        # 检查长线推荐是否包含高基本面股票
        high_fundamental_count = 0
        for stock in recommendations['long_term']:
            analysis = stock['analysis']
            dividend_yield = analysis.get('dividend_yield', 0)
            eps_growth = analysis.get('eps_growth', 0)
            foreign_net = analysis.get('foreign_net_buy', 0)
            
            if dividend_yield > 4 or eps_growth > 15 or foreign_net > 20000:
                high_fundamental_count += 1
        
        print(f"  ✅ 高基本面股票在长线推荐中占比: {high_fundamental_count}/{long_count}")
        
        if high_fundamental_count > 0:
            print("  ✅ 长线推荐成功纳入EPS高成长/高殖利率/法人大买超股票")
        else:
            print("  ⚠️ 长线推荐中高基本面股票较少，可能需要调整参数")
        
        print(f"\n主要改进:")
        print(f"  1. 基本面权重从0.5提升到1.2")
        print(f"  2. 法人买卖权重从0.4提升到0.8") 
        print(f"  3. 长线评分系统加入基本面加分机制")
        print(f"  4. 通知系统重点显示基本面信息")
        print(f"  5. HTML邮件格式全面优化")
        
        print(f"\n✅ 增强版长线推荐功能测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
