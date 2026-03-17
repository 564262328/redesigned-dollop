import os
import sys
import pandas as pd
import akshare as ak
from datetime import datetime
import re

# --- 1. CORE CONFIG ---
TARGET_STOCKS = ["上证指数", "沪深300", "创业板指", "宁德时代", "贵州茅台"] 
BIAS_LIMIT = 0.05  

def get_full_code(name):
    """Accurate Code Mapping"""
    indices = {"上证指数": "sh000001", "沪深300": "sh000300", "创业板指": "sz399006"}
    if name in indices: return indices[name], name
    try:
        df = ak.stock_zh_a_spot_em()
        match = df[df['名称'] == name]
        if not match.empty:
            code = match.iloc[0]['代码']
            full_code = ('sh' + code) if code.startswith(('60', '68')) else ('sz' + code)
            return full_code, name
    except: pass
    return "sh000001", "上证指数"

def analyze_logic(symbol, name):
    """Returns a Card-styled HTML fragment"""
    try:
        if 'sh000' in symbol or 'sz399' in symbol:
            df = ak.stock_zh_index_daily(symbol=symbol).tail(30)
        else:
            df = ak.stock_zh_a_hist(symbol=symbol[2:], period="daily", adjust="qfq").tail(30)
        
        df.columns = ['date','open','close','high','low','volume','amount','outstanding'] if len(df.columns)==8 else df.columns
        df['close'] = pd.to_numeric(df['close'])
        
        # Calculations
        last_p = df['close'].iloc[-1]
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma5, ma10 = df['close'].rolling(5).mean().iloc[-1], df['close'].rolling(10).mean().iloc[-1]
        
        is_bull = ma5 > ma10 > ma20
        bias = (last_p - ma20) / ma20
        buy_p, stop_p = round(ma20 * 0.99, 2), round(ma20 * 0.95, 2)
        
        # Dynamic Colors & Icons
        border_color = "border-emerald-500" if is_bull else "border-slate-600"
        bias_color = "text-red-400" if bias > 0 else "text-green-400"
        status_tag = "🚀 进攻" if is_bull and abs(bias) < BIAS_LIMIT else "🛡️ 防御"
        status_bg = "bg-emerald-900/40 text-emerald-400" if is_bull else "bg-slate-800 text-slate-400"

        return f"""
        <div class="glass-card p-5 border-l-4 {border_color} hover:scale-[1.02] transition-transform flex flex-col justify-between">
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="text-lg font-bold text-white tracking-tight">{name}</h3>
                    <span class="text-[10px] font-mono text-slate-500 uppercase tracking-widest">{symbol}</span>
                </div>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase {status_bg}">{status_tag}</span>
            </div>
            
            <div class="grid grid-cols-2 gap-2 mt-6">
                <div class="flex flex-col">
                    <span class="text-[10px] text-slate-500 uppercase">乖离风险</span>
                    <span class="text-sm font-bold font-mono {bias_color}">{bias:.2%}</span>
                </div>
                <div class="flex flex-col text-right">
                    <span class="text-[10px] text-slate-500 uppercase">技术状态</span>
                    <span class="text-sm font-medium text-slate-300">{'多头 ✅' if is_bull else '整理 ⚪'}</span>
                </div>
            </div>

            <div class="mt-4 pt-4 border-t border-white/5 flex justify-between items-center">
                <div class="flex flex-col">
                    <span class="text-[9px] text-slate-600 uppercase italic">建议买入</span>
                    <span class="text-xs font-bold text-amber-400 font-mono italic">¥{buy_p}</span>
                </div>
                <div class="flex flex-col text-right">
                    <span class="text-[9px] text-slate-600 uppercase italic">止损退出</span>
                    <span class="text-xs font-bold text-slate-400 font-mono italic">¥{stop_p}</span>
                </div>
            </div>
        </div>
        """
    except Exception as e:
        return f"<div class='glass-card p-5 border-l-4 border-red-500 text-xs text-red-400'>Error loading {name}: {str(e)}</div>"

def run():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    cards_html = ""
    
    for item in TARGET_STOCKS:
        code, name = get_full_code(item)
        cards_html += analyze_logic(code, name)
    
    html_tpl = f"""
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: radial-gradient(circle at top, #1e293b 0%, #080c14 100%); min-height: 100vh; color: #e2e8f0; font-family: ui-sans-serif, system-ui; }}
        .glass-card {{ background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; }}
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-5xl mx-auto">
        <header class="flex justify-between items-end mb-10 border-b border-white/10 pb-6">
            <div>
                <h1 class="text-3xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-emerald-400 to-emerald-600">QUANT TERMINAL</h1>
                <p class="text-slate-500 text-[10px] uppercase tracking-[0.3em] mt-1 font-bold">A-Share Industrial Logic v8.0</p>
            </div>
            <div class="text-right">
                <p class="text-slate-600 text-[9px] uppercase font-bold tracking-widest mb-1 italic text-red-500/80 underline-offset-4 underline decoration-red-500/30">Live Data Sync</p>
                <span class="text-xs font-mono text-slate-400 bg-slate-900/80 px-3 py-1 rounded-md border border-white/5">🕒 {now}</span>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cards_html}
        </div>

        <footer class="mt-16 text-center border-t border-white/5 pt-8">
            <p class="text-slate-700 text-[10px] tracking-[0.5em] uppercase font-medium">Algorithmic Risk Management • No Investment Advice</p>
        </footer>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_tpl)
    with open(".nojekyll", "w") as f: f.write("")
    print(f"✅ Dashboard generated successfully at {now}")

if __name__ == "__main__":
    run()



