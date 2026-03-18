import os, json, requests, pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, code, asset_type, info):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com")
    if not api_key: return None
    
    # 针对不同资产类型微调 Prompt
    prompt = f"""
    分析资产：{name} ({code})，类别：{asset_type}。
    行情数据：{info}
    请返回 JSON: {{'insights', 'buy_point', 'stop_loss'}}。
    如果是ETF，侧重规模和申赎逻辑；如果是港股，侧重南向资金和汇率影响；如果是A股，侧重技术面。
    """
    
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
    print("🚀 QUANT 终端 V15.0 启动 (全资产识别模式)...")
    dc = MarketDataCenter()
    df, source_name = dc.get_all_market_data()
    if df.empty: return

    new_count, total_count = dc.sync_and_get_new(df)
    
    # 筛选最火的前 12 个资产进行分析
    hot_df = df.head(12) 

    ai_results = []
    for _, row in hot_df.iterrows():
        name = row['name']
        code = row['code']
        asset_type = row['asset_type']
        
        print(f"🤖 AI 分析中: {name} ({code}) [{asset_type}]...")
        
        # 调用 AI
        data = get_ai_analysis(name, code, asset_type, str(row.to_dict()))
        
        # 统一封装数据
        result = {
            "stock_name": f"{name} ({code})", # 这里实现了您要求的：名字 (代码) 写在一起
            "raw_name": name,
            "stock_code": code,
            "asset_type": asset_type,
            "price": str(row.get('price', '0')),
            "change": str(row.get('change', '0')),
            "insights": data.get('insights', "分析网关繁忙...") if data else "数据加载中...",
            "buy_point": data.get('buy_point', "--") if data else "--",
            "stop_loss": data.get('stop_loss', "--") if data else "--"
        }
        ai_results.append(result)

    generate_report(ai_results, new_count, total_count, source_name)

if __name__ == "__main__":
    main()

















