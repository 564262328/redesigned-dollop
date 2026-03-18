import os, json, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com")
    if not api_key: return None

    prompt = f"你是量化专家。分析 A 股 {name} 数据及筹码: {info}。请返回 JSON: {{'stock_name', 'stock_code', 'price', 'change', 'insights', 'buy_point', 'stop_loss'}}"
    
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}},
            timeout=60)
        return json.loads(res.json()['choices']['message']['content'])
    except: return None

def main():
    print("🚀 QUANT 终端 V14.9 启动...")
    dc = MarketDataCenter()
    
    # 1. 抓取多维数据
    df, source_name = dc.get_all_market_data()
    industry_data = dc.get_industry_heatmap()
    if df.empty: return

    # 2. 数据库同步
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. 筛选前 12 只活跃股
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        code = row['code']
        # 匹配该股票属于哪个 Top 板块
        stock_industry = "其他"
        for ind in industry_data:
            if code in ind['symbols']:
                stock_industry = ind['name']
                break
        
        print(f"🤖 分析中: {row['name']}...")
        chip_info = dc.get_chip_data(code)
        # 整合 AI 分析所需数据
        combined = {**row.to_dict(), **chip_info, "industry": stock_industry}
        
        data = get_ai_analysis(row['name'], str(combined))
        if not data:
            data = {"stock_name": row['name'], "stock_code": code, "price": row['price'], "change": row['change'], 
                    "insights": "⚠️ AI 网关繁忙。技术观察：换手活跃，注意主力成本区支撑。", "buy_point": "观察", "stop_loss": "5日线"}
        
        data.update(combined)
        ai_results.append(data)

    # 4. 渲染网页
    generate_report(ai_results, new_count, total_count, source_name, industry_data)
    print(f"✅ 成功生成看板。数据源: {source_name}")

if __name__ == "__main__":
    main()













