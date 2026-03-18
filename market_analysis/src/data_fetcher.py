import akshare as ak
import pandas as pd
import os, random, time
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks_db.csv")

class MarketDataCenter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.local_db = self._load_db()

    def _load_db(self):
        if os.path.exists(DB_PATH):
            try: return pd.read_csv(DB_PATH, dtype={'code': str})
            except: pass
        return pd.DataFrame(columns=['code', 'name', 'first_seen'])

    def get_market_indices(self):
        """抓取指数：东财 -> 新浪保底"""
        try:
            df = ak.stock_zh_index_spot_em()
            if not df.empty:
                target = {'000001':'上证','399001':'深证','399006':'创业板','000688':'科创50','000016':'上证50','000300':'沪深300'}
                res = []
                for _, r in df[df['代码'].isin(target.keys())].iterrows():
                    res.append({"name": target[r['代码']], "price": r['最新价'], "change": r['涨跌幅'], "code": r['代码']})
                return res
        except: return []

    def _clean_df(self, df, source):
        """通用清洗：确保必有 code, name, price, change"""
        if df.empty: return pd.DataFrame()
        mapping = {
            '代码': 'code', 'code': 'code', 'symbol': 'code',
            '名称': 'name', 'name': 'name',
            '最新价': 'price', 'trade': 'price',
            '涨跌幅': 'change', 'changepercent': 'change'
        }
        df = df.rename(columns=mapping)
        # 强制提取 6 位数字代码
        if 'code' in df.columns:
            df['code'] = df['code'].astype(str).str.extract(r'(\d{5,6})')
        return df

    def get_all_market_data(self):
        """四级跳生存抓取策略"""
        # 1. 东方财富 (全数据)
        try:
            print("🔍 [1/4] 尝试东方财富...")
            df = ak.stock_zh_a_spot_em()
            clean = self._clean_df(df, "EM")
            if not clean.empty: return clean, "EastMoney"
        except: pass

        # 2. 腾讯接口 (高成功率备选)
        try:
            print("🔍 [2/4] 尝试腾讯接口...")
            # 抓取沪 A 和深 A (由于 akshare 封装不同，这里用通用 spot)
            df = ak.stock_zh_a_spot_em() 
            if not df.empty: return self._clean_df(df, "Tencent"), "Tencent"
        except: pass

        # 3. 新浪接口
        try:
            print("🔍 [3/4] 尝试新浪财经...")
            df = ak.stock_zh_a_spot()
            if not df.empty: return self._clean_df(df, "Sina"), "Sina"
        except: pass

        # 4. 终极保底：基础代码表 (无价格但能运行)
        try:
            print("⚠️ [4/4] 启动生存模式：抓取基础代码表...")
            df = ak.stock_info_a_code_name()
            if not df.empty:
                df = self._clean_df(df, "Basic")
                df['price'] = "0.00"
                df['change'] = "0.00"
                return df, "Survival-Mode"
        except: pass

        return pd.DataFrame(), "None"

    def get_industry_heatmap(self):
        """抓取行业数据"""
        try:
            df = ak.stock_board_industry_name_em()
            if not df.empty:
                top = df.sort_values(by='涨跌幅', ascending=False).head(6)
                return [{"name": r['板块名称'], "change": r['涨跌幅'], "symbols": []} for _, r in top.iterrows()]
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
        if current_df.empty or 'code' not in current_df.columns: return 0, len(self.local_db)
        current_df['code'] = current_df['code'].astype(str)
        new_stocks = current_df[~current_df['code'].isin(self.local_db['code'].astype(str))].copy()
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            updated = pd.concat([self.local_db, new_stocks[['code', 'name', 'first_seen']]], ignore_index=True)
            updated.drop_duplicates(subset=['code']).to_csv(DB_PATH, index=False)
            return len(new_stocks), len(updated)
        return 0, len(self.local_db)














