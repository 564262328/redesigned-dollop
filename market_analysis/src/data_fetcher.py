import time, os, json, random, logging
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self, cache_file="market_cache.json"):
        self.cache_file = cache_file
        self.cache_duration = 20  # 緩存有效時間(分鐘)
        self._circuit_breaker = {"TX": 0, "Sina": 0, "EM": 0}

    def _get_cache(self):
        """讀取本地緩存文件"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    last_time = datetime.fromisoformat(cache['timestamp'])
                    if datetime.now() - last_time < timedelta(minutes=self.cache_duration):
                        logger.info(f"⏳ 緩存有效 (生成於 {cache['timestamp']})，跳過 API 請求")
                        return pd.DataFrame(cache['data'])
            except Exception as e:
                logger.warning(f"讀取緩存出錯: {e}")
        return None

    def _save_cache(self, df):
        """保存數據至緩存，確保 GitHub Actions 能讀取"""
        if df.empty: return
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": df.to_dict(orient='records')
        }
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
            logger.info(f"✅ 緩存已寫入: {os.path.abspath(self.cache_file)}")
        except Exception as e:
            logger.error(f"❌ 緩存寫入失敗: {e}")

    def fetch_all_markets(self):
        """獲取 A股+港股+ETF 實時行情"""
        cached_df = self._get_cache()
        if cached_df is not None: return cached_df, "Local_Shared_Cache"

        try:
            logger.info("🌐 緩存失效，同步 A+HK+ETF 全市場數據...")
            # 1. 抓取 A股 + ETF (含市盈率、換手率等深度指標)
            df_a = ak.stock_zh_a_spot_em()
            df_a = df_a.rename(columns={
                "代码": "code", "名称": "name", "最新价": "price", "涨跌幅": "change",
                "换手率": "turnover", "量比": "vol_ratio", "市盈率-动态": "pe",
                "市净率": "pb", "总市值": "total_mv", "流通市值": "circ_mv"
            })
            
            # 2. 抓取 港股
            df_hk = ak.stock_hk_spot_em()
            df_hk = df_hk.rename(columns={
                "代码": "code", "名称": "name", "最新价": "price", "涨跌幅": "change",
                "换手率": "turnover", "量比": "vol_ratio", "市盈率-动态": "pe",
                "市净率": "pb", "总市值": "total_mv", "流通市值": "circ_mv"
            })

            # 數據合併與標籤識別
            df_full = pd.concat([df_a, df_hk], ignore_index=True)
            df_full['market_tag'] = df_full['code'].apply(self._identify_market)
            
            # 數值轉換
            cols = ['price', 'change', 'turnover', 'vol_ratio', 'pe', 'pb', 'total_mv', 'circ_mv']
            for col in cols:
                df_full[col] = pd.to_numeric(df_full[col], errors='coerce').fillna(0)

            self._save_cache(df_full)
            return df_full, "Live_Market_Sync"
        except Exception as e:
            logger.error(f"❌ 同步失敗: {e}")
            return pd.DataFrame(), "Sync_Error"

    def _identify_market(self, code):
        c = str(code)
        if c.startswith(('51', '52', '56', '58', '15', '16', '18')): return "ETF"
        if len(c) == 5: return "港股"
        return "A股"

    def get_chip_data(self, code):
        """模擬籌碼深度數據 (獲利盤、平均成本)"""
        random.seed(code)
        return {
            "profit_ratio": f"{random.uniform(40, 95):.1f}%",
            "avg_cost": f"{random.uniform(5, 500):.2f}",
            "chip_concentrate": f"{random.uniform(5, 15):.2f}%"
        }

    def get_market_indices(self):
        try: return ak.stock_zh_index_spot_em().to_dict(orient='records')
        except: return []

    def get_industry_heatmap(self):
        try: return ak.stock_board_industry_name_em().head(6).to_dict(orient='records')
        except: return []
























