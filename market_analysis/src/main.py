import os, json, time, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com").rstrip('/')
    if not api_key: return None
    try:
        res = requests.post(f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini", 
                "messages": [{"role": "user", "content": f"分析股票 {name}: {info}。請以 JSON 輸出繁體中文: insights, buy_point, trend_prediction。"}],
                "response_format": {"type": "json_object"}, "temperature": 0.2
            }, timeout=45)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(src_dir))
    output_path = os.path.join(project_root, "index.html")
    cache_path = os.path.join(project_root, "market_cache.json")

    dc = MarketDataCenter(cache_file=cache_path)
    df, source = dc.fetch_all_markets()
    
    if df.empty:
        print("❌ 無可用數據，終止分析。")
        return

    # --- 🎯 安全採樣邏輯修復 ---
    # 1. 優先取漲幅前 10 (如果不足 10 則取全部)
    top_10 = df.sort_values(by='change', ascending=False).head(10)
    
    # 2. 獲取剩餘可選的股票 (排除已在 top_10 中的)
    remaining_pool = df[~df['code'].isin(top_10['code'])]
    
    # 3. 從剩餘池中隨機取，最多取 10 檔 (確保 n >= 0)
    sample_size = min(10, len(remaining_pool))
    if sample_size > 0:
        others = remaining_pool.sample(n=sample_size)
        target_df = pd.concat([top_10, others]).head(20)
    else:
        target_df = top_10

    ai_results = []
    print(f"🤖 正在分析 {len(target_df)} 檔標的...")
    for _, row in target_df.iterrows():
        chip = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **chip}
        analysis = get_ai_analysis(row['name'], str(combined))
        if not analysis:
            analysis = {"insights": "數據正在計算中...", "buy_point": "觀望", "trend_prediction": "盤整"}
        analysis.update(combined)
        ai_results.append(analysis)
        time.sleep(0.3)

    indices = dc.get_market_indices()
    if not indices:
        indices = [{"名稱": "多市場監控系統", "最新價": "Online", "漲跌幅": "0"}]
        
    generate_report(ai_results, 0, len(df), source, [], indices, output_path, {"Cache": "🔵"})
    print(f"✅ 報告已更新至: {output_path}")

if __name__ == "__main__":
    main()

































