import os
import sys
import json
import time
import requests
import pandas as pd

# 1. 核心路徑修正：確保能找到同級與上級模組
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR) # market_analysis
PROJECT_ROOT = os.path.dirname(PARENT_DIR) # redesigned-dollop (根目錄)

# 將 market_analysis 加入路徑，方便導入 src.* 和 data_provider.*
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from src.analyzer import StockAnalyzer
from src.reporter import ReportGenerator
from data_provider.market_center import MarketDataCenter

def main():
    # 定義全局路徑
    output_path = os.path.join(PROJECT_ROOT, "index.html")
    cache_path = os.path.join(PROJECT_ROOT, "market_cache.json")

    print(f"🚀 QUANT Terminal V15.8 PRO 啟動...")
    print(f"📍 項目根目錄: {PROJECT_ROOT}")
    print(f"📍 緩存路徑: {cache_path}")

    # 2. 初始化數據中心 (使用根目錄緩存)
    dc = MarketDataCenter() # 確保您的 MarketDataCenter 內部使用了傳入的 Config 或 cache_path
    df, source = dc.fetch_all() 

    # 3. 獲取健康狀態 (根據您的 data_fetcher 邏輯)
    health_status = {
        "TX": "🟢", 
        "Sina": "🟢", 
        "Cache": "🔵" if "Cache" in source else "⚪"
    }

    # 4. 批量 AI 分析 (20 檔)
    analyzer = StockAnalyzer()
    ai_results = analyzer.batch_process(df, dc)

    # 5. 生成美化報告
    reporter = ReportGenerator()
    try:
        # 調用您的 ReportGenerator.render 方法
        # 確保您的 render 方法接收 output_path 參數
        reporter.render(ai_results, source, dc.get_market_indices())
        
        # 強制將生成的文件從當前目錄移動到根目錄 (如果 reporter 沒寫對路徑的保險措施)
        if not os.path.exists(output_path) and os.path.exists("index.html"):
             os.rename("index.html", output_path)
             
        print(f"✅ 報告生成成功: {output_path}")
    except Exception as e:
        print(f"❌ 報告寫入失敗: {e}")

if __name__ == "__main__":
    main()





































