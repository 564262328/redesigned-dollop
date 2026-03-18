import os
import json
import requests
import pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info):
    """
    核心 AI 分析函数：支持 AIHubMix / ChatGPT / DeepSeek 中转
    """
    api_key = os.getenv("AI_API_KEY")
    # 默认使用 AIHubMix 地址，若 Secret 中有自定义则覆盖
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    
    if not api_key:
        print(f"⚠️ 未配置 AI_API_KEY，{name} 将使用备用分析")
        return None

    # 构造 Prompt：要求 AI 返回标准 JSON
    prompt = f"""
    作为资深量化交易员，请深度分析 A 股【{name}】。
    原始行情数据：{info}
    
    请严格返回一个 JSON 对象（不要包含任何 Markdown 代码块）：
    {{
      "stock_name": "{name}",
      "stock_code": "代码",
      "price": "现价",
      "change": "涨跌幅%",
      "insights": "200字内技术面分析：包含压力支撑位、MACD/RSI 状态、资金流向判断",
      "buy_point": "精确数字(建议介入位)",
      "stop_loss": "精确数字(建议止损位)",
      "sentiment_score": 0-100数字
    }}
    """

    payload = {
        "model": "gpt-4o-mini", 
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }

    try:
        # 拼接正确的 API 地址
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        print(f"🤖 正在请求 AI 分析: {name} (网关: {base_url})...")
        
        response = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60 
        )
        
        if response.status_code == 200:
            return json.loads(response.json()['choices']['message']['content'])
        else:
            print(f"❌ API 报错 {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ AI 请求异常 ({name}): {e}")
        return None

def main():
    print("🚀 QUANT 终端 V14.6 启动 (全自动增量模式)...")
    dc = MarketDataCenter()
    
    # 1. 获取全市场行情
    df = dc.get_all_market_data()
    if df.empty:
        print("❌ 无法获取数据源，请检查网络或接口")
        return

    # 2. 增量同步数据库并获取统计数字
    new_count, total_count = dc.sync_and_get_new(df)

    # 3. 策略筛选：按成交额排序，选取前 12 只最活跃个股
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        name = row['name']
        # 调用 AI 进行深度分析
        result = get_ai_analysis(name, row.to_string())
        
        # 4. 容错处理：若 AI 失败，使用单大括号定义字典
        if not result:
            result = {
                "stock_name": name,
                "stock_code": str(row['code']),
                "price": str(row['price']),
                "change": str(row['change']),
                "insights": "⚠️ AI 分析通道拥堵。技术观察：该股成交额巨大，处于市场热点中心，波动加剧，建议关注支撑位表现。",
                "buy_point": "盘中观察",
                "stop_loss": "参考5日线",
                "sentiment_score": 50
            }
        ai_results.append(result)

    # 5. 调用 HTML 生成器渲染（传入 3 个正确参数）
    if ai_results:
        generate_report(ai_results, new_count, total_count)
        print(f"✅ 成功生成看板！今日发现新代码: {new_count}, 市场总数: {total_count}")

if __name__ == "__main__":
    main()










