# main.py
import akshare as ak
from datetime import datetime
from src.database import load_db, save_db
from src.data_fetcher import fetch_multi_source
from src.html_generator import build_dashboard

def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 量化系統 v14.0 啟動: {now_str}")

    # --- 1. 數據加載 ---
    db = load_db()
    
    # --- 2. 獲取多源數據 ---
    df_a = fetch_multi_source()  # 這裡會依次嘗試 EM -> Sina -> Tencent
    
    # --- 3. 核心數據處理與數據庫更新 ---
    new_stocks_count = 0
    if not df_a.empty:
        current_codes = [str(c) for c in df_a['代码'].tolist()]
        old_codes = set(db.get("stock_list", []))
        
        # 計算今日新上市股票
        new_stocks = list(set(current_codes) - old_codes)
        new_stocks_count = len(new_stocks)
        
        # 更新數據庫內容
        db["last_update"] = now_str
        db["total_count"] = len(current_codes)
        db["stock_list"] = current_codes
        
        # 保存數據 (這一步會被 GitHub Action 自動 commit 到倉庫)
        save_db(db)
    else:
        print("⚠️ 未能獲取最新行情數據，數據庫跳過更新。")

    # --- 4. 生成科技感 UI 網頁 ---
    # 傳入數據給生成器
    build_dashboard(now_str, db, df_a, new_stocks_count)
    print("✅ 網頁終端部署完成。")

if __name__ == "__main__":
    run()










