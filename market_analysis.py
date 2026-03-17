import os
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import json
import random

# ... [Keep load_db and fetch_safe_data as before] ...

def save_db(data):
    """v13.3: Minified JSON to save space and prevent timeouts"""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        # Use separators=(',', ':') to remove all whitespace/indentation
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = load_db()
    
    print("Scanning market...")
    df_a = fetch_safe_data(ak.stock_zh_a_spot_em)
    
    if df_a.empty:
        print("Data Error. Aborting.")
        return

    # Data Asset Logic
    current_codes = [str(c) for c in df_a['代码'].tolist()]
    old_codes = set(db.get("stock_list", []))
    new_stocks = set(current_codes) - old_codes
    
    # Update DB with Minified format
    db["last_update"] = now_str
    db["total_count"] = len(current_codes)
    db["stock_list"] = current_codes
    save_db(db)

    # ... [Keep your cards_html and html_tpl logic here] ...
    # Ensure index.html is written at the very end
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_tpl)
    with open(".nojekyll", "w") as f:
        f.write("")
    print(f"🚀 Dashboard v13.3 Compressed & Deployed: {now_str}")

if __name__ == "__main__":
    run()




