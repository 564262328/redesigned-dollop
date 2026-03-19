import os
import sys
import time
import random
import logging
from datetime import datetime

# 环境注入
def setup_runtime():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, root)
    sys.path.insert(0, os.path.join(root, "market_analysis"))
    return root

PROJECT_ROOT = setup_runtime()

from src.config import Config
from src.analyzer import StockAnalyzer
from src.reporter import ReportGenerator
from data_provider.market_center import MarketDataCenter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("MainControl")

def main():
    logger.info("🚀 QUANT PRO 终端启动诊断...")
    # 诊断 Secrets (安全脱敏输出)
    logger.info(f"🔑 AI_KEY: {'[OK]' if Config.AI_API_KEY else '[MISSING]'}")
    logger.info(f"🔑 MAIRUI_KEY: {'[OK]' if Config.MAIRUI_KEY else '[MISSING]'}")
    
    dc = MarketDataCenter()
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    # 1. 抓取数据
    full_df, source = dc.fetch_all_markets()
    indices = dc.get_market_indices()
    
    # 2. 筛选标的
    watchlist = Config.WATCHLIST
    target_df = full_df[full_df['code'].isin(watchlist)]
    if len(target_df) < 2:
        logger.info("⚠️ 自选股匹配不足，自动抓取涨幅榜...")
        target_df = full_df.sort_values(by='change', ascending=False).head(10)

    # 3. 循环分析
    ai_results = []
    for idx, (_, row) in enumerate(target_df.iterrows()):
        logger.info(f"[{idx+1}/{len(target_df)}] 分析中: {row['name']}...")
        
        tech = dc.get_tech_indicators(row['code'], row['price'])
        chips = dc.get_chip_data(row['code'])
        combined = {**row.to_dict(), **tech, **chips}
        
        res = analyzer.analyze_single(row['name'], combined)
        res.update(combined)
        ai_results.append(res)
        
        # 拟人化延迟
        if idx < len(target_df) - 1:
            time.sleep(random.uniform(3.0, 6.0))

    # 4. 生成报告
    output_path = os.path.join(PROJECT_ROOT, "index.html")
    reporter.render(
        ai_results=ai_results,
        source_name=source,
        indices=indices,
        output_path=output_path,
        health_status={"Data": "🟢", "AI": "🟢"},
        sentiment_score=65
    )
    logger.info(f"✅ 更新成功: {output_path}")

if __name__ == "__main__":
    main()















































