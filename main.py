import os
import sys

# --- BULLETPROOF PATH FIX ---
# This looks for 'src' in the current folder and subfolders
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

# If your files are inside a subfolder, this finds it
for root, dirs, files in os.walk(base_dir):
    if 'src' in dirs:
        sys.path.append(root)
        break

from datetime import datetime
try:
    from src.database import load_db, save_db
    from src.data_fetcher import fetch_multi_source_stock_data
    from src.html_generator import build_dashboard
except ImportError as e:
    print(f"FATAL: Could not find 'src' folder. Error: {e}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Directory Contents: {os.listdir(base_dir)}")
    sys.exit(1)

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
            new_count = len(set(current_codes) - old_codes)
        
        db.update({"last_update": now_str, "total_count": len(current_codes), "stock_list": current_codes})
        save_db(db)
    
    build_dashboard(now_str, db, df_a, new_count)
    print("✅ Build Finished.")

if __name__ == "__main__":
    run()










