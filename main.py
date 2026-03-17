import os
import sys
from datetime import datetime

# Fix for ModuleNotFoundError in GitHub Actions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import load_db, save_db
from src.data_fetcher import fetch_multi_source_stock_data
from src.html_generator import build_dashboard

def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 Quant System Start: {now_str}")
    
    db = load_db()
    df_a = fetch_multi_source_stock_data()
    
    new_count = 0
    if not df_a.empty:
        current_codes = [str(c) for c in df_a['代码'].tolist()]
        old_codes = set(db.get("stock_list", []))
        
        if old_codes:
            new_stocks = set(current_codes) - old_codes
            new_count = len(new_stocks)
        
        db.update({
            "last_update": now_str,
            "total_count": len(current_codes),
            "stock_list": current_codes
        })
        save_db(db)
    
    build_dashboard(now_str, db, df_a, new_count)
    print("✅ Build Finished.")

if __name__ == "__main__":
    run()










