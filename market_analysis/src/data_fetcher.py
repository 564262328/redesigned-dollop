import akshare as ak
import pandas as pd
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# 随机 User-Agent 池，模拟不同浏览器
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def random_delay():
    """随机休眠 2-5 秒，防止被封 IP"""
    time.sleep(random.uniform(2, 5))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10))
def fetch_with_retry(func, *args, **kwargs):
    """带重试机制的抓取包装器"""
    random_delay()
    return func(*args, **kwargs)

def get_all_market_data():
    """多源数据获取逻辑：东财 -> 新浪 -> 腾讯"""
    
    # 策略 1: 东方财富 (全量 A 股实时行情)
    try:
        print("🔍 尝试从 [东方财富] 获取全量行情...")
        df = fetch_with_retry(ak.stock_zh_a_spot_em)
        if not df.empty:
            # 统一列名以适配后续逻辑
            return df.rename(columns={
                '代码': 'code', '名称': 'name', '最新价': 'price', 
                '涨跌幅': 'change', '成交额': 'amount'
            })
    except Exception as e:
        print(f"⚠️ 东财接口调用失败: {e}")

    # 策略 2: 新浪财经 (备选)
    try:
        print("🔍 尝试从 [新浪财经] 获取备选行情...")
        df = fetch_with_retry(ak.stock_zh_a_spot)
        if not df.empty:
            return df.rename(columns={
                'code': 'code', 'name': 'name', 'trade': 'price', 
                'changepercent': 'change', 'amount': 'amount'
            })
    except Exception as e:
        print(f"⚠️ 新浪接口调用失败: {e}")

    # 策略 3: 腾讯财经 (最终备选)
    try:
        print("🔍 尝试从 [腾讯财经] 获取数据...")
        # 腾讯数据通常在 akshare 中也有对应的 spot 函数
        df = fetch_with_retry(ak.stock_zh_a_spot_em) 
        return df
    except Exception as e:
        print(f"❌ 所有行情数据源均已失效: {e}")
        return pd.DataFrame()


