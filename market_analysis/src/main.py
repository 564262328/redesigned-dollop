import os
import sys
import json
import time
import requests
import pandas as pd

# 強制將當前腳本所在目錄加入搜索路徑
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# 導入同目錄下的檔案
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
                "messages": [{"role": "user", "content": f"分析股票 {name}: {info}。請輸出繁體中文 JSON: insights, buy_point, trend_prediction。"}],
                "response_format": {"type": "json_object"}, "temperature": 0.2
            }, timeout=45)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    # --- 絕對路徑計算 (src -> market_analysis -> root) ---
    project_root = os.path.dirname(os.path.dirname(CURRENT_DIR))
    output_path = os.path.join(project_root, "index.html")
    cache_path = os.path.join(project_root, "market_cache.json")

    print(f"🚀 QUANT Terminal V15.8 PRO 啟動...")
    print(f"📍 緩存目標: {cache_path}")
    
    # 1. 獲取數據 (傳入緩存路徑)
    dc = MarketDataCenter(cache_file=cache_path)
    df, source = dc.fetch_all_markets()
    
    # 2. 挑選 20 檔標的 (漲幅前10 + 隨機10)
    top_10 = df.sort_values(by='change', ascending=False).head(10)
    remaining = df[~df['code'].isin(top_10['code'])]
    others = remaining.sample(n=min(10, len(remaining)))
    target_df = pd.concat([top_10, others]).head(20)

    # 3. 執行 AI 批量分析
    ai_results = []
    print(f"🤖 執行批量深度分析...")
    for _, row in target_df.iterrows():
        chip = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **chip}
        
        analysis = get_ai_analysis(row['name'], str(combined))
        if not analysis:
            analysis = {"insights": "數據正在掃描中...", "buy_point": "觀望", "trend_prediction": "盤整"}
        
        analysis.update(combined)
        ai_results.append(analysis)
        time.sleep(0.3)

    # 4. 生成報告
    health_status = {"TX": "🟢", "Sina": "🟢", "Cache": "🔵" if "Cache" in source else "⚪"}
    generate_report(ai_results, 0, len(df), source, [], dc.get_market_indices(), output_path, health_status)
    print(f"✅ 報告更新完成: {output_path}")

if __name__ == "__main__":
    main()






































