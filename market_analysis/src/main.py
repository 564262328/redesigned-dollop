import os
import json
import time
import random
import pandas as pd
import akshare as ak
from datetime import datetime

# --- CONFIGURATION ---
DB_FILE = "stocks_db.json"

# --- DATABASE LOGIC ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"last_update": "", "total_count": 0, "stock_list": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

# --- DATA FETCHING LOGIC ---
def fetch_data():
    print("  [Layer 1] Trying EastMoney...")
    try:
        time.sleep(random.uniform(3, 6))
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty: return df
    except: pass

    print("  [Layer 2] Trying Sina...")
    try:
        time.sleep(random.uniform(3, 6))
        df = ak.stock_zh_a_spot()
        if df is not None and not df.empty:
            return df.rename(columns={'trade':'最新价', 'changepercent':'涨跌幅', 'code':'代码'})
    except: pass
    return pd.DataFrame()

# --- UI GENERATION ---
def build_html(now_str, db, df_a, new_count):
    stocks_html = ""
    if not df_a.empty:
        df_a['涨跌幅'] = pd.to_numeric(df_a['涨跌幅'], errors='coerce')
        top_12 = df_a.sort_values(by="涨跌幅", ascending=False).head(12)
        for _, r in top_12.iterrows():
            stocks_html += f"""
            <div class="p-5 bg-slate-900/80 border border-white/5 rounded-2xl">
                <div class="flex justify-between mb-2">
                    <span class="text-white font-bold">{r['名称']}</span>
                    <span class="text-[10px] text-slate-500 font-mono italic">{r['代码']}</span>
                </div>
                <div class="flex justify-between items-end">
                    <span class="text-xl font-mono text-emerald-400">¥{r.get('最新价', 'N/A')}</span>
                    <span class="text-xs font-bold text-red-500">+{r.get('涨跌幅', 0)}%</span>
                </div>
            </div>"""
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script>
    <style>body {{ background: #020617; color: #f8fafc; font-family: ui-sans-serif; font-style: italic; text-transform: uppercase; }}</style>
</head>
<body class="p-6 md:p-12 font-black">
    <div class="max-w-6xl mx-auto">
        <header class="flex justify-between border-b border-white/5 pb-10 mb-12">
            <h1 class="text-4xl italic bg-clip-text text-transparent bg-gradient-to-br from-blue-400 to-emerald-400">QUANT TERMINAL v14.1</h1>
            <div class="text-sm font-mono text-slate-300 bg-slate-900 px-4 py-2 rounded-xl border border-white/10">{now_str}</div>
        </header>
        <div class="grid grid-cols-2 gap-8 mb-12">
            <div class="p-8 bg-blue-500/5 border border-blue-500/10 rounded-3xl text-center">
                <div class="text-4xl mb-1">{db.get('total_count', 0)}</div><div class="text-[10px] text-slate-500">TOTAL STOCKS</div>
            </div>
            <div class="p-8 bg-emerald-500/5 border border-emerald-500/10 rounded-3xl text-center">
                <div class="text-4xl text-emerald-400">+{new_count}</div><div class="text-[10px] text-slate-500">NEW TODAY</div>
            </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">{stocks_html}</div>
    </div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

# --- MAIN RUNNER ---
def main():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 Quant System Start: {now_str}")
    
    db = load_db()
    df_a = fetch_data()
    
    new_count = 0
    if not df_a.empty:
        current_codes = [str(c) for c in df_a['代码'].tolist()]
        old_codes = set(db.get("stock_list", []))
        if old_codes:
            new_count = len(set(current_codes) - old_codes)
        
        db.update({"last_update": now_str, "total_count": len(current_codes), "stock_list": current_codes})
        save_db(db)
    
    build_html(now_str, db, df_a, new_count)
    print("✅ Build Finished. index.html created.")

if __name__ == "__main__":
    main()
