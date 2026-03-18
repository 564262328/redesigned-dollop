import os
import json
import requests
import pandas as pd
from data_fetcher import fetch_multi_source_stock_data
from html_generator import generate_report

def get_ai_analysis_report(stock_name, raw_data_str):
    """
    調用 DeepSeek API 進行金融大數據分析
    """
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ 錯誤: 未找到 DEEPSEEK_API_KEY 環境變量")
        return None

    url = "https://api.deepseek.com"
    
    # 這裡的 Prompt 決定了 AI 輸出的專業程度
    prompt = f"""
    你是資深 A 股量化策略分析師。請根據以下 {stock_name} 的最新數據進行深度解析。
    數據來源：{raw_data_str}
    
    請嚴格返回以下 JSON 格式（不要包含任何 Markdown 標籤或額外文字）：
    {{
      "stock_name": "{stock_name}",
      "stock_code": "從數據中提取代碼",
      "price": "當前股價",
      "change": "漲跌幅(含%)",
      "insights": "150字內技術面分析(含支撐壓力位、籌碼分佈判斷)",
      "buy_point": "具體數字(建議買入位)",
      "stop_loss": "具體數字(建議止損位)",
      "target_price": "具體數字(止盈目標)",
      "sentiment_score": 0-100的整數,
      "history": [
        {{"name": "板塊熱度", "score": 75}},
        {{"name": "大單資金", "score": 60}},
        {{"name": "技術指標", "score": 45}}
      ]
    }}
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一個專業的金融分析 JSON 生成器。"},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        print(f"🤖 正在為 {stock_name} 請求 AI 大數據分析...")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['choices']['message']['content']
    except Exception as e:
        print(f"❌ AI 分析請求失敗: {e}")
        return None

def main():
    # 1. 抓取原始數據 (假設返回一個 DataFrame)
    print("Step 1: 正在獲取市場實時數據...")
    df = fetch_multi_source_stock_data()
    
    if df.empty:
        print("❌ 獲取數據失敗，請檢查網絡或 API 狀態")
        return

    # 2. 準備給 AI 的文本 (取前幾行關鍵數據，節省 Token)
    # 這裡假設你的 DataFrame 有代碼和名稱列
    stock_name = "中國石油" # 也可以從 df 中動態獲取
    raw_data_summary = df.head(5).to_string()

    # 3. 獲取 AI 分析結果
    ai_json_str = get_ai_analysis_report(stock_name, raw_data_summary)
    
    if ai_json_str:
        try:
            # 4. 解析 AI 回傳的 JSON
            report_data = json.loads(ai_json_str)
            print("Step 3: AI 分析成功，準備渲染看板...")
            
            # 5. 調用你之前的 html_generator 生成 index.html
            generate_report(report_data)
            print("🚀 全部流程完成！你的 GitHub Pages 即將更新。")
            
        except json.JSONDecodeError:
            print("❌ AI 回傳的數據格式不正確")
    else:
        print("❌ 無法生成 AI 報告")

if __name__ == "__main__":
    main()

