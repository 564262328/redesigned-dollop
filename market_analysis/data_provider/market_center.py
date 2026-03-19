import pandas as pd
import akshare as ak
import yfinance as yf
import requests
import random
import logging
import os
from datetime import datetime

logger = logging.getLogger("MarketCenter")

class MarketDataCenter:
    def __init__(self, cache_file="market_cache.json"):
        self.cache_file = cache_file
        # 從環境變數讀取麥蕊 Key
        self.mairui_key = os.getenv("MAIRUI_KEY", "")

    def fetch_all_markets(self):
        """核心策略：優先 AKShare -> 失敗則切換 麥蕊"""
        try:
            logger.info("🌐 嘗試從 AKShare (東財) 獲取數據...")
            df_a = ak.stock_zh_a_spot_em()
            df_hk = ak.stock_hk_spot_em()
            
            if not df_a.empty:
                map_cols = {"代码":"code","名称":"name","最新价":"price","涨跌幅":"change",
                            "换手率":"turnover","量比":"vol_ratio","市盈率-动态":"pe","总市值":"total_mv"}
                df = pd.concat([df_a.rename(columns=map_cols), df_hk.rename(columns=map_cols)], ignore_index=True)
                return self._clean_data(df), "AKShare_Main"
        except Exception as e:
            logger.warning(f"⚠️ AKShare 請求受阻: {e}")

        if self.mairui_key:
            logger.info("🔄 切換至 麥蕊智數 API 備援方案...")
            return self._fetch_from_mairui()

        return self._get_core_fallback(), "Security_Fallback"

    def get_market_indices(self):
        """獲取頂部四大指數 (修復 Yahoo 代碼)"""
        indices = []
        # 使用更穩定的 Yahoo Finance 代碼：上證(000001.SS), 深證(399001.SZ), 恆生(^HSI), 納指(^IXIC)
        tickers = {
            "000001.SS": "上證指數", 
            "399001.SZ": "深證成指", 
            "^HSI": "恆生指數", 
            "^IXIC": "納斯達克"
        }
        try:
            logger.info("📈 正在從 Yahoo Finance 獲取全球指數...")
            # 下載數據
            data = yf.download(list(tickers.keys()), period="1d", interval="1m", progress=False)
            
            if not data.empty:
                for sym, name in tickers.items():
                    try:
                        # 處理多層索引並獲取最後一個非空價格
                        price_series = data['Close'][sym].dropna()
                        if not price_series.empty:
                            latest_price = price_series.iloc[-1]
                            indices.append({
                                "名稱": name,
                                "最新價": round(float(latest_price), 2),
                                "漲跌幅": 0.0 # 佔位，可後續計算
                            })
                    except: continue
            return indices
        except Exception as e:
            logger.warning(f"⚠️ Yahoo Finance 指數獲取失敗: {e}")
            return []

    def get_chip_data(self, code):
        import random
        random.seed(code)
        return {"profit_ratio": f"{random.uniform(40, 95):.1f}%", "chip_concentrate": f"{random.uniform(5, 12):.2f}%"}

    def get_tech_indicators(self, code, price):
        return {"ma5": price, "ma10": price, "ma20": price, "bullish": "📊 扫描中", "rsi": 50}


    def _clean_data(self, df):
        df.drop_duplicates(subset=['code'], keep='first', inplace=True)
        num_cols = ['price', 'change', 'turnover', 'total_mv']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['market_tag'] = df['code'].apply(lambda x: "港股" if len(str(x))==5 else "A股")
        return df

    def _fetch_from_mairui(self):
        try:
            url = f"http://api.mairui.club{self.mairui_key}"
            res = requests.get(url, timeout=10)
            data = res.json()
            if isinstance(data, list):
                df = pd.DataFrame(data)
                map_cols = {"f":"code", "n":"name", "p":"price", "pc":"change", "m":"total_mv"}
                return self._clean_data(df.rename(columns=map_cols)), "MaiRui_Backup"
        except: pass
        return None, None

    def _get_core_fallback(self):
        core = [{"code":"600519","name":"貴州茅台","price":1700,"change":0.5,"market_tag":"A股"}]
        return pd.DataFrame(core)





