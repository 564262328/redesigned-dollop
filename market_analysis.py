import os
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import re

# --- 1. 核心配置 ---
TARGET_STOCKS = ["上证指数", "沪深300", "创业板指", "宁德时代", "贵州茅台", "东方财富", "比亚迪", "工业富联"] 

def get_limit_data_with_details(spot_df):
    """获取涨跌停排行，带重试逻辑"""
    if spot_df.empty:
        return '<p class="text-[10px] text-slate-600 text-center p-4">数据接口连接超时</p>', ""
    try:
        df = spot_df.copy()
        df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
        df = df.dropna(subset=['涨跌幅'])
        
        top_gainers = df.sort_values(by='涨跌幅', ascending=False).head(10)
        top_losers = df.sort_values(by='涨跌幅', ascending=True).head(10)
        
        def format_rows(sub_df, color_class):
            rows = []
            for _, row in sub_df.iterrows():
                rows.append(f"""
                <div class="flex justify-between items-center p-2 border-b border-white/5 hover:bg-white/5 transition-colors">
                    <div class="flex flex-col max-w-[70%]">
                        <span class="text-[11px] text-slate-200 font-bold leading-none">{row['名称']}</span>
                        <span class="text-[8px] text-slate-600 font-mono mt-1">{row['代码']}</span>
                    </div>
                    <span class="text-[10px] font-black font-mono {color_class}">{row['涨跌幅']}%</span>
                </div>
                """)
            return "".join(rows)

        return format_rows(top_gainers, "text-red-500"), format_rows(top_losers, "text-green-500")
    except:
        return "数据处理异常", ""

def analyze_logic(symbol, name):
    """个股逻辑：带错误捕获，失败时不中断程序"""
    try:
        # 增加延迟防止被封
        time.sleep(1)
        if 'sh000' in symbol or 'sz399' in symbol:
            df = ak.stock_zh_index_daily(symbol=symbol).tail(30)
        else:
            df = ak.stock_zh_a_hist(symbol=symbol[2:], period="daily", adjust="qfq").tail(30)
        
        df.columns = ['date','open','close','high','low','volume','amount','outstanding'] if len(df.columns)==8 else df.columns
        df['close'] = pd.to_numeric(df['close'])
        last_p = df['close'].iloc[-1]
        prev_p = df['close'].iloc[-2]
        change_pct = (last_p - prev_p) / prev_p
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        bias = (last_p - ma20) / ma20
        buy_p, stop_p = round(ma20 * 0.99, 2), round(ma20 * 0.95, 2)
        trend_color = "text-red-500" if change_pct >= 0 else "text-green-500"

        return f"""
        <div class="bg-[#12151c] rounded-xl border border-white/5 p-4 hover:border-blue-500/30 transition-all font-black uppercase">
            <div class="flex justify-between items-start mb-2 font-black uppercase">
                <div><h3 class="text-sm font-black text-white leading-none mb-1 tracking-tight font-black uppercase">{name}</h3><span class="text-[9px] font-mono text-slate-600 uppercase font-black uppercase">{symbol}</span></div>
                <div class="text-right font-black uppercase"><div class="text-lg font-black font-mono {trend_color} font-black uppercase">¥{last_p}</div><div class="text-[10px] font-bold {trend_color} font-black uppercase">{change_pct:.2%}</div></div>
            </div>
            <div class="grid grid-cols-2 gap-2 text-[9px] py-2 border-t border-white/5 font-black uppercase">
                <div class="flex flex-col font-black uppercase"><span class="text-slate-600 font-bold mb-0.5 uppercase italic font-black">Bias 20MA</span><span class="{trend_color} font-mono font-black font-black uppercase">{bias:.2%}</span></div>
                <div class="flex flex-col text-right font-black uppercase"><span class="text-slate-600 font-bold mb-0.5 uppercase italic font-black">Support</span><span class="text-amber-500 font-mono font-black font-black uppercase">¥{buy_p}</span></div>
            </div>
        </div>
        """
    except:
        return f'<div class="bg-[#12151c] p-4 rounded-xl text-slate-600 text-xs italic">数据包获取异常: {name}</div>'

