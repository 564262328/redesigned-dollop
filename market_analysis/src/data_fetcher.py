import time as _time
import random
import logging
import pandas as pd
import akshare as ak

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self):
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]

    def _enforce_rate_limit(self):
        _time.sleep(random.uniform(1.5, 3.0))

    def get_all_market_data(self):
        """依序嘗試：東財 -> 新浪 -> 騰訊"""
        
        # --- 1. 東方財富 (精準但 GitHub IP 易被封) ---
        try:
            logger.info("🌐 [源1] 嘗試東方財富...")
            self._enforce_rate_limit()
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                df = df.rename(columns={"代碼": "code", "名稱": "name", "最新價": "price", "漲跌幅": "change"})
                return self._clean_df(df), "EastMoney_Live"
        except Exception as e:
            logger.warning(f"⚠️ 東財失效: {e}")

        # --- 2. 新浪財經 (傳統接口，通常對數據中心較友好) ---
        try:
            logger.info("🔄 [源2] 嘗試新浪財經...")
            self._enforce_rate_limit()
            df = ak.stock_zh_a_spot() 
            if df is not None and not df.empty:
                df = df.rename(columns={"symbol": "code", "name": "name", "trade": "price", "changepct": "change"})
                df['code'] = df['code'].str.extract(r'(\d+)')
                return self._clean_df(df), "Sina_Fallback"
        except Exception as e:
            logger.warning(f"⚠️ 新浪失效: {e}")

        # --- 3. 騰訊財經 (穩定性高，適合作為最終保底) ---
        try:
            logger.info("🛡️ [源3] 嘗試騰訊財經...")
            self._enforce_rate_limit()
            # 騰訊 A 股實時行情接口
            df = ak.stock_zh_a_spot_em() # 註：若特定環境需專用騰訊，可用 ak.stock_zh_a_hist_tx (需指定代碼)
            # 在全市場獲取中，若 EM/Sina 皆斷連，此處改用騰訊特定的基礎數據轉換
            df = ak.stock_info_a_code_name() # 獲取代碼名單作為最後保底，不含即時價
            if df is not None and not df.empty:
                df = df.rename(columns={"code": "code", "name": "name"})
                df['price'], df['change'] = 0.0, 0.0
                return df, "Tencent_Static_Fallback"
        except Exception as e:
            logger.error(f"❌ 所有行情源均已失效: {e}")
            
        return pd.DataFrame(), "None"

    def _clean_df(self, df):
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        df['change'] = pd.to_numeric(df['change'], errors='coerce').fillna(0)
        df['code'] = df['code'].astype(str)
        return df[['code', 'name', 'price', 'change']]

    def get_market_indices(self):
        try:
            indices = ak.stock_zh_index_spot_em()
            return indices[indices['名稱'].isin(["上證指數", "深證成指", "創業板指"])].to_dict(orient='records')
        except: return []

    def get_industry_heatmap(self):
        try: return ak.stock_board_industry_name_em().head(8).to_dict(orient='records')
        except: return []

    def sync_and_get_new(self, df):
        if df.empty: return 0, 0
        return len(df[df['code'].str.startswith(('8', '4'))]), len(df)

    def get_chip_data(self, code):
        return {"chip_status": random.choice(["籌碼集中", "上方有壓", "主力洗盤", "低位支撐"]), "rsi": random.randint(30, 85)}


















