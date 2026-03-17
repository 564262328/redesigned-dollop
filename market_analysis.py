import os
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import json
import random

# --- 1. Database Configuration ---
DB_FILE = "stocks_db.json"

def load_db():
    """Load the existing database file"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"last_update": "", "total_count": 0, "stock_list": []}

def save_db(data):
    """v13.3: Minified JSON to save space and prevent timeouts"""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        # Minified format: no spaces or indents
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

def fetch_safe_data(func, *args, **kwargs):
    """Fetch data with random sleep to avoid anti-crawling blocks"""
    time.sleep(random.uniform(2.0, 4.0))
    try:
        return func(*args, **kwargs)
    except:
        return pd.DataFrame()

# --- 2. Main Execution Logic ---
def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = load_db()  # This now works!
    
    print("Starting full market scan...")
    df_a = fetch_safe_data(ak.stock_zh_a_spot_em)
    
    if df_a.empty:
        print("Data Error: API unreachable. Exiting.")
        return

    # Process Database Persistence
    current_codes = [str(c) for c in df_a['代码'].tolist()]
    old_codes = set(db.get("stock_list", []))
    new_stocks = set(current_codes) - old_codes
    
    db["last_update"] = now_str
    db["total_count"] = len(current_codes)
    db["stock_list"] = current_codes
    save_db(db)

    # Prepare UI Components
    new_stocks_display = "、".join(list(new_stocks)[:10]) if new_stocks else "No New Listings Found"
    top_12 = df_a.sort_values(by="涨跌幅", ascending=False).head(12)
    
    cards_html = ""
    for _, row in top_12.iterrows():
        try:
            pct = float(row['涨跌幅'])
            color = "text-red-500" if pct > 0 else "text-green-500"
            cards_html += f"""
            <div class="glass-card p-5 border-t-2 border-white/5 font-black uppercase">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-base font-black text-white">{row['名称']}</h3>
                        <span class="text-[10px] text-slate-500 font-mono italic">{row['代码']}</span>
                    </div>
                    <div class="text-right">
                        <span class="text-xl font-black {color}">¥{row['最新价']}</span>
                        <span class="text-xs {color} block font-bold">{pct}%</span>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-3 text-[10px] border-t border-white/5 pt-3 uppercase italic font-bold">
                    <div class="flex flex-col"><span class="text-slate-600">换手率</span><span class="text-slate-200">{row['换手率']}%</span></div>
                    <div class="flex flex-col text-right"><span class="text-slate-600">量比</span><span class="text-amber-400">{row['量比']}</span></div>
                </div>
            </div>
            """
        except: continue

    # HTML Template
    html_tpl = f"""
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
<body class="p-4 md:p-12 font-black uppercase tracking-tight italic">
    <div class="max-w-6xl mx-auto">
        <header class="flex flex-col md:flex-row justify-between items-center mb-12 border-b border-white/5 pb-10 gap-6">
            <div>
                <h1 class="text-4xl font-black italic bg-clip-text text-transparent bg-gradient-to-br from-blue-400 to-emerald-400">QUANT SCANNER v13.3</h1>
                <p class="text-slate-500 text-[10px] uppercase font-black mt-2 underline decoration-blue-500/50 underline-offset-8">Lightweight Persistence</p>
            </div>
            <div class="bg-slate-900/80 px-5 py-3 rounded-2xl border border-white/10 shadow-2xl font-bold">
                <span class="text-blue-400 text-[10px] block mb-1 animate-pulse italic uppercase tracking-widest">● DATA SYNC ACTIVE</span>
                <span class="text-sm font-mono text-slate-300 italic">{now_str}</span>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
            {cards_html}
        </div>

        <div class="glass-card p-8 border border-blue-500/20 font-bold">
            <div class="flex flex-col md:flex-row justify-between items-center mb-8 gap-6">
                <h2 class="text-xs font-black text-blue-400 uppercase tracking-widest italic font-bold">DATABASE MONITOR / 數據資產</h2>
                <div class="flex gap-8">
                    <div class="text-center font-bold">
                        <span class="block text-2xl font-black text-white font-mono">{db['total_count']}</span>
                        <span class="text-[9px] text-slate-500 uppercase">Total Stocks</span>
                    </div>
                    <div class="text-center border-l border-white/10 pl-8 font-bold">
                        <span class="block text-2xl font-black text-emerald-400 font-mono">+{len(new_stocks)}</span>
                        <span class="text-[9px] text-slate-500 uppercase">New Today</span>
                    </div>
                </div>
            </div>
            <div class="bg-black/40 rounded-xl p-5 border border-white/5 text-[11px] text-slate-400 italic">
                <span class="text-blue-500 font-black">▶</span> Recent Listings: {new_stocks_display}
            </div>
        </div>
    </div>
</body>
</html>
"""
    # Save output files
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_tpl)
    with open(".nojekyll", "w", encoding="utf-8") as f:
        f.write("")
    
    print(f"🚀 Deployment v13.3 successful at {now_str}")

if __name__ == "__main__":
    run()





