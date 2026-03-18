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
    # --- 🎯 终极路径锁定逻辑 ---
    # 1. 获取 main.py 的绝对路径 (/home/runner/work/repo/repo/market_analysis/src/main.py)
    current_file_path = os.path.abspath(__file__)
    # 2. 获取 src 目录
    src_dir = os.path.dirname(current_file_path)
    # 3. 向上跳两级，到达仓库根目录 (market_analysis/src -> market_analysis -> 根目录)
    project_root = os.path.dirname(os.path.dirname(src_dir))
    
    # 4. 强制设定 index.html 在根目录
    output_path = os.path.join(project_root, "index.html")

    print(f"🚀 QUANT Terminal V15.8 启动...")
    print(f"📍 脚本位置: {current_file_path}")
    print(f"📍 根目录定位: {project_root}")
    print(f"📍 目标生成路径: {output_path}")

    dc = MarketDataCenter()
    
    # 1. 获取数据与熔断状态
    df, source = dc.get_all_market_data()
    
    health_status = {}
    now = time.time()
    # 兼容处理熔断器字典
    breaker = getattr(dc, '_circuit_breaker', {"EM": 0, "Sina": 0, "TX": 0})
    for s_name, cooldown_time in breaker.items():
        if cooldown_time == 0: health_status[s_name] = "🟢 正常"
        elif now < cooldown_time: health_status[s_name] = f"🔴 熔断 ({int(cooldown_time - now)}s)"
        else: health_status[s_name] = "🟡 恢复中"

    if df.empty:
        print("❌ 错误：数据抓取失败，无法更新报告。")
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
            analysis = {"insights": "数据源波动，建议关注筹码分布。", "buy_point": "观望", "stop_loss": "前低"}
        
        analysis.update(combined)
        ai_results.append(analysis)

    # 4. 调用生成报告 (确保 output_path 是计算出的根目录路径)
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
    
    if os.path.exists(output_path):
        print(f"✅ 成功！index.html 已写入: {output_path}")
    else:
        print(f"❌ 警告：文件未能在预期位置生成。")

if __name__ == "__main__":
    main()


























