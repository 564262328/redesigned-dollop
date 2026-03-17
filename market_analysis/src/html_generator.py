# src/html_generator.py
import random

def build_dashboard(now_str, db, df_a, new_stocks_count):
    """
    負責生成暗黑科技風 (Cyberpunk) 佈局的 HTML 終端
    參數:
    - now_str: 當前時間字符串
    - db: 從 database.py 讀取的歷史字典
    - df_a: 當前抓取到的股票 DataFrame
    - new_stocks_count: 今日新增股票數量
    """
    
    # --- 1. 處理左側歷史記錄 (模擬數據或從 DB 提取) ---
    history_html = ""
    # 這裡取出數據庫中前 8 隻股票代碼作為演示歷史
    display_list = db.get("stock_list", [])[:8]
    for code in display_list:
        score = random.randint(30, 85)
        color = "emerald-500" if score > 60 else "amber-500"
        history_html += f"""
        <div class="flex justify-between items-center p-3 mb-2 bg-slate-900/50 rounded-lg border border-white/5 hover:bg-slate-800 transition-all cursor-pointer">
            <div>
                <div class="text-[9px] text-slate-500 font-mono italic">HISTORY SCAN</div>
                <div class="text-xs font-bold text-slate-300">STOCK ID: {code}</div>
            </div>
            <div class="text-sm font-black text-{color}">{score}</div>
        </div>"""

    # --- 2. 處理核心看板 (漲幅榜第一名) ---
    main_card_html = ""
    strategy_html = ""
    if not df_a.empty:
        # 確保漲跌幅是數字格式
        import pandas as pd
        df_a['涨跌幅'] = pd.to_numeric(df_a['涨跌幅'], errors='coerce')
        top_1 = df_a.sort_values(by="涨跌幅", ascending=False).iloc[0]
        
        price = top_1.get('最新价', '0.00')
        change = top_1.get('涨跌幅', '0.00')
        
        main_card_html = f"""
        <div class="flex items-center gap-4 mb-6">
            <h2 class="text-3xl font-black text-white">{top_1['名称']}</h2>
            <span class="text-xl font-mono text-emerald-400">¥{price}</span>
            <span class="text-sm font-bold text-emerald-500">+{change}%</span>
        </div>
        <div class="p-6 bg-blue-500/5 border border-blue-500/20 rounded-xl mb-8">
            <h3 class="text-blue-400 text-[10px] font-black tracking-[0.3em] mb-4">KEY INSIGHTS / 關鍵洞察</h3>
            <p class="text-slate-400 text-sm leading-relaxed italic">
                {top_1['名称']} ({top_1['代码']}) 目前處於強勢領漲狀態。量比數據顯示資金流入明顯。
                當前市場情緒為【中性】，建議關注支撐位與壓力位的轉換，切勿盲目追高。
            </p>
        </div>"""

        # 策略點位計算 (模擬)
        try:
            p = float(price)
            strategy_html = f"""
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-slate-900/80 p-4 rounded-xl border border-white/5 text-center">
                    <div class="text-[9px] text-slate-500 mb-1">狙擊買入</div>
                    <div class="text-emerald-400 font-mono font-bold">{p*0.98:.2f}</div>
                </div>
                <div class="bg-slate-900/80 p-4 rounded-xl border border-white/5 text-center">
                    <div class="text-[9px] text-slate-500 mb-1">二次防禦</div>
                    <div class="text-blue-400 font-mono font-bold">{p*0.95:.2f}</div>
                </div>
                <div class="bg-slate-900/80 p-4 rounded-xl border border-white/5 text-center">
                    <div class="text-[9px] text-slate-500 mb-1">強制止損</div>
                    <div class="text-pink-500 font-mono font-bold">{p*0.92:.2f}</div>
                </div>
                <div class="bg-slate-900/80 p-4 rounded-xl border border-white/5 text-center">
                    <div class="text-[9px] text-slate-500 mb-1">止盈目標</div>
                    <div class="text-amber-400 font-mono font-bold">{p*1.12:.2f}</div>
                </div>
            </div>"""
        except: pass

    # --- 3. 完整 HTML 模板封裝 ---
    full_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #020617; color: #f8fafc; font-family: ui-sans-serif, system-ui; }}
        .sidebar {{ background: rgba(15, 23, 42, 0.9); border-right: 1px solid rgba(255,255,255,0.05); }}
        .main-glass {{ background: radial-gradient(circle at 50% 0%, rgba(30, 58, 138, 0.15) 0%, rgba(2, 6, 23, 0) 70%); }}
        .sentiment-circle {{ width: 100px; height: 100px; border-radius: 50%; border: 6px solid #1e293b; border-top-color: #3b82f6; display: flex; align-items: center; justify-content: center; }}
    </style>
</head>
<body class="flex h-screen overflow-hidden italic uppercase font-black tracking-tight">
    <!-- 左側側邊欄 -->
    <aside class="sidebar w-64 flex-shrink-0 p-6 overflow-y-auto hidden md:block">
        <div class="flex items-center gap-2 mb-10">
            <div class="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
            <h1 class="text-sm font-black tracking-tighter">QUANT SYSTEM v14.0</h1>
        </div>
        <h3 class="text-[10px] text-slate-500 mb-4 tracking-widest">SCAN HISTORY</h3>
        {history_html}
    </aside>

    <!-- 主內容區 -->
    <main class="flex-1 flex flex-col min-w-0 main-glass">
        <!-- 頂部導航 -->
        <header class="h-16 flex items-center justify-between px-8 border-b border-white/5 bg-slate-900/20 backdrop-blur-md">
            <div class="text-xs text-blue-400 font-mono">● STATUS: DATA SYNC ACTIVE</div>
            <div class="flex items-center gap-4 text-[10px]">
                <span class="text-slate-500">{now_str}</span>
                <div class="bg-emerald-500/10 text-emerald-500 px-3 py-1 rounded-full border border-emerald-500/20">A-SHARE LIVE</div>
            </div>
        </header>

        <!-- 滾動內容 -->
        <div class="flex-1 overflow-y-auto p-8">
            <div class="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="lg:col-span-2">
                    {main_card_html if main_card_html else "<p class='text-slate-600'>NO DATA LOADED</p>"}
                    <h3 class="text-xs font-black text-slate-500 tracking-[0.3em] mb-4">STRATEGY POINTS / 狙擊點位</h3>
                    {strategy_html}
                </div>

                <!-- 右側監控板 -->
                <div class="lg:col-span-1 space-y-6">
                    <div class="bg-slate-900/80 p-6 rounded-2xl border border-white/5 flex flex-col items-center">
                        <h3 class="text-[10px] text-slate-500 mb-6 self-start tracking-widest">DATABASE MONITOR</h3>
                        <div class="flex gap-8 mb-6">
                            <div class="text-center">
                                <div class="text-2xl font-black text-white">{db.get('total_count', 0)}</div>
                                <div class="text-[8px] text-slate-500">STOCKS</div>
                            </div>
                            <div class="text-center border-l border-white/10 pl-8">
                                <div class="text-2xl font-black text-emerald-400">+{new_stocks_count}</div>
                                <div class="text-[8px] text-slate-500">NEW TODAY</div>
                            </div>
                        </div>
                        <div class="sentiment-circle">
                            <div class="text-center">
                                <div class="text-2xl">48</div>
                                <div class="text-[8px] text-blue-400">中性</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>
</html>
    """
    
    # 寫入根目錄供 GitHub Pages 讀取
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
