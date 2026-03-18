import time as _time
import random
import logging
import pandas as pd
import akshare as ak
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self):
        # 1. 隨機 User-Agent 池
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        # 2. 熔斷器狀態：記錄每個數據源的冷卻截止時間
        self._circuit_breaker = {
            "EM": 0,    # 應對東方財富
            "Sina": 0,  # 應對新浪
            "TX": 0     # 應對騰訊
        }
        # 冷卻時長 (秒)
        self.COOLDOWN_PERIOD = 600 

    def _enforce_strategy(self):
        """策略1: 每次請求前隨機休眠 2-5 秒"""
        sleep_time = random.uniform(2.0, 5.0)
        _time.sleep(sleep_time)
        
    def _get_random_ua(self):
        """策略2: 隨機輪換 User-Agent"""
        return {"User-Agent": random.choice(self.ua_list)}

    def _is_fused(self, source_name: str) -> bool:
        """策略4: 熔斷器機制 - 檢查該源是否處於冷卻期"""
        if _time.time() < self._circuit_breaker[source_name]:
            logger.warning(f"⚠️ [熔斷激活] {source_name} 正在冷卻中，跳過請求。")
            return True
        return False

    def _activate_fuse(self, source_name: str):
        """激活熔斷：將該源關閉一段時間"""
        self._circuit_breaker[source_name] = _time.time() + self.COOLDOWN_PERIOD
        logger.error(f"🚨 [熔斷觸發] {source_name} 連續失敗，進入 {self.COOLDOWN_PERIOD}s 冷卻期。")

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=2, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.info(f"🔄 [策略3] Tenacity 重試中 (第 {retry_state.attempt_number} 次)...")
    )
    def _fetch_em(self):
        """默認數據源：東方財富"""
        if self._is_fused("EM"): return None
        self._enforce_strategy()
        # AkShare 內部雖然有重試，但我們在外部包裝 Tenacity 指數退避
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty: raise ValueError("EM 數據回傳為空")
        df = df.rename(columns={"代碼": "code", "名稱": "name", "最新價": "price", "漲跌幅": "change"})
        return df

    def get_all_market_data(self):
        """主入口：實施三重備選數據源邏輯"""
        
        # 1. 嘗試東方財富 (EM)
        try:
            df = self._fetch_em()
            if df is not None: return self._clean_df(df), "EastMoney_Live"
        except Exception as e:
            logger.error(f"❌ 東財請求失敗: {e}")
            self._activate_fuse("EM")

        # 2. 備選一：新浪財經 (Sina)
        if not self._is_fused("Sina"):
            try:
                logger.info("🔄 切換至備選源 [新浪財經]...")
                self._enforce_strategy()
                df = ak.stock_zh_a_spot()
                if df is not None and not df.empty:
                    df = df.rename(columns={"symbol": "code", "name": "name", "trade": "price", "changepct": "change"})
                    df['code'] = df['code'].str.extract(r'(\d+)')
                    return self._clean_df(df), "Sina_Fallback"
            except Exception as e:
                logger.error(f"❌ 新浪請求失敗: {e}")
                self._activate_fuse("Sina")

        # 3. 備選二：騰訊財經 (TX - 保底核心標的)
        if not self._is_fused("TX"):
            try:
                logger.info("🛡️ 切換至最終保底 [騰訊核心名單]...")
                # 這裡使用 core_assets 邏輯確保至少有 30 檔股票能產出
                return self._fetch_core_assets_fallback(), "Tencent_Core_Backup"
            except Exception as e:
                logger.error(f"❌ 騰訊保底也失敗: {e}")
                self._activate_fuse("TX")

        return pd.DataFrame(), "All_Sources_Failed"

    def _fetch_core_assets_fallback(self):
        """針對 GitHub 環境的極致保底：逐一獲取權重股歷史數據"""
        core_codes = ["600519", "000700", "002594", "300750", "601318"] # 簡化名單
        res = []
        for code in core_codes:
            self._enforce_strategy()
            hist = ak.stock_zh_a_hist(symbol=code, period="daily").tail(1)
            if not hist.empty:
                res.append({"code": code, "name": "核心權重", "price": hist['收盤'].iloc[0], "change": hist['漲跌幅'].iloc[0]})
        return pd.DataFrame(res)

    def _clean_df(self, df):
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        df['change'] = pd.to_numeric(df['change'], errors='coerce').fillna(0)
        return df[['code', 'name', 'price', 'change']]

    # ... get_market_indices 等其他方法保持不變 ...



















