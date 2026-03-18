import os
from datetime import datetime

def generate_report(data_list, new_count, total_count, source_name, industry_data, index_data):
    # 1. 指數橫欄 (添加 id 以便 JS 刷新)
    index_html = ""
    for idx in index_data:
        index_html += f"""
        <div class="flex flex-col border-r border-white/5 last:border-0 px-8 min-w-[160px] index-box" data-code="{idx.get('code','000001')}">
            <span class="text-[10px] text-slate-500 font-black mb-1 tracking-widest">{idx['name']}</span>
            <div class="flex items-baseline gap-2">
                <span class="text-lg font-black font-mono tracking-tighter val-price">{idx['price']}</span>
                <span class="text-xs font-bold val-change">{idx.get('change','0')}%</span>
            </div>
        </div>
        """

    # 2. 個股卡片 (添加實時刷新所需的屬性)
    cards_html = ""
    for s in data_list:
        is_up = "-" not in str(s.get('change', '0'))
        color = "text-rose-500" if is_up else "text-emerald-500"
        border = "border-rose-500/20" if is_up else "border-emerald-500/20"
        
        # 搜索標籤
        search_tags = f"{s.get('stock_name')} {s.get('stock_code')}".lower()
        
        cards_html += f"""
        <div class="stock-card group p-6 bg-slate-900/40 backdrop-blur-xl border {border} rounded-[2rem] transition-all duration-500 hover:shadow-[0_0_30px_rgba(59,130,246,0.1)]" 
             data-industry="{s.get('industry','其他')}" 
             data-code="{s.get('stock_code')}"
             data-search="{search_tags}">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-xl font-black text-white">{s.get('stock_name')} <span class="text-[10px] text-slate-500 italic">({s.get('stock_code')})</span></div>
                    <div class="mt-2 inline-block px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-[8px] font-bold">板塊: {s.get('industry')}</div>
                </div>
                <div class="text-right">
                    <div class="text-2xl font-black {color} font-mono leading-none val-price">{s.get('price')}</div>
                    <div class="text-[10px] {color} font-bold mt-1 val-change">{s.get('change')}%</div>
                </div>
            </div>
            <div class="grid grid-cols-2 gap-2 mb-4 text-[9px] text-slate-500 font-mono border-y border-white/5 py-3">
                <div>換手: <span class="text-white val-turnover">{s.get('turnover', '--')}%</span></div>
                <div>量比: <span class="text-white val-volume-ratio">{s.get('volume_ratio', '--')}</span></div>
            </div>
            <div class="p-3 bg-indigo-500/10 rounded-xl mb-4 text-[10px] italic text-slate-300">
                <div class="flex justify-between"><span>獲利盤: <span class="text-rose-400 font-bold">{s.get('profit_ratio', '--')}</span></span><span>成本: <span class="text-white">{s.get('avg_cost', '--')}</span></span></div>
            </div>
            <div class="p-4 bg-black/40 rounded-2xl mb-4 min-h-[80px] text-[11px] text-slate-400 leading-relaxed italic">
                <div class="text-[7px] text-blue-500 font-bold mb-1 uppercase tracking-widest">AI 深度研判 (每日更新)</div>
                {s.get('insights')}
            </div>
            <div class="grid grid-cols-2 gap-3 text-center">
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5 text-[8px] text-slate-500">介入參考<div class="text-sm font-black text-rose-500">{s.get('buy_point')}</div></div>
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5 text-[8px] text-slate-500">安全閾值<div class="text-sm font-black text-emerald-500">{s.get('stop_loss')}</div></div>
            </div>
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT 終端 V15.5 | 實時監控中</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: radial-gradient(circle at 50% 0%, #1a1c2e 0%, #020617 100%); color: #f8fafc; font-family: system-ui; min-height: 100vh; }}
            .no-scrollbar::-webkit-scrollbar {{ display: none; }}
            .live-dot {{ animation: blink 1.5s infinite; }}
            @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
        </style>
    </head>
    <body class="p-6 md:p-12">
        <div class="max-w-7xl mx-auto">
            <header class="flex justify-between items-center border-b border-white/5 pb-10 mb-8">
                <div>
                    <h1 class="text-3xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-500 uppercase">Quant Terminal v15.5</h1>
                    <div class="flex items-center gap-2 mt-1">
                        <span class="w-2 h-2 bg-rose-500 rounded-full live-dot"></span>
                        <span class="text-[9px] text-rose-500 font-bold tracking-widest uppercase">Live Market Data Streaming</span>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-5xl font-black italic tracking-tighter text-white">{total_count}</div>
                    <div class="text-[9px] text-slate-500 font-bold uppercase tracking-widest">全市場監控量</div>
                </div>
            </header>
            
            <div class="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-3xl p-6 flex overflow-x-auto no-scrollbar mb-12 shadow-2xl">
                {index_html}
            </div>

            <div id="cardGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">{cards_html}</div>
            
            <footer class="mt-20 border-t border-white/5 pt-10 flex flex-col md:flex-row justify-between items-center gap-6 text-[10px] text-slate-600 font-mono tracking-widest uppercase">
                <div class="flex items-center gap-6">
                    <span>數據源: <span class="text-blue-400 font-bold">{source_name}</span></span>
                    <span>AI 更新: 每日 16:00</span>
                </div>
                <div id="lastUpdate">網頁實時刷新中...</div>
            </footer>
        </div>

        <script>
            // 實時數據刷新引擎
            async function refreshLiveQuotes() {{
                const items = document.querySelectorAll('.stock-card, .index-box');
                
                for (let item of items) {{
                    const rawCode = item.getAttribute('data-code');
                    if (!rawCode) continue;

                    // 處理代碼格式 (A股需區分 sh/sz, 港股需 hk)
                    let apiCode = "";
                    if (rawCode.length === 5) apiCode = "hk" + rawCode;
                    else apiCode = (rawCode.startsWith('6') || rawCode.startsWith('5') || rawCode.startsWith('000001')) ? "sh" + rawCode : "sz" + rawCode;

                    try {{
                        // 使用騰訊財經 JS 接口 (支持跨域)
                        const response = await fetch(`https://qt.gtimg.cn{{apiCode}}`);
                        const text = await response.text();
                        const parts = text.split('~');
                        
                        if (parts.length > 5) {{
                            const price = parts[3];
                            const change = parts[5];
                            
                            const priceEl = item.querySelector('.val-price');
                            const changeEl = item.querySelector('.val-change');
                            
                            if (priceEl) priceEl.innerText = price;
                            if (changeEl) {{
                                changeEl.innerText = (parseFloat(change) > 0 ? "+" : "") + change + "%";
                                // 動態更新顏色
                                const isUp = parseFloat(change) >= 0;
                                const colorClass = isUp ? "text-rose-500" : "text-emerald-500";
                                priceEl.className = `text-2xl font-black font-mono leading-none ${{colorClass}}`;
                                changeEl.className = `text-[10px] font-bold mt-1 ${{colorClass}}`;
                                if (item.classList.contains('index-box')) {{
                                    priceEl.className = `text-lg font-black font-mono tracking-tighter ${{colorClass}}`;
                                    changeEl.className = `text-xs font-bold ${{colorClass}}`;
                                }}
                            }}
                        }}
                    }} catch (e) {{ console.error("刷新出錯", e); }}
                }}
                document.getElementById('lastUpdate').innerText = "最後同步: " + new Date().toLocaleTimeString();
            }}

            // 交易時段自動刷新 (每 30 秒)
            setInterval(refreshLiveQuotes, 30000);
            window.onload = refreshLiveQuotes; // 頁面加載時立即刷一次
        </script>
    </body></html>
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(base_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f: f.write(full_html)
















