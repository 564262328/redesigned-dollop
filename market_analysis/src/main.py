import os, json, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info, market_context):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com")
    if not api_key: return None

    prompt = f"""
    【市场大环境】：{market_context}
    【个股数据】：{info}
    你是资深价值派量化员。分析【{name}】。
    1. 严禁寻妖，侧重估值与筹码。2. 若大盘差，强调风控。
    请返回 JSON: {{'stock_name', 'stock_code', 'price', 'change', 'insights', 'buy_point', 'stop_loss'}}
    """
    
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}, "temperature": 0.2},
            timeout=60)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    print("🚀 QUANT 终端 V15.7 启动...")
    dc = MarketDataCenter()
    
    indices = dc.get_market_indices()
    df, source_name = dc.get_all_market_data()
    industry_data = dc.get_industry_heatmap() # 之前这里会报错，现在已修复
    
    if df.empty: 
        print("❌ 致命错误：未能获取任何行情数据")
        return

    mkt_summary = " | ".join([f"{i['name']}:{i['change']}%" for i in indices])
    new_count, total_count = dc.sync_and_get_new(df)
    
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        stock_industry = "其他"
        for ind in industry_data:
            if code in ind['symbols']:
                stock_industry = ind['name']
                break
        
        print(f"🤖 智能分析中: {row['name']}...")
        chip_info = dc.get_chip_data(code)
        combined = {**row.to_dict(), **chip_info, "industry": stock_industry}
        
        data = get_ai_analysis(row['name'], str(combined), mkt_summary)
        if not data:
            data = {"stock_name": row['name'], "stock_code": code, "price": row['price'], "change": row['change'], 
                    "insights": "⚠️ AI 接口响应超时。技术观察：资金面活跃，建议结合大盘趋势参考成本位。", "buy_point": "价值区", "stop_loss": "止损位"}
        
        data.update(combined)
        ai_results.append(data)

    generate_report(ai_results, new_count, total_count, source_name, industry_data, indices)
    print(f"✅ 终端部署成功。数据源: {source_name}")

if __name__ == "__main__":
    main()



















