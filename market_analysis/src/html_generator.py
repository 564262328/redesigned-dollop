import os
from datetime import datetime

def generate_report(data_list):
    cards_html = ""
    for stock in data_list:
        # A 股：漲紅跌綠
        change_val = str(stock.get('change', '0'))
        is_up = "-" not in change_val and change_val != "0"
        color_class = "text-red-500" if is_up else "text-green-500"
        
        cards_html += f"""
        <div class="p-6 bg-white/5 border border-white/10 rounded-3xl hover:border-blue-500/50 transition-all group">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-xl font-black tracking-tight">{stock.get('stock_name')}</div>
                    <div class="text-[10px] text-slate-500 font-mono">{stock.get('stock_code')}</div>
                </div>
                <div class="text-right">
                    <div class="text-lg font-black {color_class} font-mono">{stock.get('price')}</div>
                    <div class="text-[10px] opacity-60 italic">{stock.get('change')}%</div>
                </div>
            </div>
            <div class="p-4 bg-blue-500/5 rounded-2xl border border-blue-500/10 mb-4">
                <p class="text-[11px] leading-relaxed text-slate-300 italic">
                    {stock.get('insights', 'AI 深度分析收集中...')}
                </p>
            </div>
            <div class="grid grid-cols-2 gap-3 text-center">
                <div class="bg-white/5 p-2 rounded-xl border border-white/5">
                    <div class="text-[9px] text-slate-500 mb-1">建議買入位</div>
                    <div class="text-xs font-bold text-red-400 font-mono">{stock.get('buy_point', '--')}</div>
                </div>
                <div class="bg-white/5 p-2 rounded-xl border border-white/5">
                    <div class="text-[9px] text-slate-500 mb-1">建議止損位</div>
                    <div class="text-xs font-bold text-green-400 font-mono">{stock.get('stop_loss', '--')}</div>
                </div>
            </div>
        </div>
        """

    cur_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: "PingFang TC", sans-serif; }}
            .terminal-font {{ font-style: italic; text-transform: uppercase; font-weight: 900; }}
        </style>
    </head>
    <body class="p-6 md:p-12">
        <div class="max-w-6xl mx-auto">
            <header class="flex justify-between border-b border-white/5 pb-8 mb-10">
                <h1 class="text-3xl terminal-font bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-red-400">QUANT 量化終端 V14.5</h1>
                <div class="text-xs font-mono text-slate-400 bg-slate-900/50 px-4 py-2 rounded-full border border-white/10">{cur_time}</div>
            </header>
            
            <div class="grid grid-cols-2 gap-6 mb-10">
                <div class="p-6 bg-blue-500/5 border border-blue-500/10 rounded-3xl text-center">
                    <div class="text-3xl font-black mb-1">{len(data_list)}</div>
                    <div class="text-[10px] text-slate-500 tracking-widest terminal-font">已分析個股</div>
                </div>
                <div class="p-6 bg-red-500/5 border border-red-500/10 rounded-3xl text-center">
                    <div class="text-3xl font-black text-red-500">+{len([s for s in data_list if "-" not in str(s.get('change'))])}</div>
                    <div class="text-[10px] text-slate-500 tracking-widest terminal-font">看漲趨勢</div>
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards_html}
            </div>
        </div>
    </body>
    </html>
    """
    with open("../../index.html", "w", encoding="utf-8") as f:
        f.write(full_html)



