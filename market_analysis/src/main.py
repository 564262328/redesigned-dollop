# market_analysis/src/main.py

import json
from data_fetcher import fetch_multi_source_stock_data
from html_generator import generate_report
# 假设你的 AI 分析函数在单独的文件或就在这里
# from ai_analyzer import get_ai_analysis 

def main():
    # 1. 抓取数据
    df = fetch_multi_source_stock_data()
    
    # 2. 假设你有一组要分析的股票列表
    # 这里需要把你 AI 分析后的结果存进一个列表里
    ai_analyzed_data_list = []
    
    # 示例：循环分析抓取到的前 4 只股票
    for index, row in df.head(4).iterrows():
        # 这里调用你之前的 DeepSeek AI 分析逻辑
        # ai_result = get_ai_analysis(row['名称'], row.to_string()) 
        
        # 模拟 AI 返回的数据结构（实际应使用 AI 返回的 json.loads 结果）
        stock_result = {
            'name': row.get('名称', '未知'),
            'code': row.get('代码', '000000'),
            'price': row.get('最新价', '0.00'),
            'change': f"+{row.get('涨跌幅', '0')}%",
            'insights': "AI 分析建议：当前处于支撑位上方，建议分批建仓。",
            'buy_point': "10.50",
            'stop_loss': "9.80"
        }
        ai_analyzed_data_list.append(stock_result)

    # ---------------------------------------------------------
    # 核心步骤：这就是你要加的那一行！
    # 它会将上面这个列表传给 html_generator.py 里的函数
    # ---------------------------------------------------------
    if ai_analyzed_data_list:
        generate_report(ai_analyzed_data_list) 
        print(f"✅ 成功渲染了 {len(ai_analyzed_data_list)} 只股票的卡片")
    else:
        print("❌ 列表为空，没有数据可以渲染")

if __name__ == "__main__":
    main()

