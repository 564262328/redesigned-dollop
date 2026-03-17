import os
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import json
import random

# --- 1. 数据库辅助函数 ---
DB_FILE = "stocks_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"last_update": "", "total_count": 0, "stock_list": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def fetch_safe_data(func, *args, **kwargs):
    time.sleep(random.uniform(1.5, 3.0)) # 随机休眠防封
    try:
        return func(*args, **kwargs)
    except:
        return pd.DataFrame()

def analyze_chip_density(row):
    try:
        turnover = float(row.get('换手率', 0))
        if turnover < 3: return "集中"
        if turnover < 10: return "活跃"
        return "发散"
    except:
        return "未知"

# --- 2. 主运行函数 ---
def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = load_db()
    
    # 获取全行情
    print("正在扫描全市场...")
    df_a = fetch_safe_data(ak.stock_zh_a_spot_em)
    
    if df_a.empty:
        print("数据获取失败，退出。")
        return

    # 识别新股逻辑
    current_codes = [str(c) for c in df_a['代码'].tolist()]
    old_codes = set(db.get("stock_list", []))
    new_stocks = set(current_codes) - old_codes
    
    # 更新数据库
    db["last_update"] = now_str
    db["total_count"] = len(current_codes)
    db["stock_list"] = current_codes
    save_db(db)

    # 准备新股显示文本 (必须在 run 函数内)
    new_stocks_display = "、".join(list(new_stocks)[:10]) + ("..." if len(new_stocks) > 10 else "")
    if not new_stocks:
        new_stocks_display = "暂无新标的入库"

    # 筛选今日强热点 (前 12 名)
    top_performers = df_a.sort_values(by="涨跌幅", ascending=False).head(12)
    
    cards_html = ""
    for _, row in top_performers.iterrows():
        color = "text-red-500" if float(row['涨跌幅']) > 0 else "text-green-500"
        chip = analyze_chip_density(row)
        cards_html += f"""
        <div class="glass-card p-5 border-t-2 border-white/5 hover:border-blue-500/50 transition-all font-black uppercase">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="text-base font-black text-white leading-tight">{row['名称']}</h3>
                    <span class="text-[10px] text-slate-500 font-mono italic">{row['代码']}</span>
                </div>
                <div class="text-right">
                    <span class="text-xl font-black {color}">¥{row['最新价']}</span>
                    <span class="text-xs {color} block font-bold tracking-tighter">{row['涨跌幅']}%</span>
                </div>
            </div>
            <div class="grid grid-cols-2 gap-3 text-[10px] border-t border-white/5 pt-3 uppercase italic">
                <div class="flex flex-col"><span class="text-slate-600 font-bold mb-1">换手</span><span class="text-slate-300 font-mono">{row['换手率']}%</span></div>
                <div class="flex flex-col text-right"><span class="text-slate-600 font-bold mb-1">量比</span><span class="text-amber-400 font-mono">{row['量比']}</span></div>
                <div class="flex flex-col"><span class="text-slate-600 font-bold mb-1">筹码</span><span class="text-blue-400 font-bold">{chip}</span></div>
                <div class="flex flex-col text-right"><span class="text-slate-600 font-bold mb-1">市盈率</span><span class="text-slate-300 font-mono">{row['动态市盈率']}</span></div>
            </div>
        </div>
        """

    # 渲染模板
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
<body class="p-4 md:p-12 font-bold italic font-black uppercase tracking-tight">
    <div class="max-w-6xl mx-auto">
        <header class="flex flex-col md:flex-row justify-between items-center mb-12 border-b border-white/5 pb-10 gap-6">
            <div>
                <h1 class="text-4xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-br from-blue-400 to-emerald-400 uppercase">QUANT SCANNER v13.1</h1>
                <p class="text-slate-500 text-[10px] uppercase tracking-[0.5em] font-black mt-2 underline decoration-blue-500/50 underline-offset-8">DATA PERSISTENCE MONITORING</p>
            </div>
            <div class="bg-slate-900/80 px-5 py-3 rounded-2xl border border-white/10 shadow-2xl">
                <span class="text-blue-400 font-black text-[10px] block mb-1 uppercase tracking-widest animate-pulse italic">● DB ASSETS ACTIVE</span>
                <span class="text-sm font-mono text-slate-300 tracking-widest italic">{now_str}</span>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
            {cards_html}
        </div>

        <div class="glass-card p-8 border border-blue-500/20">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-6">
                <div>
                    <h2 class="text-xs font-black text-blue-400 uppercase tracking-[0.3em] mb-2 flex items-center gap-2 italic">
                        <span class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span> 數據資產監控中心 / DATABASE ASSETS
                    </h2>
                </div>
                <div class="flex gap-8">
                    <div class="text-center">
                        <span class="block text-2xl font-black text-white font-mono">{db['total_count']}</span>
                        <span class="text-[9px] text-slate-500 uppercase font-bold">總標的數</span>
                    </div>
                    <div class="text-center border-l border-white/10 pl-8 font-bold italic">
                        <span class="block text-2xl font-black text-emerald-400 font-mono">+{len(new_stocks)}</span>
                        <span class="text-[9px] text-slate-500 uppercase font-bold">今日新股</span>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 font-bold italic">
                <div class="col-span-2 bg-black/40 rounded-xl p-5 border border-white/5 font-bold italic">
                    <div class="text-[9px] text-slate-600 font-black uppercase mb-3 tracking-widest italic">📋 掃描日誌 / SCAN LOGS</div>
                    <div class="space-y-2 text-[11px] font-medium italic">
                        <p class="text-slate-400 italic font-bold tracking-widest leading-relaxed"><span class="text-blue-500">▶</span> 新標的索引: <span class="text-slate-200 underline decoration-slate-700">{new_stocks_display}</span></p>
                        <p class="text-slate-400 italic font-bold tracking-widest leading-relaxed"><span class="text-blue-500">▶</span> 持久化存儲路徑: <span class="text-blue-400 font-bold italic">/redesigned-dollop/stocks_db.json</span></p>
                    </div>
                </div>
                <div class="bg-blue-500/5 rounded-xl p-5 border border-blue-500/10 flex flex-col justify-center text-center font-bold italic font-black uppercase">
                    <span class="text-[10px] text-blue-500 font-black uppercase italic tracking-widest">Git Persistence Verified</span>
                </div>
            </div>
        </div>

        <footer class="mt-20 py-10 text-center border-t border-white/5 text-slate-700 text-[10px] font-black uppercase tracking-[0.4em]">
            Persistence Engine: Git-Auto-Commit • v13.1 Stable
        </footer>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_tpl)
    with open(".nojekyll", "w") as f:
        f.write("")
    print(f"✅ 扫描完成。同步时间: {now_str}")

if __name__ == "__main__":
    run()



