import time, os, json, random, logging
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self, cache_file="market_cache.json"):
        self.cache_file = cache_file
        self.cache_duration = 20  # 20分鐘緩存
        self._circuit_breaker = {"TX": 0, "Sina": 0, "EM": 0}

    def _get_cache(self):
        """讀取本地緩存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    last_time = datetime.fromisoformat(cache['timestamp'])
                    if datetime.now() - last_time < timedelta(minutes=self.cache_duration):
                        logger.info(f"⏳ 緩存有效 (生成於 {cache['timestamp']})，跳過 API 請求")
                        return pd.DataFrame(cache['data'])
            except: pass
        return None

    def _save_cache(self, df):
        """保存數據至緩存"""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": df.to_dict(orient='records')
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False)

    def fetch_all_markets(self):
        """獲取 A股+港股+ETF 實時行情"""
        cached_df = self._get_cache()
        if cached_df is not None: return cached_df, "Local_Cache_Shared"

        try:
            logger.info("🌐 緩存失效，啟動全市場 API 同步 (A+HK+ETF)...")
            
            # 1. 抓取 A股 + ETF (東財接口)
            df_a = ak.stock_zh_a_spot_em()
            df_a = df_a.rename(columns={
                "代码": "code", "名称": "name", "最新价": "price", "涨跌幅": "change",
                "换手率": "turnover", "量比": "vol_ratio", "市盈率-动态": "pe",
                "市净率": "pb", "总市值": "total_mv", "流通市值": "circ_mv"
            })
            
            # 2. 抓取 港股 (東財接口)
            df_hk = ak.stock_hk_spot_em()
            df_hk = df_hk.rename(columns={
                "代码": "code", "名称": "name", "最新价": "price", "涨跌幅": "change",
                "换手率": "turnover", "量比": "vol_ratio", "市盈率-动态": "pe",
                "市净率": "pb", "总市值": "total_mv", "流通市值": "circ_mv"
            })

            # 數據合併與標籤識別
            df_full = pd.concat([df_a, df_hk], ignore_index=True)
            df_full['market_tag'] = df_full['code'].apply(self._identify_market)
            
            # 數據清洗
            for col in ['price', 'change', 'turnover', 'vol_ratio', 'pe', 'pb', 'total_mv', 'circ_mv']:
                df_full[col] = pd.to_numeric(df_full[col], errors='coerce').fillna(0)

            self._save_cache(df_full)
            return df_full, "Live_API_Sync"
        except Exception as e:
            logger.error(f"❌ 同步失敗: {e}")
            return pd.DataFrame(), "Sync_Error"

    def _identify_market(self, code):
        c = str(code)
        if c.startswith(('51', '52', '56', '58', '15', '16', '18')): return "ETF"
        if len(c) == 5: return "港股"
        return "A股"

    def get_chip_data(self, code):
        """模擬籌碼分佈數據 (獲利比例、平均成本、集中度)"""
        random.seed(code)
        return {
            "profit_ratio": f"{random.uniform(30, 95):.1f}%",
            "avg_cost": f"{random.uniform(5, 500):.2f}",
            "chip_concentrate": f"{random.uniform(5, 18):.2f}%"
        }























