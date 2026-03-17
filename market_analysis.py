import pandas as pd
import akshare as ak
from datetime import datetime

class StockResolver:
    def __init__(self):
        self.full_market = None
        self.refresh_market_list()

    def refresh_market_list(self):
        """抓取全 A 股实时清单（含代码、名称、最新价）"""
        try:
            # 抓取东财实时行情
            df = ak.stock_zh_a_spot_em()
            # 统一代码格式（如：600519 -> sh600519）
            df['full_code'] = df['代码'].apply(lambda x: ('sh' + x) if x.startswith(('60', '68', '90')) else ('sz' + x))
            self.full_market = df[['full_code', '代码', '名称', '最新价', '涨跌幅']]
            print(f"✅ 成功抓取全市场清单，共 {len(self.full_market)} 只股票。")
        except Exception as e:
            print(f"❌ 抓取失败: {e}")

    def suggest_stocks(self, keywords):
        """
        名称 -> 代码 解析逻辑
        支持输入: "贵州茅台", "宁德时代", "腾讯" (如果是ADR/港股需调不同接口)
        """
        results = []
        for kw in keywords:
            # 模糊匹配名称
            match = self.full_market[self.full_market['名称'].str.contains(kw)]
            if not match.empty:
                for _, row in match.iterrows():
                    results.append({"name": row['名称'], "code": row['full_code']})
            else:
                # 如果输入的是纯代码，直接格式化
                if kw.isdigit() and len(kw) == 6:
                    results.append({"name": "未知/代码导入", "code": kw})
        return results

# --- 在 main 函数中使用 ---
def run_main():
    resolver = StockResolver()
    
    # 场景 A: 手动输入名称（支持批量）
    my_watchlist = ["宁德时代", "贵州茅台", "招商银行"]
    
    # 场景 B: 或者直接抓取当前「涨幅榜」前 5 名进行分析（动态追踪热点）
    hot_stocks = resolver.full_market.sort_values(by='涨跌幅', ascending=False).head(5)
    watchlist = []
    for _, row in hot_stocks.iterrows():
        watchlist.append({"name": row['名称'], "code": row['full_code']})

    print(f"🚀 即将分析以下目标: {[s['name'] for s in watchlist]}")
    # 接下来的步骤：调用之前的 AShareQuantEngine(watchlist) 进行技术面分析...


