from data_fetcher import MarketDataCenter
from html_generator import generate_report
import pandas as pd

def main():
    print("🚀 量化终端 V14.6 启动 (增量同步模式)...")
    dc = MarketDataCenter()
    
    # 1. 执行增量同步
    new_stocks, _ = dc.sync_new_stocks()
    
    # 2. 获取实时行情
    df_quotes = dc.get_realtime_quotes()
    if df_quotes.empty: return

    # 3. 筛选今日热点 (成交额前12)
    df_quotes['amount'] = pd.to_numeric(df_quotes['amount'], errors='coerce')
    hot_df = df_quotes.sort_values(by='amount', ascending=False).head(12)

    # 4. 构建分析列表 (此处可接入之前的 AI 分析逻辑)
    results = []
    for _, row in hot_df.iterrows():
        # 这里您可以保留之前的 get_ai_analysis(row['name'], row.to_string())
        results.append({
            "stock_name": row['name'],
            "stock_code": row['code'],
            "price": row['price'],
            "change": row['change'],
            "insights": "AI 正在对该活跃个股进行大数据建模分析...",
            "buy_point": "盘中观察",
            "stop_loss": "参考5日线",
            "is_new": row['code'] in new_stocks['code'].values
        })

    # 5. 渲染看板
    generate_report(results, len(new_stocks))

if __name__ == "__main__":
    main()






