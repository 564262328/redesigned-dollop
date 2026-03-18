import os
import json
import time
import requests
import pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info, market_context):
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com").rstrip('/')
    if not api_key: return None
    
    try:
        res = requests.post(f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini", 
                "messages": [{"role": "user", "content": f"分析股票 {name} ({info})。大盘: {market_context}。请回传 JSON 包含 insights, buy_point, stop_loss。"}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }, timeout=30)
        content = res.json()['choices']['message']['content']
        return json.loads(content)
    except: return None

def main():
    # --- 🎯 终极路径修复逻辑 ---
    # 获取当前文件 main.py 的绝对路径
    current_file = os.path.abspath(__file__)
    # 获取 src 目录 (market_analysis/src)
    src_dir = os.path.dirname(current_file)
    # 向上跳两级到达项目根目录 (reDesigned-dollop)
    project_root = os.path.dirname(os.path.dirname(src_dir))
    
    # 确保输出路径是在根目录，这样 GitHub Pages 才能读到
    output_path = os.path.join(project_root, "index.html")

    print(f"🚀 QUANT Terminal V15.8 启动...")
    print(f"📍 项目根目录: {project_root}")
    print(f"📍 报告生成路径: {output_path}")

    dc = MarketDataCenter()
    
    # 1. 获取数据与熔断状态
    df, source = dc.get_all_market_data()
    
    health_status = {}
    now = time.time()
    for s_name, cooldown_time in getattr(dc, '_circuit_breaker', {}).items():
        if cooldown_time == 0: health_status[s_name] = "🟢 正常"
        elif now < cooldown_time: health_status[s_name] = f"🔴 熔断 ({int(cooldown_time - now)}s)"
        else: health_status[s_name] = "🟡 恢复中"

    if df.empty:
        print("❌ 错误：所有数据源已熔断，无法更新报告。")
        return

    # 2. 获取辅助数据
    indices = dc.get_market_indices()
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. 挑选前 12 档标的分析
    hot_df = df.sort_values(by='change', ascending=False).head(12)
    ai_results = []
    
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        chip = dc.get_chip_data(code)
        combined = {**row.to_dict(), **chip}
        
        print(f"🤖 AI 分析中: {row['name']}...")
        analysis = get_ai_analysis(row['name'], str(combined), str(indices))
        if not analysis:
            analysis = {"insights": "数据源波动，建议关注支撑位。", "buy_point": "观望", "stop_loss": "前低"}
        
        analysis.update(combined)
        ai_results.append(analysis)

    # 4. 调用生成报告 (严格匹配 8 个参数顺序)
    generate_report(
        ai_results, 
        new_count, 
        total_count, 
        source, 
        dc.get_industry_heatmap(), 
        indices, 
        output_path, 
        health_status
    )
    
    print(f"✅ 报告更新成功！生成位置: {output_path}")

if __name__ == "__main__":
    main()

























