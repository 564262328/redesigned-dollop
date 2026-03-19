import os

class Config:
    # --- 基础路径 ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # --- API 配置 (从 GitHub Secrets 读取) ---
    # 确保 URL 不带末尾斜杠
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.aihubmix.com").rstrip('/')
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    MAIRUI_KEY = os.getenv("MAIRUI_KEY", "") # 麦蕊 API Key

    # --- 策略参数 ---
    CACHE_MINUTES = 20
    # 增加自选股名册，防止只有茅台
    WATCHLIST = ["600519", "00700", "300750", "01810", "601318", "002594"]
    ANALYSIS_DELAY = 2.0


