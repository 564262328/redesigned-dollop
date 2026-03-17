import os

def build_dashboard(now_str, db, df_a, new_count):
    """Generates the Cyberpunk Dark-Theme UI"""
    stocks_html = ""
    
    if not df_a.empty:
        # Get Top 12 Gainers
        import pandas as pd
        df_a['涨跌幅'] = pd.to_numeric(df_a['涨跌幅'], errors='coerce')
        top_12 = df_a.sort_values(by="涨跌幅", ascending=False).head(12)
        
        for _, r in top_12.iterrows():
            stocks_html += f"""
            <div class="p-5 bg-slate-900/80 border border-white/5 rounded-2xl hover:border-blue-500/50 transition-all">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-white font-black">{r['名称']}</span>
                    <span class="text-[10px] text-slate-500 font-mono italic">{r['代码']}</span>
                </div>
                <div class="flex justify-between items-end">
                    <span class="text-xl font-mono text-emerald-400">¥{r.get('最新价', 'N/A')}</span>
                    <span class="text-xs font-bold text-red-500">+{r.get('涨跌幅', 0)}%</span>
                </div>
            </div>"""
    else:
        stocks_html = "<div class='col-span-full text-center p-12 text-slate-600 italic'>Waiting for market sync...</div>"

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #020617; color: #f8fafc; font-family: ui-sans-serif, system-ui; font-style: italic; text-transform: uppercase; }}
        .main-glass {{ background: radial-gradient(circle at 50% 0%, rgba(30, 58, 138, 0.15) 0%, rgba(2, 6, 23, 0) 70%); }}
    </style>
</head>
<body class="min-h-screen main-glass p-6 md:p-12 font-black tracking-tight">
    <div class="max-w-6xl mx-auto">
        <header class="flex flex-col md:flex-row justify-between items-center mb-12 border-b border-white/5 pb-10">
            <div>
                <h1 class="text-4xl font-black italic bg-clip-text text-transparent bg-gradient-to-br from-blue-400 to-emerald-400">QUANT TERMINAL v14.0</h1>
                <p class="text-slate-500 text-[10px] mt-2 tracking-[0.4em]">Multi-Source Leadership Engine</p>
            </div>
            <div class="bg-slate-900/80 px-6 py-3 rounded-2xl border border-white/10 font-bold mt-6 md:mt-0">
                <span class="text-blue-400 text-[10px] block mb-1 animate-pulse">● DATA SYNC ACTIVE</span>
                <span class="text-sm font-mono text-slate-300">{now_str}</span>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            <div class="p-8 bg-blue-500/5 border border-blue-500/10 rounded-3xl text-center">
                <div class="text-4xl font-black mb-1">{db.get('total_count', 0)}</div>
                <div class="text-[10px] text-slate-500 tracking-widest">DATABASE TOTAL STOCKS</div>
            </div>
            <div class="p-8 bg-emerald-500/5 border border-emerald-500/10 rounded-3xl text-center">
                <div class="text-4xl font-black text-emerald-400">+{new_count}</div>
                <div class="text-[10px] text-slate-500 tracking-widest">NEW LISTINGS TODAY</div>
            </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {stocks_html}
        </div>
    </div>
</body>
</html>"""
    
    # Save index.html in the SAME directory as main.py (root)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

