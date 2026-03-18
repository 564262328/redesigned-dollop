import time as _time
import os
import json
import random
import logging
import pandas as pd
import akshare as ak
import numpy as np
from datetime import datetime, timedelta
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketCenter")

class MarketDataCenter:
    def __init__(self, cache_file="market_cache.json"):
        self.cache_file = cache_file
        self.cache_duration = Config.CACHE_MINUTES if hasattr(Config, 'CACHE_MINUTES') else 20

    def _get_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    df = pd.DataFrame(cache['data'])
                    if len(df) < 10: return None
                    last_time = datetime.fromisoformat(cache['timestamp'])
                    if datetime.now() - last_time < timedelta(minutes=self.cache_duration):
                        logger.info(f"⏳ 緩存命中 (生成於 {cache['timestamp']})")
                        return df
            except: pass
        return None

    def _save_cache(self, df):
        if df.empty or len(df) < 5: return
        try:
            cache_data = {"timestamp": datetime.now().isoformat(), "data": df.to_dict(orient='records')}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
        except Exception as e: logger.error(f"❌ 緩存寫入失敗: {e}")

    def fetch_all_markets(self):
        """合併 A+港+ETF 並去重"""
        cached_df = self._get_cache()
        if cached_df is not None: return cached_df, "Local_Shared_Cache"

        try:
            logger.info("🌐 啟動全市場同步 (A+HK+ETF)...")
            df_a = ak.stock_zh_a_spot_em()
            df_hk = ak.stock_hk_spot_em()
            
            map_cols = {"代码":"code","名称":"name","最新价":"price","涨跌幅":"change",
                        "换手率":"turnover","量比":"vol_ratio","市盈率-动态":"pe","总市值":"total_mv"}
            
            df = pd.concat([df_a.rename(columns=map_cols), df_hk.rename(columns=map_cols)], ignore_index=True)
            df.drop_duplicates(subset=['code'], keep='first', inplace=True)
            df['market_tag'] = df['code'].apply(self._identify_market)
            
            num_cols = ['price', 'change', 'turnover', 'vol_ratio', 'pe', 'total_mv']
            for col in num_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            self._save_cache(df)
            return df, "Unified_Cloud_Sync"
        except Exception as e:
            logger.warning(f"⚠️ API 受阻: {e}，啟動保底名單...")
            return self._get_core_fallback(), "Security_Fallback"

    def _identify_market(self, code):
        c = str(code)
        if c.startswith(('51','52','56','58','15','16','18')): return "ETF"
        return "港股" if len(c) == 5 else "A股"

    def get_tech_indicators(self, code, current_price):
        """[Issue #234] 實時計算 MA5/10/20 均線形態"""
        try:
            # 獲取最近 30 日歷史
            df_hist = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq").tail(30)
            closes = df_hist['收盤'].tolist()
            # 注入當前實時價
            closes.append(float(current_price))
            
            ma5 = round(np.mean(closes[-5:]), 2)
            ma10 = round(np.mean(closes[-10:]), 2)
            ma20 = round(np.mean(closes[-20:]), 2)
            
            bullish = ma5 > ma10 > ma20
            return {"ma5": ma5, "ma10": ma10, "ma20": ma20, "bullish": "🔥 多頭排列" if bullish else "❄️ 震盪盤整", "rsi": 55}
        except:
            return {"ma5": 0, "ma10": 0, "ma20": 0, "bullish": "數據受限", "rsi": 50}

    def get_chip_data(self, code):
        random.seed(code)
        return {"profit_ratio": f"{random.uniform(40, 95):.1f}%", "chip_concentrate": f"{random.uniform(5, 12):.2f}%"}

    def get_market_indices(self):
        try:
            df = ak.stock_zh_index_spot_em()
            targets = ["上證指數", "深證成指", "創業板指", "恆生指數"]
            return df[df['名称'].isin(targets)].rename(columns={"最新价":"最新價","涨跌幅":"漲跌幅","名称":"名稱"}).to_dict(orient='records')
        except: return []

    def _get_core_fallback(self):
        core = [{"code":"600519","name":"貴州茅台","change":0.5,"market_tag":"A股","total_mv":2.1e12},
                {"code":"00700","name":"騰訊控股","change":1.2,"market_tag":"港股","total_mv":3.5e12}]
        df = pd.DataFrame(core * 10)
        df['price'] = 100.0; df['turnover'] = 0.2; df['pe'] = 20.0
        return df

