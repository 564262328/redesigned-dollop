import os
import json
import time
import requests
import pandas as pd
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
                "messages": [{"role": "user", "content": f"分析股票 {name} ({info})。大盤: {market_context}。請以 JSON 返回 insights, buy_point, stop_loss。"}],
                "response_format": {"type": "json_object"}, "temperature": 0.3
            }, timeout=30)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    # --- 絕對路徑計算 (防止 404) ---
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(src_dir))
    output_path = os.path.join(project_root, "index.html")

    print(f"🚀 QUANT Terminal V15.8 啟動...")
    dc = MarketDataCenter()
    
    # 1. 獲取行情
    df, source = dc.get_all_market_data()
    indices = dc.get_market_indices()
    _, total_count = dc.sync_and_get_new(df)
    
    # 2. 準備健康狀態數據
    health_status = {
        "TX": "🔴" if dc._circuit_breaker["TX"] else "🟢",
        "Sina": "🔴" if dc._circuit_breaker["Sina"] else "🟢",
        "EM": "🔴" # 已知封鎖
    }

    # 3. AI 分析 (篩選前 8 檔)
    hot_df = df.sort_values(by='change', ascending=False).head(8)
    ai_results = []
    for _, row in hot_df.iterrows():
        print(f"🤖 正在分析: {row['name']} ({row['code']})...")
        chip = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **chip}
        
        analysis = get_ai_analysis(row['name'], str(combined), str(indices[:3]))
        if not analysis:
            analysis = {"insights": "網絡延遲，請關注技術位。", "buy_point": "觀望", "stop_loss": "前低"}
        analysis.update(combined)
        ai_results.append(analysis)

    # 4. 生成報告
    try:
        generate_report(ai_results, 0, total_count, source, dc.get_industry_heatmap(), indices, output_path, health_status)
        print(f"✅ 成功！報告已保存至: {output_path}")
    except Exception as e:
        print(f"❌ 報告生成失敗: {e}")

if __name__ == "__main__":
    main()





























