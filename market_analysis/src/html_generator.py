import os
from datetime import datetime

def generate_report(data_list, new_count, total_count):
    cards_html = ""
    for s in data_list:
        is_up = "-" not in str(s.get('change', ''))
        color = "text-rose-500" if is_up else "text-emerald-500"
        border = "border-rose-500/20" if is_up else "border-emerald-500/20"
        search_terms = f"{s.get('stock_name')} {s.get('stock_code')}".lower()
        
        # Calculation for Billion Display
        total_mv = s.get('total_mv', 0)
        mv_display = f"{(float(total_mv)/1e8):.1f}亿" if total_mv else "--"

        cards_html += f"""
        <div class="stock-card group p-6 bg-slate-900/50 border {border} rounded-3xl hover:border-blue-500/50 transition-all duration-300" data-search="{search_terms}">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-xl font-black text-white group-hover:text-blue-400 transition-colors">{s.get('stock_name')}</div>
                    <div class="text-[10px] text-slate-500 font-mono tracking-tighter">{s.get('stock_code')}</div>
                </div>
                <div class="text-right">
                    <div class="text-lg font-black {color} font-mono leading-none">{s.get('price')}</div>
                    <div class="text-[10px] {color} opacity-80 italic font-bold">{s.get('change')}%</div>
                </div>
            </div>

            <!-- Market Metrics Grid -->
            <div class="grid grid-cols-3 gap-y-2 gap-x-1 mb-4 text-[9px] text-slate-500 font-mono border-y border-white/5 py-3">
                <div>PE: <span class="text-white">{s.get('pe', '--')}</span></div>
                <div>PB: <span class="text-white">{s.get('pb', '--')}</span></div>
                <div>换手: <span class="text-white">{s.get('turnover', '--')}%</span></div>
                <div>量比: <span class="text-white">{s.get('volume_ratio', '--')}</span></div>
                <div class="col-span-2">市值: <span class="text-blue-400 font-bold">{mv_display}</span></div>
            </div>

            <!-- Chip Distribution Card -->
            <div class="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 mb-4">
                <div class="text-[8px] text-indigo-400 font-black mb-2 tracking-widest uppercase italic">筹码分布 · Data Insight</div>
                <div class="grid grid-cols-2 gap-2 text-[10px] italic">
                    <div class="text-slate-400">获利比例: <span class="text-rose-400 font-bold">{s.get('profit_ratio', '--')}</span></div>
                    <div class="text-slate-400">平均成本: <span class="text-white">{s.get('avg_cost', '--')}</span></div>
                    <div class="text-slate-400 col-span-2">90%集中度: <span class="text-indigo-300 font-bold">{s.get('concentration_90', '--')}</span></div>
                </div>
            </div>
            
            <div class="p-3 bg-slate-950/50 rounded-2xl border border-white/5 mb-4 min-h-[60px]">
                <p class="text-[11px] leading-relaxed text-slate-400 italic">
                    {s.get('insights', 'AI 终端正在处理大数据分析内容...')}
                </p>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5">
                    <div class="text-[8px] text-slate-500 mb-0.5 italic">狙击买入位</div>
                    <div class="text-xs font-bold text-rose-500 font-mono">{s.get('buy_point', '--')}</div>
                </div>
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5">
                    <div class="text-[8px] text-slate-500 mb-0.5 italic">防御止损位</div>
                    <div class="text-xs font-bold text-emerald-500 font-mono">{s.get('stop_loss', '--')}</div>
                </div>
            </div>
        </div>
        """

    cur_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: ui-sans-serif; }}
            .terminal-glow {{ text-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }}
        </style>
    </head>
    <body class="p-6 md:p-12">
        <div class="max-w-7xl mx-auto">
            <header class="flex flex-col md:flex-row justify-between items-center border-b border-white/5 pb-10 mb-12 gap-6">
                <div>
                    <h1 class="text-4xl font-black italic tracking-tighter terminal-glow bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-rose-400">QUANT TERMINAL</h1>
                    <p class="text-[10px] text-slate-500 font-mono mt-1 uppercase tracking-[0.2em]">Data Sync: {cur_time}</p>
                </div>
                <div class="relative w-full md:w-96">
                    <input type="text" id="stockSearch" placeholder="搜索名称或代码..." 
                        class="w-full bg-slate-900 border border-white/10 rounded-2xl px-5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-white transition-all">
                </div>
            </header>

            <div class="grid grid-cols-2 gap-8 mb-12">
                <div class="p-8 bg-blue-500/5 border border-blue-500/10 rounded-[2.5rem] text-center shadow-2xl">
                    <div class="text-5xl font-black mb-1 italic tracking-tighter text-blue-400">{total_count}</div>
                    <div class="text-[10px] text-slate-500 font-bold uppercase tracking-widest">全市场覆盖指标</div>
                </div>
                <div class="p-8 bg-emerald-500/5 border border-emerald-500/10 rounded-[2.5rem] text-center shadow-2xl">
                    <div class="text-5xl font-black text-emerald-400 mb-1 italic tracking-tighter">+{new_count}</div>
                    <div class="text-[10px] text-slate-500 font-bold uppercase tracking-widest">今日探测新代码</div>
                </div>
            </div>

            <div id="cardGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards_html}
            </div>
            <div id="noResults" class="hidden text-center py-20 text-slate-600 italic font-black uppercase">No Matching Data Found</div>
        </div>

        <script>
            const searchInput = document.getElementById('stockSearch');
            const cards = document.querySelectorAll('.stock-card');
            const noResults = document.getElementById('noResults');

            searchInput.addEventListener('input', (e) => {{
                const term = e.target.value.toLowerCase().trim();
                let found = false;
                cards.forEach(card => {{
                    const searchData = card.getAttribute('data-search');
                    if (searchData.includes(term)) {{
                        card.style.display = 'block';
                        found = true;
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
                noResults.style.display = found ? 'none' : 'block';
            }});
        </script>
    </body>
    </html>
    """
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(base_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"✅ 看板已更新: {output_path}")










