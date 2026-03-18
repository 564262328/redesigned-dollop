import os
from datetime import datetime

def generate_report(data_list, new_count, total_count, source_name, industry_data):
    # 1. 行业热力图 HTML
    industry_html = ""
    for ind in industry_data:
        industry_html += f"""
        <div class="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex justify-between items-center transition-transform hover:scale-105">
            <span class="text-xs font-bold">{ind.get('板块名称')}</span>
            <span class="text-sm font-black text-emerald-400">+{ind.get('涨跌幅')}%</span>
        </div>
        """

    # 2. 股票卡片 HTML
    cards_html = ""
    for s in data_list:
        is_up = "-" not in str(s.get('change', ''))
        color = "text-rose-500" if is_up else "text-green-500"
        border = "border-rose-500/20" if is_up else "border-green-500/20"
        total_mv = s.get('total_mv', 0)
        mv_display = f"{(float(total_mv)/1e8):.1f}亿" if total_mv else "--"
        search_terms = f"{s.get('stock_name')} {s.get('stock_code')}".lower()

        cards_html += f"""
        <div class="stock-card group p-6 bg-slate-900/50 border {border} rounded-3xl hover:border-blue-500/50 transition-all duration-300" data-search="{search_terms}">
            <div class="flex justify-between items-start mb-4">
                <div><div class="text-xl font-black text-white">{s.get('stock_name')}</div><div class="text-[10px] text-slate-500 font-mono">{s.get('stock_code')}</div></div>
                <div class="text-right"><div class="text-lg font-black {color} font-mono">{s.get('price')}</div><div class="text-[10px] {color} opacity-80 italic font-bold">{s.get('change')}%</div></div>
            </div>
            <div class="grid grid-cols-3 gap-y-2 gap-x-1 mb-4 text-[9px] text-slate-500 font-mono border-y border-white/5 py-3">
                <div>PE: <span class="text-white">{s.get('pe', '--')}</span></div>
                <div>PB: <span class="text-white">{s.get('pb', '--')}</span></div>
                <div>换手: <span class="text-white">{s.get('turnover', '--')}%</span></div>
                <div class="col-span-3">市值: <span class="text-blue-400 font-bold">{mv_display}</span></div>
            </div>
            <div class="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 mb-4 text-[10px] italic">
                <div class="text-[8px] text-indigo-400 font-black mb-1 uppercase">筹码分布</div>
                <div class="flex justify-between"><span>获利盘: <span class="text-rose-400 font-bold">{s.get('profit_ratio', '--')}</span></span><span>平均成本: <span class="text-white">{s.get('avg_cost', '--')}</span></span></div>
            </div>
            <div class="p-3 bg-slate-950/50 rounded-2xl border border-white/5 mb-4 min-h-[60px] text-[11px] text-slate-400 leading-relaxed italic">{s.get('insights')}</div>
            <div class="grid grid-cols-2 gap-3">
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5 text-center"><div class="text-[8px] text-slate-500 uppercase">狙击买入</div><div class="text-xs font-bold text-rose-500 font-mono">{s.get('buy_point')}</div></div>
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5 text-center"><div class="text-[8px] text-slate-500 uppercase">防御止损</div><div class="text-xs font-bold text-green-500 font-mono">{s.get('stop_loss')}</div></div>
            </div>
        </div>
        """

    source_color = "text-blue-400" if "EastMoney" in source_name else "text-orange-400"
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script><style>body {{ background: #020617; color: #f8fafc; font-family: ui-sans-serif; }}</style></head>
    <body class="p-6 md:p-12">
        <div class="max-w-7xl mx-auto">
            <header class="flex flex-col md:flex-row justify-between items-center border-b border-white/5 pb-10 mb-12 gap-6">
                <div><h1 class="text-4xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-rose-400">QUANT TERMINAL V14.8</h1></div>
                <div class="relative w-full md:w-96"><input type="text" id="stockSearch" placeholder="搜索名称或代码..." class="w-full bg-slate-900 border border-white/10 rounded-2xl px-5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-white transition-all"></div>
            </header>
            <div class="grid grid-cols-2 gap-8 mb-12 text-center">
                <div class="p-8 bg-blue-500/5 border border-blue-500/10 rounded-[2.5rem]"><div class="text-5xl font-black mb-1 italic text-blue-400">{total_count}</div><div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">全市场覆盖</div></div>
                <div class="p-8 bg-emerald-500/5 border border-emerald-500/10 rounded-[2.5rem]"><div class="text-5xl font-black text-emerald-400 mb-1 italic">+{new_count}</div><div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">今日探测新增</div></div>
            </div>
            <div class="mb-12"><div class="text-[10px] text-slate-500 font-bold uppercase tracking-[0.3em] mb-4 flex items-center gap-2"><span class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span> 行业板块热力图 (TOP 6)</div><div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">{industry_html}</div></div>
            <div id="cardGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">{cards_html}</div>
            <footer class="mt-20 border-t border-white/5 pt-10 flex flex-col md:flex-row justify-between items-center gap-6 text-[10px] text-slate-600 font-mono tracking-widest uppercase">
                <div class="flex items-center gap-4"><span>系统状态: <span class="text-green-500 animate-pulse">正常运行</span></span><span>数据源: <span class="{source_color} font-bold">{source_name}</span></span></div>
                <div>同步时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
            </footer>
        </div>
        <script>
            const searchInput = document.getElementById('stockSearch');
            const cards = document.querySelectorAll('.stock-card');
            searchInput.addEventListener('input', (e) => {{
                const term = e.target.value.toLowerCase().trim();
                cards.forEach(card => {{
                    const searchData = card.getAttribute('data-search');
                    card.style.display = searchData.includes(term) ? 'block' : 'none';
                }});
            }});
        </script>
    </body></html>
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(base_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f: f.write(full_html)











