import os
import sys
import time
import argparse
import logging
import pandas as pd
from datetime import datetime

# --- 🎯 核心路徑自動化校準 ---
# 當前路徑: /market_analysis/src/main.py -> 跳三級到達項目根目錄
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)  # /market_analysis
PROJECT_ROOT = os.path.dirname(PARENT_DIR) # / (redesigned-dollop)

# 確保 Python 搜索路徑包含 market_analysis，方便模組導入
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# 導入自定義模組 (請確保檔案已存在於對應資料夾)
from src.config import Config
from src.analyzer import StockAnalyzer
from src.reporter import ReportGenerator
from data_provider.market_center import MarketDataCenter

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MainControl")

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="QUANT PRO 2026 終端主程序")
    parser.add_argument('--stocks', type=str, help='指定分析代碼，逗號分隔 (如 600519,00700)')
    parser.add_argument('--no-news', action='store_true', help='禁用新聞檢索功能')
    parser.add_argument('--force-run', action='store_true', help='非交易日強制執行')
    parser.add_argument('--dry-run', action='store_true', help='僅抓取數據，不調用 AI')
    parser.add_argument('--realtime-tech', default='on', choices=['on', 'off'], help='實時技術面計算開關')
    return parser.parse_args()

def calculate_dynamic_sentiment(ai_results):
    """
    [視覺進化] 根據 20 檔標的的數據動態計算市場熱度 (0-100)
    公式：50% 漲跌分佈 + 50% 平均 RSI
    """
    if not ai_results: return 50
    
    # 1. 漲幅貢獻
    up_count = sum(1 for res in ai_results if float(res.get('change', 0)) > 0)
    up_ratio = up_count / len(ai_results)
    
    # 2. RSI 貢獻 (平均超買壓力)
    avg_rsi = sum(float(res.get('rsi', 50)) for res in ai_results) / len(ai_results)
    
    # 綜合評分
    sentiment = (up_ratio * 100 * 0.5) + (avg_rsi * 0.5)
    return max(min(sentiment, 100), 0)

def main():
    args = parse_arguments()
    logger.info(f"🚀 QUANT PRO [2026-03-19] 啟動中...")

    # 定義全局文件路徑
    output_path = os.path.join(PROJECT_ROOT, "index.html")
    cache_path = os.path.join(PROJECT_ROOT, "market_cache.json")
    
    # 1. 初始化數據中心與分析器
    dc = MarketDataCenter(cache_file=cache_path)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    # 2. 獲取全市場數據 (A+港+ETF 合併去重版)
    full_df, source = dc.fetch_all_markets()
    indices = dc.get_market_indices()
    
    if full_df.empty:
        logger.error("❌ 數據採集終止：全數據源失效。")
        return

    # 3. 篩選分析標的 (自選優先 -> 漲幅前10 -> 隨機補充)
    watchlist = Config.WATCHLIST if hasattr(Config, 'WATCHLIST') else []
    
    if args.stocks:
        # 如果 CLI 指定了股票代碼
        target_codes = args.stocks.split(',')
        target_df = full_df[full_df['code'].isin(target_codes)]
    else:
        # 自動模式：優先 Watchlist
        w_df = full_df[full_df['code'].isin(watchlist)]
        # 漲幅榜前 10 (去重)
        top_df = full_df.sort_values(by='change', ascending=False).head(10)
        # 隨機補充剩餘名額至 20 檔
        others = full_df[~full_df['code'].isin(pd.concat([w_df, top_df])['code'])]
        target_df = pd.concat([w_df, top_df, others.sample(n=min(len(others), 5))]).drop_duplicates(subset=['code']).head(20)

    # 4. 批量執行分析任務
    ai_results = []
    logger.info(f"🤖 正在分析 {len(target_df)} 檔精選標的 (來源: {source})...")
    
    for idx, (_, row) in enumerate(target_df.iterrows()):
        stock_name = row['name']
        stock_code = row['code']
        
        # 4.1 獲取籌碼與實時技術指標 (Issue #234)
        tech_data = dc.get_tech_indicators(stock_code, row['price']) if hasattr(dc, 'get_tech_indicators') else {}
        chips = dc.get_chip_data(stock_code)
        
        # 4.2 整合行情數據
        combined_info = {**row.to_dict(), **tech_data, **chips}
        
        # 4.3 執行 AI 分析 (帶 RAG 新聞檢索)
        if not args.dry_run:
            print(f"[{idx+1}/{len(target_df)}] 正在解析消息面與技術面: {stock_name}...")
            analysis = analyzer.analyze_single(stock_name, combined_info)
            # 若分析失敗則給予保底佔位符
            if not analysis:
                analysis = {"insights": "AI 響應同步中，請參考基本面與技術均線。", "buy_point": "觀望", "trend_prediction": "盤整"}
        else:
            analysis = {"insights": "Dry Run 模式：僅測試數據獲取，未調用 AI。", "buy_point": "-", "trend_prediction": "-"}

        analysis.update(combined_info)
        ai_results.append(analysis)
        
        # 策略性延遲，防止 API 限流
        time.sleep(Config.ANALYSIS_DELAY if hasattr(Config, 'ANALYSIS_DELAY') else 1.5)

    # 5. 計算動態情緒分數
    sentiment_score = calculate_dynamic_sentiment(ai_results)
    
    # 6. 生成美化版報告
    health_status = {"TX": "🟢", "Sina": "🟢", "Cache": "🔵" if "Cache" in source else "⚪"}
    try:
        reporter.render(
            ai_results=ai_results,
            source_name=source,
            indices=indices,
            output_path=output_path,
            health_status=health_status,
            sentiment_score=sentiment_score
        )
        logger.info(f"✅ 報告更新成功！目標: {output_path}")
    except Exception as e:
        logger.error(f"❌ 報告寫入失敗: {e}")

if __name__ == "__main__":
    main()








































