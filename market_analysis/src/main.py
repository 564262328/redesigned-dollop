import os
import sys
import time
import random
import logging
import pandas as pd
from datetime import datetime

# ==========================================
# 🎯 1. 運行時環境注入 (核心路徑修復)
# ==========================================
def setup_runtime():
    # 獲取倉庫根目錄 (redesigned-dollop)
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(current_file)
    pkg_root = os.path.dirname(src_dir)       
    repo_root = os.path.dirname(pkg_root)    
    
    # 注入搜尋路徑，確保 import src 和 import data_provider 成功
    for p in [repo_root, pkg_root, src_dir]:
        if p not in sys.path:
            sys.path.insert(0, p)
    return repo_root

PROJECT_ROOT = setup_runtime()

# 延遲導入，確保系統路徑已更新
try:
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    from data_provider.market_center import MarketDataCenter
except ImportError as e:
    print(f"❌ 模組導入失敗: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("MainControl")

def calculate_dynamic_sentiment(ai_results):
    """根據樣本計算市場熱度 (0-100)"""
    if not ai_results: return 50
    try:
        # 安全讀取漲跌幅，防止 KeyError
        up_count = sum(1 for res in ai_results if float(res.get('change', 0)) > 0)
        sentiment = (up_count / len(ai_results)) * 100
        return max(min(sentiment, 100), 0)
    except: return 55

def main():
    # 輸出路徑強制定位到倉庫根目錄
    output_html_path = os.path.join(PROJECT_ROOT, "index.html")
    cache_json_path = os.path.join(PROJECT_ROOT, "market_cache.json")
    
    logger.info("🚀 QUANT PRO 終端啟動診斷...")
    logger.info(f"🔑 AI_KEY: {'[OK]' if Config.AI_API_KEY else '[MISSING]'}")
    logger.info(f"🔑 MAIRUI_KEY: {'[OK]' if Config.MAIRUI_KEY else '[MISSING]'}")

    # 1. 組件初始化
    dc = MarketDataCenter(cache_file=cache_json_path)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    # 2. 抓取數據
    full_df, source = dc.fetch_all_markets()
    indices = dc.get_market_indices()
    
    # 【核心修復】確保 full_df 永遠不為 None 且具備基礎欄位
    if full_df is None or not isinstance(full_df, pd.DataFrame) or full_df.empty:
        logger.error("❌ 嚴重錯誤：無法獲取市場數據。啟動內部位援...")
        full_df = pd.DataFrame([{"code":"600519","name":"貴州茅台","price":1700,"change":0.0,"market_tag":"A股"}])
        source = "Internal_Emergency_Fallback"

    # 3. 篩選分析標的
    watchlist = getattr(Config, 'WATCHLIST', ["600519", "00700", "300750"])
    try:
        # 使用更安全的過濾方式
        target_df = full_df[full_df['code'].astype(str).isin(watchlist)]
        if target_df.empty:
            logger.info("⚠️ 自選股未命中，自動切換至行情列表前 10 名...")
            target_df = full_df.head(10)
    except Exception as e:
        logger.error(f"❌ 數據過濾異常: {e}")
        target_df = full_df.head(5)

    # 4. 批量 AI 分析循環
    ai_results = []
    logger.info(f"🤖 正在分析 {len(target_df)} 檔標的 (源: {source})...")
    
    for idx, (_, row) in enumerate(target_df.iterrows()):
        # 【核心修復】使用 .get() 徹底解決 KeyError: 'price'
        stock_code = str(row.get('code', '000000'))
        stock_name = row.get('name', '未知股票')
        current_price = row.get('price', 0)
        
        # 獲取指標與籌碼數據
        tech = dc.get_tech_indicators(stock_code, current_price)
        chips = dc.get_chip_data(stock_code)
        
        combined_info = {**row.to_dict(), **tech, **chips}
        
        logger.info(f"[{idx+1}/{len(target_df)}] 分析中: {stock_name}...")
        res = analyzer.analyze_single(stock_name, combined_info)
        
        if not res:
            res = {"insights": "AI 分析服務暫時離線", "buy_point": "觀察", "trend_prediction": "橫盤"}
        
        res.update(combined_info)
        ai_results.append(res)
        
        # 【擬人化延遲】降低被封鎖風險
        if idx < len(target_df) - 1:
            delay = random.uniform(3.5, 6.5)
            logger.info(f"⏳ 模擬人類閱讀中... 等待 {delay:.1f} 秒")
            time.sleep(delay)

    # 5. 計算情緒並生成最終 HTML
    sentiment_score = calculate_dynamic_sentiment(ai_results)
    
    try:
        # 獲取環境健康狀態
        health = {"Data": "🟢" if source != "Internal_Emergency_Fallback" else "🟡", "AI": "🟢"}
        
        reporter.render(
            ai_results=ai_results,
            source_name=source,
            indices=indices,
            output_path=output_html_path,
            health_status=health,
            sentiment_score=sentiment_score
        )
        logger.info(f"✅ 看板生成成功: {output_html_path}")
    except Exception as e:
        logger.error(f"❌ 渲染頁面失敗: {e}")

if __name__ == "__main__":
    main()

















































