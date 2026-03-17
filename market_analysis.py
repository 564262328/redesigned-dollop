import os
import pandas as pd
import akshare as ak
from datetime import datetime
import re

# --- 1. 核心配置 ---
TARGET_STOCKS = ["上证指数", "沪深300", "创业板指", "宁德时代", "贵州茅台", "东方财富", "比亚迪", "工业富联"] 
BIAS_LIMIT = 0.05  

def get_market_snapshot():
    try:
        return ak.stock_zh_a_spot_em()
    except:
        return pd.DataFrame()

def get_full_code(name, spot_df):
    indices = {"上证指数": "sh000001", "沪深300": "sh000300", "创业板指": "sz399006"}
    if name in indices: 
        return indices[name], name, "指数", "-", "-", "-", 0, 0, 0
    try:
        if not spot_df.empty:
            match = spot_df[spot_df['名称'] == name]
            if not match.empty:
                row = match.iloc[0]
                code = row['代码']
                sector = row.get('板块', '其它')
                pe = row.get('动态市盈率', '-')
                turnover = row.get('换手率', '-')
                vol_ratio = row.get('量比', '-')
                high, low, current = row.get('最高', 0), row.get('最低', 0), row.get('最新价', 0)
                full_code = ('sh' + code) if code.startswith(('60', '68')) else ('sz' + code)
                return full_code, name, sector, pe, turnover, vol_ratio, high, low, current
    except: pass
    return "sh000001", name, "N/A", "-", "-", "-", 0, 0, 0

def analyze_logic(symbol, name, sector, pe, turnover, vol_ratio, high, low, current):
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
        ma5, ma10 = df['close'].rolling(5).mean().iloc[-1], df['close'].rolling(10).mean().iloc[-1]
        
        is_bull = ma5 > ma10 > ma20
        bias = (last_p - ma20) / ma20
        buy_p, stop_p = round(ma20 * 0.99, 2), round(ma20 * 0.95, 2)
        
        v_alert = False
        try:
            if str(vol_ratio) != '-' and float(vol_ratio) >= 2.0: v_alert = True
        except: pass

        range_pos = ((current - low) / (high - low) * 100) if high > low else 0
        trend_color = "text-red-500" if change_pct >= 0 else "text-green-500"

        card_html = f"""
        <div class="glass-card p-5 border-t-4 {"border-red-500 shadow-red-500/10" if is_bull else "border-green-500/30"} relative overflow-hidden">
            {"<div class='absolute top-0 right-0 bg-amber-500 text-black text-[8px] font-black px-2 py-0.5 animate-pulse uppercase tracking-tighter'>⚠️ 异动放量</div>" if v_alert else ""}
            <div class="flex justify-between items-start mb-2">
                <div>
                    <h3 class="text-xl font-black text-white leading-tight">{name}</h3>
                    <div class="flex items-center gap-2 mt-1">
                        <span class="text-[9px] px-1.5 py-0.5 bg-white/5 text-slate-400 border border-white/10 rounded font-bold">{sector}</span>
                        <span class="text-[9px] font-mono text-slate-600">{symbol}</span>
                    </div>
                </div>
                <div class="text-right">
                    <div class="{trend_color} font-black text-xl leading-none font-mono">{"▲" if change_pct >= 0 else "▼"} {change_pct:.2%}</div>
                </div>
            </div>
            <div class="mt-4 mb-2">
                <div class="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden relative">
                    <div class="h-full bg-gradient-to-r {"from-red-600 to-red-400" if change_pct >= 0 else "from-green-600 to-green-400"} rounded-full" style="width: {range_pos}%"></div>
                </div>
            </div>
            <div class="grid grid-cols-2 gap-y-3 py-4 border-y border-white/5 text-[11px]">
                <div class="flex flex-col"><span class="text-slate-500 font-bold uppercase italic">Bias 20MA</span><span class="font-mono font-bold {trend_color}">{bias:.2%}</span></div>
                <div class="flex flex-col text-right"><span class="text-slate-500 font-bold uppercase italic">量比 (Vol)</span><span class="font-mono {"text-amber-400 font-black" if v_alert else "text-slate-200"}">{vol_ratio}</span></div>
                <div class="flex flex-col"><span class="text-slate-500 font-bold uppercase italic">PE Ratio</span><span class="text-amber-500 font-mono font-bold">{pe}</span></div>
                <div class="flex flex-col text-right"><span class="text-slate-500 font-bold uppercase italic">换手率</span><span class="text-slate-200 font-mono">{turnover}%</span></div>
            </div>
            <div class="mt-4 flex justify-between items-center bg-white/5 p-2 rounded-lg border border-white/5">
                <div><span class="text-[9px] text-red-500 font-bold uppercase block">支撑位</span><span class="text-sm font-black text-red-400 font-mono italic">¥{buy_p}</span></div>
                <div class="text-right"><span class="text-[9px] text-green-500 font-bold uppercase block">止损位</span><span class="text-sm font-black text-green-400 font-mono italic">¥{stop_p}</span></div>
            </div>
        </div>
        """
        return card_html, is_bull, change_pct
    except Exception: return "", False, 0

