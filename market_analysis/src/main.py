import os
import json
import requests
import pandas as pd
from data_fetcher import fetch_multi_source_stock_data
from html_generator import generate_report

def get_ai_analysis(stock_name, stock_info):
    """
    核心：调用 AIHubMix 或 ChatGPT 进行分析
    """
    # 从 GitHub Secrets 读取配置
    api_key = os.getenv("AI_API_KEY")
    # AIHubMix 的地址通常是 https://aihubmix.com
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    
    if not api_key:
        print("⚠️ 未配置 AI_API_KEY，将使用本地备用分析")
        return None

    prompt = f"""
    你是量化专家。分析股票【{stock_name}】。数据：{stock_info}
    请严格返回 JSON：
    {{
      "stock_name": "{stock_name}",
      "stock_code": "代码",
      "price": "价格",
      "change": "涨跌幅",
      "insights": "200字内深度技术分析，包含MACD、支撑压力位和筹码分布",
      "buy_point": "建议介入位",
      "stop_loss": "止损位",
      "target_price": "止盈位",
      "sentiment_score": 0-100
    }}
    """

    payload = {
        "model": "gpt-4o-mini", # 或者换成 deepseek-chat
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }

    try:
        print(f"🤖 正在请求 AI 分析 ({base_url}): {stock_name}...")
        # 拼接路径，确保 URL 格式正确
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        response = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=40
        )
        response.raise_for_status()
        return json.loads(response.json()['choices']['message']['content'])
    except Exception as e:
        print(f"❌ AI 分析失败: {e}")
        return None

def main():
    print("🚀 QUANT 终端 V14.3 启动 (AIHubMix 增强版)...")
    df = fetch_multi_source_stock_data()
    
    if df is None or df.empty:
        print("❌ 无法获取行情数据")
        return

    ai_results = []
    # 分析前 8 只热门股票
    for _, row in df.head(8).iterrows():
        name = row.get('名称', '未知')
        result = get_ai_analysis(name, row.to_string())
        
        # 容错：如果 AI 挂了，显示默认提示
        if not result:
            result = {
                "stock_name": name,
                "stock_code": str(row.get('代码', '000000')),
                "price": str(row.get('最新价', '0.00')),
                "change": f"{row.get('涨跌幅', '0')}%",
                "insights": "⚠️ 实时 AI 分析通道拥堵。技术面：处于震荡区间，建议关注量价配合情况。",
                "buy_point": "待定",
                "stop_loss": "5日线",
                "target_price": "压力位",
                "sentiment_score": 50
            }
        ai_results.append(result)

    if ai_results:
        generate_report(ai_results)
        print(f"✅ 完成！分析了 {len(ai_results)} 只股票。")

if __name__ == "__main__":
    main()




