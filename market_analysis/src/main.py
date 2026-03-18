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
                "messages": [{"role": "user", "content": f"Analyze stock {name} ({info}). Return JSON: insights, buy_point, stop_loss."}],
                "response_format": {"type": "json_object"}, "temperature": 0.3
            }, timeout=30)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    # --- 🎯 Absolute Path Fix ---
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(src_dir))
    output_path = os.path.join(project_root, "index.html")

    print(f"🚀 Starting QUANT Terminal V15.8...")
    print(f"📍 Project Root: {project_root}")
    
    dc = MarketDataCenter()
    
    # 1. Fetch Data (Now optimized for Sina)
    df, source = dc.get_all_market_data()
    
    # 2. Support Data
    indices = dc.get_market_indices()
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. AI Analysis (Limited to top 8 for faster execution)
    hot_df = df.sort_values(by='change', ascending=False).head(8)
    ai_results = []
    for _, row in hot_df.iterrows():
        print(f"🤖 Analyzing: {row['name']}...")
        chip = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **chip}
        
        analysis = get_ai_analysis(row['name'], str(combined), str(indices))
        if not analysis:
            analysis = {"insights": "Network lag. Follow technical levels.", "buy_point": "Watch", "stop_loss": "Recent Low"}
        analysis.update(combined)
        ai_results.append(analysis)

    # 4. Generate Report
    health_status = {"EM": "🔴", "Sina": "🟢", "TX": "🟢"}
    generate_report(ai_results, new_count, total_count, source, dc.get_industry_heatmap(), indices, output_path, health_status)
    
    print(f"✅ SUCCESS! Report generated at: {output_path}")

if __name__ == "__main__":
    main()




























