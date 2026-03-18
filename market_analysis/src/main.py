import os
import sys
import time
import argparse
import logging
import pandas as pd
from datetime import datetime

# --- 🎯 終極路徑自癒系統 ---
CURRENT_FILE = os.path.abspath(__file__)
SRC_DIR = os.path.dirname(CURRENT_FILE)
PKG_ROOT = os.path.dirname(SRC_DIR)      # .../market_analysis
REPO_ROOT = os.path.dirname(PKG_ROOT)   # .../redesigned-dollop

# 將路徑加入 sys.path，確保可以導入 data_provider.*
for p in [PKG_ROOT, REPO_ROOT, SRC_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    # 診斷：嘗試導入，失敗則列出資料夾內容
    try:
        from data_provider.market_center import MarketDataCenter
        from data_provider.news_center import NewsCenter
    except ImportError as e:
        print(f"❌ 導入失敗！檢查資料夾內容:")
        dp_path = os.path.join(PKG_ROOT, "data_provider")
        if os.path.exists(dp_path):
            print(f"📂 {dp_path} 內容: {os.listdir(dp_path)}")
        raise e
    print("✅ 模組導入成功")
except ImportError as e:
    print(f"❌ 嚴重導入失敗: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("MainControl")

def calculate_dynamic_sentiment(ai_results):
    if not ai_results: return 50
    up_count = sum(1 for res in ai_results if float(res.get('change', 0)) > 0)
    avg_rsi = sum(float(res.get('rsi', 50)) for res in ai_results) / len(ai_results)
    return max(min((up_count/len(ai_results)*100*0.5) + (avg_rsi*0.5), 100), 0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stocks', type=str)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    output_html = os.path.join(REPO_ROOT, "index.html")
    cache_json = os.path.join(REPO_ROOT, "market_cache.json")
    
    logger.info(f"🚀 QUANT PRO V15.8 PRO 啟動...")

    dc = MarketDataCenter(cache_file=cache_json)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    full_df, source = dc.fetch_all_markets()
    if full_df.empty: return

    # 挑選 20 檔標的
    top_10 = full_df.sort_values(by='change', ascending=False).head(10)
    target_df = pd.concat([top_10, full_df.sample(n=min(len(full_df), 10))]).drop_duplicates(subset=['code']).head(20)

    ai_results = []
    logger.info(f"🤖 正在分析 {len(target_df)} 檔標的...")
    
    for idx, (_, row) in enumerate(target_df.iterrows()):
        tech = dc.get_tech_indicators(row['code'], row['price']) if hasattr(dc, 'get_tech_indicators') else {}
        chips = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **tech, **chips}
        
        if not args.dry_run:
            print(f"[{idx+1}/20] 執行 RAG 檢索: {row['name']}...")
            res = analyzer.analyze_single(row['name'], combined)
        else:
            res = {"insights": "Dry Run", "buy_point": "-", "trend_prediction": "-"}

        res.update(combined)
        ai_results.append(res)
        time.sleep(1.5)

    health = {"TX": "🟢", "Sina": "🟢", "Cache": "🔵" if "Cache" in source else "⚪"}
    reporter.render(ai_results, source, dc.get_market_indices(), output_html, health, calculate_dynamic_sentiment(ai_results))
    logger.info(f"✅ 任務完成！目標: {output_html}")

if __name__ == "__main__":
    main()












































