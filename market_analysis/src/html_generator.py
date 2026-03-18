import os
from datetime import datetime

def generate_report(data_list, new_count, total_count, source_name, industry_data, index_data):
    # 1. 頂部指數橫欄
    index_html = ""
    for idx in index_data:
        val = str(idx.get('change', '0'))
        color = "text-rose-500" if "-" not in val else "text-emerald-500"
        index_html += f"""
        <div class="flex flex-col border-r border-white/5 last:border-0 px-8 min-w-[160px]">
            <span class="text-[10px] text-slate-500 font-black mb-1 tracking-widest">{idx['name']}</span>
            <div class="flex items-baseline gap-2">
                <span class="text-lg font-black font-mono tracking-tighter">{idx['price']}</span>
                <span class="text-xs font-bold {color}">{val}%</span>
            </div>
        </div>
        """

    # 2. 行業按鈕
    industry_html = "".join([f"""
        <button onclick="filterIndustry('{i['name']}')" class="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex justify-between items-center hover:bg-emerald-500/20 transition-all">
            <span class="text-xs font-bold">{i['name']}</span>
            <span class="text-sm font-black text-emerald-400">+{i['change']}%</span>
        </button>""" for i in industry_data])

    # 3. 個股卡片
    cards_html = ""
    for s in data_list:
        is_up = "-" not in str(s.get('change', ''))
        color = "text-rose-500" if is_up else "text-emerald-500"
        border = "border-rose-500/20" if is_up else "border-emerald-500/20"
        cards_html += f"""
        <div class="stock-card group p-6 bg-slate-900/40 backdrop-blur-xl border {border} rounded-[2rem] transition-all duration-500 hover:shadow-[0_0_30px_rgba(59,130,246,0.1)]" data-industry="{s.get('industry','其他')}">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-xl font-black text-white">{s.get('stock_name')} <span class="text-[10px] text-slate-500 italic">({s.get('stock_code')})</span></div>
                    <div class="mt-2 inline-block px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-[8px] font-bold">所屬: {s.get('industry')}</div>
                </div>
                <div class="text-right">
                    <div class="text-2xl font-black {color} font-mono leading-none">{s.get('price')}</div>
                    <div class="text-[10px] {color} font-bold mt-1">{s.get('change')}%</div>
                </div>
            </div>
            <div class="grid grid-cols-2 gap-2 mb-4 text-[9px] text-slate-500 font-mono border-y border-white/5 py-3">
                <div>換手: <span class="text-white">{s.get('turnover', '--')}%</span></div>
                <div>量比: <span class="text-white">{s.get('volume_ratio', '--')}</span></div>
            </div>
            <div class="p-3 bg-indigo-500/10 rounded-xl mb-4 text-[10px] italic text-slate-300">
                <div class="flex justify-between"><span>獲利盤: <span class="text-rose-400 font-bold">{s.get('profit_ratio', '--')}</span></span><span>均價: <span class="text-white">{s.get('avg_cost', '--')}</span></span></div>
            </div>
            <div class="p-4 bg-black/40 rounded-2xl mb-4 min-h-[80px] text-[11px] text-slate-400 leading-relaxed italic">{s.get('insights')}</div>
            <div class="grid grid-cols-2 gap-3 text-center">
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5 text-[8px] text-slate-500">建議買入<div class="text-sm font-black text-rose-500">{s.get('buy_point')}</div></div>
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5 text-[8px] text-slate-500">建議防禦<div class="text-sm font-black text-emerald-500">{s.get('stop_loss')}</div></div>
            </div>
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script>
    <style>body {{ background: radial-gradient(circle at 50% 0%, #1a1c2e 0%, #020617 100%); color: #f8fafc; font-family: system-ui; }}</style></head>
    <body class="p-6 md:p-12 min-h-screen">
        <div class="max-w-7xl mx-auto">
            <header class="flex justify-between items-center border-b border-white/5 pb-10 mb-8">
                <div><h1 class="text-3xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-500">QUANT 終端 V15.2</h1><p class="text-[10px] text-blue-500 font-mono tracking-widest uppercase">AI-Driven Multi-Asset Terminal</p></div>
                <div class="text-right"><div class="text-5xl font-black italic">{total_count}</div><div class="text-[9px] text-slate-500 font-bold tracking-widest uppercase">全市場監控量</div></div>
            </header>
            
            <!-- 指數橫欄 -->
            <div class="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-3xl p-6 flex overflow-x-auto no-scrollbar mb-12 shadow-2xl">
                {index_html}
            </div>

            <div class="mb-12">
                <div class="flex justify-between items-center mb-6 text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                    <span><span class="w-2 h-2 bg-emerald-500 inline-block rounded-full animate-pulse mr-2"></span> 行業熱力 (點擊過濾)</span>
                    <button onclick="filterIndustry('all')" class="text-blue-400">重置過濾</button>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">{industry_html}</div>
            </div>

            <div id="cardGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">{cards_html}</div>
            
            <footer class="mt-20 border-t border-white/5 pt-10 flex justify-between text-[10px] text-slate-600 font-mono">
                <div>數據源: <span class="text-blue-400 font-bold">{source_name}</span> | 今日新增: {new_count}</div>
                <div>最後同步: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
            </footer>
        </div>
        <script>
            function filterIndustry(name) {{
                document.querySelectorAll('.stock-card').forEach(c => {{
                    c.style.display = (name === 'all' || c.getAttribute('data-industry') === name) ? 'block' : 'none';
                }});
            }}
        </script>
    </body></html>
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(base_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f: f.write(full_html)















