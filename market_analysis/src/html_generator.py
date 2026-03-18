import os
from datetime import datetime

def generate_report(data_list, new_count, total_count):
    # 生成股票卡片 HTML 字符串
    cards_html = ""
    for s in data_list:
        change_val = str(s.get('change', '0'))
        is_up = "-" not in change_val and change_val != "0"
        color = "text-rose-500" if is_up else "text-emerald-500"
        border = "border-rose-500/20" if is_up else "border-emerald-500/20"
        
        # 搜索标签
        search_tags = f"{s.get('stock_name')} {s.get('stock_code')}".lower()
        
        cards_html += f"""
        <div class="stock-card group p-6 bg-slate-900/40 border {border} rounded-3xl hover:border-blue-500/50 transition-all duration-500 hover:shadow-[0_0_30px_rgba(59,130,246,0.1)]" data-search="{search_tags}">
            <div class="flex justify-between items-start mb-6">
                <div>
                    <div class="text-xl font-black tracking-tighter text-white group-hover:text-blue-400 transition-colors">{s.get('stock_name')}</div>
                    <div class="text-[10px] text-slate-500 font-mono tracking-widest">{s.get('stock_code')}</div>
                </div>
                <div class="text-right">
                    <div class="text-xl font-black {color} font-mono leading-none">{s.get('price')}</div>
                    <div class="text-[10px] {color} opacity-80 italic font-bold mt-1">{s.get('change')}%</div>
                </div>
            </div>
            
            <div class="p-4 bg-slate-950/60 rounded-2xl border border-white/5 mb-6 min-h-[80px]">
                <div class="text-[8px] text-blue-500/50 font-black mb-2 tracking-[0.2em]">AI 核心观点</div>
                <p class="text-[11px] leading-relaxed text-slate-400 italic">
                    {s.get('insights', 'AI 终端正在深度解析大数据内容...')}
                </p>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-slate-950/80 p-3 rounded-xl border border-white/5 group-hover:border-blue-500/20 transition-colors">
                    <div class="text-[8px] text-slate-500 mb-1 font-bold italic">狙击买入位</div>
                    <div class="text-sm font-black text-rose-500 font-mono tracking-tighter">{s.get('buy_point', '--')}</div>
                </div>
                <div class="bg-slate-950/80 p-3 rounded-xl border border-white/5 group-hover:border-blue-500/20 transition-colors">
                    <div class="text-[8px] text-slate-500 mb-1 font-bold italic">防御止损位</div>
                    <div class="text-sm font-black text-emerald-500 font-mono tracking-tighter">{s.get('stop_loss', '--')}</div>
                </div>
            </div>
        </div>
        """

    cur_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 核心：所有 CSS/JS 的大括号必须写成 {{ }} 避免语法错误
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT TERMINAL V14.6</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #020617 100%); color: #f8fafc; font-family: ui-sans-serif; }}
            .glass {{ background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); }}
        </style>
    </head>
    <body class="p-6 md:p-12 min-h-screen">
        <div class="max-w-7xl mx-auto">
            <nav class="flex flex-col md:flex-row justify-between items-center mb-16 gap-8 border-b border-white/5 pb-10">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 bg-blue-600 rounded-2xl rotate-12 flex items-center justify-center shadow-lg"><span class="text-2xl font-black -rotate-12 italic text-white">Q</span></div>
                    <div>
                        <h1 class="text-3xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-500">QUANT TERMINAL V14.6</h1>
                        <p class="text-[9px] text-blue-500/60 font-mono uppercase tracking-[0.4em]">Data Sync Status: Operational</p>
                    </div>
                </div>
                <div class="relative w-full md:w-96 group">
                    <input type="text" id="stockSearch" placeholder="搜索名称、代码或关键字..." 
                        class="w-full glass border border-white/10 rounded-2xl px-6 py-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-white">
                </div>
            </nav>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
                <div class="glass p-10 border border-white/5 rounded-[3rem]">
                    <div class="text-6xl font-black mb-2 italic tracking-tighter text-white">{total_count}</div>
                    <div class="text-[11px] text-slate-500 font-bold uppercase tracking-[0.3em]">全市场分析总量</div>
                </div>
                <div class="glass p-10 border border-white/5 rounded-[3rem]">
                    <div class="text-6xl font-black text-emerald-400 mb-2 italic tracking-tighter">+{new_count}</div>
                    <div class="text-[11px] text-slate-500 font-bold uppercase tracking-[0.3em]">今日发现新代码</div>
                </div>
            </div>

            <div id="cardGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                {cards_html}
            </div>

            <div id="noResults" class="hidden text-center py-40 text-slate-700 text-xs font-bold tracking-[0.5em] uppercase">未找到匹配的个股数据</div>

            <footer class="mt-20 border-t border-white/5 pt-10 flex justify-between text-[10px] text-slate-600 font-mono">
                <div>QUANT SYSTEM v14.6</div><div>SYNC TIME: {cur_time}</div>
            </footer>
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
    
    # 强制将 index.html 写到根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(base_dir, "index.html")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"🔥 写入成功: {output_path}")









