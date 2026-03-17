import os
import pandas as pd
import akshare as ak
from datetime import datetime
import re

# --- 1. 核心配置 ---
TARGET_STOCKS = ["上证指数", "沪深300", "创业板指", "宁德时代", "贵州茅台", "东方财富", "比亚迪", "工业富联"] 

def get_limit_data_with_details():
    """获取涨跌停排行，计算连板天数并标注所属行业"""
    try:
        df = ak.stock_zh_a_spot_em()
        df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
        df = df.dropna(subset=['涨跌幅'])
        
        # 获取涨停与跌停前十
        top_gainers = df.sort_values(by='涨跌幅', ascending=False).head(10)
        top_losers = df.sort_values(by='涨跌幅', ascending=True).head(10)
        
        def get_details(symbol, name):
            if name in ["上证指数", "沪深300", "创业板指"]: return "", ""
            try:
                # 1. 计算连板数
                hist = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").tail(6)
                hist['pct'] = hist['收盘'].pct_change() * 100
                count = 0
                for p in reversed(hist['pct'].tolist()):
                    if p >= 9.4: count += 1
                    else: break
                streak_html = f'<span class="ml-1 px-1 bg-red-600 text-white text-[8px] rounded-sm font-black animate-pulse leading-tight">{count}连板</span>' if count > 1 else ""
                
                # 2. 获取行业标签
                sector = df[df['代码'] == symbol]['板块'].values[0] if '板块' in df.columns else "未知"
                sector_html = f'<span class="ml-1 text-[8px] text-blue-400 font-bold border border-blue-900/50 px-1 rounded-sm tracking-tighter">#{sector}</span>'
                
                return streak_html, sector_html
            except: return "", ""

        def format_rows(sub_df, color_class, is_up=True):
            rows = []
            for _, row in sub_df.iterrows():
                streak, sector = get_details(row['代码'], row['名称']) if is_up else ("", "")
                rows.append(f"""
                <div class="flex justify-between items-center p-2 border-b border-white/5 hover:bg-white/5 transition-colors">
                    <div class="flex flex-col max-w-[70%]">
                        <div class="flex items-center flex-wrap gap-y-1">
                            <span class="text-[11px] text-slate-200 font-bold leading-none">{row['名称']}</span>
                            {streak}
                            {sector}
                        </div>
                        <span class="text-[8px] text-slate-600 font-mono mt-1">{row['代码']}</span>
                    </div>
                    <span class="text-[10px] font-black font-mono {color_class}">{row['涨跌幅']}%</span>
                </div>
                """)
            return "".join(rows)

        return format_rows(top_gainers, "text-red-500", True), format_rows(top_losers, "text-green-500", False)
    except:
        return '<p class="text-[10px] text-slate-600 text-center p-4 italic">数据解密中...</p>', ""

def analyze_logic(symbol, name, spot_df):
    try:
        if 'sh000' in symbol or 'sz399' in symbol:
            df = ak.stock_zh_index_daily(symbol=symbol).tail(30)
        else:
            df = ak.stock_zh_a_hist(symbol=symbol[2:], period="daily", adjust="qfq").tail(30)
        
        df.columns = ['date','open','close','high','low','volume','amount','outstanding'] if len(df.columns)==8 else df.columns
        df['close'] = pd.to_numeric(df['close'])
        last_p, prev_p = df['close'].iloc[-1], df['close'].iloc[-2]
        change_pct = (last_p - prev_p) / prev_p
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        bias = (last_p - ma20) / ma20
        buy_p, stop_p = round(ma20 * 0.99, 2), round(ma20 * 0.95, 2)
        trend_color = "text-red-500" if change_pct >= 0 else "text-green-500"

        return f"""
        <div class="bg-[#12151c] rounded-xl border border-white/5 p-4 hover:border-blue-500/30 transition-all group">
            <div class="flex justify-between items-start mb-2">
                <div><h3 class="text-sm font-black text-white leading-none mb-1 tracking-tight">{name}</h3><span class="text-[9px] font-mono text-slate-600 uppercase italic">{symbol}</span></div>
                <div class="text-right"><div class="text-lg font-black font-mono {trend_color}">¥{last_p}</div><div class="text-[10px] font-bold {trend_color}">{change_pct:.2%}</div></div>
            </div>
            <div class="grid grid-cols-2 gap-2 text-[9px] py-2 border-t border-white/5">
                <div class="flex flex-col"><span class="text-slate-600 font-bold mb-0.5 uppercase tracking-widest italic font-bold italic">Bias 20MA</span><span class="{trend_color} font-mono font-black">{bias:.2%}</span></div>
                <div class="flex flex-col text-right"><span class="text-slate-600 font-bold mb-0.5 uppercase italic tracking-widest font-bold italic">Buy Support</span><span class="text-amber-500 font-mono font-black font-bold italic">¥{buy_p}</span></div>
            </div>
        </div>
        """
    except: return ""

