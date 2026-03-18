import os, json, requests, pandas as pd
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
                "messages": [{"role": "user", "content": f"分析股票 {name} ({info})。大盤: {market_context}。請回傳 JSON 包含 insights, buy_point, stop_loss。"}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }, timeout=30) # 縮短超時時間
        
        content = res.json()['choices']['message']['content']
        return json.loads(content)
    except: return None

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    output_path = os.path.join(root_dir, "index.html")

    print(f"🚀 QUANT Terminal V15.8 啟動...")
    dc = MarketDataCenter()
    
    df, source = dc.get_all_market_data()
    if df.empty:
        print("❌ 錯誤：無法獲取行情數據")
        return

    # --- 優化：僅挑選前 6 名進行深度 AI 分析，其餘僅展示基礎數據 ---
    hot_df = df.sort_values(by='change', ascending=False).head(6) 
    indices = dc.get_market_indices()
    new_count, total_count = dc.sync_and_get_new(df)
    
    ai_results = []
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        print(f"🤖 AI 分析中: {row['name']}...")
        chip = dc.get_chip_data(code)
        
        analysis = get_ai_analysis(row['name'], str({**row.to_dict(), **chip}), str(indices))
        if not analysis:
            analysis = {"insights": "數據源波動，請關注支撐位。", "buy_point": "觀望", "stop_loss": "前低"}
            
        analysis.update({**row.to_dict(), **chip})
        ai_results.append(analysis)

    generate_report(ai_results, new_count, total_count, source, dc.get_industry_heatmap(), indices, output_path)
    print(f"✅ 看板更新成功！數據源: {source}")

if __name__ == "__main__":
    main()






















