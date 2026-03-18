import os
from datetime import datetime

def generate_report(data_list, new_count, total_count, source_name):
    cards_html = ""
    for s in data_list:
        is_up = "-" not in str(s.get('change', ''))
        color = "text-rose-500" if is_up else "text-emerald-500"
        border = "border-rose-500/20" if is_up else "border-emerald-500/20"
        
        # 类型标签颜色
        type_tag = s.get('asset_type', 'A股')
        tag_style = "bg-blue-500/20 text-blue-400" # A股
        if type_tag == "ETF基金": tag_style = "bg-purple-500/20 text-purple-400"
        if type_tag == "港股": tag_style = "bg-orange-500/20 text-orange-400"

        cards_html += f"""
        <div class="stock-card group p-6 bg-slate-900/40 border {border} rounded-3xl hover:shadow-[0_0_30px_rgba(59,130,246,0.1)] transition-all duration-500">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <!-- 核心：名称 (代码) -->
                    <div class="text-lg font-black tracking-tighter text-white group-hover:text-blue-400">{s['stock_name']}</div>
                    <div class="mt-2 inline-block px-2 py-0.5 rounded text-[8px] font-bold uppercase {tag_style}">{type_tag}</div>
                </div>
                <div class="text-right">
                    <div class="text-xl font-black {color} font-mono leading-none">{s['price']}</div>
                    <div class="text-[10px] {color} font-bold mt-1">{s['change']}%</div>
                </div>
            </div>
            
            <div class="p-4 bg-slate-950/60 rounded-2xl border border-white/5 mb-6 min-h-[80px]">
                <div class="text-[8px] text-slate-500 font-black mb-2 tracking-widest uppercase">Quant Insight</div>
                <p class="text-[11px] leading-relaxed text-slate-400 italic">{s['insights']}</p>
            </div>
            
            <div class="grid grid-cols-2 gap-4 text-center">
                <div class="bg-slate-950/80 p-3 rounded-xl border border-white/5">
                    <div class="text-[8px] text-slate-500 mb-1 font-bold">建议介入</div>
                    <div class="text-sm font-black text-rose-500 font-mono tracking-tighter">{s['buy_point']}</div>
                </div>
                <div class="bg-slate-950/80 p-3 rounded-xl border border-white/5">
                    <div class="text-[8px] text-slate-500 mb-1 font-bold">建议防守</div>
                    <div class="text-sm font-black text-emerald-500 font-mono tracking-tighter">{s['stop_loss']}</div>
                </div>
            </div>
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>body {{ background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #020617 100%); color: #f8fafc; font-family: system-ui; }}</style>
    </head>
    <body class="p-6 md:p-12">
        <div class="max-w-7xl mx-auto">
            <header class="flex justify-between items-center border-b border-white/5 pb-10 mb-12">
                <div>
                    <h1 class="text-3xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-500">QUANT TERMINAL V15.0</h1>
                    <p class="text-[10px] text-blue-500 font-mono uppercase tracking-[0.4em]">AI Asset Intelligence System</p>
                </div>
                <div class="text-right">
                    <div class="text-4xl font-black italic">{total_count}</div>
                    <div class="text-[9px] text-slate-500 uppercase tracking-widest">Total Assets Tracked</div>
                </div>
            </header>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                {cards_html}
            </div>

            <footer class="mt-20 border-t border-white/5 pt-10 text-[10px] text-slate-600 font-mono flex justify-between uppercase">
                <div>Source: <span class="text-blue-400 font-bold">{source_name}</span></div>
                <div>Sync Time: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
            </footer>
        </div>
    </body>
    </html>
    """
    
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)













