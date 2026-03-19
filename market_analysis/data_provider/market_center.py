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
        # 從環境變數獲取 MAIRUI_KEY 並清理空格
        self.mairui_key = os.getenv("MAIRUI_KEY", "").strip()

    def fetch_all_markets(self):
        """數據獲取鏈條：AKShare -> 麥蕊 API -> 保底數據"""
        # 1. 優先嘗試 AKShare (東方財富源)
        try:
            logger.info("🌐 嘗試 AKShare 同步 (東財數據源)...")
            df_a = ak.stock_zh_a_spot_em()
            df_hk = ak.stock_hk_spot_em()
            
            if df_a is not None and not df_a.empty:
                map_cols = {
                    "代码": "code", "名称": "name", "最新价": "price", "涨跌幅": "change",
                    "换手率": "turnover", "量比": "vol_ratio", "市盈率-动态": "pe", "总市值": "total_mv"
                }
                df = pd.concat([df_a.rename(columns=map_cols), df_hk.rename(columns=map_cols)], ignore_index=True)
                return self._clean_data(df), "AKShare_Main"
        except Exception as e:
            logger.warning(f"⚠️ AKShare 請求受阻 (通常為 GitHub IP 封鎖): {e}")

        # 2. 切換至麥蕊 API 備援 (解決 1700 保底價問題)
        if self.mairui_key:
            logger.info(f"🔄 切換至麥蕊 API 備援方案 (Key: {self.mairui_key[:5]}...)")
            res_df = self._fetch_from_mairui()
            if res_df is not None:
                return res_df, "MaiRui_Realtime_API"

        # 3. 終極保底：防止程式崩潰
        logger.error("❌ 所有動態數據源失效，啟動保底清單")
        return self._get_core_fallback(), "Security_Fallback"

    def _fetch_from_mairui(self):
        """核心修正：自動偵測並強制校正 URL 格式 (防呆路徑拼接)"""
        try:
            # 1. 確保 Key 有效
            key = self.mairui_key.lstrip('/')
            if not key:
                return None

            # 2. 強制拼接正確的 API 路徑，確保域名與路徑之間有斜槓
            # 域名: https://api.mairui.club
            # 路徑: /hslt/list/
            base_url = "https://api.mairui.club"
            endpoint = "/hslt/list/"
            url = f"{base_url}{endpoint}{key}"
            
            # 3. 輸出診斷日誌
            logger.info(f"🔗 正在請求麥蕊接口: {base_url}{endpoint}***")
            
            res = requests.get(url, timeout=15)
            res.raise_for_status() # 檢查 HTTP 狀態碼
            
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                # 麥蕊 A 股字段對齊：f(代碼), n(名稱), p(當前價), pc(漲跌幅), m(市值)
                map_cols = {"f":"code", "n":"name", "p":"price", "pc":"change", "m":"total_mv"}
                return self._clean_data(df.rename(columns=map_cols))
            else:
                logger.warning("⚠️ 麥蕊 API 返回數據格式不符或內容為空")
                
        except Exception as e:
            logger.error(f"❌ 麥蕊接口執行失敗: {str(e)[:100]}")
            
        return None

    def get_market_indices(self):
        """獲取頂部四大指數 (Yahoo Finance)"""
        indices = []
        # 代碼：上證(000001.SS), 深證(399001.SZ), 恆生(^HSI), 納指(^IXIC)
        tickers = {
            "000001.SS": "上證指數", 
            "399001.SZ": "深證成指", 
            "^HSI": "恆生指數", 
            "^IXIC": "納斯達克"
        }
        try:
            logger.info("📈 正在從 Yahoo Finance 獲取全球指數...")
            data = yf.download(list(tickers.keys()), period="1d", interval="1m", progress=False)
            
            if not data.empty:
                for sym, name in tickers.items():
                    try:
                        # 獲取最後一個非空收盤價
                        p_series = data['Close'][sym].dropna()
                        if not p_series.empty:
                            p = p_series.iloc[-1]
                            indices.append({
                                "名稱": name, 
                                "最新價": round(float(p), 2), 
                                "漲跌幅": 0.0
                            })
                    except: continue
            return indices
        except Exception as e:
            logger.warning(f"⚠️ 指數抓取失敗: {e}")
            return []

    def get_chip_data(self, code):
        """提供模擬籌碼數據，防止 main.py AttributeError"""
        random.seed(code)
        return {
            "profit_ratio": f"{random.uniform(40, 95):.1f}%", 
            "chip_concentrate": f"{random.uniform(5, 12):.2f}%"
        }

    def get_tech_indicators(self, code, price):
        """提供模擬技術指標，防止 main.py AttributeError"""
        return {
            "ma5": price, 
            "ma10": price, 
            "ma20": price, 
            "bullish": "📊 數據同步中", 
            "rsi": 52
        }

    def _clean_data(self, df):
        """通用數據清洗與類型轉換"""
        df.drop_duplicates(subset=['code'], keep='first', inplace=True)
        num_cols = ['price', 'change', 'turnover', 'total_mv']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        # 自動識別市場標籤
        df['market_tag'] = df['code'].apply(lambda x: "港股" if len(str(x))==5 else "A股")
        return df

    def _get_core_fallback(self):
        """終極保底數據 (防止頁面空白)"""
        return pd.DataFrame([{"code":"600519","name":"貴州茅台","price":1700,"change":0.5,"market_tag":"A股"}])












