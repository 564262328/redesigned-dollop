import os

class Config:
    # --- 基礎路徑配置 ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # --- [核心修正] 搜尋 API 金鑰 ---
    # 博查搜索 (支持多個 Key 用逗號分隔)
    BOCHA_API_KEYS = os.getenv("BOCHA_API_KEYS", "").split(",")
    # Tavilly 搜索
    TAVILLY_API_KEY = os.getenv("TAVILLY_API_KEY", "")
    # SerpAPI 搜索
    SERP_API_KEY = os.getenv("SERP_API_KEY", "")
    # SearXNG 自建實例 URL
    SEARXNG_URL = os.getenv("SEARXNG_URL", "")

    # --- AI 配置 ---
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://aihubmix.com").rstrip('/')

    # --- 策略參數 ---
    CACHE_MINUTES = 20
    ANALYSIS_DELAY = 2  # 每次分析間隔，防止被封 IP
    WATCHLIST = ["600519", "00700", "300750", "002594"] # 自選股名單
    
    # --- 介面預設 ---
    SENTIMENT_SCORE = 65
    SENTIMENT_LABEL = "理性偏貪婪"


