# src/data_fetcher.py
import akshare as ak
import pandas as pd
import requests
import random
import time
from src.config import USER_AGENTS, TENCENT_URL

def fetch_safe_ak(func):
    for _ in range(2):
        try:
            time.sleep(random.uniform(3, 6))
            data = func()
            if data is not None and not data.empty: return data
        except: continue
    return pd.DataFrame()

def fetch_tencent_enhanced(codes):
    """腾讯增强数据源"""
    try:
        formatted = [("sh"+c if c.startswith("6") else "sz"+c) for c in codes[:10]]
        resp = requests.get(f"{TENCENT_URL}{','.join(formatted)}", timeout=10)
        # 解析逻辑... (同之前代码)
        return pd.DataFrame(...) 
    except: return pd.DataFrame()
