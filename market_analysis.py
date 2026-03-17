import os
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import json
import random
import requests

# --- 1. 配置与辅助函数 ---
DB_FILE = "stocks_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"last_update": "", "total_count": 0, "stock_list": []}

def fetch_safe_ak(func):
    try:
        time.sleep(random.uniform(2, 4))
        return func()
    except: return pd.DataFrame()

# --- 2. 数据抓取与 UI 组件生成 ---
def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = load_db()
    
    # 抓取数据 (以东财和腾讯作为示例数据源)
    df_a = fetch_safe_ak(ak.stock_zh_a_spot_em)
    
    # 模拟左侧历史记录 HTML
    history_html = ""
    if not df_a.empty:
        # 取最后几只作为历史记录模拟
        for _, r in df_a.tail(8).iterrows():
            score = random.randint(30, 70)
            color = "emerald-500" if score > 50 else "amber-500"
            history_html += f"""
            <div class="flex justify-between items-center p-3 mb-2 bg-slate-900/50 rounded-lg border border-white/5 hover:bg-slate-800 transition-all cursor-pointer">
                <div>
                    <div class="text-xs font-bold text-slate-300">{r['名称']}</div>
                    <div class="text-[9px] text-slate-500 font-mono">{r['代码']} · {now_str.split(' ')[0]}</div>
                </div>
                <div class="text-sm font-black text-{color}">{score}</div>
            </div>"""

    # 核心看板 (Top Gainer)
    main_card_html = ""
    strategy_html = ""
    if not df_a.empty:
        df_a['涨跌幅'] = pd.to_numeric(df_a['涨跌幅'], errors='coerce')
        top_1 = df_a.sort_values(by="涨跌幅", ascending=False).iloc[0]
        
        # 主卡片数据
        main_card_html = f"""
        <div class="flex items-center gap-4 mb-6">
            <h2 class="text-3xl font-black text-white">{top_1['名称']}</h2>
            <span class="text-xl font-mono text-emerald-400">{top_1['最新价']}</span>
            <span class="text-sm font-bold text-emerald-500">+{top_1['涨跌幅']}%</span>
        </div>
        <div class="p-6 bg-blue-500/5 border border-blue-500/20 rounded-xl mb-8">
            <h3 class="text-blue-400 text-[10px] font-black tracking-[0.3em] mb-4">KEY INSIGHTS</h3>
            <p class="text-slate-400 text-sm leading-relaxed italic">
                {top_1['名称']}当前处于强力突破阶段。技术面均线系统多头排列，量比显著放大。
                建议关注该股在 {float(top_1['最新价'])*0.98:.2f} 附近的支撑力度，不符合趋势交易原则时不宜盲目追高。
            </p>
        </div>"""

        # 策略点 (Sniper Points)
        strategy_html = f"""
        <div class="grid grid-cols-4 gap-4">
            <div class="bg-slate-900/80 p-4 rounded-xl border border-white/5 text-center">
                <div class="text-[9px] text-slate-500 mb-1">理想买入</div>
                <div class="text-emerald-400 font-mono font-bold">{float(top_1['最新价'])*0.97:.2f}</div>
            </div>
            <div class="bg-slate-900/80 p-4 rounded-xl border border-white/5 text-center">
                <div class="text-[9px] text-slate-500 mb-1">二次补仓</div>
                <div class="text-blue-400 font-mono font-bold">{float(top_1['最新价'])*0.95:.2f}</div>
            </div>
            <div class="bg-slate-900/80 p-4 rounded-xl border border-white/5 text-center">
                <div class="text-[9px] text-slate-500 mb-1">止损点位</div>
                <div class="text-pink-500 font-mono font-bold">{float(top_1['最新价'])*0.92:.2f}</div>
            </div>
            <div class="bg-slate-900/80 p-4 rounded-xl border border-white/5 text-center">
                <div class="text-[9px] text-slate-500 mb-1">止盈目标</div>
                <div class="text-amber-400 font-mono font-bold">{float(top_1['最新价'])*1.15:.2f}</div>
            </div>
        </div>"""

    # --- 3. 完整 HTML 模板 ---
    html_tpl = f"""
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
        .sentiment-circle {{ width: 120px; height: 120px; border-radius: 50%; border: 8px solid #1e293b; border-top-color: #3b82f6; display: flex; align-items: center; justify-content: center; }}
    </style>
</head>
<body class="flex h-screen overflow-hidden italic uppercase font-black">
    <!-- 左侧侧边栏 -->
    <aside class="sidebar w-64 flex-shrink-0 p-6 overflow-y-auto hidden md:block">
        <div class="flex items-center gap-2 mb-10">
            <div class="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
            <h1 class="text-sm font-black tracking-tighter">QUANT SYSTEM v14</h1>
        </div>
        
        <div class="mb-8">
            <h3 class="text-[10px] text-slate-500 mb-4 tracking-widest">ANALYSIS TASKS</h3>
            <div class="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <div class="text-xs text-blue-400 mb-1">605019正在分析...</div>
                <div class="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                    <div class="bg-blue-500 h-full w-2/3"></div>
                </div>
            </div>
        </div>

        <h3 class="text-[10px] text-slate-500 mb-4 tracking-widest">HISTORY RECORDS</h3>
        {history_html}
    </aside>

    <!-- 主操作区 -->
    <main class="flex-1 flex flex-col min-w-0 main-glass">
        <!-- 顶部导航 -->
        <header class="h-16 flex items-center justify-between px-8 border-b border-white/5 bg-slate-900/20 backdrop-blur-md">
            <div class="relative w-96">
                <input type="text" placeholder="输入股票代码, 如 600519..." class="w-full bg-slate-900/80 border border-white/10 rounded-full py-2 px-10 text-xs focus:border-blue-500 outline-none transition-all">
                <span class="absolute left-4 top-2 text-slate-500">🔍</span>
            </div>
            <div class="flex items-center gap-4 text-xs">
                <span class="text-slate-500">{now_str}</span>
                <div class="bg-emerald-500/10 text-emerald-500 px-3 py-1 rounded-full border border-emerald-500/20">LIVE DATA</div>
            </div>
        </header>

        <!-- 内容滚动区 -->
        <div class="flex-1 overflow-y-auto p-8">
            <div class="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- 中间主体 -->
                <div class="lg:col-span-2">
                    {main_card_html}
                    
                    <div class="mb-8">
                        <h3 class="text-xs font-black text-slate-500 tracking-[0.3em] mb-4">STRATEGY POINTS / 狙击点位</h3>
                        {strategy_html}
                    </div>

                    <div class="p-6 bg-slate-900/50 border border-white/5 rounded-2xl">
                        <h3 class="text-xs font-black text-blue-500 tracking-[0.3em] mb-4">NEWS FEED 相关资讯</h3>
                        <div class="space-y-4">
                            <div class="border-b border-white/5 pb-4">
                                <h4 class="text-sm font-bold text-slate-200 mb-1 hover:text-blue-400 cursor-pointer transition-colors">2026年中国石油行业市场现状及趋势分析</h4>
                                <p class="text-[10px] text-slate-500">石油石化行业竞争格局及中石油、中石化中长期表现预测...</p>
                            </div>
                            <div class="pb-4">
                                <h4 class="text-sm font-bold text-slate-200 mb-1 hover:text-blue-400 cursor-pointer transition-colors">【行业深度】洞察2026：中国石油石化行业竞争格局</h4>
                                <p class="text-[10px] text-slate-500">行业主要上市公司：中国石化(600028)、中国石油(601857)...</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 右侧看板 -->
                <div class="lg:col-span-1 space-y-8">
                    <div class="bg-slate-900/80 p-8 rounded-2xl border border-white/5 flex flex-col items-center">
                        <h3 class="text-xs font-black text-slate-500 mb-6 self-start">MARKET SENTIMENT</h3>
                        <div class="sentiment-circle">
                            <div class="text-center">
                                <div class="text-4xl font-black text-white">48</div>
                                <div class="text-[10px] text-blue-400">中性</div>
                            </div>
                        </div>
                        <p class="mt-6 text-[10px] text-slate-500 text-center">当前市场恐慌贪婪指数处于均衡状态，建议轻仓观望。</p>
                    </div>

                    <div class="bg-slate-900/80 p-6 rounded-2xl border border-white/5">
                        <h3 class="text-xs font-black text-emerald-500 mb-4 tracking-widest">操作建议: 观望</h3>
                        <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                            <div class="bg-emerald-500 h-full w-1/2"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_tpl)
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")
    print("🚀 Build v14 Dashboard Finished.")

if __name__ == "__main__":
    run()









