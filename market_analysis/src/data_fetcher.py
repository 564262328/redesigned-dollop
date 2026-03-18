import akshare as ak
import pandas as pd
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 随机 User-Agent 池
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]

def random_delay():
    """随机休眠 2-5 秒"""
    time.sleep(random.uniform(2, 5))

class DataFetcher:
    def __init__(self):
        self.failure_count = 0
        self.max_failures = 3

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def fetch_from_em(self):
        """数据源 1: 东方财富 (全量 A 股)"""
        print("🔍 尝试从 [东方财富] 获取全量数据...")
        random_delay()
        df = ak.stock_zh_a_spot_em()
        return df[['代码', '名称', '最新价', '涨跌幅', '成交额']]

    def fetch_from_sina(self):
        """数据源 2: 新浪财经"""
        print("🔍 尝试从 [新浪财经] 获取备选数据...")
        random_delay()
        df = ak.stock_zh_a_spot() # 新浪接口
        return df.rename(columns={'code': '代码', 'name': '名称', 'trade': '最新价', 'changepercent': '涨跌幅', 'amount': '成交额'})

    def fetch_from_tencent(self):
        """数据源 3: 腾讯财经"""
        print("🔍 尝试从 [腾讯财经] 获取备选数据...")
        random_delay()
        # 腾讯数据通常通过特定的行情函数获取
        df = ak.stock_zh_a_spot_em() # 示例，实际可替换为腾讯特定 API
        return df

    def get_market_data(self):
        """主入口：带熔断机制的多源抓取"""
        if self.failure_count >= self.max_failures:
            print("⚠️ 触发熔断保护，进入冷却状态...")
            return pd.DataFrame()

        sources = [self.fetch_from_em, self.fetch_from_sina, self.fetch_from_tencent]
        
        for fetch_func in sources:
            try:
                df = fetch_func()
                if not df.empty:
                    self.failure_count = 0
                    print(f"✅ 成功获取 {len(df)} 只股票数据")
                    return df
            except Exception as e:
                print(f"❌ 数据源调用失败: {e}")
                self.failure_count += 1
                continue
        
        return pd.DataFrame()

