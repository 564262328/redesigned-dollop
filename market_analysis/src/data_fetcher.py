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
        # 如果文件不存在，創建帶有正確列名的空 DataFrame
        return pd.DataFrame(columns=['code', 'name', 'first_seen'])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10))
    def get_all_market_data(self):
        """多源獲取全量行情，並強制統一列名"""
        random_delay()
        df = pd.DataFrame()
        
        # 嘗試從東方財富獲取
        try:
            print("🔍 嘗試從 [東方財富] 獲取數據...")
            df = ak.stock_zh_a_spot_em()
            if not df.empty:
                # 東財列名轉換
                mapping = {'代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'change', '成交额': 'amount'}
                return df.rename(columns=mapping)[list(mapping.values())]
        except Exception as e:
            print(f"⚠️ 東財接口異常: {e}")

        # 備選：從新浪財經獲取
        try:
            print("⚠️ 切換至 [新浪財經] 備選接口...")
            df = ak.stock_zh_a_spot()
            if not df.empty:
                # 新浪接口列名通常是 symbol, code, name 等
                # 強制轉換關鍵列
                df = df.rename(columns={
                    'code': 'code', 
                    'symbol': 'code_full', 
                    'name': 'name', 
                    'trade': 'price', 
                    'changepercent': 'change', 
                    'amount': 'amount'
                })
                # 確保 code 列存在且為字串
                if 'code' not in df.columns and 'symbol' in df.columns:
                    df['code'] = df['symbol']
                return df[['code', 'name', 'price', 'change', 'amount']]
        except Exception as e:
            print(f"❌ 所有數據源均已失效: {e}")
            
        return pd.DataFrame()

    def sync_and_get_new(self, current_df):
        """識別並存儲新股票，增加安全性檢查"""
        if current_df.empty or 'code' not in current_df.columns:
            print("⚠️ 當前數據為空或缺少 'code' 列，跳過同步")
            return 0, len(self.local_db)

        # 確保代碼格式一致
        current_df['code'] = current_df['code'].astype(str)
        self.local_db['code'] = self.local_db['code'].astype(str)

        # 識別新股票
        new_stocks = current_df[~current_df['code'].isin(self.local_db['code'])].copy()
        
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            # 只要代碼和名稱存入資料庫
            to_save = new_stocks[['code', 'name', 'first_seen']]
            updated_db = pd.concat([self.local_db, to_save], ignore_index=True).drop_duplicates(subset=['code'])
            updated_db.to_csv(DB_PATH, index=False)
            print(f"✨ 發現 {len(new_stocks)} 隻新個股並更新資料庫")
            return len(new_stocks), len(updated_db)
        
        return 0, len(self.local_db)



