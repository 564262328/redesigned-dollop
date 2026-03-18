import os, json, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info, market_context):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com")
    if not api_key: return None

    # AI Prompt 升級：加入市場大環境感知
    prompt = f"""
    【市場大環境】：{market_context}
    【個股數據】：{info}
    
    你是資深交易員。請結合市場大環境分析該股【{name}】。
    1. 如果大盤暴跌，請在 insights 中給出明確防守警示。
    2. 如果板塊強勢而個股滯漲，分析其補漲潛力。
    請嚴格返回 JSON: {{'stock_name', 'stock_code', 'price', 'change', 'insights', 'buy_point', 'stop_loss'}}
    """
    
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}},
            timeout=60)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    print("🚀 QUANT 終端 V15.2 啟動 (全環境感知模式)...")
    dc = MarketDataCenter()
    
    # 1. 抓取多維數據
    indices = dc.get_market_indices()
    df, source_name = dc.get_all_market_data()
    industry_data = dc.get_industry_heatmap()
    if df.empty: return

    # 2. 構建 AI 市場上下文
    mkt_summary = " | ".join([f"{i['name']}:{i['change']}%" for i in indices])
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. 篩選熱點
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        stock_industry = "其他"
        for ind in industry_data:
            if code in ind['symbols']:
                stock_industry = ind['name']
                break
        
        print(f"🤖 智能分析中: {row['name']}...")
        chip_info = dc.get_chip_data(code)
        combined = {**row.to_dict(), **chip_info, "industry": stock_industry}
        
        # 傳入市場背景信息
        data = get_ai_analysis(row['name'], str(combined), mkt_summary)
        
        if not data:
            data = {"stock_name": row['name'], "stock_code": code, "price": row['price'], "change": row['change'], 
                    "insights": "⚠️ AI 網關擁堵。注意大盤波動對該活躍品種的衝擊。", "buy_point": "看盤決定", "stop_loss": "參考支撐"}
        
        data.update(combined)
        data['asset_type'] = "A股" # 預設標籤
        ai_results.append(data)

    # 4. 生成看板 (傳入所有數據)
    generate_report(ai_results, new_count, total_count, source_name, industry_data, indices)
    print(f"✅ 終端部署成功！數據源: {source_name}")

if __name__ == "__main__":
    main()


















