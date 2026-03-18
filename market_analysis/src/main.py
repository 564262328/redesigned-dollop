import os
import json
import requests
import pandas as pd
from data_fetcher import MarketDataCenter
from html_generator import generate_report

def get_ai_analysis(name, info):
    """
    核心 AI 分析函數：支持 AIHubMix / ChatGPT 中轉
    """
    api_key = os.getenv("AI_API_KEY")
    # 預設使用 AIHubMix 地址，若 Secret 中有自定義則覆蓋
    base_url = os.getenv("AI_BASE_URL", "https://aihubmix.com")
    
    if not api_key:
        print(f"⚠️ 未配置 AI_API_KEY，{name} 將使用備用分析")
        return None

    # 優化 Prompt：要求 AI 提供更具深度的技術指標分析
    prompt = f"""
    作為資深量化交易員，請深度分析 A 股【{name}】。
    原始行情：{info}
    
    請嚴格返回一個 JSON 對象（禁止包含任何 Markdown 代碼塊或額外文字）：
    {{
      "stock_name": "{name}",
      "stock_code": "代碼",
      "price": "現價",
      "change": "漲跌幅%",
      "insights": "200字內技術面分析：包含壓力支撐位、MACD/RSI 狀態、資金流向判斷",
      "buy_point": "精確數字(建議介入位)",
      "stop_loss": "精確數字(建議止損位)",
      "sentiment_score": 0-100數字
    }}
    """

    payload = {
        "model": "gpt-4o-mini", # AIHubMix 推薦模型，性價比極高
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }

    try:
        # 拼接正確的 API 地址
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        print(f"🤖 正在請求 AI 分析: {name} (網關: {base_url})...")
        
        response = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60 # 增加到 60 秒防止超時
        )
        
        if response.status_code == 200:
            return json.loads(response.json()['choices']['message']['content'])
        else:
            print(f"❌ API 報錯 {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ AI 請求異常 ({name}): {e}")
        return None

def main():
    print("🚀 QUANT 終端 V14.6 啟動 (全自動 AI 驅動模式)...")
    dc = MarketDataCenter()
    
    # 1. 獲取全市場行情
    df = dc.get_all_market_data()
    if df.empty:
        print("❌ 無法獲取數據源，請檢查網絡或接口")
        return

    # 2. 增量同步數據庫並獲取統計數字
    new_count, total_count = dc.sync_and_get_new(df)

    # 3. 策略篩選：按成交額排序，選取前 12 隻最活躍個股（資金關注熱點）
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    hot_df = df.sort_values(by='amount', ascending=False).head(12)

    ai_results = []
    for _, row in hot_df.iterrows():
        name = row['name']
        # 調用 AI 進行深度分析
        result = get_ai_analysis(name, row.to_string())
        
        # 4. 容錯處理：若 AI 失敗，使用帶中文的備用數據，不讓網頁顯示英文或空白
        if not result:
            result = {
                "stock_name": name,
                "stock_code": str(row['code']),
                "price": str(row['price']),
                "change": str(row['change']),
                "insights": "⚠️ 實時 AI 網關擁堵。技術觀察：該股成交額巨大，處於市場博弈中心，波動率加劇，建議密切關注支撐位表現。",
                "buy_point": "盤中觀察",
                "stop_loss": "參考5日線",
                "sentiment_score": 50
            }
        ai_results.append(result)

    # 5. 調用 HTML 生成器渲染（傳入 3 個正確參數）
    if ai_results:
        generate_report(ai_results, new_count, total_count)
        print(f"✅ 成功生成看板！今日新增: {new_count}, 市場總數: {total_count}")

if __name__ == "__main__":
    main()








