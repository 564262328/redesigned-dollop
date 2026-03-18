import os

class Config:
    # --- [原有配置] ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 基本面專用緩存文件
    FUNDAMENTAL_CACHE_PATH = os.path.join(BASE_DIR, "fundamental_cache.json")

    # --- [新增] 基本面聚合總開關 ---
    # 關閉時僅返回 not_supported 塊，不改變原分析邏輯
    ENABLE_FUNDAMENTAL_AGGREGATION = os.getenv("ENABLE_FUNDAMENTAL", "true").lower() == "true"

    # --- [新增] 基本面性能與限流配置 ---
    FUNDAMENTAL_TOTAL_LATENCY_BUDGET = 30  # 階段總預算 (秒)
    FUNDAMENTAL_SOURCE_TIMEOUT = 10       # 單源調用超時 (秒)
    FUNDAMENTAL_MAX_RETRIES = 2           # 重試次數 (含首次共 3 次)
    
    # --- [新增] 基本面聚合服務器 TTL ---
    # 短 TTL (如 3600) 可減少 1 小時內的重複拉取，減輕對手方服務器壓力
    FUNDAMENTAL_TTL = int(os.getenv("FUNDAMENTAL_TTL", "3600")) 

    # --- [原有 AI 與路徑配置] ---
    AI_API_KEY = os.getenv("AI_API_KEY")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://aihubmix.com").rstrip('/')

