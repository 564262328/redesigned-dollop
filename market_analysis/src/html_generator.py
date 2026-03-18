import os
from datetime import datetime

def generate_report(data_list, new_count, total_count, source_name, industry_data):
    # 1. 行业板块按钮生成
    industry_html = ""
    for ind in industry_data:
        name = ind.get('name')
        industry_html += f"""
        <button onclick="filterIndustry('{name}')" class="sector-btn p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex justify-between items-center transition-all hover:bg-emerald-500/20 active:scale-95 text-left">
            <span class="text-xs font-bold">{name}</span>
            <span class="text-sm font-black text-emerald-400">+{ind.get('change')}%</span>
        </button>
        """

    # 2. 个股卡片生成
    cards_html = ""
    for s in data_list:
        is_up = "-" not in str(s.get('change', ''))
        color = "text-rose-500" if is_up else "text-green-500"
        border = "border-rose-500/20" if is_up else "border-green-500/20"
        ind_tag = s.get('industry', '其他')
        search_terms = f"{s.get('stock_name')} {s.get('stock_code')}".lower()

        cards_html += f"""
        <div class="stock-card group p-6 bg-slate-900/50 border {border} rounded-3xl transition-all duration-300" data-search="{search_terms}" data-industry="{ind_tag}">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-xl font-black text-white group-hover:text-blue-400 transition-colors">{s.get('stock_name')}</div>
                    <div class="text-[10px] text-blue-400 font-bold uppercase tracking-widest">{ind_tag}</div>
                </div>
                <div class="text-right">
                    <div class="text-lg font-black {color} font-mono">{s.get('price')}</div>
                    <div class="text-[10px] {color} opacity-80 font-bold">{s.get('change')}%</div>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-2 mb-4 text-[9px] text-slate-500 font-mono border-y border-white/5 py-3">
                <div>换手: <span class="text-white">{s.get('turnover', '--')}%</span></div>
                <div>量比: <span class="text-white">{s.get('volume_ratio', '--')}</span></div>
            </div>

            <div class="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 mb-4 text-[10px] italic text-slate-300">
                <div class="flex justify-between">
                    <span>获利盘: <span class="text-rose-400 font-bold">{s.get('profit_ratio', '--')}</span></span>
                    <span>均价: <span class="text-white font-bold">{s.get('avg_cost', '--')}</span></span>
                </div>
            </div>
            
            <div class="p-3 bg-slate-950/50 rounded-2xl mb-4 min-h-[60px] text-[11px] text-slate-400 leading-relaxed italic">
                {s.get('insights')}
            </div>
            
            <div class="grid grid-cols-2 gap-3 text-center">
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5">
                    <div class="text-[8px] text-slate-500 uppercase">建议买入</div>
                    <div class="text-xs font-bold text-rose-500 font-mono">{s.get('buy_point')}</div>
                </div>
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5">
                    <div class="text-[8px] text-slate-500 uppercase">防御止损</div>
                    <div class="text-xs font-bold text-green-500 font-mono">{s.get('stop_loss')}</div>
                </div>
            </div>
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT TERMINAL V14.9</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: ui-sans-serif; }}
            .terminal-glow {{ text-shadow: 0 0 20px rgba(59, 130, 246, 0.4); }}
        </style>
    </head>
    <body class="p-6 md:p-12">
        <div class="max-w-7xl mx-auto">
            <header class="flex flex-col md:flex-row justify-between items-center border-b border-white/5 pb-10 mb-12 gap-6">
                <div>
                    <h1 class="text-4xl font-black italic tracking-tighter terminal-glow bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-rose-400">QUANT TERMINAL V14.9</h1>
                    <p class="text-[10px] text-slate-500 font-mono mt-1 uppercase">2026 AI-QUANT DATA SYSTEM</p>
                </div>
                <div class="relative w-full md:w-96">
                    <input type="text" id="stockSearch" placeholder="搜索个股或代码..." 
                        class="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all">
                </div>
            </header>

            <div class="mb-12">
                <div class="flex justify-between items-center mb-6 text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                    <div class="flex items-center gap-2">
                        <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                        强势行业热力 (点击过滤个股)
                    </div>
                    <button onclick="filterIndustry('all')" class="text-blue-400 hover:text-white transition-colors">显示全部股票</button>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    {industry_html}
                </div>
            </div>

            <div id="cardGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards_html}
            </div>

            <footer class="mt-20 border-t border-white/5 pt-10 flex flex-col md:flex-row justify-between items-center gap-6 text-[10px] text-slate-600 font-mono uppercase tracking-widest">
                <div class="flex items-center gap-6">
                    <span>系统状态: <span class="text-green-500">运行中</span></span>
                    <span>数据来源: <span class="text-blue-400">{source_name}</span></span>
                    <span>总覆盖: {total_count} | 新增: {new_count}</span>
                </div>
                <div>同步时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
            </footer>
        </div>

        <script>
            // 行业过滤逻辑
            function filterIndustry(name) {{
                const cards = document.querySelectorAll('.stock-card');
                cards.forEach(card => {{
                    if (name === 'all' || card.getAttribute('data-industry') === name) {{
                        card.style.display = 'block';
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
            }}

            // 搜索逻辑
            document.getElementById('stockSearch').addEventListener('input', (e) => {{
                const term = e.target.value.toLowerCase().trim();
                document.querySelectorAll('.stock-card').forEach(card => {{
                    const searchStr = card.getAttribute('data-search');
                    card.style.display = searchStr.includes(term) ? 'block' : 'none';
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(base_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)












