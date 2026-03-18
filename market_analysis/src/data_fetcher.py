import akshare as ak
import pandas as pd
import os
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks_db.csv")

def random_delay(min_s=3, max_s=7):
    time.sleep(random.uniform(min_s, max_s))

class MarketDataCenter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.local_db = self._load_db()

    def _load_db(self):
        if os.path.exists(DB_PATH):
            try:
                df = pd.read_csv(DB_PATH, dtype={'code': str})
                if not df.empty and 'code' in df.columns: return df
            except: pass
        return pd.DataFrame(columns=['code', 'name', 'first_seen'])

    def _force_clean_columns(self, df, source_name):
        """核心：暴力识别列名，无视接口返回的原始标签"""
        if df.empty: return pd.DataFrame()
        
        # 打印原始列名以便在日志中排查
        print(f"📊 {source_name} 原始列名: {df.columns.tolist()}")

        # 定义特征映射
        new_df = pd.DataFrame()
        
        # 1. 寻找代码列 (通常是 6 位数字字符串)
        for col in df.columns:
            sample = str(df[col].iloc[0]) if not df.empty else ""
            if col in ['代码', 'code', 'symbol', 's_code'] or (len(sample) >= 6 and sample[-6:].isdigit()):
                new_df['code'] = df[col].astype(str).str.extract(r'(\d{6})')[0]
                break

        # 2. 寻找名称列
        for col in df.columns:
            if col in ['名称', 'name', 's_name'] or "名称" in col:
                new_df['name'] = df[col]
                break

        # 3. 基础行情字段补齐
        mapping = {
            'price': ['最新价', 'trade', 'price', '最新', '成交价'],
            'change': ['涨跌幅', 'changepercent', '涨跌率', 'p_change'],
            'amount': ['成交额', 'amount', '成交金额', 'amount_all']
        }
        
        for target, keys in mapping.items():
            for col in df.columns:
                if col in keys:
                    new_df[target] = df[col]
                    break
        
        # 4. 补充缺失的增强指标 (统一设为 0)
        for col in ['volume_ratio', 'turnover', 'pe', 'pb', 'total_mv']:
            if col in df.columns: new_df[col] = df[col]
            else: new_df[col] = "0"

        return new_df if 'code' in new_df.columns else pd.DataFrame()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=3, min=10, max=40))
    def get_all_market_data(self):
        """三源滚动抓取策略"""
        random_delay(5, 10)
        
        # 源 1: 东方财富
        try:
            print("🔍 尝试同步 [东方财富] 行情...")
            df = ak.stock_zh_a_spot_em()
            clean = self._force_clean_columns(df, "EastMoney")
            if not clean.empty: return clean, "EastMoney"
        except Exception as e: print(f"⚠️ 东财源失败: {e}")

        # 源 2: 新浪财经
        try:
            print("🔍 尝试同步 [新浪财经] 行情...")
            df = ak.stock_zh_a_spot()
            clean = self._force_clean_columns(df, "Sina")
            if not clean.empty: return clean, "Sina"
        except Exception as e: print(f"⚠️ 新浪源失败: {e}")

        # 源 3: 腾讯/通用代码表 (最终保底)
        try:
            print("🔍 尝试同步 [基础代码表] (降级模式)...")
            df = ak.stock_info_a_code_name()
            clean = self._force_clean_columns(df, "BasicInfo")
            if not clean.empty:
                for col in ['price', 'change', 'amount']: clean[col] = "0"
                return clean, "Fallback-System"
        except Exception as e: print(f"⚠️ 保底源失败: {e}")

        return pd.DataFrame(), "None"

    def get_industry_heatmap(self):
        """抓取行业数据，增加空值保护"""
        try:
            print("🔍 抓取行业热力数据...")
            df = ak.stock_board_industry_name_em()
            if not df.empty:
                top_boards = df.sort_values(by='涨跌幅', ascending=False).head(6)
                res = []
                for _, row in top_boards.iterrows():
                    res.append({"name": row['板块名称'], "change": row['涨跌幅'], "symbols": []})
                return res
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









