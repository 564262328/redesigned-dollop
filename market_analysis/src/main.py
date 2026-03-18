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
                "messages": [{"role": "user", "content": f"分析股票 {name}: {info}。輸出繁體中文 JSON: insights, buy_point, trend_prediction。"}],
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
    
    # --- 安全採樣：確保選出 20 檔 ---
    if len(df) <= 20:
        target_df = df
    else:
        top_10 = df.sort_values(by='change', ascending=False).head(10)
        others = df[~df['code'].isin(top_10['code'])].sample(n=10)
        target_df = pd.concat([top_10, others])

    ai_results = []
    print(f"🤖 正在分析 {len(target_df)} 檔精選標的...")
    for _, row in target_df.iterrows():
        chip = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **chip}
        analysis = get_ai_analysis(row['name'], str(combined))
        if not analysis:
            analysis = {"insights": "數據正在計算中...", "buy_point": "觀望", "trend_prediction": "盤整"}
        analysis.update(combined)
        ai_results.append(analysis)
        time.sleep(0.3)

    generate_report(ai_results, 0, len(df), source, [], dc.get_market_indices(), output_path, {"Cache": "🔵"})
    print(f"✅ 更新完成。")

if __name__ == "__main__":
    main()



































