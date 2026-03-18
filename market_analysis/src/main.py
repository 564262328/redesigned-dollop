import os
import json
import requests
import pandas as pd
from data_fetcher import fetch_multi_source_stock_data
from html_generator import generate_report

def get_deepseek_analysis(stock_name, stock_info):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key: return None
    
    url = "https://api.deepseek.com"
    prompt = f"分析股票 {stock_name} 的数据: {stock_info}。返回JSON: stock_name, stock_code, price, change, insights, buy_point, stop_loss。"
    
    try:
        response = requests.post(url, 
            headers={{"Authorization": f"Bearer {{api_key}}", "Content-Type": "application/json"}},
            json={{
                "model": "deepseek-chat",
                "messages": [{{"role": "user", "content": prompt}}],
                "response_format": {{"type": "json_object"}}
            }}, timeout=30)
        return json.loads(response.json()['choices'][0]['message']['content'])
    except:
        return None

def main():
    print("🚀 启动量化终端...")
    df = fetch_multi_source_stock_data()
    if df.empty: return

    ai_results = []
    # 选取前4只热门股票进行分析
    for _, row in df.head(4).iterrows():
        name = row.get('名称', '未知')
        print(f"分析中: {{name}}...")
        # 实际使用时开启 AI 调用
        # result = get_deepseek_analysis(name, row.to_string())
        
        # 暂时使用模拟数据进行排版测试
        result = {{
            'stock_name': name,
            'stock_code': row.get('代码', '000000'),
            'price': row.get('最新价', '0.00'),
            'change': f"{{row.get('涨跌幅', '0')}}%",
            'insights': "技术面显示资金持续流入，均线多头排列，短期看涨。",
            'buy_point': "支撑位介入",
            'stop_loss': "破5日线离场"
        }}
        ai_results.append(result)

    if ai_results:
        generate_report(ai_results)

if __name__ == "__main__":
    main()

