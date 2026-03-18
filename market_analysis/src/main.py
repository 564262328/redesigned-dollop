import os
import json
import requests
import pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, full_info):
    """
    调用 AIHubMix/ChatGPT 结合增强数据和筹码数据进行深度量化分析
    """
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    
    if not api_key:
        print(f"⚠️ 未配置 AI_API_KEY，{name} 将使用基础逻辑")
        return None

    # 将增强后的数据字典转换为字符串喂给 AI
    prompt = f"""
    作为资深 A 股量化专家，请根据以下多维度数据对股票【{name}】进行深度研判。
    包含：实时行情、估值指标、以及筹码分布（获利盘、成本等）。
    数据源：{full_info}
    
    请严格返回 JSON 对象：
    {{
      "stock_name": "{name}",
      "stock_code": "代码",
      "price": "现价",
      "change": "涨跌幅%",
      "insights": "200字内深度分析：结合筹码获利盘比例与换手率判断主力动向，给出技术面压力位与支撑位判断。",
      "buy_point": "建议介入位",
      "stop_loss": "建议止损位",
      "sentiment_score": 0-100
    }}
    """

    payload = {
        "model": "gpt-4o-mini", 
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }

    try:
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        response = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        if response.status_code == 200:
            return json.loads(response.json()['choices']['message']['content'])
        return None
    except Exception as e:
        print(f"❌ AI 请求失败: {e}")
        return None

def main():
    print("🚀 QUANT 终端 V14.7 启动 (增强数据 + 筹码分析模式)...")
    dc = MarketDataCenter()
    
    # 1. 获取增强行情数据 (PE, PB, 换手率, 量比, 市值等)
    df = dc.get_all_market_data()
    if df.empty:
        print("❌ 行情数据抓取失败")
        return

    # 2. 增量同步数据库
    new_count, total_count = dc.sync_and_get_new(df)

    # 3. 筛选资金最活跃的 12 只个股 (按成交额排序)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        name = row['name']
        code = row['code']
        print(f"📊 正在处理: {name} ({code})...")
        
        # 4. 抓取该个股的【筹码分布】数据
        chip_info = dc.get_chip_data(code)
        
        # 5. 合并所有数据维度 (基础行情 + 增强指标 + 筹码指标)
        combined_info = row.to_dict()
        combined_info.update(chip_info)
        
        # 6. 调用 AI 进行大数据补全分析
        ai_report = get_ai_analysis(name, str(combined_info))
        
        # 如果 AI 失败，使用基础兜底数据
        if not ai_report:
            ai_report = {
                "stock_name": name,
                "stock_code": code,
                "price": str(row['price']),
                "change": str(row['change']),
                "insights": "⚠️ 实时 AI 通道拥堵。技术面：换手率与筹码集中度显示资金博弈激烈，建议关注平均成本位支撑。",
                "buy_point": "盘中观察",
                "stop_loss": "参考5日线",
                "sentiment_score": 50
            }
        
        # 将筹码和行情数据合并进最终结果，供 HTML 渲染
        ai_report.update(combined_info)
        ai_results.append(ai_report)

    # 7. 渲染 HTML 看板
    if ai_results:
        generate_report(ai_results, new_count, total_count)
        print(f"✅ 任务完成！今日新增: {new_count}, 总数: {total_count}")

if __name__ == "__main__":
    main()











