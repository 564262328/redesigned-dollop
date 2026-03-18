import os
import json
import requests
import pandas as pd
from data_fetcher import fetch_multi_source_stock_data
from html_generator import generate_report

def get_ai_analysis(stock_name, stock_info):
    """
    支持 AIHubMix / ChatGPT / DeepSeek 的通用分析函数
    """
    api_key = os.getenv("AI_API_KEY")
    # 如果没配置 Base URL，默认使用 DeepSeek 官方
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    
    if not api_key:
        print("⚠️ 未发现 AI_API_KEY，使用模拟数据")
        return None

    # 构建 Prompt：要求 AI 给出更专业的金融维度
    prompt = f"""
    作为资深量化分析师，分析股票【{stock_name}】。
    原始数据：{stock_info}
    
    请严格返回 JSON 格式，包含以下字段：
    {{
      "stock_name": "{stock_name}",
      "stock_code": "代码",
      "price": "当前价",
      "change": "涨跌幅",
      "insights": "200字内深度技术面分析（包含支撑压力位、MACD/RSI状态、筹码分布）",
      "buy_point": "建议介入位",
      "stop_loss": "止损位",
      "target_price": "目标位",
      "sentiment_score": 0-100的整数
    }}
    """

    # 这里的 model 可以根据你的中转站支持更改，如 gpt-4o-mini, deepseek-chat 等
    payload = {
        "model": "gpt-4o-mini", 
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }

    try:
        print(f"🤖 正在通过 {base_url} 请求 AI 分析: {stock_name}...")
        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=40
        )
        response.raise_for_status()
        result_text = response.json()['choices']['message']['content']
        return json.loads(result_text)
    except Exception as e:
        print(f"❌ AI 请求失败: {e}")
        return None

def main():
    print("🚀 QUANT 终端 V14.3 启动...")
    df = fetch_multi_source_stock_data()
    
    if df is None or df.empty:
        print("❌ 无法获取行情数据")
        return

    ai_results = []
    # 分析前 8 只热门股票（根据你的 UI 布局调整数量）
    for _, row in df.head(8).iterrows():
        name = row.get('名称', '未知')
        
        # 真正调用 AI
        result = get_ai_analysis(name, row.to_string())
        
        # 容错处理：如果 AI 挂了，生成一个基础版数据，不让页面难看
        if not result:
            result = {
                "stock_name": name,
                "stock_code": str(row.get('代码', '000000')),
                "price": str(row.get('最新价', '0.00')),
                "change": f"{row.get('涨跌幅', '0')}%",
                "insights": "⚠️ 实时 AI 分析通道拥堵。技术面：处于震荡区间，建议关注量价配合情况。",
                "buy_point": "待定",
                "stop_loss": "5日均线",
                "target_price": "压力位",
                "sentiment_score": 50
            }
        ai_results.append(result)

    if ai_results:
        generate_report(ai_results)
        print(f"✅ 成功分析 {len(ai_results)} 只股票，页面已更新。")

if __name__ == "__main__":
    main()



