import os

class Config:
    # 基础路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CACHE_PATH = os.path.join(BASE_DIR, "market_cache.json")
    REPORT_PATH = os.path.join(BASE_DIR, "index.html")
    
    # 策略参数
    CACHE_MINUTES = 20
    ANALYSIS_COUNT = 20  # 10涨幅 + 10随机
    
    # AI 配置
    AI_API_KEY = os.getenv("AI_API_KEY")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://aihubmix.com").rstrip('/')
    
    # 界面预设
    SENTIMENT_SCORE = 68
    SENTIMENT_LABEL = "貪婪模式"
