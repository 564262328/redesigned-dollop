import time as _time
import random
import logging
import pandas as pd
import akshare as ak
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self):
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]

    def _enforce_rate_limit(self):
        _time.sleep(random.uniform(1.0, 2.0))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_all_market_data(self):
        """獲取實時行情，帶自動重試機制"""
        try:
            logger.info("🌐 正在獲取東財實時行情數據...")
            self._enforce_rate_limit()
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty: raise ValueError("數據為空")

            column_map = {"代碼": "code", "名稱": "name", "最新價": "price", "漲跌幅": "change"}
            df = df.rename(columns=column_map)
            # 強制轉換數值，填充空值
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
            df['change'] = pd.to_numeric(df['change'], errors='coerce').fillna(0)
            
            return df[['code', 'name', 'price', 'change']], "EastMoney_Live"
        except Exception as e:
            logger.warning(f"⚠️ 行情獲取失敗，嘗試重試: {e}")
            raise e

    def get_market_indices(self):
        try:
            indices = ak.stock_zh_index_spot_em()
            targets = ["上證指數", "深證成指", "創業板指"]
            return indices[indices['名稱'].isin(targets)].to_dict(orient='records')
        except: return []

    def get_industry_heatmap(self):
        try:
            return ak.stock_board_industry_name_em().head(8).to_dict(orient='records')
        except: return []

    def sync_and_get_new(self, df):
        return len(df[df['code'].str.startswith(('8', '4'))]), len(df)

    def get_chip_data(self, code):
        """模擬籌碼數據，可擴展 ak.stock_zh_a_hist_pre_job"""
        return {
            "chip_status": random.choice(["籌碼集中", "上方有壓", "主力洗盤"]),
            "rsi": random.randint(30, 80)
        }

















