import os, json, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com")
    if not api_key: return None

    prompt = f"分析 A 股 {name} 數據: {info}。請嚴格返回 JSON: {{'stock_name', 'stock_code', 'price', 'change', 'insights', 'buy_point', 'stop_loss'}}"
    
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={{"Authorization": f"Bearer {{api_key}}", "Content-Type": "application/json"}},
            json={{"model": "gpt-4o-mini", "messages": [{{"role": "user", "content": prompt}}], "response_format": {{"type": "json_object"}}, "temperature": 0.3}},
            timeout=60)
        return json.loads(res.json()['choices']['message']['content'])
    except:
        return None

def main():
    print("🚀 QUANT 終端啟動...")
    dc = MarketDataCenter()
    df = dc.get_all_market_data()
    if df.empty: return

    # 同步增量數據
    new_count, total_count = dc.sync_and_get_new(df)

    # 篩選熱度前 12 名
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        name = row['name']
        print(f"🤖 AI 分析中: {{name}}...")
        data = get_ai_analysis(name, row.to_string())
        if not data:
            data = {{"stock_name": name, "stock_code": row['code'], "price": row['price'], "change": row['change'], 
                    "insights": "⚠️ AI 分析通道擁堵。技術觀察：該股資金流向活躍，建議關注支撐位表現。", 
                    "buy_point": "盤中觀察", "stop_loss": "5日線"}}
        ai_results.append(data)

    generate_report(ai_results, new_count, total_count)
    print(f"✅ 任務完成！今日發現新代碼: {{new_count}}")

if __name__ == "__main__":
    main()









