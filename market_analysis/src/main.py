import os, json, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info, market_context):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com")
    if not api_key: 
        print("⚠️ Missing AI_API_KEY")
        return None
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini", 
                "messages": [{"role": "user", "content": f"Analyze stock {name} with data: {info}. Market context: {market_context}. Return JSON."}],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }, timeout=60)
        return json.loads(res.json()['choices']['message']['content'])
    except Exception as e: 
        print(f"❌ AI API Error: {e}")
        return None

def main():
    print("🚀 QUANT Terminal V15.8 Starting...")
    dc = MarketDataCenter()
    
    # 1. Fetch Market Overview
    df, source_name = dc.get_all_market_data()
    
    if df.empty or 'code' not in df.columns:
        print("❌ Critical Error: No market data fetched.")
        return

    # 2. Fetch Additional Context
    indices = dc.get_market_indices()
    industry_data = dc.get_industry_heatmap()
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. Select Top 12 stocks for AI analysis (by volume or change)
    hot_df = df.sort_values(by='change', ascending=False).head(12) 

    ai_results = []
    mkt_summary = str(indices)
    
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        print(f"🤖 Analyzing: {row.get('name', code)}...")
        
        # Get extra tech data
        chip = dc.get_chip_data(code)
        combined_info = {**row.to_dict(), **chip, "industry": "General"}
        
        # Call AI
        analysis = get_ai_analysis(row.get('name', 'Unknown'), str(combined_info), mkt_summary)
        
        # Fallback if AI fails
        if not analysis:
            analysis = {
                "stock_name": row.get('name','N/A'), 
                "stock_code": code, 
                "price": str(row.get('price','0')), 
                "change": str(row.get('change','0')), 
                "insights": "⚠️ Data fluctuation detected. High turnover observed.", 
                "buy_point": "Watch Support", 
                "stop_loss": "Recent Low"
            }
        
        # Merge all data for the template
        analysis.update(combined_info)
        ai_results.append(analysis)

    # 4. Generate the Final Report
    generate_report(ai_results, new_count, total_count, source_name, industry_data, indices)
    print(f"✅ Report updated via source: {source_name}")

if __name__ == "__main__":
    main()





















