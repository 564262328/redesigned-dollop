import os
import sys
import time
import argparse
import logging
import pandas as pd
from datetime import datetime

# ==========================================
# 🎯 核心路徑與導入修復引擎
# ==========================================
def setup_runtime_env():
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(current_file)
    pkg_root = os.path.dirname(src_dir)       # /market_analysis
    repo_root = os.path.dirname(pkg_root)    # 倉庫根目錄 (redesigned-dollop)

    # 強制注入搜尋路徑，確保跨資料夾導入成功
    for p in [repo_root, pkg_root, src_dir]:
        if p not in sys.path:
            sys.path.insert(0, p)
    return repo_root

PROJECT_ROOT = setup_runtime_env()

try:
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    from data_provider.market_center import MarketDataCenter
    from data_provider.news_center import NewsCenter
    print("✅ 所有核心模組導入成功")
except ImportError as e:
    print(f"❌ 導入失敗詳情: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("MainControl")

def calculate_dynamic_sentiment(ai_results):
    """根據樣本計算市場熱度 (0-100)"""
    if not ai_results: return 50
    try:
        up_count = sum(1 for res in ai_results if float(res.get('change', 0)) > 0)
        up_ratio = up_count / len(ai_results)
        avg_rsi = sum(float(res.get('rsi', 50)) for res in ai_results) / len(ai_results)
        sentiment = (up_ratio * 100 * 0.5) + (avg_rsi * 0.5)
        return max(min(sentiment, 100), 0)
    except: return 55

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stocks', type=str)
    parser.add_argument('--dry-run', action='store_true')
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

    # ==========================================
    # 🎯 3. 【修復核心】安全採樣邏輯
    # ==========================================
    watchlist = getattr(Config, 'WATCHLIST', ["600519", "00700", "300750"])
    
    if args.stocks:
        target_df = full_df[full_df['code'].isin(args.stocks.split(','))]
    else:
        # A. 基礎池：自選股 + 漲幅榜
        w_df = full_df[full_df['code'].isin(watchlist)]
        top_df = full_df.sort_values(by='change', ascending=False).head(12)
        combined = pd.concat([w_df, top_df]).drop_duplicates(subset=['code'])
        
        # B. 補足 20 檔：從剩餘池子採樣
        remaining_needed = 20 - len(combined)
        if remaining_needed > 0:
            pool = full_df[~full_df['code'].isin(combined['code'])]
            pool_size = len(pool)
            if pool_size > 0:
                sample_n = min(pool_size, remaining_needed)
                others = pool.sample(n=sample_n)
                target_df = pd.concat([combined, others])
            else:
                target_df = combined
        else:
            target_df = combined.head(20)

    # 4. 批量 AI 分析循環
    ai_results = []
    logger.info(f"🤖 正在分析 {len(target_df)} 檔標的 (源: {source})...")
    
    # ... 前面 1 到 4 步驟代碼保持不變 ...

    # 4. 批量 AI 分析循環
    for idx, (_, row) in enumerate(target_df.iterrows()):
        stock_code = str(row['code'])
        tech = dc.get_tech_indicators(stock_code, row['price']) if hasattr(dc, 'get_tech_indicators') else {}
        chips = dc.get_chip_data(stock_code)
        combined_info = {**row.to_dict(), **tech, **chips}
        
        if not args.dry_run:
            print(f"[{idx+1}/{len(target_df)}] 分析中: {row['name']}...")
            res = analyzer.analyze_single(row['name'], combined_info)
            if not res:
                res = {"insights": "AI 同步中...", "buy_point": "觀察", "trend_prediction": "盤整"}
        else:
            res = {"insights": "Dry Run 測試", "buy_point": "-", "trend_prediction": "-"}

        res.update(combined_info)
        ai_results.append(res)
        
        # ==========================================
        # 🎯 【新增在此處】擬人化延遲防封號
        # ==========================================
        if idx < len(target_df) - 1: # 如果不是最後一檔，就等待
            # 這裡我們將原本固定的 1.5 秒換成隨機的 3.5 到 6.5 秒
            sleep_time = random.uniform(3.5, 6.5)
            logger.info(f"⏳ 模擬人類閱讀中... 等待 {sleep_time:.1f} 秒後分析下一檔")
            time.sleep(sleep_time)
        # ==========================================

    # 5. 生成與發布
    sentiment_score = calculate_dynamic_sentiment(ai_results)
    health = {"TX": "🟢", "Sina": "🟢", "Cache": "🔵" if "Cache" in source else "⚪"}

    output_html_path = os.path.join(PROJECT_ROOT, "index.html") # Force root path
    
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
        logger.error(f"渲染失敗: {e}")

if __name__ == "__main__":
    main()














































