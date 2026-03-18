import time as _time
import os
import json
import random
import logging
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self, cache_file="market_cache.json"):
        self.cache_file = cache_file
        self.cache_duration = 20  # 緩存 20 分鐘
        self._circuit_breaker = {"TX": 0, "Sina": 0, "EM": 0}

    def _get_cache(self):
        """讀取緩存並驗證數據品質"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    df = pd.DataFrame(cache['data'])
                    # 若緩存數據太少（少於10筆），視為損壞，強制重新抓取
                    if len(df) < 10: return None
                    
                    last_time = datetime.fromisoformat(cache['timestamp'])
                    if datetime.now() - last_time < timedelta(minutes=self.cache_duration):
                        logger.info(f"⏳ 緩存有效 (生成於 {cache['timestamp']})")
                        return df
            except: pass
        return None

    def _save_cache(self, df):
        """保存數據並確保不寫入壞數據"""
        if df.empty or len(df) < 5: return
        try:
            cache_data = {"timestamp": datetime.now().isoformat(), "data": df.to_dict(orient='records')}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
            logger.info(f"✅ 數據已保存至緩存: {self.cache_file}")
        except: pass

    def fetch_all_markets(self):
        """多市場數據統一合併與去重"""
        cached_df = self._get_cache()
        if cached_df is not None: return cached_df, "Shared_Cache_Sync"

        try:
            logger.info("🌐 緩存失效，同步 A+港+ETF 全市場數據...")
            # 1. 抓取數據 (使用東財接口獲取深度指標)
            df_a = ak.stock_zh_a_spot_em()
            df_hk = ak.stock_hk_spot_em()
            
            map_cols = {
                "代码": "code", "名称": "name", "最新价": "price", "涨跌幅": "change",
                "换手率": "turnover", "量比": "vol_ratio", "市盈率-动态": "pe", "总市值": "total_mv"
            }
            
            # 2. 合併與對齊
            df = pd.concat([df_a.rename(columns=map_cols), df_hk.rename(columns=map_cols)], ignore_index=True)
            
            # 3. 【關鍵】物理去重：根據股票代碼去重
            df.drop_duplicates(subset=['code'], keep='first', inplace=True)
            
            # 4. 自動識別標籤
            df['market_tag'] = df['code'].apply(self._identify_market)
            
            # 5. 數值格式化與清洗
            num_cols = ['price', 'change', 'turnover', 'vol_ratio', 'pe', 'total_mv']
            for col in num_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            self._save_cache(df)
            return df, "Unified_Cloud_Sync"

        except Exception as e:
            logger.warning(f"⚠️ API 請求受限: {e}，切換至跨市場保底名單...")
            return self._get_unique_fallback(), "Security_Fallback_Mode"

    def _identify_market(self, code):
        c = str(code)
        if c.startswith(('51','52','56','58','15','16','18')): return "ETF"
        if len(c) == 5: return "港股"
        return "A股"

    def _get_unique_fallback(self):
        """提供 20 檔完全不重複的跨市場保底數據"""
        core = [
            {"code":"600519","name":"貴州茅台","change":0.2,"market_tag":"A股","total_mv":2.1e12,"pe":28.5},
            {"code":"00700","name":"騰訊控股","change":1.2,"market_tag":"港股","total_mv":3.5e12,"pe":22.4},
            {"code":"300750","name":"寧德時代","change":-0.5,"market_tag":"A股","total_mv":8.5e11,"pe":16.8},
            {"code":"510300","name":"滬深300ETF","change":0.1,"market_tag":"ETF","total_mv":2e11,"pe":0},
            {"code":"01810","name":"小米集團-W","change":2.5,"market_tag":"港股","total_mv":4.5e11,"pe":24.1},
            {"code":"09988","name":"阿里巴巴-W","change":-1.2,"market_tag":"港股","total_mv":1.8e12,"pe":15.2},
            {"code":"002594","name":"比亞迪","change":0.8,"market_tag":"A股","total_mv":6.8e11,"pe":20.5},
            {"code":"601318","name":"中國平安","change":-0.2,"market_tag":"A股","total_mv":9.5e11,"pe":9.2},
            {"code":"159915","name":"創業板ETF","change":0.6,"market_tag":"ETF","total_mv":5e10,"pe":0},
            {"code":"600036","name":"招商銀行","change":0.3,"market_tag":"A股","total_mv":8.8e11,"pe":5.8},
            {"code":"03690","name":"美團-W","change":1.8,"market_tag":"港股","total_mv":7.2e11,"pe":35.2},
            {"code":"300059","name":"東方財富","change":3.5,"market_tag":"A股","total_mv":2.4e11,"pe":25.4},
            {"code":"601857","name":"中國石油","change":0.1,"market_tag":"A股","total_mv":1.5e12,"pe":12.1},
            {"code":"00388","name":"香港交易所","change":-0.4,"market_tag":"港股","total_mv":4e11,"pe":30.1},
            {"code":"513100","name":"納指ETF","change":1.1,"market_tag":"ETF","total_mv":3e10,"pe":0},
            {"code":"600900","name":"長江電力","change":0.2,"market_tag":"A股","total_mv":6.2e11,"pe":18.5},
            {"code":"000651","name":"格力電器","change":0.5,"market_tag":"A股","total_mv":2.1e11,"pe":8.4},
            {"code":"601012","name":"隆基綠能","change":-2.3,"market_tag":"A股","total_mv":1.5e11,"pe":14.2},
            {"code":"01024","name":"快手-W","change":1.5,"market_tag":"港股","total_mv":2.2e11,"pe":22.8},
            {"code":"159949","name":"創業板50ETF","change":0.8,"market_tag":"ETF","total_mv":2e10,"pe":0}
        ]
        df = pd.DataFrame(core)
        df['price'] = 100.0; df['turnover'] = 0.5; df['vol_ratio'] = 1.0
        return df

    def get_chip_data(self, code):
        """模擬深度籌碼數據"""
        random.seed(code)
        return {
            "profit_ratio": f"{random.uniform(40, 95):.1f}%",
            "avg_cost": f"{random.uniform(10, 500):.2f}",
            "chip_concentrate": f"{random.uniform(5, 12):.2f}%",
            "rsi": random.randint(30, 80)
        }

    def get_market_indices(self):
        try:
            df = ak.stock_zh_index_spot_em()
            targets = ["上證指數", "深證成指", "創業板指", "恆生指數"]
            return df[df['名称'].isin(targets)].rename(columns={"最新价":"最新價","涨跌幅":"漲跌幅","名称":"名稱"}).to_dict(orient='records')
        except: return []





























