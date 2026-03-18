import akshare as ak
import pandas as pd
import os
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential

DB_PATH = "../data/stocks_db.csv"

def random_delay():
    time.sleep(random.uniform(2, 5))

class MarketDataCenter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.local_db = self._load_db()

    def _load_db(self):
        if os.path.exists(DB_PATH):
            return pd.read_csv(DB_PATH, dtype={'code': str})
        return pd.DataFrame(columns=['code', 'name', 'first_seen'])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10))
    def get_all_market_data(self):
        """多源獲取全量行情 (東財 -> 新浪)"""
        random_delay()
        try:
            print("🔍 同步東方財富全量行情...")
            df = ak.stock_zh_a_spot_em()
            return df.rename(columns={'代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'change', '成交额': 'amount'})
        except:
            print("⚠️ 東財異常，嘗試新浪備選...")
            df = ak.stock_zh_a_spot()
            return df.rename(columns={'code': 'code', 'name': 'name', 'trade': 'price', 'changepercent': 'change', 'amount': 'amount'})

    def sync_and_get_new(self, current_df):
        """識別並存儲新股票"""
        new_stocks = current_df[~current_df['code'].isin(self.local_db['code'])].copy()
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            updated_db = pd.concat([self.local_db, new_stocks[['code', 'name', 'first_seen']]], ignore_index=True)
            updated_db.to_csv(DB_PATH, index=False)
            print(f"✨ 發現 {len(new_stocks)} 隻新個股")
        return len(new_stocks), len(current_df)



