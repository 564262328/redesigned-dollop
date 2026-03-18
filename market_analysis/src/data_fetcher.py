import akshare as ak
import pandas as pd
import os
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import akshare as ak
import pandas as pd
import os, random, time
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks_db.csv")

def identify_asset_type(code):
    """
    AI 逻辑判定资产类型
    """
    code_str = str(code).lower()
    
    # 1. 港股判定 (5位数字 或 hk前缀)
    if code_str.startswith('hk') or (code_str.isdigit() and len(code_str) == 5):
        return "港股"
    
    # 2. ETF 基金判定
    # 上交所 ETF: 51, 52, 56, 58 开头 | 深交所 ETF: 15, 16, 18 开头
    etf_prefixes = ['51', '52', '56', '58', '15', '16', '18']
    if len(code_str) == 6 and code_str[:2] in etf_prefixes:
        return "ETF基金"
    
    return "A股"

class MarketDataCenter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.local_db = self._load_db()

    def _load_db(self):
        if os.path.exists(DB_PATH):
            try: return pd.read_csv(DB_PATH, dtype={'code': str})
            except: pass
        return pd.DataFrame(columns=['code', 'name', 'first_seen'])

    def _force_clean_columns(self, df):
        # 暴力识别代码列
        new_df = pd.DataFrame()
        for col in df.columns:
            if any(k in col for k in ['代码', 'code', 'symbol']):
                # 提取数字部分
                new_df['code'] = df[col].astype(str).str.extract(r'(\d{5,6})')[0]
                break
        for col in df.columns:
            if any(k in col for k in ['名称', 'name']):
                new_df['name'] = df[col]
                break
        
        # 提取行情字段
        mapping = {'price': ['最新价', 'trade', 'price'], 'change': ['涨跌幅', 'changepercent']}
        for target, keys in mapping.items():
            for col in df.columns:
                if any(k in col for k in keys):
                    new_df[target] = df[col]
                    break
        
        # 自动标注类型
        if 'code' in new_df.columns:
            new_df['asset_type'] = new_df['code'].apply(identify_asset_type)
            
        return new_df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=3, min=10, max=40))
    def get_all_market_data(self):
        """三源滚动抓取策略"""
        try:
            print("🔍 尝试同步东方财富行情...")
            df = ak.stock_zh_a_spot_em()
            clean = self._force_clean_columns(df)
            if not clean.empty: return clean, "EastMoney"
        except Exception as e: print(f"⚠️ 东财源失败: {e}")

        try:
            print("🔍 尝试同步新浪行情...")
            df = ak.stock_zh_a_spot()
            clean = self._force_clean_columns(df)
            if not clean.empty: return clean, "Sina"
        except: pass
        
        return pd.DataFrame(), "None"

    def sync_and_get_new(self, current_df):
        if current_df.empty or 'code' not in current_df.columns:
            return 0, len(self.local_db)
        current_df['code'] = current_df['code'].astype(str)
        new_stocks = current_df[~current_df['code'].isin(self.local_db['code'].astype(str))].copy()
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            updated = pd.concat([self.local_db, new_stocks[['code', 'name', 'first_seen']]], ignore_index=True)
            updated.drop_duplicates(subset=['code']).to_csv(DB_PATH, index=False)
            return len(new_stocks), len(updated)
        return 0, len(self.local_db)










