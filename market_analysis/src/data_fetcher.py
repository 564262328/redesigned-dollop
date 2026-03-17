import akshare as ak
import pandas as pd
import random
import time

def fetch_safe_ak(func):
    for _ in range(2):
        try:
            time.sleep(random.uniform(3, 6))
            data = func()
            if data is not None and not data.empty: return data
        except: continue
    return pd.DataFrame()

def fetch_multi_source_stock_data():
    print("  [Layer 1] Trying EastMoney...")
    df = fetch_safe_ak(ak.stock_zh_a_spot_em)
    if not df.empty: return df

    print("  [Layer 2] Trying Sina...")
    df = fetch_safe_ak(ak.stock_zh_a_spot)
    if not df.empty:
        return df.rename(columns={'trade':'最新价', 'changepercent':'涨跌幅', 'code':'代码'})
    
    return pd.DataFrame()
