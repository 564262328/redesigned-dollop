import os
import json
import requests
import pandas as pd
from data_fetcher import fetch_multi_source_stock_data
from html_generator import generate_report

def get_deepseek_analysis(stock_name, stock_info):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key: 
        print("⚠️ 未发现 API KEY，将跳过 AI 分析")
        return None
    
    url = "https://api.deepseek.com"
    # 在 f-string 内部，如果要输出大括号 {}，必须用双大括号 {{}}
    prompt = f"分析股票 {stock_name} 的数据: {stock_info}。请严格返回 JSON 格式，包含字段: stock_name, stock_code, price, change, insights, buy_point, stop_loss。"
    
    try:
        response = requests.post(url, 
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }, timeout=30)
        return json.loads(response.json()['choices']['message']['content'])
    except Exception as e:
        print(f"❌ AI 分析出错: {e}")
        return None

def main():
    print("🚀 启动量化终端...")
    df = fetch_multi_source_stock_data()
    if df is None or df.empty:
        print("❌ 未抓取到有效数据")
        return

    ai_results = []
    # 选取前 4 只股票进行展示
    for _, row in df.head(4).iterrows():
        name = row.get('名称', '未知')
        print(f"正在处理: {name}...")
        
        # 尝试调用 AI 分析
        result = get_deepseek_analysis(name, row.to_string())
        
        # 如果 AI 失败或没有 KEY，使用基础数据填充防止页面空白
        if not result:
            result = {
                'stock_name': name,
                'stock_code': str(row.get('代码', '000000')),
                'price': str(row.get('最新价', '0.00')),
                'change': f"{row.get('涨跌幅', '0')}%",
                'insights': "技术面显示近期波动较大，建议关注支撑位表现。",
                'buy_point': "观察中",
                'stop_loss': "止损参考5日线"
            }
        ai_results.append(result)

    if ai_results:
        generate_report(ai_results)
        print(f"✅ 任务完成，成功处理 {len(ai_results)} 只股票")

if __name__ == "__main__":
    main()


