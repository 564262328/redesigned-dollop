from data_provider.market_center import MarketDataCenter
from src.analyzer import StockAnalyzer
from src.reporter import ReportGenerator
import logging

def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 QUANT PRO 2026 終端啟動...")
    
    # 1. 数据采集与缓存检查
    dc = MarketDataCenter()
    df, source = dc.fetch_all()
    
    # 2. AI 深度分析 (20档)
    analyzer = StockAnalyzer()
    results = analyzer.batch_process(df, dc)
    
    # 3. 生成美化版报告
    reporter = ReportGenerator()
    reporter.render(results, source)
    
    print("✅ 任务圆满完成！")

if __name__ == "__main__":
    main()




































