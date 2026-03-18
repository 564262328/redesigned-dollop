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

    def _universal_cleaner(self, df):
        """核心：超級通用列名轉換器"""
        if df.empty: return df
        
        # 定義關鍵字映射
        mapping = {
            'code': ['代码', 'code', 'symbol', '证券代码'],
            'name': ['名称', 'name', '证券名称'],
            'price': ['最新价', 'trade', 'price', '最新', '成交价'],
            'change': ['涨跌幅', 'changepercent', '涨跌率'],
            'amount': ['成交额', 'amount', '成交金额']
        }
        
        new_cols = {}
        for target, keywords in mapping.items():
            for kw in keywords:
                if kw in df.columns:
                    new_cols[kw] = target
                    break
        
        df = df.rename(columns=new_cols)
        
        # 檢查是否獲取了核心列，如果沒有則手動補齊
        required = ['code', 'name', 'price', 'change', 'amount']
        available = [col for col in required if col in df.columns]
        
        print(f"📊 數據列匹配結果: {available}")
        
        if 'code' not in available:
            print("❌ 無法識別股票代碼列")
            return pd.DataFrame()
            
        return df[available]

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=4, max=10))
    def get_all_market_data(self):
        """多源獲取邏輯"""
        random_delay()
        
        # 嘗試 1: 東方財富
        try:
            print("🔍 嘗試從 [東方財富] 獲取...")
            df = ak.stock_zh_a_spot_em()
            clean_df = self._universal_cleaner(df)
            if not clean_df.empty: return clean_df
        except Exception as e:
            print(f"⚠️ 東財失敗: {e}")

        # 嘗試 2: 新浪財經
        try:
            print("🔍 嘗試從 [新浪財經] 獲取...")
            df = ak.stock_zh_a_spot()
            clean_df = self._universal_cleaner(df)
            if not clean_df.empty: return clean_df
        except Exception as e:
            print(f"⚠️ 新浪失敗: {e}")

        return pd.DataFrame()

    def sync_and_get_new(self, current_df):
        """安全同步邏輯"""
        if current_df.empty or 'code' not in current_df.columns:
            return 0, len(self.local_db)

        current_df['code'] = current_df['code'].astype(str)
        self.local_db['code'] = self.local_db['code'].astype(str)

        new_stocks = current_df[~current_df['code'].isin(self.local_db['code'])].copy()
        
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            updated_db = pd.concat([self.local_db, new_stocks[['code', 'name', 'first_seen']]], ignore_index=True)
            updated_db = updated_db.drop_duplicates(subset=['code'])
            updated_db.to_csv(DB_PATH, index=False)
            print(f"✨ 發現 {len(new_stocks)} 隻新股")
            return len(new_stocks), len(updated_db)
        
        return 0, len(self.local_db)




