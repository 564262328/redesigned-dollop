import akshare as ak
import pandas as pd
import os
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks_db.csv")

def random_delay(min_s=2, max_s=5):
    time.sleep(random.uniform(min_s, max_s))

class MarketDataCenter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.local_db = self._load_db()

    def _load_db(self):
        if os.path.exists(DB_PATH):
            try:
                df = pd.read_csv(DB_PATH, dtype={'code': str})
                if 'code' in df.columns: return df
            except: pass
        return pd.DataFrame(columns=['code', 'name', 'first_seen'])

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=3, min=10, max=30))
    def get_all_market_data(self):
        """增强型抓取：确保无论哪个源，结果必含 'code' 列"""
        random_delay(5, 8)
        # 源 1: 东方财富
        try:
            print("🔍 尝试同步东方财富行情...")
            df = ak.stock_zh_a_spot_em()
            if not df.empty:
                mapping = {
                    '代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'change',
                    '成交额': 'amount', '量比': 'volume_ratio', '换手率': 'turnover',
                    '市盈率-动态': 'pe', '市净率': 'pb', '总市值': 'total_mv'
                }
                df = df.rename(columns=mapping)
                if 'code' in df.columns:
                    return df[[c for c in mapping.values() if c in df.columns]], "EastMoney"
        except Exception as e:
            print(f"⚠️ 东财异常: {e}")

        # 源 2: 新浪财经
        try:
            print("🔍 切换新浪财经源...")
            df = ak.stock_zh_a_spot()
            if not df.empty:
                df = df.rename(columns={'symbol':'code_full', 'code': 'code', 'name': 'name', 'trade': 'price', 'changepercent': 'change', 'amount': 'amount'})
                if 'code' not in df.columns and 'code_full' in df.columns:
                    df['code'] = df['code_full']
                for col in ['volume_ratio', 'turnover', 'pe', 'pb', 'total_mv']: df[col] = "0"
                return df, "Sina"
        except: pass
        return pd.DataFrame(), "None"

    def get_industry_heatmap(self):
        """抓取行业板块数据"""
        try:
            print("🔍 正在抓取行业热力及成份股数据...")
            df = ak.stock_board_industry_name_em()
            if not df.empty:
                top_boards = df.sort_values(by='涨跌幅', ascending=False).head(6)
                boards_list = []
                for _, row in top_boards.iterrows():
                    b_name = row['板块名称']
                    try:
                        cons = ak.stock_board_industry_cons_em(symbol=b_name)
                        symbols = cons['代码'].astype(str).tolist() if not cons.empty else []
                    except: symbols = []
                    boards_list.append({"name": b_name, "change": row['涨跌幅'], "symbols": symbols})
                return boards_list
        except: pass
        return []

    def get_chip_data(self, symbol):
        try:
            df = ak.stock_cyq_em(symbol=symbol)
            if not df.empty:
                latest = df.iloc[-1]
                return {"profit_ratio": f"{latest['获利比例']}%", "avg_cost": f"{latest['平均成本']:.2f}"}
        except: pass
        return {"profit_ratio": "--", "avg_cost": "--"}

    def sync_and_get_new(self, current_df):
        """同步新股，增加 KeyError 保护"""
        if current_df.empty or 'code' not in current_df.columns:
            return 0, len(self.local_db)
        
        current_df['code'] = current_df['code'].astype(str)
        if not self.local_db.empty:
            self.local_db['code'] = self.local_db['code'].astype(str)

        new_stocks = current_df[~current_df['code'].isin(self.local_db['code'])].copy()
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            updated_db = pd.concat([self.local_db, new_stocks[['code', 'name', 'first_seen']]], ignore_index=True)
            updated_db.drop_duplicates(subset=['code']).to_csv(DB_PATH, index=False)
            return len(new_stocks), len(updated_db)
        return 0, len(self.local_db)









