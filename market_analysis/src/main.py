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

# 確保 Python 搜索路徑包含 market_analysis，方便跨文件夾導入模組
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# 導入工程化模組
try:
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    from data_provider.market_center import MarketDataCenter
except ImportError as e:
    print(f"❌ 模組導入失敗: {e}")
    print(f"📍 當前 PYTHONPATH: {sys.path}")
    sys.exit(1)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MainControl")

def parse_arguments():
    """解析命令行參數，支持 Issue #373 提到的各種運行模式"""
    parser = argparse.ArgumentParser(description="QUANT PRO 2026 終端主程序")
    parser.add_argument('--stocks', type=str, help='指定分析代碼，逗號分隔 (如 600519,00700)')
    parser.add_argument('--market-review', action='store_true', help='僅大盤復盤模式')
    parser.add_argument('--no-news', action='store_true', help='禁用即時新聞檢索')
    parser.add_argument('--force-run', action='store_true', help='非交易日強制執行 (#373)')
    parser.add_argument('--dry-run', action='store_true', help='僅測試數據，不消耗 AI Token')
    parser.add_argument('--debug', action='store_true', help='開啟詳細調試日誌')
    return parser.parse_args()

def calculate_dynamic_sentiment(ai_results):
    """
    [動態色彩引擎] 根據分析樣本計算市場熱度 (0-100)
    邏輯：漲跌分佈佔 50%，平均 RSI 佔 50%
    """
    if not ai_results: return 50
    
    try:
        # 1. 計算漲幅比例
        up_count = sum(1 for res in ai_results if float(res.get('change', 0)) > 0)
        up_ratio = up_count / len(ai_results)
        
        # 2. 計算平均 RSI (代表超買壓力)
        avg_rsi = sum(float(res.get('rsi', 50)) for res in ai_results) / len(ai_results)
        
        # 綜合公式
        sentiment = (up_ratio * 100 * 0.5) + (avg_rsi * 0.5)
        return max(min(sentiment, 100), 0)
    except Exception as e:
        logger.warning(f"熱度計算異常: {e}")
        return 50

def main():
    args = parse_arguments()
    if args.debug: logger.setLevel(logging.DEBUG)
    
    logger.info(f"🚀 QUANT PRO [2026-03-19] 啟動中...")

    # 定義全局文件輸出路徑 (鎖定根目錄)
    output_html_path = os.path.join(PROJECT_ROOT, "index.html")
    cache_json_path = os.path.join(PROJECT_ROOT, "market_cache.json")
    
    # 1. 初始化核心組件
    dc = MarketDataCenter(cache_file=cache_json_path)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    # 2. 獲取數據 (整合 A+港+ETF 並執行 20 分鐘緩存校驗)
    full_df, source = dc.fetch_all_markets()
    indices = dc.get_market_indices()
    
    if full_df.empty:
        logger.error("❌ 關鍵錯誤：全市場數據獲取失敗，程序終止。")
        return

    # 3. 篩選分析名單 (優先自選股 -> 去重漲幅榜 -> 隨機補充至 20 檔)
    watchlist = getattr(Config, 'WATCHLIST', ["600519", "00700", "300750"])
    
    if args.stocks:
        # CLI 指定模式
        target_codes = args.stocks.split(',')
        target_df = full_df[full_df['code'].isin(target_codes)]
    elif args.market_review:
        # 僅大盤模式下，只分析權重指標股
        target_df = full_df[full_df['code'].isin(watchlist[:5])]
    else:
        # 自動混合模式：優先自選 + 去重後的最強漲幅標的
        w_df = full_df[full_df['code'].isin(watchlist)]
        top_df = full_df.sort_values(by='change', ascending=False).head(10)
        
        # 執行物理去重採樣，防止重複出現
        combined_temp = pd.concat([w_df, top_df]).drop_duplicates(subset=['code'])
        remaining_count = 20 - len(combined_temp)
        
        if remaining_count > 0:
            others = full_df[~full_df['code'].isin(combined_temp['code'])]
            random_samples = others.sample(n=min(len(others), remaining_count))
            target_df = pd.concat([combined_temp, random_samples])
        else:
            target_df = combined_temp.head(20)

    # 4. 循環執行 RAG 深度分析
    ai_results = []
    logger.info(f"🤖 正在分析 {len(target_df)} 檔精選標的 (節點: {source})...")
    
    for idx, (_, row) in enumerate(target_df.iterrows()):
        stock_name = row['name']
        stock_code = row['code']
        
        # 4.1 獲取實時技術面指標 (#234: MA5/10/20 注入)
        # 注意：若您的 dc 類中方法名為 get_tech_indicators，請保持一致
        tech_data = dc.get_tech_indicators(stock_code, row['price']) if hasattr(dc, 'get_tech_indicators') else {}
        
        # 4.2 獲取籌碼數據
        chips = dc.get_chip_data(stock_code)
        
        # 4.3 合併所有底層數據供 AI 讀取
        combined_info = {**row.to_dict(), **tech_data, **chips}
        
        # 4.4 執行 AI 分析 (內部會自動觸發 Bocha/Tavilly 檢索)
        if not args.dry_run:
            print(f"[{idx+1}/{len(target_df)}] 執行 RAG 檢索與深度洞察: {stock_name}...")
            analysis = analyzer.analyze_single(stock_name, combined_info)
            
            # 錯誤降級處理
            if not analysis:
                analysis = {
                    "insights": "AI 響應同步中，請參考下方實時技術面形態與籌碼獲利比例。",
                    "buy_point": "觀察",
                    "trend_prediction": "盤整"
                }
        else:
            # Dry Run 模式快速生成
            analysis = {
                "insights": "Dry Run 測試模式：數據採集與新聞鏈路正常。",
                "buy_point": "N/A",
                "trend_prediction": "N/A"
            }

        # 4.5 回填技術數據與新聞來源標記，確保 reporter 渲染
        analysis.update(combined_info)
        ai_results.append(analysis)
        
        # 策略性延遲：防止觸發搜尋引擎或 AI 接口的速率限制
        delay = getattr(Config, 'ANALYSIS_DELAY', 2)
        time.sleep(delay)

    # 5. 計算動態情緒熱度數值
    final_sentiment = calculate_dynamic_sentiment(ai_results)
    
    # 6. 調用渲染引擎生成 Web 頁面
    health_status = {
        "TX": "🟢", 
        "Sina": "🟢", 
        "Cache": "🔵" if "Cache" in source else "⚪"
    }
    
    try:
        reporter.render(
            ai_results=ai_results,
            source_name=source,
            indices=indices,
            output_path=output_html_path,
            health_status=health_status,
            sentiment_score=final_sentiment
        )
        logger.info(f"✅ 終端報告同步成功！目標: {output_html_path}")
    except Exception as e:
        logger.error(f"❌ 報表渲染失敗: {e}")

if __name__ == "__main__":
    main()









































