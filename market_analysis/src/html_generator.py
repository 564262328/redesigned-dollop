import os
from datetime import datetime

def generate_report(data_list, new_count, total_count):
    cards_html = ""
    for s in data_list:
        color = "text-red-500" if "-" not in str(s.get('change')) else "text-green-500"
        cards_html += f"""
        <div class="p-6 bg-white/5 border border-white/10 rounded-3xl">
            <div class="flex justify-between mb-4">
                <div><div class="text-xl font-bold">{s['stock_name']}</div><div class="text-xs text-slate-500">{s['stock_code']}</div></div>
                <div class="text-right"><div class="text-lg font-black {color}">{s['price']}</div><div class="text-xs opacity-50">{s['change']}%</div></div>
            </div>
            <div class="p-3 bg-blue-500/10 rounded-xl mb-4 text-[11px] italic text-slate-300">{s['insights']}</div>
            <div class="grid grid-cols-2 gap-2 text-center text-[10px]">
                <div class="bg-white/5 p-2 rounded-lg border border-white/5"><div class="text-slate-500">建議買入</div><div class="text-red-400 font-bold">{s['buy_point']}</div></div>
                <div class="bg-white/5 p-2 rounded-lg border border-white/5"><div class="text-slate-500">建議止損</div><div class="text-green-400 font-bold">{s['stop_loss']}</div></div>
            </div>
        </div>"""

    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="p-8 bg-[#020617] text-slate-100 font-black italic uppercase">
        <div class="max-w-6xl mx-auto">
            <header class="flex justify-between border-b border-white/5 pb-8 mb-10">
                <h1 class="text-3xl bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-red-400">QUANT 終端 V14.6</h1>
                <div class="text-xs font-mono text-slate-400">{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
            </header>
            <div class="grid grid-cols-2 gap-6 mb-10 text-center">
                <div class="p-6 bg-blue-500/5 border border-blue-500/10 rounded-3xl">
                    <div class="text-4xl mb-1">{total_count}</div><div class="text-[10px] text-slate-500">全市場股票總數</div>
                </div>
                <div class="p-6 bg-emerald-500/5 border border-emerald-500/10 rounded-3xl">
                    <div class="text-4xl text-emerald-400">+{new_count}</div><div class="text-[10px] text-slate-500">今日發現新代碼</div>
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">{cards_html}</div>
        </div>
    </body></html>"""
    with open("../../index.html", "w", encoding="utf-8") as f:
        f.write(full_html)




