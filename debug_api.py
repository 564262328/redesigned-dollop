import akshare as ak
import pandas as pd

def check(name, func):
    try:
        print(f"🔍 正在測試 {name}...")
        df = func()
        if df is not None and not df.empty:
            print(f"✅ {name} 成功！獲取到 {len(df)} 筆數據。")
        else:
            print(f"⚠️ {name} 回傳數據為空。")
    except Exception as e:
        print(f"❌ {name} 失敗: {str(e)[:100]}")

print("--- 🚀 AkShare 接口連通性診斷 ---")
check("東方財富 (EM)", ak.stock_zh_a_spot_em)
check("新浪財經 (Sina)", ak.stock_zh_a_spot)