def run():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    spot_df = get_market_snapshot()
    
    # --- 市场情绪指数计算 (Fear & Greed Index) ---
    up_count = len(spot_df[spot_df['涨跌幅'] > 0]) if not spot_df.empty else 1
    total_count = len(spot_df) if not spot_df.empty else 1
    breadth_score = (up_count / total_count) * 100
    
    cards_html = ""
    bull_count = 0
    for item in TARGET_STOCKS:
        res = analyze_logic(*get_full_code(item, spot_df))
        cards_html += res[0]
        if res[1]: bull_count += 1
    
    bull_ratio = (bull_count / len(TARGET_STOCKS)) * 100
    fear_greed_index = int((breadth_score * 0.6) + (bull_ratio * 0.4))
    
    # 情绪文案
    sentiment_text = "极度恐惧" if fear_greed_index < 20 else "恐惧" if fear_greed_index < 45 else "中性" if fear_greed_index < 55 else "贪婪" if fear_greed_index < 80 else "极度贪婪"
    sentiment_color = "text-green-500" if fear_greed_index < 45 else "text-slate-400" if fear_greed_index < 55 else "text-red-500"

    html_tpl = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #020617; background-image: radial-gradient(circle at 50% -20%, #1e293b 0%, #020617 80%); min-height: 100vh; color: #f8fafc; font-family: ui-sans-serif, system-ui; }}
        .glass-card {{ background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); border-radius: 20px; }}
    </style>
</head>
<body class="p-4 md:p-12">
    <div class="max-w-6xl mx-auto">
        <header class="flex justify-between items-center mb-10 pb-8 border-b border-white/5">
            <div>
                <h1 class="text-4xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-500 uppercase">Quant Terminal V9.0</h1>
                <p class="text-slate-500 text-[10px] uppercase tracking-[0.5em] font-black mt-2 italic">Institutional Grade Market Intelligence</p>
            </div>
            <div class="text-right text-xs font-mono text-slate-500 uppercase">Data Sync: {now}</div>
        </header>

        <!-- Fear & Greed Meter -->
        <div class="mb-10 p-8 glass-card flex flex-col md:flex-row items-center justify-between gap-8 border-b-4 border-blue-500/30">
            <div class="text-center md:text-left">
                <h2 class="text-xs font-black text-slate-500 uppercase tracking-[0.3em] mb-2 font-bold">恐惧与贪婪指数 / Fear & Greed Index</h2>
                <div class="text-5xl font-black {sentiment_color} tracking-tighter font-bold">{fear_greed_index} <span class="text-xl uppercase font-bold tracking-normal">{sentiment_text}</span></div>
            </div>
            <div class="flex-1 w-full max-w-md">
                <div class="flex justify-between text-[10px] text-slate-500 font-bold mb-2 uppercase font-bold italic">
                    <span>恐惧 (0)</span><span>中性 (50)</span><span>贪婪 (100)</span>
                </div>
                <div class="h-4 w-full bg-slate-900 rounded-full overflow-hidden flex p-1 border border-white/5 font-bold">
                    <div class="h-full rounded-full transition-all duration-1000 shadow-[0_0_20px_rgba(239,68,68,0.5)] bg-gradient-to-r from-green-500 via-yellow-500 to-red-500" style="width: {fear_greed_index}%"></div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {cards_html}
        </div>

        <!-- Intelligence Analysis Info -->
        <div class="mt-16 p-8 glass-card border border-blue-500/20 bg-blue-500/5">
            <h2 class="text-xs font-black text-blue-400 uppercase tracking-widest mb-4 flex items-center gap-2">● 智能分析准确性与算法说明</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 text-[10px] text-slate-400 leading-relaxed uppercase font-bold italic">
                <div class="space-y-2">
                    <p><span class="text-slate-200 font-bold">● 情绪对冲算法:</span> 综合「全场上涨家数比(60%)」与「核心标的多头比例(40%)」得出情绪值。20以下代表极度超卖，80以上代表超买风险。</p>
                    <p><span class="text-slate-200 font-bold">● 数据来源:</span> 实时接入 AkShare 工业级金融接口，原始数据源自东方财富(EM)及新浪财经。确保了量化指标的权威性与一致性。</p>
                </div>
                <div class="space-y-2">
                    <p><span class="text-slate-200 font-bold">● 动态风控逻辑:</span> 支撑位(Buy Support)基于 MA20 均线 -1% 浮动计算，止损位(Stop Loss)基于 -5% 极值计算，符合机构级趋势追踪逻辑。</p>
                </div>
            </div>
        </div>

        <footer class="mt-20 py-10 text-center border-t border-white/5 text-slate-700 text-[10px] font-black uppercase tracking-[0.4em]">Algo V9.0 • Market Psychology Hub • Investment is Risk</footer>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_tpl)
    with open(".nojekyll", "w") as f: f.write("")
    print(f"✅ V9.0 Dashboard with Fear & Greed Index generated: {now}")

if __name__ == "__main__":
    run()


