import os
import sys
import time
import argparse
import logging
import pandas as pd
from datetime import datetime

# ==========================================
# 🎯 自動化路徑與導入修復引擎
# ==========================================
def setup_python_path():
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(current_file)
    pkg_root = os.path.dirname(src_dir)       # .../market_analysis
    repo_root = os.path.dirname(pkg_root)    # .../redesigned-dollop

    # 將所有可能的路徑加入 sys.path
    for path in [repo_root, pkg_root, src_dir]:
        if path not in sys.path:
            sys.path.insert(0, path)
    return pkg_root, repo_root

PKG_ROOT, PROJECT_ROOT = setup_python_path()

# 動態導入：適配檔案命名差異
try:
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    
    # 這裡執行「寬容導入」：嘗試新命名，失敗則回退到舊命名
    try:
        from data_provider.market_center import MarketDataCenter
    except ImportError:
        print("⚠️ 未找到 market_center，嘗試導入舊版 data_fetcher...")
        from data_fetcher import MarketDataCenter
    
    print("✅ 模組導入成功")
except ImportError as e:
    print(f"❌ 嚴重導入失敗: {e}")
    sys.exit(1)

# --- 以下邏輯保持不變 ---
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

    output_html_path = os.path.join(PROJECT_ROOT, "index.html")
    cache_json_path = os.path.join(PROJECT_ROOT, "market_cache.json")
    
    logger.info(f"🚀 QUANT PRO V15.8 啟動 | 目標: {output_html_path}")

    dc = MarketDataCenter(cache_file=cache_json_path)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    full_df, source = dc.fetch_all_markets()
    if full_df.empty: return

    # 採樣與分析邏輯
    top_10 = full_df.sort_values(by='change', ascending=False).head(10)
    target_df = pd.concat([top_10, full_df.sample(n=min(len(full_df), 10))]).drop_duplicates(subset=['code']).head(20)

    ai_results = []
    for idx, (_, row) in enumerate(target_df.iterrows()):
        tech = dc.get_tech_indicators(row['code'], row['price']) if hasattr(dc, 'get_tech_indicators') else {}
        chips = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **tech, **chips}
        
        res = analyzer.analyze_single(row['name'], combined) if not args.dry_run else {"insights":"Dry Run"}
        if res:
            res.update(combined)
            ai_results.append(res)
        time.sleep(1.5)

    reporter.render(ai_results, source, dc.get_market_indices(), output_html_path, {"TX":"🟢","Sina":"🟢"}, calculate_dynamic_sentiment(ai_results))
    logger.info(f"✅ 任務完成")

if __name__ == "__main__":
    main()











































