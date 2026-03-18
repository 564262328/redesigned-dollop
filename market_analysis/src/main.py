import os
import json
import requests
import pandas as pd
# 核心：从 data_fetcher 导入统一命名的函数
from data_fetcher import get_all_market_data
from html_generator import generate_report

def get_ai_analysis(stock_name, stock_info):
    """
    通过 AIHubMix / ChatGPT 接口获取深度分析
    """
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    
    if not api_key:
        print("⚠️ 未发现 AI_API_KEY，跳过 AI 分析阶段")
        return None

    prompt = f"""
    你是资深金融量化分析师。请分析 A 股股票 {stock_name} 的最新行情：{stock_info}。
    请严格返回一个 JSON 对象，包含以下字段：
    {{
      "stock_name": "{stock_name}",
      "stock_code": "提取代码",
      "price": "当前价",
      "change": "涨跌幅%",
      "insights": "200字内技术面深度解析，包含支撑位、压力位及趋势判断",
      "buy_point": "建议买入位数字",
      "stop_loss": "建议止损位数字"
    }}
    """

    # 适配 AIHubMix 模型，建议使用 gpt-4o-mini 或 deepseek-chat
    payload = {
        "model": "gpt-4o-mini", 
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }

    try:
        print(f"🤖 正在请求 AI 深度分析: {stock_name}...")
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        response = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=50
        )
        response.raise_for_status()
        return json.loads(response.json()['choices']['message']['content'])
    except Exception as e:
        print(f"❌ AI 分析失败 ({stock_name}): {e}")
        return None

def main():
    print("🚀 QUANT 量化终端 V14.5 启动...")
    
    # 1. 获取全市场数据
    df = get_all_market_data()
    
    if df is None or df.empty:
        print("❌ 无法获取全市场行情，程序终止")
        return

    # 2. 筛选策略：按成交额排序，选取前 12 只最活跃的个股
    # 这代表了当前市场资金关注度最高的热点
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    top_stocks = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in top_stocks.iterrows():
        name = row['name']
        # 3. 真正进行 AI 分析
        ai_data = get_ai_analysis(name, row.to_string())
        
        # 4. 如果 AI 接口报错或超时，使用基础数据进行中文补全填充
        if not ai_data:
            ai_data = {
                "stock_name": name,
                "stock_code": row['code'],
                "price": str(row['price']),
                "change": str(row['change']),
                "insights": "⚠️ AI 分析接口拥堵或授权失败。技术观察：该股今日成交额巨大，处于市场热点中心，波动加剧，建议谨慎关注支撑位。",
                "buy_point": "盘中观察",
                "stop_loss": "参考5日均线"
            }
        ai_results.append(ai_data)

    # 5. 调用 HTML 生成器渲染最终页面
    if ai_results:
        generate_report(ai_results)
        print(f"✅ 任务完成！成功生成 {len(ai_results)} 只热门个股分析看板")

if __name__ == "__main__":
    main()





