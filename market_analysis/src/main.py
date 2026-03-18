import os, json, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com")
    if not api_key: return None

    prompt = f"分析 A 股 {name} 数据及筹码: {info}。请返回 JSON: {{'stock_name', 'stock_code', 'price', 'change', 'insights', 'buy_point', 'stop_loss'}}"
    try:
        res = requests.post(f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}},
            timeout=60)
        if res.status_code == 200:
            return json.loads(res.json()['choices']['message']['content'])
    except: pass
    return None

def main():
    print("🚀 QUANT 终端 V14.9.1 启动 (KeyError 修复版)...")
    dc = MarketDataCenter()
    
    # 1. 抓取行情 (处理元组返回)
    df, source_name = dc.get_all_market_data()
    industry_data = dc.get_industry_heatmap()
    
    # 安全检查：如果 DataFrame 连 code 列都没有，说明抓取彻底失败
    if df.empty or 'code' not in df.columns:
        print(f"❌ 严重错误: 数据抓取失败或格式错误 (来源: {source_name})")
        return

    # 2. 安全同步新股
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. 筛选前 12 只活跃股
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        # 匹配板块标签
        stock_industry = "其他"
        for ind in industry_data:
            if code in ind['symbols']:
                stock_industry = ind['name']
                break
        
        print(f"🤖 分析中: {row['name']}...")
        chip_info = dc.get_chip_data(code)
        combined = {**row.to_dict(), **chip_info, "industry": stock_industry}
        
        data = get_ai_analysis(row['name'], str(combined))
        if not data:
            data = {
                "stock_name": row['name'], "stock_code": code, "price": str(row['price']), 
                "change": str(row['change']), "insights": "⚠️ AI 网关繁忙。该股当前资金博弈激烈，建议关注板块联动效应。", 
                "buy_point": "盘中观察", "stop_loss": "参考5日线"
            }
        
        data.update(combined)
        ai_results.append(data)

    # 4. 生成报告
    generate_report(ai_results, new_count, total_count, source_name, industry_data)
    print(f"✅ 任务成功完成！数据源: {source_name}, 股票总数: {total_count}")

if __name__ == "__main__":
    main()














