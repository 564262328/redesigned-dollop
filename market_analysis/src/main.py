import os
import sys
import time
import argparse
import logging
import pandas as pd
from datetime import datetime

# ==========================================
# 🎯 核心路徑與導入修復引擎 (2026 穩定版)
# ==========================================
def setup_runtime_env():
    # 檔案物理位置: /market_analysis/src/main.py
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(current_file)
    pkg_root = os.path.dirname(src_dir)       # /market_analysis
    repo_root = os.path.dirname(pkg_root)    # 倉庫根目錄 (redesigned-dollop)

    # 將所有相關目錄注入系統路徑，確保跨資料夾導入 100% 成功
    paths_to_add = [repo_root, pkg_root, src_dir]
    for p in paths_to_add:
        if p not in sys.path:
            sys.path.insert(0, p)
    
    return repo_root

PROJECT_ROOT = setup_runtime_env()

# 模組導入 (在路徑注入後執行)
try:
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    from data_provider.market_center import MarketDataCenter
    from data_provider.news_center import NewsCenter
    print("✅ 所有核心模組導入成功")
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    sys.exit(1)

# 日誌配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MainControl")

def calculate_dynamic_sentiment(ai_results):
    """根據 20 檔樣本計算市場情緒 (0-100)"""
    if not ai_results: return 50
    try:
        up_count = sum(1 for res in ai_results if float(res.get('change', 0)) > 0)
        up_ratio = up_count / len(ai_results)
        avg_rsi = sum(float(res.get('rsi', 50)) for res in ai_results) / len(ai_results)
        # 混合公式：50% 漲跌分佈 + 50% RSI 超買壓
        sentiment = (up_ratio * 100 * 0.5) + (avg_rsi * 0.5)
        return max(min(sentiment, 100), 0)
    except: return 50

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stocks', type=str, help='指定分析代碼 (如 600519,00700)')
    parser.add_argument('--dry-run', action='store_true', help='僅測試數據不調用 AI')
    args = parser.parse_args()

    # 輸出路徑定位至根目錄
    output_html_path = os.path.join(PROJECT_ROOT, "index.html")
    cache_json_path = os.path.join(PROJECT_ROOT, "market_cache.json")
    
    logger.info(f"🚀 QUANT PRO V15.8 [2026-03-19] 啟動...")

    # 1. 組件初始化
    dc = MarketDataCenter(cache_file=cache_json_path)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    # 2. 獲取數據
    full_df, source = dc.fetch_all_markets()
    indices = dc.get_market_indices()
    
    if full_df.empty:
        logger.error("數據獲取中斷：全數據源失效。")
        return

    # 3. 採樣邏輯：自選優先 -> 漲幅榜 -> 隨機補充至 20 檔
    watchlist = getattr(Config, 'WATCHLIST', ["600519", "00700", "300750"])
    if args.stocks:
        target_df = full_df[full_df['code'].isin(args.stocks.split(','))]
    else:
        w_df = full_df[full_df['code'].isin(watchlist)]
        top_df = full_df.sort_values(by='change', ascending=False).head(12)
        # 物理去重確保不出現重複卡片
        combined = pd.concat([w_df, top_df]).drop_duplicates(subset=['code'])
        remaining = 20 - len(combined)
        if remaining > 0:
            others = full_df[~full_df['code'].isin(combined['code'])].sample(n=min(len(full_df)-len(combined), remaining))
            target_df = pd.concat([combined, others])
        else:
            target_df = combined.head(20)

    # 4. 批量 AI 分析循環
    ai_results = []
    logger.info(f"🤖 正在分析 {len(target_df)} 檔精選標的 (Node: {source})...")
    
    for idx, (_, row) in enumerate(target_df.iterrows()):
        stock_code = str(row['code'])
        # 注入實時技術指標 (#234 MA5/10/20)
        tech = dc.get_tech_indicators(stock_code, row['price']) if hasattr(dc, 'get_tech_indicators') else {}
        chips = dc.get_chip_data(stock_code)
        combined_info = {**row.to_dict(), **tech, **chips}
        
        if not args.dry_run:
            print(f"[{idx+1}/20] 深度檢索並分析: {row['name']}...")
            res = analyzer.analyze_single(row['name'], combined_info)
            if not res:
                res = {"insights": "AI 響應同步中，請參考下方實時數據。", "buy_point": "觀察", "trend_prediction": "盤整"}
        else:
            res = {"insights": "Dry Run 測試模式", "buy_point": "N/A", "trend_prediction": "N/A"}

        res.update(combined_info)
        ai_results.append(res)
        time.sleep(getattr(Config, 'ANALYSIS_DELAY', 1.5)) # 防 API 封鎖

    # 5. 渲染與發布
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
        logger.info(f"✅ 看板更新成功: {output_html_path}")
    except Exception as e:
        logger.error(f"渲染報錯: {e}")

if __name__ == "__main__":
    main()













































