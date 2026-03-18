import time, os, json, logging
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from src.config import Config

logger = logging.getLogger("FundamentalCenter")

class FundamentalCenter:
    def __init__(self):
        self.cache_path = Config.FUNDAMENTAL_CACHE_PATH

    def get_stock_fundamentals(self, code):
        """核心聚合入口"""
        # 1. 總開關檢查
        if not Config.ENABLE_FUNDAMENTAL_AGGREGATION:
            return {"status": "not_supported", "data": {}}

        # 2. TTL 快取檢查
        cached_data = self._get_valid_cache(code)
        if cached_data:
            return {"status": "cached", "data": cached_data}

        # 3. 多源能力調用 (帶重試與超時)
        start_time = time.time()
        for attempt in range(Config.FUNDAMENTAL_MAX_RETRIES + 1):
            # 檢查是否超出總預算
            if time.time() - start_time > Config.FUNDAMENTAL_TOTAL_LATENCY_BUDGET:
                logger.warning(f"⏳ {code} 基本面分析超出總時延預算，強制截止")
                break
                
            try:
                data = self._fetch_from_sources(code)
                if data:
                    self._save_cache(code, data)
                    return {"status": "success", "data": data}
            except Exception as e:
                logger.warning(f"⚠️ 第 {attempt+1} 次抓取失敗: {e}")
                time.sleep(1) # 重試間隔

        return {"status": "failed", "data": {}}

    def _fetch_from_sources(self, code):
        """具體調用 AkShare 基本面接口"""
        # 這裡以個股主營業務、財務指標為例
        # 使用單源超時邏輯 (雖然 AkShare 本身是同步的，但可在外部包裝或使用特定接口)
        try:
            # 獲取主要財務指標
            df = ak.stock_financial_abstract_ths(symbol=code, indicator="主要指標").head(1)
            if df.empty: return None
            
            return {
                "eps": df['每股收益'].iloc[0],
                "net_profit_growth": df['淨利潤同比增長'].iloc[0],
                "roe": df['淨資產收益率'].iloc[0],
                "debt_ratio": df['資產負債率'].iloc[0]
            }
        except:
            return None

    def _get_valid_cache(self, code):
        if not os.path.exists(self.cache_path): return None
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                full_cache = json.load(f)
                if code in full_cache:
                    item = full_cache[code]
                    last_update = datetime.fromisoformat(item['timestamp'])
                    if datetime.now() - last_update < timedelta(seconds=Config.FUNDAMENTAL_TTL):
                        return item['data']
        except: pass
        return None

    def _save_cache(self, code, data):
        full_cache = {}
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                full_cache = json.load(f)
        
        full_cache[code] = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(full_cache, f, ensure_ascii=False)
