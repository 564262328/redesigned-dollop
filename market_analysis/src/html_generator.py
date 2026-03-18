import os
from datetime import datetime

def generate_report(data_list):
    """
    data_list: 包含多只股票分析字典的列表
    """
    cards_html = ""
    for stock in data_list:
        # A股习惯：涨红跌绿
        is_up = "-" not in str(stock.get('change', ''))
        color_class = "text-rose-500" if is_up else "text-emerald-500"
        bg_class = "bg-rose-500/5" if is_up else "bg-emerald-500/5"
        border_class = "border-rose-500/10" if is_up else "border-emerald-500/10"

        cards_html += f"""
        <div class="p-6 bg-white/5 border border-white/10 rounded-3xl hover:border-blue-500/50 transition-all group">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-xl font-black">{stock.get('stock_name', '未知')}</div>
                    <div class="text-[10px] text-slate-500 font-mono">{stock.get('stock_code', '000000')}</div>
                </div>
                <div class="text-right">
                    <div class="text-lg font-black {color_class} font-mono">{stock.get('price', '0.00')}</div>
                    <div class="text-[10px] opacity-60 italic">{stock.get('change', '0%')}</div>
                </div>
            </div>
            <div class="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 mb-4">
                <p class="text-[10px] leading-relaxed text-slate-300 italic lowercase">
                    {stock.get('insights', 'AI 正在解析大数据...')}
                </p>
            </div>
            <div class="grid grid-cols-2 gap-2 text-center">
                <div class="bg-white/5 p-2 rounded-lg border border-white/5">
                    <div class="text-[8px] text-slate-500">BUY位</div>
                    <div class="text-xs font-bold text-emerald-400 font-mono">{stock.get('buy_point', '--')}</div>
                </div>
                <div class="bg-white/5 p-2 rounded-lg border border-white/5">
                    <div class="text-[8px] text-slate-500">STOP位</div>
                    <div class="text-xs font-bold text-rose-400 font-mono">{stock.get('stop_loss', '--')}</div>
                </div>
            </div>
        </div>
        """

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: ui-sans-serif; font-style: italic; text-transform: uppercase; }}
        </style>
    </head>
    <body class="p-6 md:p-12 font-black">
        <div class="max-w-6xl mx-auto">
            <header class="flex justify-between border-b border-white/5 pb-10 mb-12">
                <h1 class="text-4xl italic bg-clip-text text-transparent bg-gradient-to-br from-blue-400 to-emerald-400">QUANT TERMINAL v14.2</h1>
                <div class="text-sm font-mono text-slate-300 bg-slate-900 px-4 py-2 rounded-xl border border-white/10">{current_time}</div>
            </header>
            
            <div class="grid grid-cols-2 gap-8 mb-12">
                <div class="p-8 bg-blue-500/5 border border-blue-500/10 rounded-3xl text-center">
                    <div class="text-4xl mb-1">{len(data_list)}</div>
                    <div class="text-[10px] text-slate-500 tracking-widest">ANALYZED STOCKS</div>
                </div>
                <div class="p-8 bg-emerald-500/5 border border-emerald-500/10 rounded-3xl text-center">
                    <div class="text-4xl text-emerald-400">+{len([s for s in data_list if "-" not in str(s.get('change'))])}</div>
                    <div class="text-[10px] text-slate-500 tracking-widest">UP TRENDS</div>
                </div>
            </div>

            <!-- 卡片容器 -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards_html}
            </div>
        </div>
    </body>
    </html>
    """
    
    # 强制保存到仓库根目录
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../index.html"))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"✅ 成功生成看板至: {output_path}")


