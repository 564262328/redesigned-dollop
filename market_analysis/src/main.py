import os
import sys
import time
import argparse
import logging
import pandas as pd
from datetime import datetime

# ==========================================
# 🎯 核心路徑與導入修復區 (Critical Fix)
# ==========================================
# 檔案位置: market_analysis/src/main.py
CURRENT_FILE_PATH = os.path.abspath(__file__)
SRC_DIR = os.path.dirname(CURRENT_FILE_PATH)          # .../market_analysis/src
PKG_ROOT = os.path.dirname(SRC_DIR)                   # .../market_analysis
PROJECT_ROOT = os.path.dirname(PKG_ROOT)              # .../redesigned-dollop (倉庫根目錄)

# 強制將 PKG_ROOT 加入搜尋路徑，確保可以找到 data_provider
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

try:
    # 這裡的導入現在能同時匹配本地與 Actions 環境
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    from data_provider.market_center import MarketDataCenter
    print("✅ 模組導入成功")
except ImportError as e:
    print(f"❌ 導入失敗詳情: {e}")
    print(f"📍 嘗試路徑 (PKG_ROOT): {PKG_ROOT}")
    # 列出 PKG_ROOT 目錄內容以便除錯
    if os.path.exists(PKG_ROOT):
        print(f"📂 目錄內容: {os.listdir(PKG_ROOT)}")
    sys.exit(1)

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("MainControl")

def calculate_dynamic_sentiment(ai_results):
    """[視覺進化] 動態熱度算法：漲跌分佈(50%) + RSI(50%)"""
    if not ai_results: return 50
    try:
        up_count = sum(1 for res in ai_results if float(res.get('change', 0)) > 0)
        up_ratio = up_count / len(ai_results)
        avg_rsi = sum(float(res.get('rsi', 50)) for res in ai_results) / len(ai_results)
        sentiment = (up_ratio * 100 * 0.5) + (avg_rsi * 0.5)
        return max(min(sentiment, 100), 0)
    except: return 50

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stocks', type=str, help='指定代碼分析')
    parser.add_argument('--dry-run', action='store_true', help='僅抓取不分析')
    args = parser.parse_args()

    # 定義全局文件輸出路徑（確保 index.html 生成在倉庫最外層根目錄）
    output_html_path = os.path.join(PROJECT_ROOT, "index.html")
    cache_json_path = os.path.join(PROJECT_ROOT, "market_cache.json")
    
    logger.info(f"🚀 QUANT PRO V15.8 PRO 啟動...")
    logger.info(f"📍 HTML 輸出路徑: {output_html_path}")

    # 1. 初始化
    dc = MarketDataCenter(cache_file=cache_json_path)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    # 2. 獲取數據
    full_df, source = dc.fetch_all_markets()
    indices = dc.get_market_indices()
    
    if full_df.empty:
        logger.error("數據源全面封鎖，任務終止。")
        return

    # 3. 安全採樣 20 檔 (漲幅前10 + 隨機補充)
    top_10 = full_df.sort_values(by='change', ascending=False).head(10)
    remaining = full_df[~full_df['code'].isin(top_10['code'])]
    others = remaining.sample(n=min(len(remaining), 10))
    target_df = pd.concat([top_10, others]).drop_duplicates(subset=['code']).head(20)

    # 4. 批量 AI 分析
    ai_results = []
    logger.info(f"🤖 正在處理 {len(target_df)} 檔精選標的...")
    
    for idx, (_, row) in enumerate(target_df.iterrows()):
        stock_code = str(row['code'])
        # 獲取技術指標 (#234) 與 籌碼數據
        tech = dc.get_tech_indicators(stock_code, row['price']) if hasattr(dc, 'get_tech_indicators') else {}
        chips = dc.get_chip_data(stock_code)
        combined = {**row.to_dict(), **tech, **chips}
        
        if not args.dry_run:
            print(f"[{idx+1}/20] 分析中: {row['name']}...")
            res = analyzer.analyze_single(row['name'], combined)
            if not res: res = {"insights": "數據同步中...", "buy_point": "觀望", "trend_prediction": "盤整"}
        else:
            res = {"insights": "Dry Run 測試數據", "buy_point": "-", "trend_prediction": "-"}

        res.update(combined)
        ai_results.append(res)
        time.sleep(getattr(Config, 'ANALYSIS_DELAY', 1.5))

    # 5. 生成報告
    sentiment_score = calculate_dynamic_sentiment(ai_results)
    health = {"TX": "🟢", "Sina": "🟢", "Cache": "🔵" if "Cache" in source else "⚪"}
    
    try:
        reporter.render(
            ai_results=ai_results,
            source_name=source,
            indices=indices,
            output_path=output_html_path,
            health_status=health,
            sentiment_score=sentiment_score
        )
        logger.info(f"✅ 終端報告同步成功！")
    except Exception as e:
        logger.error(f"❌ 渲染失敗: {e}")

if __name__ == "__main__":
    main()











































