import os, json, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info, market_context):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com")
    if not api_key: return None
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini", 
                "messages": [{"role": "user", "content": f"分析 {name} 数据: {info}。大盘: {market_context}"}],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }, timeout=60)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    print("🚀 QUANT 终端 V15.8 启动 (生存模式)...")
    dc = MarketDataCenter()
    
    # 1. 抓取行情 (获取结果及来源)
    df, source_name = dc.get_all_market_data()
    
    # 即使行情为空，只要拿到了 code 列表，就不报错退出
    if df.empty or 'code' not in df.columns:
        print("❌ 致命错误：全网数据源封锁。")
        return

    indices = dc.get_market_indices()
    industry_data = dc.get_industry_heatmap()
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 筛选展示逻辑
    hot_df = df.head(12) 

    ai_results = []
    mkt_summary = str(indices)
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        print(f"🤖 分析中: {row.get('name', code)}...")
        chip = dc.get_chip_data(code)
        combined = {**row.to_dict(), **chip, "industry": "全市场"}
        
        data = get_ai_analysis(row.get('name', '未知'), str(combined), mkt_summary)
        if not data:
            data = {"stock_name": row.get('name','未知'), "stock_code": code, "price": str(row.get('price','0')), 
                    "change": str(row.get('change','0')), "insights": "⚠️ 数据源波动，建议关注筹码分布。", 
                    "buy_point": "安全位", "stop_loss": "止损位"}
        data.update(combined)
        ai_results.append(data)

    generate_report(ai_results, new_count, total_count, source_name, industry_data, indices)
    print(f"✅ 看板已更新。模式: {source_name}")

if __name__ == "__main__":
    main()




















