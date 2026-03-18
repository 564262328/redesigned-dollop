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
                "messages": [{"role": "user", "content": f"分析股票 {name}。數據: {info}。參考市場狀態。請回傳 JSON: insights, buy_point, trend_prediction。"}],
                "response_format": {"type": "json_object"}, "temperature": 0.2
            }, timeout=45)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    # --- 絕對路徑定位 (確保緩存與 HTML 在倉庫根目錄) ---
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(src_dir))
    output_path = os.path.join(project_root, "index.html")
    cache_path = os.path.join(project_root, "market_cache.json")

    print(f"🚀 QUANT Terminal V15.8 PRO 啟動...")
    print(f"📍 緩存路徑: {cache_path}")
    
    dc = MarketDataCenter(cache_file=cache_path)
    
    # 1. 獲取全市場數據 (自動緩存)
    df, source = dc.fetch_all_markets()
    if df.empty:
        # 保底機制：防止程序崩潰
        df = pd.DataFrame([{"code":"000001","name":"數據更新中","price":0,"change":0,"market_tag":"A股"}])
        dc._save_cache(df)

    # 2. 挑選分析對象 (漲幅前10 + 隨機10)
    top_10 = df.sort_values(by='change', ascending=False).head(10)
    random_10 = df.sample(n=min(10, len(df)))
    target_df = pd.concat([top_10, random_10]).drop_duplicates().head(20)

    ai_results = []
    print(f"🤖 批量分析中 ({len(target_df)} 檔)...")
    for _, row in target_df.iterrows():
        chip = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **chip}
        
        analysis = get_ai_analysis(row['name'], str(combined), "多市場聯動模式")
        if not analysis:
            analysis = {"insights": "數據正在掃描...", "buy_point": "觀望", "trend_prediction": "盤整"}
        analysis.update(combined)
        ai_results.append(analysis)
        time.sleep(0.5)

    # 3. 生成報告
    health_status = {"TX": "🟢", "Sina": "🟢", "Cache": "🔵" if "Cache" in source else "⚪"}
    generate_report(ai_results, 0, len(df), source, dc.get_industry_heatmap(), dc.get_market_indices(), output_path, health_status)
    print(f"✅ 任務完成。報告位置: {output_path}")

if __name__ == "__main__":
    main()































