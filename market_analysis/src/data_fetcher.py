import akshare as ak
import pandas as pd
import os, random, time
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks_db.csv")

# 增强型 User-Agent
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

def random_delay(min_s=3, max_s=8):
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

    def get_market_indices(self):
        """抓取大盘指数：带自动切换数据源逻辑"""
        target_map = {
            '000001': '上证指数', '399001': '深证成指', 
            '399006': '创业板指', '000688': '科创50', 
            '000016': '上证50', '000300': '沪深300'
        }
        
        # 策略1: 东方财富
        try:
            print("🔍 指数抓取 [1/2]: 尝试东方财富...")
            df = ak.stock_zh_index_spot_em()
            if not df.empty:
                indices = []
                mask = df['代码'].isin(target_map.keys())
                for _, row in df[mask].iterrows():
                    indices.append({"name": target_map.get(row['代码']), "code": row['代码'], "price": row['最新价'], "change": row['涨跌幅']})
                if indices: return indices
        except Exception as e:
            print(f"⚠️ 东财指数源异常: {e}")

        # 策略2: 新浪财经 (保底)
        try:
            print("🔍 指数抓取 [2/2]: 切换新浪财经...")
            random_delay(2, 4)
            # 新浪指数接口
            df = ak.stock_zh_index_spot_sina()
            if not df.empty:
                indices = []
                # 新浪的代码通常带 sh/sz
                for _, row in df.iterrows():
                    pure_code = row['symbol'][-6:]
                    if pure_code in target_map:
                        indices.append({"name": target_map[pure_code], "code": pure_code, "price": row['trade'], "change": row['amount']}) # 简化处理
                return indices
        except Exception as e:
            print(f"❌ 所有指数数据源均失效: {e}")
        
        return [{"name": k, "code": v, "price": "0", "change": "0"} for v, k in target_map.items()]

    def get_all_market_data(self):
        """抓取全量行情：严格的自动切换逻辑"""
        
        # 尝试 1: 东方财富 (最全)
        try:
            print("🔍 行情抓取 [1/3]: 尝试东方财富...")
            random_delay(5, 10)
            df = ak.stock_zh_a_spot_em()
            if not df.empty:
                mapping = {'代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'change', '成交额': 'amount', '换手率': 'turnover', '量比': 'volume_ratio', '市盈率-动态': 'pe', '平均成本': 'avg_cost'}
                df = df.rename(columns=mapping)
                return df[[c for c in mapping.values() if c in df.columns]], "EastMoney"
        except Exception as e:
            print(f"⚠️ 东财行情失败，准备切换: {e}")

        # 尝试 2: 新浪财经 (基础)
        try:
            print("🔍 行情抓取 [2/3]: 尝试新浪财经...")
            random_delay(5, 10)
            df = ak.stock_zh_a_spot()
            if not df.empty:
                df = df.rename(columns={'code': 'code', 'name': 'name', 'trade': 'price', 'changepercent': 'change', 'amount': 'amount'})
                # 填充缺失列
                for col in ['turnover', 'volume_ratio', 'pe', 'avg_cost']: df[col] = "0"
                return df, "Sina"
        except Exception as e:
            print(f"⚠️ 新浪行情失败: {e}")

        # 尝试 3: 基础代码列表 (降级生存)
        try:
            print("🔍 行情抓取 [3/3]: 尝试基础代码表 (保底模式)...")
            df = ak.stock_info_a_code_name()
            if not df.empty:
                df = df.rename(columns={'code': 'code', 'name': 'name'})
                for col in ['price', 'change', 'amount', 'turnover', 'volume_ratio', 'pe', 'avg_cost']: df[col] = "0"
                return df, "Standard-List"
        except: pass

        return pd.DataFrame(), "None"

    def get_chip_data(self, symbol):
        """筹码分布获取"""
        try:
            df = ak.stock_cyq_em(symbol=symbol)
            if not df.empty:
                latest = df.iloc[-1]
                return {"profit_ratio": f"{latest['获利比例']}%", "avg_cost": f"{latest['平均成本']:.2f}"}
        except: pass
        return {"profit_ratio": "--", "avg_cost": "--"}

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












