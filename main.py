# main.py
import os
from datetime import datetime
import pandas as pd
import akshare as ak

# 從 src 模組導入我們之前寫好的功能
from src.database import load_db, save_db
from src.html_generator import build_dashboard
# 假設你已經把多源抓取邏輯寫在了 src/data_fetcher.py 中
from src.data_fetcher import fetch_multi_source_stock_data 

def run():
    # 獲取當前時間
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 量化系統啟動: {now_str}")

    # --- 1. 讀取數據庫 (src/database.py) ---
    db = load_db()
    
    # --- 2. 獲取當前股票行情 (src/data_fetcher.py) ---
    # 這裡會依次嘗試 東方財富 -> 新浪 -> 騰訊 接口
    df_a = fetch_multi_source_stock_data()
    
    # --- 3. 計算新股數量並更新數據庫 ---
    new_count = 0
    if not df_a.empty:
        # 提取當前所有股票代碼
        current_codes = [str(c) for c in df_a['代码'].tolist()]
        # 讀取數據庫中舊的股票代碼集合
        old_codes = set(db.get("stock_list", []))
        
        # 計算新上市股票 (當前有但以前沒有的)
        if old_codes: # 第一次運行時 old_codes 為空，new_count 應為 0
            new_stocks = set(current_codes) - old_codes
            new_count = len(new_stocks)
            print(f"📈 偵測到今日新上市股票: {new_count} 隻")
        
        # 更新數據庫內容
        db["last_update"] = now_str
        db["total_count"] = len(current_codes)
        db["stock_list"] = current_codes
        
        # 保存數據庫 (src/database.py)
        save_db(db)
    else:
        print("⚠️ 無法獲取行情數據，跳過數據庫更新。")

    # --- 4. 調用 HTML 生成器 (src/html_generator.py) ---
    # 將所有處理好的數據傳給 UI 生成器，生成 index.html
    build_dashboard(now_str, db, df_a, new_count)
    
    print(f"✅ 任務完成。終端頁面已生成於根目錄。")

if __name__ == "__main__":
    run()










