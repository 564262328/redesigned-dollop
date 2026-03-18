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
                "messages": [{"role": "user", "content": f"分析股票 {name}。數據: {info}。大盤環境: {market_context}。請以 JSON 格式返回，包含 insights, buy_point, stop_loss。"}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }, timeout=45)
        
        content = res.json()['choices']['message']['content']
        # 兼容 Markdown 格式標籤
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        print(f"❌ AI 解析失敗 ({name}): {e}")
        return None

def main():
    # 計算路徑：確保 index.html 生成在項目根目錄
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    output_path = os.path.join(root_dir, "index.html")

    print(f"🚀 QUANT Terminal V15.8 啟動... 目標路徑: {output_path}")
    dc = MarketDataCenter()
    
    df, source = dc.get_all_market_data()
    if df.empty: return

    indices = dc.get_market_indices()
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 挑選漲幅前 10 名
    hot_df = df.sort_values(by='change', ascending=False).head(10)
    ai_results = []

    for _, row in hot_df.iterrows():
        code = str(row['code'])
        print(f"🤖 AI 分析中: {row['name']} ({code})...")
        chip = dc.get_chip_data(code)
        combined = {**row.to_dict(), **chip}
        
        analysis = get_ai_analysis(row['name'], str(combined), str(indices))
        if not analysis:
            analysis = {"insights": "數據源異常，建議觀察支撐位。", "buy_point": "待定", "stop_loss": "前低"}
            
        analysis.update(combined)
        ai_results.append(analysis)

    generate_report(ai_results, new_count, total_count, source, dc.get_industry_heatmap(), indices, output_path)
    print(f"✅ 看板更新成功！")

if __name__ == "__main__":
    main()






















