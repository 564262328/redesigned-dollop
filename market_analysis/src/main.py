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
    print("🚀 QUANT 终端 V14.9.2 启动 (全兼容生存模式)...")
    dc = MarketDataCenter()
    
    # 1. 抓取行情 (获取结果及来源)
    df, source_name = dc.get_all_market_data()
    
    # 如果所有源都彻底失败（连列表都没拿到），才报错
    if df.empty or 'code' not in df.columns:
        print(f"❌ 严重错误: 所有数据源均不可用。")
        return

    # 2. 同步新股
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. 行业数据 (不影响主流程)
    industry_data = dc.get_industry_heatmap()
    
    # 4. 筛选热点（如果没有成交额字段，就随机选12个）
    if 'amount' in df.columns and source_name != "Fallback-System":
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        hot_df = df.sort_values(by='amount', ascending=False).head(12)
    else:
        hot_df = df.head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        print(f"🤖 分析中: {row.get('name', code)}...")
        
        chip_info = dc.get_chip_data(code)
        combined = {**row.to_dict(), **chip_info, "industry": "全市场"}
        
        data = get_ai_analysis(row.get('name', '未知'), str(combined))
        if not data:
            data = {
                "stock_name": row.get('name', '未知'), "stock_code": code, 
                "price": str(row.get('price', '0')), "change": str(row.get('change', '0')),
                "insights": "⚠️ 数据源不稳定，当前展示基础技术指标。请关注主力成本区。",
                "buy_point": "盘中观察", "stop_loss": "参考5日线"
            }
        data.update(combined)
        ai_results.append(data)

    # 5. 生成报告
    generate_report(ai_results, new_count, total_count, source_name, industry_data)
    print(f"✅ 看板更新成功！来源: {source_name}")

if __name__ == "__main__":
    main()















