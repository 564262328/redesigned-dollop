# main.py
import os
from datetime import datetime
from src.database import load_db, save_db
from src.data_fetcher import fetch_safe_ak, fetch_multi_source
from src.html_generator import build_dashboard
import akshare as ak

def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 Quant System Start: {now_str}")
    
    # 1. 加载数据库
    db = load_db()
    
    # 2. 抓取数据
    df_base = fetch_safe_ak(ak.stock_zh_a_spot_em)
    df_sector = fetch_safe_ak(ak.stock_board_industry_name_em)
    
    # 3. 业务逻辑处理 (更新数据库)
    if not df_base.empty:
        # 你的数据库更新逻辑...
        save_db(db)
    
    # 4. 生成网页
    build_dashboard(now_str, db, df_base, df_sector)
    print("✅ Web Terminal Deployed.")

if __name__ == "__main__":
    run()










