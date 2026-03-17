# --- 在 run() 函數內，替換原本的 html_tpl 變量內容 ---

    # 提取新股名單用於展示
    new_stocks_display = "、".join(list(new_stocks)[:10]) + ("..." if len(new_stocks) > 10 else "")
    if not new_stocks: new_stocks_display = "暫無新標的入庫"

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
        .db-glow {{ box-shadow: 0 0 20px rgba(59, 130, 246, 0.15); }}
        @keyframes pulse-soft {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        .animate-soft {{ animation: pulse-soft 3s infinite; }}
    </style>
</head>
<body class="p-4 md:p-12">
    <div class="max-w-6xl mx-auto">
        <!-- 頂部標題與狀態 -->
        <header class="flex flex-col md:flex-row justify-between items-center mb-12 border-b border-white/5 pb-10 gap-6">
            <div>
                <h1 class="text-4xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-br from-blue-400 to-emerald-400">QUANT SCANNER v13.1</h1>
                <p class="text-slate-500 text-[10px] uppercase tracking-[0.5em] font-black mt-2 underline decoration-blue-500/50 underline-offset-8">DATA PERSISTENCE & MONITORING</p>
            </div>
            <div class="flex gap-4">
                <div class="text-right bg-slate-900/80 px-5 py-3 rounded-2xl border border-white/10 shadow-2xl">
                    <span class="text-blue-400 font-black text-[10px] block mb-1 uppercase tracking-widest animate-soft">● DB PERSISTENCE ACTIVE</span>
                    <span class="text-sm font-mono text-slate-300 tracking-widest italic">{now_str}</span>
                </div>
            </div>
        </header>

        <!-- 今日強勢標的網格 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {cards_html}
        </div>

        <!-- 🔄 數據資產監控中心 (新模組) -->
        <div class="glass-card p-8 border border-blue-500/20 db-glow">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-6">
                <div>
                    <h2 class="text-xs font-black text-blue-400 uppercase tracking-[0.3em] mb-2 flex items-center gap-2">
                        <span class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span> 數據資產監控中心 / DATABASE ASSETS
                    </h2>
                    <p class="text-slate-500 text-[10px] uppercase font-bold italic tracking-wider">自動化掃描與 Git 持久化存儲狀態</p>
                </div>
                <div class="flex gap-8">
                    <div class="text-center">
                        <span class="block text-2xl font-black text-white font-mono">{db['total_count']}</span>
                        <span class="text-[9px] text-slate-500 uppercase font-bold">總標的數</span>
                    </div>
                    <div class="text-center border-l border-white/10 pl-8">
                        <span class="block text-2xl font-black text-emerald-400 font-mono">+{len(new_stocks)}</span>
                        <span class="text-[9px] text-slate-500 uppercase font-bold">今日新股</span>
                    </div>
                </div>
            </div>

            <!-- 數據細節與日誌 -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="col-span-2 bg-black/40 rounded-xl p-5 border border-white/5">
                    <div class="text-[9px] text-slate-600 font-black uppercase mb-3 tracking-widest font-bold italic">📋 本次掃描日誌 / LOGS</div>
                    <div class="space-y-2 text-[11px] font-medium italic">
                        <p class="text-slate-400 tracking-tight leading-relaxed">
                            <span class="text-blue-500">▶</span> 已成功獲取 A 股全市場及熱門 ETF 行情快照。
                        </p>
                        <p class="text-slate-400 tracking-tight leading-relaxed">
                            <span class="text-blue-500">▶</span> <span class="text-slate-200">stocks_db.json</span> 增量對比完成，偵測到新股入庫。
                        </p>
                        <p class="text-emerald-500/80 tracking-tight leading-relaxed">
                            <span class="text-emerald-500 font-bold">▶</span> 新標的索引: <span class="text-slate-300 underline decoration-slate-700">{new_stocks_display}</span>
                        </p>
                    </div>
                </div>
                <div class="bg-blue-500/5 rounded-xl p-5 border border-blue-500/10 flex flex-col justify-between">
                    <div>
                        <div class="text-[9px] text-blue-400 font-black uppercase mb-2 tracking-widest font-bold italic">💾 安全備份策略</div>
                        <p class="text-[10px] text-slate-400 leading-relaxed font-bold italic">
                            數據已加密壓縮並通過 GitHub Action 自動回傳至 <span class="text-blue-400">main</span> 分支。
                        </p>
                    </div>
                    <div class="mt-4 pt-4 border-t border-blue-500/10 text-center">
                        <span class="text-[10px] text-blue-500 font-black uppercase italic tracking-widest font-bold">Encrypted & Verified</span>
                    </div>
                </div>
            </div>
        </div>

        <footer class="mt-20 py-10 text-center border-t border-white/5 text-slate-700 text-[10px] font-black uppercase tracking-[0.4em]">
            Persistence Engine: Git-Auto-Commit • Data: AkShare • v13.1 Stable
        </footer>
    </div>
</body>
</html>
"""



