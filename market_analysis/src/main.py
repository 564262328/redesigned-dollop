import os
import sys
import time
import random
import logging
import argparse
import pandas as pd
from datetime import datetime

def setup_runtime_env():
    # Force the root directory as the source for all imports
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(current_file)
    pkg_root = os.path.dirname(src_dir)       
    repo_root = os.path.dirname(pkg_root)    
    
    for p in [repo_root, pkg_root, src_dir]:
        if p not in sys.path:
            sys.path.insert(0, p)
    return repo_root

PROJECT_ROOT = setup_runtime_env()

# Imports after path setup
try:
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    from data_provider.market_center import MarketDataCenter
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("MainControl")

def calculate_dynamic_sentiment(ai_results):
    if not ai_results: return 50
    try:
        up_count = sum(1 for res in ai_results if float(res.get('change', 0)) > 0)
        sentiment = (up_count / len(ai_results)) * 100
        return max(min(sentiment, 100), 0)
    except: return 55

def main():
    # ABSOLUTE PATHS ARE KEY
    output_html_path = os.path.join(PROJECT_ROOT, "index.html")
    cache_json_path = os.path.join(PROJECT_ROOT, "market_cache.json")
    
    logger.info(f"🚀 QUANT PRO V15.8 Deployment Started")

    dc = MarketDataCenter(cache_file=cache_json_path)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    full_df, source = dc.fetch_all_markets()
    indices = dc.get_market_indices()
    
    if full_df.empty:
        logger.error("Data source failed.")
        return

    # Sampling logic
    watchlist = getattr(Config, 'WATCHLIST', ["600519", "00700", "300750"])
    target_df = full_df[full_df['code'].isin(watchlist)].head(15)

    ai_results = []
    for idx, (_, row) in enumerate(target_df.iterrows()):
        stock_code = str(row['code'])
        # Get indicators from MarketDataCenter
        tech = dc.get_tech_indicators(stock_code, row['price'])
        chips = dc.get_chip_data(stock_code)
        
        combined_info = {**row.to_dict(), **tech, **chips}
        
        logger.info(f"[{idx+1}/{len(target_df)}] Analyzing: {row['name']}")
        res = analyzer.analyze_single(row['name'], combined_info)
        
        if not res:
            res = {"insights": "AI Syncing...", "buy_point": "Hold", "trend_prediction": "Neutral"}
        
        res.update(combined_info)
        ai_results.append(res)
        
        # Human-like delay
        if idx < len(target_df) - 1:
            wait = random.uniform(3.5, 6.5)
            time.sleep(wait)

    sentiment_score = calculate_dynamic_sentiment(ai_results)
    health = {"Status": "🟢 OK"}
    
    try:
        reporter.render(
            ai_results=ai_results,
            source_name=source,
            indices=indices,
            output_path=output_html_path,
            health_status=health,
            sentiment_score=sentiment_score
        )
        logger.info(f"✅ Dashboard updated at: {output_html_path}")
    except Exception as e:
        logger.error(f"Render failed: {e}")

if __name__ == "__main__":
    main()














































