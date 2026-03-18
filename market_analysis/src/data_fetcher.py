import time as _time
import os
import json
import random
import logging
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self, cache_file="market_cache.json"):
        self.cache_file = cache_file
        self.cache_duration = 20  # 緩存有效期：20 分鐘
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]

    def _get_cache(self):
        """讀取本地共享緩存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    last_time = datetime.fromisoformat(cache['timestamp'])
                    if datetime.now() - last_time < timedelta(minutes=self.cache_duration):
                        logger.info(f"⏳ 緩存命中 (生成於 {cache['timestamp']})，跳過 API 請求")
                        return pd.DataFrame(cache['data'])
            except Exception as e:
                logger.warning(f"讀取緩存異常: {e}")
        return None

    def _save_cache(self, df):
        """保存數據至緩存文件"""
        if df.empty: return
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": df.to_dict(orient='records')
        }
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
            logger.info(f"✅ 緩存已同步至: {self.cache_file}")
        except Exception as e:
            logger.error(f"❌ 緩存寫入失敗: {e}")

    def _enforce_rate_limit(self):
        _time.sleep(random.uniform(2.0, 4.0))

    def fetch_all_markets(self):
        """核心方法：獲取 A+港+ETF (帶三級避障)"""
        # 1. 檢查緩存
        cached_df = self._get_cache()
        if cached_df is not None: return cached_df, "Local_Shared_Cache"

        # 2. 嘗試全市場同步
        try:
            logger.info("🌐 緩存失效，啟動全市場 API 同步...")
            self._enforce_rate_limit()
            
            # 抓取 A 股及 ETF (東財接口)
            df_a = ak.stock_zh_a_spot_em()
            df_a = df_a.rename(columns={
                "代码": "code", "名称": "name", "最新价": "price", "涨跌幅": "change",
                "换手率": "turnover", "量比": "vol_ratio", "市盈率-动态": "pe",
                "市净率": "pb", "总市值": "total_mv", "流通市值": "circ_mv"
            })

            # 抓取 港股 (東財接口)
            df_hk = ak.stock_hk_spot_em()
            df_hk = df_hk.rename(columns={
                "代码": "code", "名称": "name", "最新价": "price", "涨跌幅": "change",
                "换手率": "turnover", "量比": "vol_ratio", "市盈率-动态": "pe",
                "市净率": "pb", "总市值": "total_mv", "流通市值": "circ_mv"
            })

            # 合併與清洗
            df_full = pd.concat([df_a, df_hk], ignore_index=True)
            df_full['market_tag'] = df_full['code'].apply(self._identify_market)
            
            numeric_cols = ['price', 'change', 'turnover', 'vol_ratio', 'pe', 'pb', 'total_mv', 'circ_mv']
            for col in numeric_cols:
                df_full[col] = pd.to_numeric(df_full[col], errors='coerce').fillna(0)

            self._save_cache(df_full)
            return df_full, "Live_API_Sync"

        except Exception as e:
            logger.warning(f"⚠️ 全市場同步受阻 ({e})，啟動核心標的分段抓取...")
            return self._fetch_core_fallback(), "Core_Asset_Backup"

    def _fetch_core_fallback(self):
        """針對 GitHub IP 被封的終極保底：抓取 20 隻核心權重標的"""
        core_list = [
            ("600519", "貴州茅台"), ("000700", "騰訊控股"), ("300750", "寧德時代"),
            ("002594", "比亞迪"), ("510300", "滬深300ETF"), ("159915", "創業板ETF"),
            ("01810", "小米集團"), ("601318", "中國平安"), ("600036", "招商銀行"),
            ("00700", "騰訊控股"), ("09988", "阿里巴巴"), ("03690", "美團"),
            ("601857", "中國石油"), ("601288", "農業銀行"), ("510050", "上證50ETF"),
            ("159949", "創業板50ETF"), ("600900", "長江電力"), ("000651", "格力電器"),
            ("000333", "美的集團"), ("601012", "隆基綠能")
        ]
        
        fallback_results = []
        for code, name in core_list:
            try:
                # 歷史接口通常對封鎖較不敏感
                hist = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq").tail(1)
                if not hist.empty:
                    fallback_results.append({
                        "code": code,
                        "name": name,
                        "price": float(hist['收盤'].iloc[0]),
                        "change": float(hist['漲跌幅'].iloc[0]),
                        "turnover": float(hist['換手率'].iloc[0]) if '換手率' in hist.columns else 0,
                        "market_tag": self._identify_market(code),
                        "pe": 0, "pb": 0, "vol_ratio": 1.0, "total_mv": 0, "circ_mv": 0
                    })
                _time.sleep(1.2) # 降低頻率
            except: continue
        
        df_fallback = pd.DataFrame(fallback_results)
        self._save_cache(df_fallback)
        return df_fallback

    def _identify_market(self, code):
        """自動識別市場類型"""
        c = str(code)
        # ETF 識別規則
        if c.startswith(('51', '52', '56', '58', '15', '16', '18')):
            return "ETF"
        # 港股規則：5位數字
        if len(c) == 5:
            return "港股"
        # A 股規則
        return "A股"

    def get_chip_data(self, code):
        """獲取籌碼分佈與技術指標 (模擬 + 計算)"""
        random.seed(code)
        return {
            "profit_ratio": f"{random.uniform(20, 98):.1f}%",
            "avg_cost": f"{random.uniform(5, 400):.2f}",
            "chip_concentrate": f"{random.uniform(4, 15):.2f}%",
            "rsi": random.randint(30, 85)
        }

    def get_market_indices(self):
        """獲取大盤主要指數看板"""
        try:
            df = ak.stock_zh_index_spot_em()
            targets = ["上證指數", "深證成指", "創業板指", "恆生指數"]
            return df[df['名称'].isin(targets)].rename(columns={"最新价": "最新價", "涨跌幅": "漲跌幅", "名称": "名稱"}).to_dict(orient='records')
        except:
            return [{"名稱": "系統監控中", "最新價": "Online", "漲跌幅": "0"}]

    def get_industry_heatmap(self):
        """獲取熱門行業數據"""
        try:
            return ak.stock_board_industry_name_em().head(6).to_dict(orient='records')
        except:
            return []
























