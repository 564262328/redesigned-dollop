import os

class Config:
    # --- 基础路径 ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # --- GitHub Secrets 读取 (必须与 GitHub 设置的名称完全一致) ---
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.aihubmix.com").rstrip('/')
    MAIRUI_KEY = os.getenv("MAIRUI_KEY", "")
    
    # --- 搜索与新闻 ---
    BOCHA_API_KEYS = os.getenv("BOCHA_API_KEYS", "").split(",")
    TAVILLY_API_KEY = os.getenv("TAVILLY_API_KEY", "")

    # --- 策略参数 ---
    CACHE_MINUTES = 20
    ANALYSIS_DELAY = 3.5  # 增加延迟防止封禁
    # 核心监控名册
    WATCHLIST = ["600519", "00700", "300750", "01810", "601318", "002594", "300059"]


