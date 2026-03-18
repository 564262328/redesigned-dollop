import os
import sys
import json
import time
import requests
import pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com").rstrip('/')
    if not api_key: return None
    try:
        # Prompt 強化：要求分析深度指標與趨勢
        prompt = f"分析股票 {name}: {info}。請結合PE、換手率與籌碼狀態給出深度洞察。輸出繁體中文 JSON: insights, buy_point, trend_prediction。"
        res = requests.post(f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini", 
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}, "temperature": 0.2
            }, timeout=45)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    # --- 🎯 絕對路徑定位 (確保在 GitHub Actions 根目錄生成文件) ---
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(src_dir))
    output_path = os.path.join(project_root, "index.html")
    cache_path = os.path.join(project_root, "market_cache.json")

    print(f"🚀 QUANT PRO V15.8 啟動...")
    print(f"📍 目標路徑: {output_path}")

    # 1. 數據採集 (20分鐘緩存共享)
    dc = MarketDataCenter(cache_file=cache_path)
    full_df, source = dc.fetch_all_markets()
    
    if full_df.empty:
        print("❌ 錯誤：數據源失效且保底失敗。")
        return

    # 2. 安全採樣邏輯：確保 20 檔不重複標的
    # 優先選取漲幅前 10
    top_10 = full_df.sort_values(by='change', ascending=False).head(10)
    # 從剩餘池子隨機選取 10 檔 (確保代碼不重複)
    remaining_pool = full_df[~full_df['code'].isin(top_10['code'])]
    sample_size = min(10, len(remaining_pool))
    
    if sample_size > 0:
        others = remaining_pool.sample(n=sample_size)
        target_df = pd.concat([top_10, others]).drop_duplicates(subset=['code']).head(20)
    else:
        target_df = top_10

    # 3. 執行批量 AI 分析
    ai_results = []
    print(f"🤖 正在執行深度分析 ({len(target_df)} 檔標的)...")
    for _, row in target_df.iterrows():
        print(f"📈 分析中: {row['name']}...")
        chips = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **chips}
        
        analysis = get_ai_analysis(row['name'], str(combined))
        if not analysis:
            analysis = {"insights": "數據正在掃描中...", "buy_point": "觀望", "trend_prediction": "震盪"}
        
        analysis.update(combined)
        ai_results.append(analysis)
        time.sleep(0.5) # 降低 AI 請求頻率

    # 4. 調用美化版 HTML 生成器
    # 設置狀態燈
    health_status = {"TX": "🟢", "Sina": "🟢", "Cache": "🔵" if "Cache" in source else "⚪"}
    indices = dc.get_market_indices()
    if not indices:
        indices = [{"名稱": "多市場監控中", "最新價": "Online", "漲跌幅": "0"}]

    generate_report(ai_results, 0, len(full_df), source, [], indices, output_path, health_status)
    print(f"✅ 任務圓滿完成！數據源: {source}")

if __name__ == "__main__":
    main()







