def run():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 尝试获取全市场快照，带3次重试
    spot_df = pd.DataFrame()
    for _ in range(3):
        try:
            spot_df = ak.stock_zh_a_spot_em()
            if not spot_df.empty: break
        except:
            time.sleep(5)
    
    zt_html, dt_html = get_limit_data_with_details(spot_df)
    
    # 情绪计算降级处理
    if not spot_df.empty:
        up_market = len(spot_df[spot_df['涨跌幅'] > 0])
        total_market = len(spot_df)
        sentiment_score = int((up_market / total_market) * 100)
    else:
        up_market, total_market, sentiment_score = "N/A", "N/A", 50

    # 生成核心卡片
    cards_html = ""
    stock_map = {"上证指数":"sh000001", "沪深300":"sh000300", "创业板指":"sz399006", 
                 "宁德时代":"sz300750", "贵州茅台":"sh600519", "东方财富":"sz300059", 
                 "比亚迪":"sz002594", "工业富联":"sh601138"}
    
    for name, code in stock_map.items():
        cards_html += analyze_logic(code, name)

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
    <aside class="sidebar hidden lg:flex flex-col font-black uppercase">
        <div class="p-6 border-b border-white/5 bg-[#12151c]">
            <h1 class="text-blue-500 font-black italic tracking-tighter text-2xl uppercase">THE DRAGON V12.8</h1>
            <p class="text-[9px] text-slate-500 mt-1 uppercase tracking-[0.4em] font-black underline decoration-blue-500/30">Stable Release</p>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-8 font-black uppercase">
            <section>
                <h2 class="text-[10px] text-red-500 font-black uppercase mb-3 tracking-widest italic font-black">今日涨幅前十 / LIMIT UP</h2>
                <div class="bg-black/40 rounded-xl overflow-hidden border border-red-500/10 shadow-2xl">{zt_html}</div>
            </section>
            <section>
                <h2 class="text-[10px] text-green-500 font-black uppercase mb-3 tracking-widest italic font-black">今日跌幅前十 / CRASH</h2>
                <div class="bg-black/40 rounded-xl overflow-hidden border border-green-500/10 shadow-2xl">{dt_html}</div>
            </section>
        </div>
        <div class="p-4 bg-slate-900/50 text-center border-t border-white/5 text-[9px] text-slate-600 font-bold uppercase italic">Sync: {now}</div>
    </aside>

    <main class="main-content flex flex-col font-black uppercase">
        <header class="p-6 bg-[#0c0e14] border-b border-white/5 flex justify-between items-center">
            <div class="flex flex-col">
                <h2 class="text-2xl font-black text-white tracking-tighter italic">QUANT COMMAND CENTER</h2>
                <div class="flex gap-4 mt-1 text-[10px] font-bold text-slate-500 uppercase">
                    <span>UP: <b class="text-red-500">{up_market}</b></span>
                    <span>SENTIMENT: <b class="text-purple-400">{sentiment_score}</b></span>
                </div>
            </div>
            <div class="bg-slate-900/40 p-3 rounded-2xl border border-white/5">
                <span class="text-3xl font-black text-white font-mono italic tracking-tighter">{sentiment_score}</span>
            </div>
        </header>

        <div class="p-6 space-y-6 font-black uppercase">
            <div class="bg-gradient-to-br from-[#1e293b] to-[#0c0e14] rounded-3xl p-10 border border-white/10 shadow-2xl relative overflow-hidden">
                <div class="absolute top-0 right-0 p-12 opacity-[0.03] scale-150 transform rotate-12 font-black uppercase">
                    <svg width="200" height="200" fill="white" viewBox="0 0 24 24"><path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z"></path></svg>
                </div>
                <div class="inline-block px-3 py-1 bg-blue-600 text-black text-[10px] font-black uppercase rounded-sm mb-4 tracking-widest">Stability Mode</div>
                <h2 class="text-4xl font-black text-white tracking-tighter mb-4 italic underline decoration-blue-600/30 underline-offset-8">题材龙头共振终端</h2>
                <p class="text-slate-400 text-sm leading-relaxed max-w-3xl font-medium italic border-l-4 border-blue-600 pl-8 font-black uppercase">
                    数据连接已优化。系统采用自动重试逻辑以应对网络抖动。当前市场情绪为 {sentiment_score}，请重点关注下方量化支点。
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
    print(f"🚀 v12.8 Stable Deployed: {now}")

if __name__ == "__main__":
    run()


