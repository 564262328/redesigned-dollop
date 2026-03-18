import akshare as ak
import pandas as pd

def check(name, func, **kwargs):
    try:
        print(f"🔍 正在測試 {name}...")
        df = func(**kwargs)
        if df is not None and not df.empty:
            print(f"✅ {name} 成功！獲取到 {len(df)} 筆數據。")
        else:
            print(f"⚠️ {name} 回傳數據為空。")
    except Exception as e:
        print(f"❌ {name} 失敗: {str(e)[:120]}")

print("--- 🚀 AkShare 接口 (EM/Sina/TX) 連通性診斷 ---")

# 測試東財
check("東方財富 (EM)", ak.stock_zh_a_spot_em)

# 測試新浪
check("新浪財經 (Sina)", ak.stock_zh_a_spot)

# 測試騰訊 (使用個股歷史接口診斷)
check("騰訊財經 (TX)", ak.stock_zh_a_hist_tx, symbol="sh600519")

print("\n💡 診斷結束")
