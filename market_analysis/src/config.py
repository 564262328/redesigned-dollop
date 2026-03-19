import os

class Config:
    # --- 基礎路徑 ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # --- [關鍵] GitHub Secrets 讀取 ---
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.aihubmix.com").rstrip('/')
    
    # 數據源密鑰
    MAIRUI_KEY = os.getenv("MAIRUI_KEY", "")
    TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "") # 新增 Tushare Token

    # 搜尋與新聞
    BOCHA_API_KEYS = os.getenv("BOCHA_API_KEYS", "").split(",")

    # --- 策略參數 ---
    CACHE_MINUTES = 20
    ANALYSIS_DELAY = 3.5 
    # 監控名單
    WATCHLIST = ["600519", "00700", "300750", "01810", "601318", "002594", "300059"]



