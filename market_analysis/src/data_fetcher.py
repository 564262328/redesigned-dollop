import akshare as ak
import pandas as pd
import os
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# 存储路径
DB_PATH = "../data/stocks_db.csv"

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
]

def random_delay():
    time.sleep(random.uniform(2, 5))

class MarketDataCenter:
    def __init__(self):
        # 确保数据目录存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.local_df = self._load_local_db()

    def _load_local_db(self):
        if os.path.exists(DB_PATH):
            return pd.read_csv(DB_PATH, dtype={'code': str})
        return pd.DataFrame(columns=['code', 'name', 'first_seen'])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10))
    def fetch_full_market(self):
        """从东财抓取全量列表 (主选)"""
        random_delay()
        print("🔍 正在同步东方财富全量数据...")
        df = ak.stock_zh_a_spot_em()
        return df[['代码', '名称']].rename(columns={'代码': 'code', '名称': 'name'})

    def sync_new_stocks(self):
        """增量更新逻辑：只保留新出现的股票"""
        try:
            current_df = self.fetch_full_market()
        except:
            print("⚠️ 东财接口异常，尝试新浪备选...")
            current_df = ak.stock_zh_a_spot().rename(columns={'symbol': 'code', 'name': 'name'})

        # 识别新股票
        new_stocks = current_df[~current_df['code'].isin(self.local_df['code'])].copy()
        
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            # 更新本地库
            updated_db = pd.concat([self.local_df, new_stocks], ignore_index=True)
            updated_db.to_csv(DB_PATH, index=False)
            print(f"✨ 发现 {len(new_stocks)} 只新上市股票并已存入本地库")
        else:
            print("✅ 暂无新股票发现")
            
        return new_stocks, current_df

    def get_realtime_quotes(self):
        """获取实时行情用于看板展示"""
        return ak.stock_zh_a_spot_em().rename(columns={
            '代码': 'code', '名称': 'name', '最新价': 'price', 
            '涨跌幅': 'change', '成交额': 'amount'
        })



