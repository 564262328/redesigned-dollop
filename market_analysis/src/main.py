import os
import sys
import time
import argparse
import logging
import pandas as pd
from datetime import datetime

# --- 🎯 核心路徑校準 ---
# 檔案位置: market_analysis/src/main.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))    # .../market_analysis/src
PARENT_DIR = os.path.dirname(CURRENT_DIR)                 # .../market_analysis
PROJECT_ROOT = os.path.dirname(PARENT_DIR)                # .../redesigned-dollop (根目錄)

# 將 market_analysis 加入搜尋路徑，確保可以導入 src.* 和 data_provider.*
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    from data_provider.market_center import MarketDataCenter
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    print(f"📍 嘗試路徑: {PARENT_DIR}")
    sys.exit(1)

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("MainControl")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stocks', type=str, help='指定代碼，逗號分隔')
    parser.add_argument('--force-run', action='store_true', help='強制執行')
    parser.add_argument('--dry-run', action='store_true', help='不調用 AI')
    return parser.parse_args()

def calculate_sentiment(ai_results):
    """根據樣本計算市場情緒 (0-100)"""
    if not ai_results: return 50
    up_ratio = sum(1 for r in ai_results if float(r.get('change', 0)) > 0) / len(ai_results)
    avg_rsi = sum(float(r.get('rsi', 50)) for r in ai_results) / len(ai_results)
    score = (up_ratio * 100 * 0.5) + (avg_rsi * 0.5)
    return max(min(score, 100), 0)

def main():
    args = parse_args()
    logger.info("🚀 QUANT PRO 終端啟動...")

    # 定義全局路徑（確保 index.html 和緩存存在最外層根目錄）
    output_html = os.path.join(PROJECT_ROOT, "index.html")
    cache_json = os.path.join(PROJECT_ROOT, "market_cache.json")
    
    # 1. 初始化
    dc = MarketDataCenter(cache_file=cache_json)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    # 2. 數據獲取 (20分鐘緩存共享)
    df, source = dc.fetch_all_markets()
    indices = dc.get_market_indices()
    
    if df.empty:
        logger.error("數據獲取失敗，程序終止")
        return

    # 3. 採樣 20 檔標的 (自選優先 + 漲幅榜 + 去重)
    watchlist = getattr(Config, 'WATCHLIST', ["600519", "00700", "300750"])
    if args.stocks:
        target_df = df[df['code'].isin(args.stocks.split(','))]
    else:
        w_df = df[df['code'].isin(watchlist)]
        top_df = df.sort_values(by='change', ascending=False).head(10)
        target_df = pd.concat([w_df, top_df]).drop_duplicates(subset=['code']).head(20)

    # 4. 批量分析
    ai_results = []
    logger.info(f"🤖 正在分析 {len(target_df)} 檔標的 (源: {source})")
    
    for idx, (_, row) in enumerate(target_df.iterrows()):
        # 獲取技術指標與籌碼
        tech = dc.get_tech_indicators(row['code'], row['price']) if hasattr(dc, 'get_tech_indicators') else {}
        chips = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **tech, **chips}
        
        if not args.dry_run:
            print(f"[{idx+1}/{len(target_df)}] 分析中: {row['name']}...")
            res = analyzer.analyze_single(row['name'], combined)
            if not res:
                res = {"insights": "AI 同步中...", "buy_point": "觀望", "trend_prediction": "盤整"}
        else:
            res = {"insights": "Dry Run 測試", "buy_point": "-", "trend_prediction": "-"}
            
        res.update(combined)
        ai_results.append(res)
        time.sleep(getattr(Config, 'ANALYSIS_DELAY', 2))

    # 5. 生成報告
    sentiment_score = calculate_sentiment(ai_results)
    health = {"TX": "🟢", "Sina": "🟢", "Cache": "🔵" if "Cache" in source else "⚪"}
    
    try:
        reporter.render(
            ai_results=ai_results,
            source_name=source,
            indices=indices,
            output_path=output_html,
            health_status=health,
            sentiment_score=sentiment_score
        )
        logger.info(f"✅ 報告已生成: {output_html}")
    except Exception as e:
        logger.error(f"渲染失敗: {e}")

if __name__ == "__main__":
    main()










































