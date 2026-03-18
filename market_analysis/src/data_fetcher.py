import akshare as ak
import pandas as pd
import os, random, time
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks_db.csv")

def identify_asset_type(code):
    code_str = str(code).lower()
    if code_str.startswith('hk') or (code_str.isdigit() and len(code_str) == 5):
        return "港股"
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

    def get_market_indices(self):
        """抓取大盘指数：带自动切换数据源"""
        target_map = {
            '000001': '上证指数', '399001': '深证成指', 
            '399006': '创业板指', '000688': '科创50', 
            '000016': '上证50', '000300': '沪深300'
        }
        # 尝试东财
        try:
            print("🔍 指数抓取: 尝试东方财富...")
            df = ak.stock_zh_index_spot_em()
            if not df.empty:
                indices = []
                mask = df['代码'].isin(target_map.keys())
                for _, row in df[mask].iterrows():
                    indices.append({"name": target_map.get(row['代码']), "code": row['代码'], "price": row['最新价'], "change": row['涨跌幅']})
                if indices: return indices
        except: pass

        # 尝试新浪 (修复解析逻辑)
        try:
            print("🔍 指数抓取: 切换新浪财经...")
            df = ak.stock_zh_index_spot()
            if not df.empty:
                indices = []
                for s_code, s_name in target_map.items():
                    full_code = f"sh{s_code}" if s_code.startswith('000') or s_code.startswith('6') else f"sz{s_code}"
                    row = df[df['code'] == full_code]
                    if not row.empty:
                        indices.append({"name": s_name, "code": s_code, "price": row['trade'].iloc[0], "change": row['changepercent'].iloc[0]})
                return indices
        except: pass
        return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=3, min=10, max=40))
    def get_all_market_data(self):
        """抓取全量行情"""
        try:
            print("🔍 行情抓取: 尝试东方财富...")
            df = ak.stock_zh_a_spot_em()
            if not df.empty:
                mapping = {'代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'change', '成交额': 'amount', '换手率': 'turnover', '量比': 'volume_ratio', '市盈率-动态': 'pe'}
                df = df.rename(columns=mapping)
                df['asset_type'] = df['code'].apply(identify_asset_type)
                return df[[c for c in mapping.values() if c in df.columns] + ['asset_type']], "EastMoney"
        except: pass

        try:
            print("🔍 行情抓取: 尝试新浪财经...")
            df = ak.stock_zh_a_spot()
            if not df.empty:
                df = df.rename(columns={'code': 'code', 'name': 'name', 'trade': 'price', 'changepercent': 'change', 'amount': 'amount'})
                for col in ['turnover', 'volume_ratio', 'pe']: df[col] = "0"
                df['asset_type'] = df['code'].apply(identify_asset_type)
                return df, "Sina"
        except: pass
        return pd.DataFrame(), "None"

    def get_industry_heatmap(self):
        """修复 AttributeError: 添加行业抓取函数"""
        try:
            print("🔍 抓取行业热力数据...")
            df = ak.stock_board_industry_name_em()
            if not df.empty:
                top = df.sort_values(by='涨跌幅', ascending=False).head(6)
                res = []
                for _, row in top.iterrows():
                    name = row['板块名称']
                    try:
                        cons = ak.stock_board_industry_cons_em(symbol=name)
                        symbols = cons['代码'].astype(str).tolist() if not cons.empty else []
                    except: symbols = []
                    res.append({"name": name, "change": row['涨跌幅'], "symbols": symbols})
                return res
        except: return []
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
        if current_df.empty: return 0, len(self.local_db)
        current_df['code'] = current_df['code'].astype(str)
        new_stocks = current_df[~current_df['code'].isin(self.local_db['code'].astype(str))].copy()
        if not new_stocks.empty:
            new_stocks['first_seen'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            updated = pd.concat([self.local_db, new_stocks[['code', 'name', 'first_seen']]], ignore_index=True)
            updated.drop_duplicates(subset=['code']).to_csv(DB_PATH, index=False)
            return len(new_stocks), len(updated)
        return 0, len(self.local_db)













