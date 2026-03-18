import time as _time
import random
import logging
import pandas as pd
import akshare as ak
from typing import Optional, List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self):
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]

    def _enforce_rate_limit(self):
        """Random sleep to avoid IP blocking"""
        _time.sleep(random.uniform(0.8, 1.5))

    def get_all_market_data(self):
        """Fetch real-time A-share market data (Main loop in main.py)"""
        try:
            logger.info("🌐 Fetching real-time market spot data...")
            self._enforce_rate_limit()
            df = ak.stock_zh_a_spot_em()
            
            # Map Chinese columns to English for main.py compatibility
            column_map = {
                "代码": "code", "名称": "name", "最新价": "price", 
                "涨跌幅": "change", "成交量": "volume", "成交额": "amount"
            }
            df = df.rename(columns=column_map)
            # Ensure price/change are numeric
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df['change'] = pd.to_numeric(df['change'], errors='coerce')
            
            return df[['code', 'name', 'price', 'change', 'volume', 'amount']], "EastMoney_Spot"
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return pd.DataFrame(), "Fallback_Source"

    def get_market_indices(self):
        """Get summary of major indices"""
        try:
            indices = ak.stock_zh_index_spot_em()
            targets = ["上证指数", "深证成指", "创业板指"]
            df_filtered = indices[indices['名称'].isin(targets)]
            return df_filtered.to_dict(orient='records')
        except:
            return []

    def get_industry_heatmap(self):
        """Get top industry sectors"""
        try:
            df = ak.stock_board_industry_name_em()
            return df.head(10).to_dict(orient='records')
        except:
            return []

    def sync_and_get_new(self, df: pd.DataFrame):
        """Simulate syncing and counting new listings"""
        total = len(df)
        # Mock calculation for new stocks (e.g., Beijing stock exchange codes)
        new_count = len(df[df['code'].str.startswith(('8', '4'))]) if not df.empty else 0
        return new_count, total

    def get_chip_data(self, code: str):
        """Get mock technical/chip data for a specific stock"""
        return {
            "chip_status": random.choice(["Concentrated", "Dispersed", "Strong Support"]),
            "rsi": random.randint(30, 75),
            "turnover": f"{random.uniform(0.5, 5.0):.2f}%"
        }
















