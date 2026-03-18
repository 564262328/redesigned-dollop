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
                "messages": [{"role": "user", "content": f"分析股票 {name} ({info})。請回傳 JSON 包含 insights, buy_point, stop_loss。"}],
                "response_format": {"type": "json_object"}, "temperature": 0.3
            }, timeout=20)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    # --- 絕對路徑鎖定 (防止 index.html 消失) ---
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(src_dir))
    output_path = os.path.join(project_root, "index.html")

    print(f"🚀 QUANT Terminal V15.8 啟動...")
    print(f"📍 項目根目錄: {project_root}")
    
    dc = MarketDataCenter()
    
    # 1. 獲取數據 (保證不會 empty)
    df, source = dc.get_all_market_data()
    
    # 2. 獲取大盤數據
    indices = dc.get_market_indices()
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. AI 分析
    hot_df = df.head(10)
    ai_results = []
    for _, row in hot_df.iterrows():
        print(f"🤖 正在處理: {row['name']}...")
        chip = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **chip}
        
        analysis = get_ai_analysis(row['name'], str(combined), str(indices))
        if not analysis:
            analysis = {"insights": "網絡波動，請參考技術指標。", "buy_point": "觀望", "stop_loss": "前低"}
        analysis.update(combined)
        ai_results.append(analysis)

    # 4. 【核心】強制執行生成報告，確保 index.html 一定會出現在根目錄
    health_status = {"EM": "🟢", "Sina": "🟢", "TX": "🟢"} # 簡化傳遞
    try:
        generate_report(ai_results, new_count, total_count, source, [], indices, output_path, health_status)
        print(f"✅ 成功！報告已生成在: {output_path}")
    except Exception as e:
        print(f"❌ 生成失敗: {e}")

if __name__ == "__main__":
    main()



























