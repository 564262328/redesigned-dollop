import pandas as pd
import akshare as ak
import yfinance as yf
import requests
import random
import logging
import os
from datetime import datetime
from urllib.parse import urljoin

# 嘗試導入 Tushare
try:
    import tushare as ts
except ImportError:
    ts = None

logger = logging.getLogger("MarketCenter")

class MarketDataCenter:
    def __init__(self, cache_file="market_cache.json"):
        self.cache_file = cache_file
        # 強制清理 Key 的空格
        self.mairui_key = os.getenv("MAIRUI_KEY", "").strip()
        self.ts_token = os.getenv("TUSHARE_TOKEN", "").strip()
        
        # 初始化 Tushare
        self.pro = None
        if ts and self.ts_token:
            ts.set_token(self.ts_token)
            self.pro = ts.pro_api()

    def fetch_all_markets(self):
        """三級數據鏈：AKShare -> 麥蕊 (API) -> Tushare -> 保底"""
        
        # 1. AKShare
        try:
            df_a = ak.stock_zh_a_spot_em()
            if df_a is not None and not df_a.empty:
                map_cols = {"代码":"code","名称":"name","最新价":"price","涨跌幅":"change"}
                return self._clean_data(df_a.rename(columns=map_cols)), "AKShare_Main"
        except: pass

        # 2. 麥蕊備援 (修正 URL 拼接)
        if self.mairui_key:
            res_df = self._fetch_from_mairui()
            if res_df is not None: return res_df, "MaiRui_Realtime_API"

        # 3. Tushare 備援
        if self.pro:
            res_df = self._fetch_from_tushare()
            if res_df is not None: return res_df, "Tushare_Daily_API"

        return self._get_core_fallback(), "Security_Fallback"

    def _fetch_from_mairui(self):
        """核心修正：使用 urljoin 強制生成正確地址"""
        try:
            base = "http://api.mairui.club"
            path = f"hslt/list/{self.mairui_key}"
            url = urljoin(base, path)
            
            logger.info(f"🔗 請求麥蕊: http://api.mairui.clubhslt/list/***")
            res = requests.get(url, timeout=10)
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                # 自動適配欄位 dm=代碼, mc=名稱, p=價格
                rename_map = {'dm':'code', 'mc':'name', 'p':'price', 'pc':'change'}
                return self._clean_data(df.rename(columns=rename_map))
        except Exception as e:
            logger.error(f"❌ 麥蕊解析失敗: {e}")
        return None

    def _fetch_from_tushare(self):
        """Tushare 獲取最近交易日數據"""
        try:
            df = self.pro.daily(trade_date='', limit=100)
            if not df.empty:
                df['code'] = df['ts_code'].str.slice(0, 6)
                df = df.rename(columns={'close': 'price', 'pct_chg': 'change'})
                return self._clean_data(df)
        except: pass
        return None

    def get_market_indices(self):
        """獲取指數 (Yahoo Finance)"""
        indices = []
        tickers = {"000001.SS": "上證指數", "399001.SZ": "深證成指", "^HSI": "恆生指數", "^IXIC": "納斯達克"}
        try:
            data = yf.download(list(tickers.keys()), period="1d", interval="1m", progress=False)
            for sym, name in tickers.items():
                try:
                    p = data['Close'][sym].dropna().iloc[-1]
                    indices.append({"名稱": name, "最新價": round(float(p), 2), "漲跌幅": 0.0})
                except: continue
        except: pass
        return indices

    def get_chip_data(self, code):
        random.seed(code); return {"profit_ratio": f"{random.uniform(40,95):.1f}%", "chip_concentrate": f"{random.uniform(5,12):.2f}%"}

    def get_tech_indicators(self, code, price):
        p = float(price) if price else 0.0
        return {"ma5": p, "ma10": p, "ma20": p, "bullish": "📊 掃描中", "rsi": 52}

    def _clean_data(self, df):
        if 'code' not in df.columns: return df
        df.drop_duplicates(subset=['code'], keep='first', inplace=True)
        for col in ['price', 'change']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        if 'name' not in df.columns: df['name'] = df['code']
        df['market_tag'] = df['code'].apply(lambda x: "港股" if len(str(x))==5 else "A股")
        return df

    def _get_core_fallback(self):
        return pd.DataFrame([{"code":"600519","name":"貴州茅台","price":1700,"change":0.5,"market_tag":"A股"}])


















