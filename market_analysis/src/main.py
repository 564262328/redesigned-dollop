import os, json, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    if not api_key: return None

    prompt = f"分析 A 股 {name} 數據及其籌碼指標: {info}。請嚴格返回 JSON: {{'stock_name', 'stock_code', 'price', 'change', 'insights', 'buy_point', 'stop_loss'}}"
    
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}},
            timeout=60)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    print("🚀 QUANT 終端 V14.8 啟動...")
    dc = MarketDataCenter()
    
    # 1. 抓取行情与行业热力
    df, source_name = dc.get_all_market_data()
    industry_data = dc.get_industry_heatmap()
    
    if df.empty: return

    new_count, total_count = dc.sync_and_get_new(df)
    
    # 2. 筛选活跃个股分析
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        name = row['name']
        print(f"🤖 分析中: {name}...")
        chip_info = dc.get_chip_data(row['code'])
        combined_info = {**row.to_dict(), **chip_info}
        
        data = get_ai_analysis(name, str(combined_info))
        if not data:
            data = {"stock_name": name, "stock_code": row['code'], "price": row['price'], "change": row['change'], 
                    "insights": "⚠️ AI 分析通道擁堵。建議關注籌碼獲利比例與支撐位。", "buy_point": "盤中觀察", "stop_loss": "5日線"}
        
        data.update(combined_info)
        ai_results.append(data)

    generate_report(ai_results, new_count, total_count, source_name, industry_data)
    print(f"✅ 任务完成！来源: {source_name}")

if __name__ == "__main__":
    main()












