import akshare as ak
import pandas as pd
import os
import random
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks_db.csv")

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
]

def random_delay(min_s=2, max_s=5):
    time.sleep(random.uniform(min_s, max_s))

class MarketDataCenter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.local_db = self._load_db()

    def _load_db(self):
        if os.path.exists(DB_PATH):
            try: return pd.read_csv(DB_PATH, dtype={'code': str})
            except: pass
        return pd.DataFrame(columns=['code', 'name', 'first_seen'])

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=3, min=10, max=30))
    def get_all_market_data(self):
        """增强型抓取：多源回退与状态记录"""
        random_delay(5, 10)
        # Source 1: EastMoney
        try:
            print("🔍 尝试同步东方财富实时行情...")
            df = ak.stock_zh_a_spot_em()
            if not df.empty:
                mapping = {
                    '代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'change',
                    '成交额': 'amount', '量比': 'volume_ratio', '换手率': 'turnover',
                    '市盈率-动态': 'pe', '市净率': 'pb', '总市值': 'total_mv'
                }
                return df.rename(columns=mapping)[[c for c in mapping.values() if c in df.columns]], "EastMoney (东方财富)"
        except Exception as e:
            print(f"⚠️ 东财源连接中断: {e}")

        # Source 2: Sina
        try:
            print("🔍 切换至新浪财经备选...")
            df = ak.stock_zh_a_spot()
            if not df.empty:
                df = df.rename(columns={'code': 'code', 'name': 'name', 'trade': 'price', 'changepercent': 'change', 'amount': 'amount'})
                for col in ['volume_ratio', 'turnover', 'pe', 'pb', 'total_mv']: df[col] = "0"
                return df, "Sina (新浪财经)"
        except: pass
        return pd.DataFrame(), "None (获取失败)"

    def get_industry_heatmap(self):
        """抓取行业板块热力图 (TOP 6)"""
        try:
            print("🔍 抓取行业板块热力数据...")
            df = ak.stock_board_industry_name_em()
            if not df.empty:
                # 按涨跌幅降序排列，取前6个板块
                top_boards = df.sort_values(by='涨跌幅', ascending=False).head(6)
                return top_boards.to_dict('records')
        except: pass
        return []

    def get_chip_data(self, symbol):
        """抓取筹码分布数据"""
        random_delay(1, 3)
        try:
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
        if current_df.empty: return 0, len(self.local_db)
        current_df['code'] = current_df['code'].astype(str)
        self.local_db['code'] = self.local_db['code'].astype(str)
        new_stocks = current_df[~current_df['code'].isin(self.local_db['code'])].copy()
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            updated_db = pd.concat([self.local_db, new_stocks[['code', 'name', 'first_seen']]], ignore_index=True)
            updated_db.drop_duplicates(subset=['code']).to_csv(DB_PATH, index=False)
            return len(new_stocks), len(updated_db)
        return 0, len(self.local_db)







