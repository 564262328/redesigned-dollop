# main.py - Revised to be "Always-On"
import os
from datetime import datetime
from src.database import load_db, save_db
from src.data_fetcher import fetch_multi_source_stock_data
from src.html_generator import build_dashboard

def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = load_db()
    
    try:
        df_a = fetch_multi_source_stock_data()
    except Exception as e:
        print(f"⚠️ Data Fetch Failed: {e}")
        import pandas as pd
        df_a = pd.DataFrame() # Fallback to empty data

    new_count = 0
    if not df_a.empty:
        current_codes = [str(c) for c in df_a['代码'].tolist()]
        old_codes = set(db.get("stock_list", []))
        new_count = len(set(current_codes) - old_codes)
        db.update({"last_update": now_str, "total_count": len(current_codes), "stock_list": current_codes})
        save_db(db)

    # CRITICAL: This must be OUTSIDE any 'if' blocks to guarantee file creation
    build_dashboard(now_str, db, df_a, new_count)
    print("✅ Build Finished. index.html is now guaranteed to exist.")

if __name__ == "__main__":
    run()












