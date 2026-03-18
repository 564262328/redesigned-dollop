import akshare as ak
import pandas as pd
import os
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks_db.csv")

def random_delay():
    time.sleep(random.uniform(2, 4))

class MarketDataCenter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.local_db = self._load_db()

    def _load_db(self):
        if os.path.exists(DB_PATH):
            try: return pd.read_csv(DB_PATH, dtype={'code': str})
            except: pass
        return pd.DataFrame(columns=['code', 'name', 'first_seen'])

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=4, max=10))
    def get_all_market_data(self):
        """Fetch all A-share data with enhanced indicators (PE, PB, Cap, Turnover)"""
        random_delay()
        try:
            print("🔍 Fetching enhanced spot data from EastMoney...")
            df = ak.stock_zh_a_spot_em()
            # Map required fields including PE, PB, Turnover, Ratio, and Market Caps
            mapping = {
                '代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'change',
                '成交额': 'amount', '量比': 'volume_ratio', '换手率': 'turnover',
                '市盈率-动态': 'pe', '市净率': 'pb', '总市值': 'total_mv', '流通市值': 'circ_mv'
            }
            df = df.rename(columns=mapping)
            valid_cols = [c for c in mapping.values() if c in df.columns]
            return df[valid_cols]
        except Exception as e:
            print(f"⚠️ Spot data error: {e}")
            return pd.DataFrame()

    def get_chip_data(self, symbol):
        """Fetch Chip Distribution (筹码分布) indicators"""
        try:
            # Fetch Profit Ratio, Avg Cost, and Concentration
            df = ak.stock_cyq_em(symbol=symbol)
            if not df.empty:
                latest = df.iloc[-1]
                return {
                    "profit_ratio": f"{latest['获利比例']}%",
                    "avg_cost": f"{latest['平均成本']:.2f}",
                    "concentration_90": f"{latest['90%筹码集中度']:.2f}%"
                }
        except: pass
        return {"profit_ratio": "--", "avg_cost": "--", "concentration_90": "--"}

    def sync_and_get_new(self, current_df):
        if current_df.empty or 'code' not in current_df.columns:
            return 0, len(self.local_db)
        current_df['code'] = current_df['code'].astype(str)
        self.local_db['code'] = self.local_db['code'].astype(str)
        new_stocks = current_df[~current_df['code'].isin(self.local_db['code'])].copy()
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            updated_db = pd.concat([self.local_db, new_stocks[['code', 'name', 'first_seen']]], ignore_index=True)
            updated_db.drop_duplicates(subset=['code']).to_csv(DB_PATH, index=False)
            return len(new_stocks), len(updated_db)
        return 0, len(self.local_db)





