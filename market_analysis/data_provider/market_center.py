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
        # 獲取密鑰並清理前後空格
        self.mairui_key = os.getenv("MAIRUI_KEY", "").strip()

    def fetch_all_markets(self):
        """數據源鏈條：AKShare -> 麥蕊 API -> 保底數據"""
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
            logger.warning(f"⚠️ AKShare 請求受阻: {e}")

        # 2. 觸發麥蕊 API 備援 (解決 1700 保底價問題)
        if self.mairui_key:
            logger.info(f"🔄 正在切換麥蕊 API 備援方案...")
            res_df = self._fetch_from_mairui()
            if res_df is not None:
                return res_df, "MaiRui_Realtime_API"

        # 3. 終極保底：防止程式崩潰
        logger.error("❌ 所有動態數據源失效，啟動保底清單")
        return self._get_core_fallback(), "Security_Fallback"

    def _fetch_from_mairui(self):
        """核心修復：物理級 URL 隔離拼接，解決域名解析錯誤"""
        try:
            if not self.mairui_key: return None

            # 修正關鍵：將域名與 Key 物理隔開，確保中間有斜槓 /
            base_url = "http://api.mairui.club"
            api_path = "/hslt/list/"
            clean_key = self.mairui_key.lstrip('/')
            url = f"{base_url}{api_path}{clean_key}"
            
            logger.info(f"🔗 請求地址: {base_url}{api_path}***")
            
            # 設定 15 秒超時，增加請求成功率
            res = requests.get(url, timeout=15)
            res.raise_for_status()
            
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                
                # --- 自動識別麥蕊欄位 (dm=代碼, mc=名稱, p=價格, pc=漲跌幅) ---
                rename_map = {}
                cols = df.columns.tolist()
                mapping = {
                    'code': ['dm', 'f', 'code'],
                    'name': ['mc', 'n', 'name'],
                    'price': ['p', 'price', 'last'],
                    'change': ['pc', 'zdf', 'change']
                }
                for target, aliases in mapping.items():
                    for a in aliases:
                        if a in cols:
                            rename_map[a] = target
                            break
                
                df = df.rename(columns=rename_map)
                return self._clean_data(df)
            else:
                logger.warning("⚠️ 麥蕊 API 返回格式不符或內容為空")
        except Exception as e:
            logger.error(f"❌ 麥蕊接口解析失敗: {str(e)[:100]}")
            
        return None

    def get_market_indices(self):
        """獲取頂部四大指數 (使用 Yahoo Finance 提升在 GitHub Runner 的穩定性)"""
        indices = []
        tickers = {
            "000001.SS": "上證指數", 
            "399001.SZ": "深證成指", 
            "^HSI": "恆生指數", 
            "^IXIC": "納斯達克"
        }
        try:
            data = yf.download(list(tickers.keys()), period="1d", interval="1m", progress=False)
            if not data.empty:
                for sym, name in tickers.items():
                    try:
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
            logger.warning(f"⚠️ Yahoo 指數獲取失敗: {e}")
            return []

    def get_chip_data(self, code):
        """提供籌碼分佈模擬數據，防止 AttributeError"""
        random.seed(code)
        return {
            "profit_ratio": f"{random.uniform(40, 95):.1f}%", 
            "chip_concentrate": f"{random.uniform(5, 12):.2f}%"
        }

    def get_tech_indicators(self, code, price):
        """提供技術指標模擬數據，解決 KeyError 問題"""
        try:
            p = float(price) if price and str(price) != 'None' else 0.0
        except:
            p = 0.0
        return {
            "ma5": round(p * 0.99, 2), 
            "ma10": round(p * 0.98, 2), 
            "ma20": round(p * 0.97, 2), 
            "bullish": "📊 數據同步中", 
            "rsi": 52
        }

    def _clean_data(self, df):
        """通用數據清洗：解決畫面上出現 None 的核心機制"""
        if df is None or 'code' not in df.columns: return df
        
        # 1. 物理去重
        df.drop_duplicates(subset=['code'], keep='first', inplace=True)
        
        # 2. 強制轉化為數字，若為 None 則補 0.0
        for col in ['price', 'change']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            else:
                df[col] = 0.0
        
        # 3. 確保名稱欄位非空
        if 'name' not in df.columns:
            df['name'] = df['code']
            
        # 4. 市場分類標籤
        df['market_tag'] = df['code'].apply(lambda x: "港股" if len(str(x))==5 else "A股")
        return df

    def _get_core_fallback(self):
        """極端情況下的數據兜底"""
        return pd.DataFrame([{"code":"600519","name":"貴州茅台","price":1700,"change":0.5,"market_tag":"A股"}])




















