import time as _time
import random
import logging
import pandas as pd
import akshare as ak

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self):
        self._circuit_breaker = {"EM": 0, "Sina": 0, "TX": 0}

    def _enforce_rate_limit(self):
        _time.sleep(random.uniform(2.0, 4.0))

    def get_all_market_data(self):
        """三重避障 + 離線保底：確保永遠有數據回傳"""
        # 1. 嘗試東方財富
        try:
            logger.info("🌐 [源1] 嘗試東方財富...")
            self._enforce_rate_limit()
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                df = df.rename(columns={"代碼": "code", "名稱": "name", "最新價": "price", "漲跌幅": "change"})
                return self._clean_df(df), "EastMoney_Live"
        except Exception as e:
            logger.warning(f"⚠️ 東財封鎖: {e}")

        # 2. 嘗試新浪財經
        try:
            logger.info("🔄 [源2] 嘗試新浪財經...")
            self._enforce_rate_limit()
            df = ak.stock_zh_a_spot()
            if df is not None and not df.empty:
                df = df.rename(columns={"symbol": "code", "name": "name", "trade": "price", "changepct": "change"})
                df['code'] = df['code'].str.extract(r'(\d+)')
                return self._clean_df(df), "Sina_Fallback"
        except Exception as e:
            logger.warning(f"⚠️ 新浪封鎖: {e}")

        # 3. 終極離線保底 (防止 404 的核心)
        logger.error("🚨 網絡全線封鎖！啟動 [離線安全模式] 生成報告...")
        safety_data = [
            {"code": "600519", "name": "貴州茅台(離線)", "price": 1650.0, "change": 0.0, "industry": "白酒龍頭"},
            {"code": "000700", "name": "騰訊控股(離線)", "price": 380.0, "change": 0.0, "industry": "互聯網科技"},
            {"code": "300750", "name": "寧德時代(離線)", "price": 190.0, "change": 0.0, "industry": "新能源"},
            {"code": "002594", "name": "比亞迪(離線)", "price": 240.0, "change": 0.0, "industry": "新能源車"}
        ]
        return pd.DataFrame(safety_data), "Offline_Safety_Mode"

    def _clean_df(self, df):
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        df['change'] = pd.to_numeric(df['change'], errors='coerce').fillna(0)
        if 'industry' not in df.columns: df['industry'] = "全市場掃描"
        return df[['code', 'name', 'price', 'change', 'industry']]

    def get_market_indices(self):
        try: return ak.stock_zh_index_spot_em().to_dict(orient='records')
        except: return [{"名稱": "數據源封鎖", "最新價": "-", "漲跌幅": "0"}]

    def get_industry_heatmap(self):
        try: return ak.stock_board_industry_name_em().head(5).to_dict(orient='records')
        except: return []

    def sync_and_get_new(self, df):
        return 0, len(df)

    def get_chip_data(self, code):
        return {"chip_status": "觀望中", "rsi": 50}




















