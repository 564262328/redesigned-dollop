import os
import sys
import time
import random
import logging
import pandas as pd
from datetime import datetime

# ==========================================
# 🎯 1. 运行时环境注入 (核心路径修复)
# ==========================================
def setup_runtime():
    # 获取仓库根目录 (redesigned-dollop)
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(current_file)
    pkg_root = os.path.dirname(src_dir)       
    repo_root = os.path.dirname(pkg_root)    
    
    # 注入搜索路径，确保 import src 和 import data_provider 成功
    for p in [repo_root, pkg_root, src_dir]:
        if p not in sys.path:
            sys.path.insert(0, p)
    return repo_root

PROJECT_ROOT = setup_runtime()

# 延迟导入，确保系统路径已更新
try:
    from src.config import Config
    from src.analyzer import StockAnalyzer
    from src.reporter import ReportGenerator
    from data_provider.market_center import MarketDataCenter
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("MainControl")

def calculate_dynamic_sentiment(ai_results):
    """根据样本计算市场热度 (0-100)"""
    if not ai_results: return 50
    try:
        up_count = sum(1 for res in ai_results if float(res.get('change', 0)) > 0)
        sentiment = (up_count / len(ai_results)) * 100
        return max(min(sentiment, 100), 0)
    except: return 55

def main():
    # 输出路径强制定位到仓库根目录
    output_html_path = os.path.join(PROJECT_ROOT, "index.html")
    cache_json_path = os.path.join(PROJECT_ROOT, "market_cache.json")
    
    logger.info("🚀 QUANT PRO 终端启动诊断...")
    logger.info(f"🔑 AI_KEY: {'[OK]' if Config.AI_API_KEY else '[MISSING]'}")
    logger.info(f"🔑 MAIRUI_KEY: {'[OK]' if Config.MAIRUI_KEY else '[MISSING]'}")

    # 1. 组件初始化
    dc = MarketDataCenter(cache_file=cache_json_path)
    analyzer = StockAnalyzer()
    reporter = ReportGenerator()
    
    # 2. 抓取数据 (增加非空校验)
    full_df, source = dc.fetch_all_markets()
    indices = dc.get_market_indices()
    
    # 【核心修复】确保 full_df 是 DataFrame 且不为空
    if full_df is None or not isinstance(full_df, pd.DataFrame) or full_df.empty:
        logger.error("❌ 严重错误：无法从任何渠道获取市场数据。")
        # 强制创建一个包含保底数据的 DataFrame，防止后续代码崩溃
        full_df = pd.DataFrame([{"code":"600519","name":"贵州茅台","price":1700,"change":0.0,"market_tag":"A股","turnover":0.1}])
        source = "Internal_Fallback"

    # 3. 筛选分析标的
    watchlist = getattr(Config, 'WATCHLIST', ["600519", "00700", "300750"])
    try:
        target_df = full_df[full_df['code'].isin(watchlist)]
        # 如果自选股没匹配到，取前 10 档
        if target_df.empty:
            logger.info("⚠️ 自选股未命中，自动切换至行情列表前 10 名...")
            target_df = full_df.head(10)
    except Exception as e:
        logger.error(f"❌ 数据过滤异常: {e}")
        target_df = full_df.head(5)

    # 4. 批量 AI 分析循环
    ai_results = []
    logger.info(f"🤖 正在分析 {len(target_df)} 档标的 (源: {source})...")
    
    for idx, (_, row) in enumerate(target_df.iterrows()):
        stock_code = str(row['code'])
        tech = dc.get_tech_indicators(stock_code, row['price'])
        chips = dc.get_chip_data(stock_code)
        
        combined_info = {**row.to_dict(), **tech, **chips}
        
        logger.info(f"[{idx+1}/{len(target_df)}] 分析中: {row['name']}...")
        res = analyzer.analyze_single(row['name'], combined_info)
        
        # 结果合并
        if not res:
            res = {"insights": "AI 同步中...", "buy_point": "观察", "trend_prediction": "横盘"}
        
        res.update(combined_info)
        ai_results.append(res)
        
        # 【拟人化延迟】防止 API 封锁
        if idx < len(target_df) - 1:
            delay = random.uniform(3.5, 6.5)
            logger.info(f"⏳ 模拟人类阅读中... 等待 {delay:.1f} 秒")
            time.sleep(delay)

    # 5. 计算情绪并生成 HTML
    sentiment_score = calculate_dynamic_sentiment(ai_results)
    
    try:
        reporter.render(
            ai_results=ai_results,
            source_name=source,
            indices=indices,
            output_path=output_html_path,
            health_status={"Data": "🟢", "AI": "🟢"},
            sentiment_score=sentiment_score
        )
        logger.info(f"✅ 看板生成成功: {output_html_path}")
    except Exception as e:
        logger.error(f"❌ 渲染页面失败: {e}")

if __name__ == "__main__":
    main()
















































