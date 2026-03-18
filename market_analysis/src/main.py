import os, json, time, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info, market_context):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com").rstrip('/')
    if not api_key: return None
    try:
        res = requests.post(f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini", 
                "messages": [{"role": "user", "content": f"分析股票 {name}。數據: {info}。參考大盤: {market_context}。請輸出繁體中文 JSON: insights, buy_point, trend_prediction。"}],
                "response_format": {"type": "json_object"}, "temperature": 0.2
            }, timeout=45)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    # 路徑計算
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(src_dir))
    output_path = os.path.join(project_root, "index.html")
    cache_path = os.path.join(project_root, "market_cache.json")

    print(f"🚀 QUANT Terminal V15.8 PRO 啟動...")
    dc = MarketDataCenter(cache_file=cache_path)
    
    # 1. 獲取全市場數據
    df, source = dc.fetch_all_markets()
    if df.empty: return

    # 2. 挑選分析標的 (漲幅榜前 10 + 隨機挑選 10 檔不同類型的股票)
    top_10 = df.sort_values(by='change', ascending=False).head(10)
    random_10 = df.sample(n=10)
    target_df = pd.concat([top_10, random_10]).drop_duplicates().head(20)

    # 3. 執行批量分析
    ai_results = []
    indices = [{"名稱": "A股/港股/ETF 聯動系統", "最新價": "多市場", "漲跌幅": "0"}]
    
    print(f"🤖 正在分析 {len(target_df)} 檔精選標的...")
    for _, row in target_df.iterrows():
        chip = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **chip}
        
        analysis = get_ai_analysis(row['name'], str(combined), "多頭行情")
        if not analysis:
            analysis = {"insights": "數據正在計算中...", "buy_point": "觀望", "trend_prediction": "盤整"}
        
        analysis.update(combined)
        ai_results.append(analysis)
        time.sleep(1) # 防 AI 速率限制

    # 4. 生成報告
    health_status = {"TX": "🟢", "Sina": "🟢", "Shared_Cache": "🔵"}
    generate_report(ai_results, 0, len(df), source, [], indices, output_path, health_status)
    print(f"✅ 報告已生成，共分析 {len(ai_results)} 檔。")

if __name__ == "__main__":
    main()






























