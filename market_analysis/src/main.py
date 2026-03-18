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
                "messages": [{"role": "user", "content": f"分析股票 {name} ({info})。大盤: {market_context}。請回傳 JSON 包含 insights, buy_point, stop_loss。"}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }, timeout=30)
        content = res.json()['choices']['message']['content']
        return json.loads(content)
    except: return None

def main():
    # --- 精確路徑計算 ---
    # 獲取 main.py 所在目錄 (market_analysis/src)
    src_dir = os.path.dirname(os.path.abspath(__file__))
    # 向上跳兩級，到達項目根目錄 (/)
    project_root = os.path.dirname(os.path.dirname(src_dir))
    output_path = os.path.join(project_root, "index.html")

    print(f"🚀 QUANT Terminal V15.8 啟動...")
    print(f"📍 當前工作目錄: {os.getcwd()}")
    print(f"📍 報告目標路徑: {output_path}")

    dc = MarketDataCenter()
    
    # 1. 獲取數據與當前熔斷狀態
    df, source = dc.get_all_market_data()
    
    health_status = {}
    now = time.time()
    # 確保 dc._circuit_breaker 存在 (由 data_fetcher 定義)
    for s_name, cooldown_time in getattr(dc, '_circuit_breaker', {}).items():
        if cooldown_time == 0: health_status[s_name] = "🟢 正常"
        elif now < cooldown_time: health_status[s_name] = f"🔴 熔斷 ({int(cooldown_time - now)}s)"
        else: health_status[s_name] = "🟡 恢復中"

    if df.empty:
        print("❌ 嚴重錯誤：數據源全線失效，無法更新。")
        return

    # 2. 獲取輔助數據
    indices = dc.get_market_indices()
    industry_data = dc.get_industry_heatmap()
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. 挑選前 12 檔標的分析 (包含行業標籤)
    hot_df = df.sort_values(by='change', ascending=False).head(12)
    ai_results = []
    
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        chip = dc.get_chip_data(code)
        combined = {**row.to_dict(), **chip}
        
        print(f"🤖 正在分析: {row['name']} ({code})...")
        analysis = get_ai_analysis(row['name'], str(combined), str(indices))
        if not analysis:
            analysis = {"insights": "AI 響應超時，建議參考技術指標。", "buy_point": "觀察中", "stop_loss": "前低"}
        
        analysis.update(combined)
        ai_results.append(analysis)

    # 4. 調用生成報告
    generate_report(ai_results, new_count, total_count, source, industry_data, indices, output_path, health_status)
    
    # 最終校驗：檢查文件是否真的寫入了
    if os.path.exists(output_path):
        print(f"✅ 成功！文件已寫入根目錄: {output_path}")
    else:
        print(f"❌ 警告：文件寫入失敗，請檢查權限。")

if __name__ == "__main__":
    main()
























