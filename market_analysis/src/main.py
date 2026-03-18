import os
import json
import requests
import pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info):
    """調用 AIHubMix / ChatGPT 進行深度分析"""
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    if not api_key: return None

    prompt = f"分析 A 股 {name} 數據: {info}。請嚴格返回 JSON: {{'stock_name', 'stock_code', 'price', 'change', 'insights', 'buy_point', 'stop_loss'}}"
    
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}},
            timeout=45)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    print("🚀 QUANT 終端 V14.6 啟動 (增量數據模式)...")
    dc = MarketDataCenter()
    
    # 1. 獲取全量數據
    df = dc.get_all_market_data()
    if df.empty:
        print("❌ 無法獲取行情數據")
        return

    # 2. 進行增量同步並獲取統計數字 (這是關鍵！)
    # 這裡的 sync_and_get_new 會返回 (今日新增數, 市場總數)
    new_count, total_count = dc.sync_and_get_new(df)

    # 3. 篩選熱點 (例如成交額前 12 隻)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        name = row['name']
        print(f"🤖 AI 分析中: {name}...")
        data = get_ai_analysis(name, row.to_string())
        
        if not data:
            data = {
                "stock_name": name, "stock_code": row['code'], "price": row['price'], "change": row['change'], 
                "insights": "⚠️ AI 擁堵。該股今日成交活躍，建議關注支撐位。", 
                "buy_point": "盤中觀察", "stop_loss": "5日線"
            }
        ai_results.append(data)

    # 4. 調用生成器 (傳入三個參數：列表、新增數、總數)
    # ---------------------------------------------------------
    generate_report(ai_results, new_count, total_count)
    # ---------------------------------------------------------
    
    print(f"✅ 成功生成看板！今日新增: {new_count}, 總數: {total_count}")

if __name__ == "__main__":
    main()







