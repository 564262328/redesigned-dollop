import os

def generate_report(data_list):
    """
    data_list: 应该是一个包含多个股票分析结果的列表
    """
    # 1. 动态生成股票卡片 HTML
    cards_html = ""
    for stock in data_list:
        # 判断颜色
        color_class = "text-emerald-400" if "+" in str(stock.get('change', '')) else "text-rose-400"
        
        cards_html += f"""
        <div class="p-6 bg-white/5 border border-white/10 rounded-3xl hover:border-blue-500/50 transition-all group">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-xl font-black">{stock.get('name')}</div>
                    <div class="text-[10px] text-slate-500 font-mono">{stock.get('code')}</div>
                </div>
                <div class="text-right">
                    <div class="text-lg font-black {color_class}">{stock.get('price')}</div>
                    <div class="text-[10px] opacity-60 italic">{stock.get('change')}</div>
                </div>
            </div>
            <div class="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 mb-4">
                <p class="text-[10px] leading-relaxed text-slate-300 italic lowercase">
                    {stock.get('insights', 'AI 分析生成中...')}
                </p>
            </div>
            <div class="grid grid-cols-2 gap-2 text-center">
                <div class="bg-white/5 p-2 rounded-lg border border-white/5">
                    <div class="text-[8px] text-slate-500">BUY</div>
                    <div class="text-xs font-bold text-emerald-400">{stock.get('buy_point')}</div>
                </div>
                <div class="bg-white/5 p-2 rounded-lg border border-white/5">
                    <div class="text-[8px] text-slate-500">STOP</div>
                    <div class="text-xs font-bold text-rose-400">{stock.get('stop_loss')}</div>
                </div>
            </div>
        </div>
        """

    # 2. 完整的 HTML 模板
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script>
        <style>body {{ background: #020617; color: #f8fafc; font-family: ui-sans-serif; font-style: italic; text-transform: uppercase; }}</style>
    </head>
    <body class="p-6 md:p-12 font-black">
        <div class="max-w-6xl mx-auto">
            <header class="flex justify-between border-b border-white/5 pb-10 mb-12">
                <h1 class="text-4xl italic bg-clip-text text-transparent bg-gradient-to-br from-blue-400 to-emerald-400">QUANT TERMINAL v14.1</h1>
                <div class="text-sm font-mono text-slate-300 bg-slate-900 px-4 py-2 rounded-xl border border-white/10">2026-03-18 11:06</div>
            </header>
            <div class="grid grid-cols-2 gap-8 mb-12">
                <div class="p-8 bg-blue-500/5 border border-blue-500/10 rounded-3xl text-center">
                    <div class="text-4xl mb-1">{len(data_list)}</div><div class="text-[10px] text-slate-500">ANALYZED STOCKS</div>
                </div>
                <div class="p-8 bg-emerald-500/5 border border-emerald-500/10 rounded-3xl text-center">
                    <div class="text-4xl text-emerald-400">+{len([s for s in data_list if "+" in str(s.get('change'))])}</div><div class="text-[10px] text-slate-500">UP TODAY</div>
                </div>
            </div>
            <!-- 这里是注入点：把生成的卡片放进 grid 容器 -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards_html}
            </div>
        </div>
    </body>
    </html>
    """
    
    # 保存文件（注意路径）
    with open("../../index.html", "w", encoding="utf-8") as f:
        f.write(full_html)


