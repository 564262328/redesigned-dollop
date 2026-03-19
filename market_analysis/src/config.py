import os

class Config:
    # --- Path Config ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # --- API Config ---
    # Correct Base URL for AIHubMix
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.aihubmix.com")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    
    # Other Keys
    BOCHA_API_KEYS = os.getenv("BOCHA_API_KEYS", "").split(",")
    TAVILLY_API_KEY = os.getenv("TAVILLY_API_KEY", "")
    MAIRUI_KEY = os.getenv("MAIRUI_KEY", "")

    # --- Strategy Config ---
    CACHE_MINUTES = 20
    ANALYSIS_DELAY = 2.0
    WATCHLIST = ["600519", "00700", "300750", "01810", "601318"]