def run():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    spot_df = ak.stock_zh_a_spot_em()
    zt_html, dt_html = get_limit_data_with_details()
    
    up_market = len(spot_df[spot_df['涨跌幅'] > 0]) if not spot_df.empty else 1
    total_market = len(spot_df) if not spot_df.empty else 1
    sentiment_score = int((up_market / total_market) * 100)
    
    cards_html = "".join([analyze_logic(spot_df[spot_df['名称']==item].iloc[0]['代码'] if item not in ["上证指数","沪深300","创业板指"] else "sh000001", item, spot_df) for item in TARGET_STOCKS])

    html_tpl = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #080a0f; color: #f8fafc; font-family: ui-sans-serif, system-ui; }}
        .sidebar {{ width: 320px; background: #0c0e14; border-right: 1px solid rgba(255,255,255,0.05); }}
        .main-content {{ flex: 1; overflow-y: auto; }}
        ::-webkit-scrollbar {{ width: 2px; }}
        ::-webkit-scrollbar-thumb {{ background: #1e293b; }}
    </style>
</head>
<body class="h-screen flex overflow-hidden font-bold italic font-black uppercase tracking-tight">
    
    <aside class="sidebar hidden lg:flex flex-col">
        <div class="p-6 border-b border-white/5 bg-[#12151c]">
            <h1 class="text-blue-500 font-black italic tracking-tighter text-2xl uppercase italic font-bold">THE DRAGON V12.6</h1>
            <p class="text-[9px] text-slate-500 mt-1 uppercase tracking-[0.4em] font-black italic underline decoration-blue-500/30 font-bold italic">Theme Radar</p>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-8">
            <section>
                <h2 class="text-[10px] text-red-500 font-black uppercase mb-3 tracking-widest flex items-center gap-2 italic">
                    <span class="w-1.5 h-1.5 bg-red-600 rounded-full animate-ping"></span> 龙头基因 & 题材共振
                </h2>
                <div class="bg-black/40 rounded-xl overflow-hidden border border-red-500/10 shadow-2xl shadow-red-500/5">{zt_html}</div>
            </section>
            <section>
                <h2 class="text-[10px] text-green-500 font-black uppercase mb-3 tracking-widest flex items-center gap-2 italic">⚠️ 恐慌抛售清单 / CRASH</h2>
                <div class="bg-black/40 rounded-xl overflow-hidden border border-green-500/10 shadow-2xl shadow-green-500/5">{dt_html}</div>
            </section>
        </div>
        <div class="p-4 bg-slate-900/50 text-center border-t border-white/5 text-[9px] text-slate-600 font-bold uppercase italic tracking-widest">Market Sync: {now}</div>
    </aside>

    <main class="main-content flex flex-col">
        <header class="p-6 bg-[#0c0e14] border-b border-white/5 flex justify-between items-center">
            <div class="flex flex-col">
                <h2 class="text-2xl font-black text-white tracking-tighter italic">ALPHA COMMAND CENTER</h2>
                <div class="flex gap-4 mt-1 text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">
                    <span>UP: <b class="text-red-500">{up_market}</b></span>
                    <span>DOWN: <b class="text-green-500">{total_market - up_market}</b></span>
                </div>
            </div>
            <div class="flex items-center gap-8 bg-slate-900/40 p-3 rounded-2xl border border-white/5">
                <div class="text-right">
                    <p class="text-[9px] text-slate-500 font-black uppercase tracking-widest mb-1 italic">SENTIMENT</p>
                    <div class="h-1 w-24 bg-slate-800 rounded-full overflow-hidden flex">
                        <div class="h-full bg-red-600 shadow-[0_0_10px_red]" style="width: {sentiment_score}%"></div>
                    </div>
                </div>
                <span class="text-3xl font-black text-white font-mono italic tracking-tighter">{sentiment_score}</span>
            </div>
        </header>

        <div class="p-6 space-y-6">
            <div class="bg-gradient-to-br from-[#1e293b] to-[#0c0e14] rounded-3xl p-10 border border-white/10 shadow-2xl relative overflow-hidden">
                <div class="absolute top-0 right-0 p-12 opacity-[0.03] scale-150 transform rotate-12">
                    <svg width="200" height="200" fill="white" viewBox="0 0 24 24"><path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z""")/>></svg>
                </div>
                <div class="inline-block px-3 py-1 bg-blue-600 text-black text-[10px] font-black uppercase rounded-sm mb-4 italic tracking-widest">Theme Momentum Mode</div>
                <h2 class="text-4xl font-black text-white tracking-tighter mb-4 italic underline decoration-blue-600/30 underline-offset-8">题材龙头共振终端</h2>
                <p class="text-slate-400 text-sm leading-relaxed max-w-3xl font-medium italic border-l-4 border-blue-600 pl-8 uppercase tracking-widest font-bold italic">
                    系统已切换至「题材深度扫描」模式。左侧名单自动匹配标的所属之<span class="text-blue-400 font-black">行业板块</span>。若同一行业出现多只标的连板，则该题材具备参与价值。配合右侧个股的 MA20 支撑位，可有效筛选龙头股。
                </p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {cards_html}
            </div>
        </div>
    </main>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_tpl)
    with open(".nojekyll", "w") as f: f.write("")
    print(f"🚀 v12.6 Theme Radar Fixed: {now}")

if __name__ == "__main__":
    run()


