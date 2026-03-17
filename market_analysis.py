import os
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import json
import random
import requests

# --- 1. CONFIG & DB FUNCTIONS (MUST BE AT TOP) ---
DB_FILE = "stocks_db.json"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

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

def fetch_safe_data(func, *args, **kwargs):
    """Fetcher with browser-like headers and retries"""
    for attempt in range(3):
        try:
            # Random sleep (5-10s) to avoid bot detection
            time.sleep(random.uniform(5.0, 10.0))
            data = func(*args, **kwargs)
            if data is not None and not data.empty:
                return data
        except:
            continue
    return pd.DataFrame()

# --- 2. MAIN EXECUTION ---
def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = load_db()  # Now correctly defined above
    
    print(f"🚀 Syncing: {now_str}")
    
    # Fetch Data
    df_a = fetch_safe_data(ak.stock_zh_a_spot_em)
    df_sector = fetch_safe_data(ak.stock_board_industry_name_em)
    
    # Default Placeholders
    sector_html = "<p class='text-slate-500 italic'>Syncing sector data...</p>"
    cards_html = "<div class='col-span-full p-12 text-center border-2 border-dashed border-white/10 rounded-3xl'><p class='text-amber-500 font-black'>⚠️ API SYNC DELAYED. RETRYING...</p></div>"
    new_stocks = set()

    if not df_a.empty:
        # DB Update
        current_codes = [str(c) for c in df_a['代码'].tolist()]
        old_codes = set(db.get("stock_list", []))
        new_stocks = set(current_codes) - old_codes
        db.update({"last_update": now_str, "total_count": len(current_codes), "stock_list": current_codes})
        save_db(db)

        # Sectors
        if not df_sector.empty:
            sector_html = ""
            df_sector['涨跌幅'] = pd.to_numeric(df_sector['涨跌幅'], errors='coerce')
            top_5 = df_sector.sort_values(by="涨跌幅", ascending=False).head(5)
            for _, s in top_5.iterrows():
                sector_html += f"<div class='flex justify-between items-center py-2 border-b border-white/5'><span class='text-xs font-bold text-slate-300'>#{s['板块名称']}</span><span class='text-xs font-mono font-black text-red-500'>+{s['涨跌幅']}%</span></div>"

        # Stock Cards
        top_12 = df_a.sort_values(by="涨跌幅", ascending=False).head(12)
        cards_html = "".join([f"""
        <div class="glass-card p-5 border-t-2 border-white/5 hover:border-blue-500/50 transition-all font-black uppercase">
            <div class="flex justify-between items-start mb-4">
                <div><h3 class="text-base font-black text-white">{r['名称']}</h3><span class="text-[10px] text-slate-500 font-mono italic">{r['代码']}</span></div>
                <div class="text-right"><span class="text-xl font-black text-red-500">¥{r.get('最新价', 'N/A')}</span><span class="text-xs text-red-500 block font-bold">{r.get('涨跌幅', 0)}%</span></div>
            </div>
            <div class="grid grid-cols-2 gap-3 text-[10px] border-t border-white/5 pt-3 uppercase italic font-bold">
                <div class="flex flex-col"><span class="text-slate-600">换手率</span><span class="text-slate-200">{r.get('换手率', 0)}%</span></div>
                <div class="flex flex-col text-right"><span class="text-slate-600">量比</span><span class="text-amber-400">{r.get('量比', 0)}</span></div>
            </div>
        </div>""" for _, r in top_12.iterrows()])

    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #020617; background-image: radial-gradient(circle at 50% -20%, #1e293b 0%, #020617 80%); min-height: 100vh; color: #f8fafc; }}
        .glass-card {{ background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); border-radius: 20px; }}
    </style>
</head>
<body class="p-4 md:p-12 font-black uppercase italic">
    <div class="max-w-6xl mx-auto">
        <header class="flex flex-col md:flex-row justify-between items-center mb-12 border-b border-white/5 pb-10">
            <h1 class="text-4xl font-black italic bg-clip-text text-transparent bg-gradient-to-br from-blue-400 to-emerald-400">QUANT SCANNER v13.4</h1>
            <div class="bg-slate-900/80 px-5 py-3 rounded-2xl border border-white/10 font-bold">
                <span class="text-sm font-mono text-slate-300 font-black">{now_str}</span>
            </div>
        </header>
        <div class="mb-12 glass-card p-8 border border-red-500/20 bg-red-500/5">
            <h2 class="text-xs font-black text-red-500 mb-6">● TOP 5 SECTORS</h2>
            <div class="grid grid-cols-1 md:grid-cols-5 gap-8">{sector_html}</div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">{cards_html}</div>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")
    print("✅ Build Finished.")

if __name__ == "__main__":
    run()






