import os, json, requests, pandas as pd
from data_fetcher import get_all_market_data
from html_generator import generate_report

def get_ai_analysis(name, info):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    if not api_key: return None

    prompt = f"分析 A 股 {name} 數據: {info}。請嚴格返回 JSON: {{'stock_name', 'stock_code', 'price', 'change', 'insights', 'buy_point', 'stop_loss'}}"
    
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={{"Authorization": f"Bearer {{api_key}}", "Content-Type": "application/json"}},
            json={{"model": "gpt-4o-mini", "messages": [{{"role": "user", "content": prompt}}], "response_format": {{"type": "json_object"}}}},
            timeout=45)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    print("🚀 啟動量化終端防封禁模式...")
    df = get_all_market_data()
    if df.empty: return

    # 策略：按成交額選取前 12 名最活躍個股
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    top_df = df.sort_values(by='amount', ascending=False).head(12)

    results = []
    for _, row in top_df.iterrows():
        name = row['name']
        print(f"🤖 分析中: {name}...")
        ai_data = get_ai_analysis(name, row.to_string())
        
        if not ai_data:
            ai_data = {
                "stock_name": name, "stock_code": row['code'], "price": row['price'],
                "change": row['change'], "insights": "⚠️ AI 分析暫時擁堵，技術面顯示該股成交極其活躍，建議關注支撐位。",
                "buy_point": "盤中觀察", "stop_loss": "參考 5 日線"
            }
        results.append(ai_data)

    generate_report(results)
    print("✅ 看板已更新")

if __name__ == "__main__":
    main()




