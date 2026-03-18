import time as _time
import random
import logging
import pandas as pd
import akshare as ak

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataCenter")

class MarketDataCenter:
    def __init__(self):
        # 按行業分類的核心資產名單 (代碼: [名稱, 行業])
        self.core_assets = {
            # 數位科技與半導體
            "000700": ["騰訊控股", "互聯網科技"], "300059": ["東方財富", "金融科技"], 
            "002415": ["海康威視", "智能安防"], "002475": ["立訊精密", "消費電子"], 
            "300408": ["三環集團", "電子元件"],
            # 大消費 (白酒、家電、物流)
            "600519": ["貴州茅台", "白酒龍頭"], "000858": ["五糧液", "白酒龍頭"], 
            "000651": ["格力電器", "白色家電"], "000333": ["美的集團", "白色家電"], 
            "600887": ["伊利股份", "乳製品"], "002352": ["順豐控股", "物流快遞"],
            # 新能源與資源
            "300750": ["寧德時代", "動力電池"], "002594": ["比亞迪", "新能源車"], 
            "601012": ["隆基綠能", "光伏太陽能"], "601899": ["紫金礦業", "有色金屬"], 
            "600900": ["長江電力", "綠色電力"], "601857": ["中國石油", "能源化工"],
            # 大金融 (銀行、保險、證券)
            "601318": ["中國平安", "保險金融"], "600036": ["招商銀行", "商業銀行"], 
            "600030": ["中信證券", "證券券商"], "601398": ["工商銀行", "國有大行"], 
            "601288": ["農業銀行", "國有大行"], "601939": ["建設銀行", "國有大行"],
            # 生物醫療
            "600276": ["恆瑞醫藥", "創新藥"], "603259": ["藥明康德", "醫藥外包"], 
            "300015": ["愛爾眼科", "醫療服務"],
            # 工業基建與房產
            "601668": ["中國建築", "基礎建設"], "600048": ["保利發展", "地產開發"], 
            "000002": ["萬科A", "地產開發"], "600585": ["海螺水泥", "建築材料"]
        }

    def _enforce_rate_limit(self):
        """強化延遲策略，針對核心標的逐一抓取"""
        _time.sleep(random.uniform(1.2, 2.8))

    def get_all_market_data(self):
        """獲取數據：優先全市場，若封鎖則啟動 30 檔核心標的逐一突破"""
        
        # --- 策略 1: 嘗試全市場 (容易被斷連) ---
        try:
            logger.info("🌐 [策略1] 嘗試全市場實時掃描...")
            self._enforce_rate_limit()
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                df = df.rename(columns={"代碼": "code", "名稱": "name", "最新價": "price", "漲跌幅": "change"})
                # 為全市場匹配行業信息 (選填)
                df['industry'] = "全市場掃描"
                return self._clean_df(df), "EastMoney_FullScan"
        except Exception as e:
            logger.warning(f"⚠️ 全市場接口封鎖: {e}")

        # --- 策略 2: 核心標的逐一突破 (GitHub 環境最穩方案) ---
        logger.info("🛡️ [策略2] 啟動核心資產保底模式 (分板塊抓取)...")
        fallback_results = []
        
        for code, info in self.core_assets.items():
            name, industry = info[0], info[1]
            try:
                # 抓取日 K 線最新一筆，此接口特徵不明顯，不易被封
                df_hist = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq").tail(1)
                
                if not df_hist.empty:
                    fallback_results.append({
                        "code": code,
                        "name": name,
                        "industry": industry, # 加入行業標籤
                        "price": float(df_hist['收盤'].iloc[0]),
                        "change": float(df_hist['漲跌幅'].iloc[0])
                    })
                    logger.info(f"✅ [已獲取] {industry} | {name}")
                
                # 關鍵：逐筆請求必須拉長間隔
                self._enforce_rate_limit()
                
            except Exception as e:
                logger.error(f"❌ 抓取失敗 {name}: {e}")
                continue
        
        if fallback_results:
            return pd.DataFrame(fallback_results), "Tencent_Core_Asset_Backup"
            
        return pd.DataFrame(), "None"

    def _clean_df(self, df):
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        df['change'] = pd.to_numeric(df['change'], errors='coerce').fillna(0)
        df['code'] = df['code'].astype(str)
        return df[['code', 'name', 'price', 'change', 'industry']]

    def get_market_indices(self):
        try:
            return ak.stock_zh_index_spot_em().to_dict(orient='records')
        except: return []

    def get_industry_heatmap(self):
        try: return ak.stock_board_industry_name_em().head(8).to_dict(orient='records')
        except: return []

    def sync_and_get_new(self, df):
        return 0, len(df)

    def get_chip_data(self, code):
        """基於代碼生成具備板塊特性的模擬籌碼"""
        random.seed(code)
        return {
            "chip_status": random.choice(["主力高度控盤", "機構底部建倉", "籌碼換手充分", "高位震盪出貨"]),
            "rsi": random.randint(35, 75)
        }



















