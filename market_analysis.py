import os
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import json
import random
import requests

# --- 1. Database & Helper Functions ---
DB_FILE = "stocks_db.json"

# List of real browser User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def fetch_safe_data(func, *args, **kwargs):
    """Enhanced fetcher with browser-like headers and retries"""
    # Create a session with a random User-Agent
    session = requests.Session()
    session.headers.update({"User-Agent": random.choice(USER_AGENTS)})
    
    # Try up to 3 times
    for attempt in range(3):
        try:
            # Random sleep to mimic human behavior (5-10 seconds)
            wait_time = random.uniform(5.0, 10.0)
            print(f"  [Attempt {attempt+1}] Waiting {wait_time:.1f}s before request...")
            time.sleep(wait_time)
            
            # Execute the akshare function
            data = func(*args, **kwargs)
            
            if data is not None and not data.empty:
                print(f"  ✅ Data received: {len(data)} rows.")
                return data
            else:
                print(f"  ⚠️ Attempt {attempt+1} returned empty data.")
        except Exception as e:
            print(f"  ❌ Attempt {attempt+1} failed: {e}")
            
    return pd.DataFrame()

# ... (The rest of your run() function stays the same) ...

# --- 2. Main Execution Logic ---
def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = load_db()
    
    print(f"🚀 Starting Quant Scan at {now_str}...")
    
    # Fetch Data
    df_a = fetch_safe_data(ak.stock_zh_a_spot_em)
    df_sector = fetch_safe_data(ak.stock_board_industry_name_em)
    
    # Initialize UI Components (Placeholders if data fails)
    sector_html = "<p class='text-slate-500 italic'>Sector data unavailable. Retrying next sync...</p>"
    cards_html = """
    <div class="col-span-full p-12 text-center border-2 border-dashed border-white/10 rounded-3xl">
        <p class="text-amber-500 font-black text-xl mb-2">⚠️ API SYNC DELAYED</p>
        <p class="text-slate-500 text-xs uppercase tracking-widest">Provider connection timed out. System is in fallback mode.</p>
    </div>"""
    new_stocks = set()

    # --- Data Processing (Only runs if API returns data) ---
    if not df_a.empty:
        # Update Database
        current_codes = [str(c) for c in df_a['代码'].tolist()]
        old_codes = set(db.get("stock_list", []))
        new_stocks = set(current_codes) - old_codes
        db.update({"last_update": now_str, "total_count": len(current_codes), "stock_list": current_codes})
        save_db(db)

        # Process Sector Ranking (Top 5)
        if not df_sector.empty:
            sector_html = ""
            df_sector['涨跌幅'] = pd.to_numeric(df_sector['涨跌幅'], errors='coerce')
            top_5_sectors = df_sector.sort_values(by="涨跌幅", ascending=False).head(5)
            for _, s in top_5_sectors.iterrows():
                sector_html += f"""
                <div class="flex justify-between items-center py-2 border-b border-white/5">
                    <span class="text-xs font-bold text-slate-300 tracking-wider">#{s['板块名称']}</span>
                    <span class="text-xs font-mono font-black text-red-500">+{s['涨跌幅']}%</span>
                </div>"""

        # Process Individual Stock Cards (Top 12)
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

    # --- 3. HTML Generation (Always runs) ---
    html_tpl = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #020617; background-image: radial-gradient(circle at 50% -20%, #1e293b 0%, #020617 80%); min-height: 100vh; color: #f8fafc; font-family: ui-sans-serif, system-ui; }}
        .glass-card {{ background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); border-radius: 20px; }}
    </style>
</head>
<body class="p-4 md:p-12 font-black uppercase tracking-tight italic">
    <div class="max-w-6xl mx-auto">
        <header class="flex flex-col md:flex-row justify-between items-center mb-12 border-b border-white/5 pb-10 gap-6">
            <div>
                <h1 class="text-4xl font-black italic bg-clip-text text-transparent bg-gradient-to-br from-blue-400 to-emerald-400">QUANT SCANNER v13.4</h1>
                <p class="text-slate-500 text-[10px] uppercase font-black mt-2 tracking-[0.4em] underline decoration-blue-500/50 underline-offset-8">Market Leadership Engine</p>
            </div>
            <div class="bg-slate-900/80 px-5 py-3 rounded-2xl border border-white/10 shadow-2xl font-bold">
                <span class="text-blue-400 text-[10px] block mb-1 animate-pulse italic uppercase tracking-widest">● DATA SYNC ACTIVE</span>
                <span class="text-sm font-mono text-slate-300 italic font-black">{now_str}</span>
            </div>
        </header>

        <div class="mb-12 glass-card p-8 border border-red-500/20 bg-red-500/5">
            <h2 class="text-xs font-black text-red-500 uppercase tracking-[0.3em] mb-6 flex items-center gap-2">
                <span class="w-2 h-2 bg-red-500 rounded-full animate-ping"></span> TOP 5 INDUSTRY SECTORS
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-5 gap-8">{sector_html}</div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">{cards_html}</div>

        <div class="glass-card p-8 border border-blue-500/20">
            <div class="flex flex-col md:flex-row justify-between items-center mb-8 gap-6 font-bold">
                <h2 class="text-xs font-black text-blue-400 uppercase tracking-widest italic font-bold">DATABASE MONITOR</h2>
                <div class="flex gap-8">
                    <div class="text-center"><span class="block text-2xl font-black text-white font-mono">{db['total_count']}</span><span class="text-[9px] text-slate-500 uppercase">Total Stocks</span></div>
                    <div class="text-center border-l border-white/10 pl-8"><span class="block text-2xl font-black text-emerald-400 font-mono">+{len(new_stocks)}</span><span class="text-[9px] text-slate-500 uppercase">New Today</span></div>
                </div>
            </div>
            <div class="bg-black/40 rounded-xl p-5 border border-white/5 text-[11px] text-slate-400 italic">
                <span class="text-blue-500 font-black">▶</span> New Listings Log: {", ".join(list(new_stocks)[:10]) if new_stocks else "No New Listings Found"}
            </div>
        </div>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f: 
        f.write(html_tpl)
    
    # Create .nojekyll to ensure GitHub Pages doesn't ignore files
    with open(".nojekyll", "w", encoding="utf-8") as f: 
        f.write("")
        
    print(f"✅ Success: index.html generated and ready for deployment.")

if __name__ == "__main__":
    run()





