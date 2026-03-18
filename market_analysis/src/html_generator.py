import os
from datetime import datetime

def generate_report(data_list, new_count, total_count, source_name, industry_data, index_data):
    # 1. 指數橫欄 (帶數據標籤)
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

    # 2. 個股卡片
    cards_html = ""
    for s in data_list:
        is_up = "-" not in str(s.get('change', '0'))
        color = "text-rose-500" if is_up else "text-emerald-500"
        border = "border-rose-500/20" if is_up else "border-emerald-500/20"
        search_tags = f"{s.get('stock_name')} {s.get('stock_code')}".lower()
        
        cards_html += f"""
        <div class="stock-card group p-6 bg-slate-900/40 backdrop-blur-xl border {border} rounded-[2rem] transition-all duration-500 hover:shadow-[0_0_30px_rgba(59,130,246,0.1)]" 
             data-industry="{s.get('industry','其他')}" 
             data-code="{s.get('stock_code')}"
             data-search="{search_tags}">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-xl font-black text-white">{s.get('stock_name')} <span class="text-[10px] text-slate-500 italic">({s.get('stock_code')})</span></div>
                    <div class="mt-2 inline-block px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-[8px] font-bold tracking-widest">區域: {s.get('asset_type','A股')}</div>
                </div>
                <div class="text-right">
                    <div class="text-2xl font-black {color} font-mono leading-none val-price">{s.get('price')}</div>
                    <div class="text-[10px] {color} font-bold mt-1 val-change">{s.get('change')}%</div>
                </div>
            </div>
            <div class="grid grid-cols-2 gap-2 mb-4 text-[9px] text-slate-500 font-mono border-y border-white/5 py-3">
                <div>換手: <span class="text-white">{s.get('turnover', '--')}%</span></div>
                <div>量比: <span class="text-white">{s.get('volume_ratio', '--')}</span></div>
            </div>
            <div class="p-3 bg-indigo-500/10 rounded-xl mb-4 text-[10px] italic text-slate-300">
                <div class="flex justify-between"><span>獲利盤: <span class="text-rose-400 font-bold">{s.get('profit_ratio', '--')}</span></span><span>平均成本: <span class="text-white">{s.get('avg_cost', '--')}</span></span></div>
            </div>
            <div class="p-4 bg-black/40 rounded-2xl mb-4 min-h-[80px] text-[11px] text-slate-400 leading-relaxed italic">
                <div class="text-[7px] text-blue-500 font-bold mb-1 uppercase tracking-widest border-b border-blue-500/20 pb-1 mb-2">AI 理性價值研判</div>
                {s.get('insights')}
            </div>
            <div class="grid grid-cols-2 gap-3 text-center">
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5">
                    <div class="text-[8px] text-slate-500 uppercase">價值參考</div>
                    <div class="text-sm font-black text-rose-500">{s.get('buy_point')}</div>
                </div>
                <div class="bg-slate-950/80 p-2 rounded-xl border border-white/5">
                    <div class="text-[8px] text-slate-500 uppercase">安全閾值</div>
                    <div class="text-sm font-black text-emerald-500">{s.get('stop_loss')}</div>
                </div>
            </div>
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT 終端 V15.6 | 多源實時版</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: radial-gradient(circle at 50% 0%, #1a1c2e 0%, #020617 100%); color: #f8fafc; font-family: system-ui; min-height: 100vh; }}
            .no-scrollbar::-webkit-scrollbar {{ display: none; }}
            .live-indicator {{ animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }}
            @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .4; }} }}
        </style>
    </head>
    <body class="p-6 md:p-12">
        <div class="max-w-7xl mx-auto">
            <header class="flex justify-between items-center border-b border-white/5 pb-10 mb-8">
                <div>
                    <h1 class="text-3xl font-black italic tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-500">QUANT TERMINAL V15.6</h1>
                    <div class="flex items-center gap-2 mt-1">
                        <span class="w-2 h-2 bg-emerald-500 rounded-full live-indicator"></span>
                        <span class="text-[9px] text-emerald-500 font-bold tracking-widest uppercase" id="syncStatus">Dual-Engine Live Streaming</span>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-5xl font-black italic tracking-tighter text-white">{total_count}</div>
                    <div class="text-[9px] text-slate-500 font-bold tracking-widest uppercase">全市場監控總量</div>
                </div>
            </header>
            
            <div class="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-3xl p-6 flex overflow-x-auto no-scrollbar mb-12 shadow-2xl">
                {index_html}
            </div>

            <div id="cardGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">{cards_html}</div>
            
            <footer class="mt-20 border-t border-white/5 pt-10 flex flex-col md:flex-row justify-between items-center gap-6 text-[10px] text-slate-600 font-mono tracking-widest uppercase">
                <div class="flex items-center gap-6">
                    <span>Python 來源: <span class="text-blue-400 font-bold">{source_name}</span></span>
                    <span>JS 引擎: <span id="jsEngine" class="text-emerald-400 font-bold">Tencent (Primary)</span></span>
                </div>
                <div id="lastUpdate">初始化實時數據...</div>
            </footer>
        </div>

        <script>
            // V15.6 核心鏡像切換引擎
            let currentEngine = "tencent"; 

            async function refreshLiveQuotes() {{
                const items = document.querySelectorAll('.stock-card, .index-box');
                
                for (let item of items) {{
                    const rawCode = item.getAttribute('data-code');
                    if (!rawCode) continue;

                    let apiCode = "";
                    if (rawCode.length === 5) apiCode = "hk" + rawCode;
                    else apiCode = (rawCode.startsWith('6') || rawCode.startsWith('5') || rawCode.startsWith('000001')) ? "sh" + rawCode : "sz" + rawCode;

                    try {{
                        let price, change;

                        if (currentEngine === "tencent") {{
                            // 引擎 A: 騰訊財經
                            const response = await fetch(`https://qt.gtimg.cn{{apiCode}}`);
                            const text = await response.text();
                            const parts = text.split('~');
                            if (parts.length > 5) {{
                                price = parts;
                                change = parts;
                            }} else {{ throw new Error("Format error"); }}
                        }} else {{
                            // 引擎 B: 網易鏡像 (跨域備選)
                            const neteaseCode = (apiCode.startsWith('sh') ? '0' : '1') + rawCode;
                            const response = await fetch(`https://api.money.126.net{{neteaseCode}}`);
                            const jsonText = await response.text();
                            const cleanJson = JSON.parse(jsonText.match(/\\((.*)\\)/)[1]);
                            const data = cleanJson[neteaseCode];
                            price = data.price;
                            change = (data.updown * 100).toFixed(2);
                        }}
                        
                        const priceEl = item.querySelector('.val-price');
                        const changeEl = item.querySelector('.val-change');
                        
                        if (priceEl && price) priceEl.innerText = price;
                        if (changeEl && change) {{
                            changeEl.innerText = (parseFloat(change) > 0 ? "+" : "") + change + "%";
                            const colorClass = parseFloat(change) >= 0 ? "text-rose-500" : "text-emerald-500";
                            priceEl.className = item.classList.contains('index-box') ? 
                                `text-lg font-black font-mono tracking-tighter ${{colorClass}}` : 
                                `text-2xl font-black font-mono leading-none ${{colorClass}}`;
                            changeEl.className = item.classList.contains('index-box') ? 
                                `text-xs font-bold ${{colorClass}}` : 
                                `text-[10px] font-bold mt-1 ${{colorClass}}`;
                        }}

                    }} catch (e) {{ 
                        console.warn("切換備援引擎..."); 
                        currentEngine = "netease";
                        document.getElementById('jsEngine').innerText = "NetEase (Backup)";
                    }}
                }}
                document.getElementById('lastUpdate').innerText = "最後同步: " + new Date().toLocaleTimeString();
            }}

            setInterval(refreshLiveQuotes, 20000); // 縮短至 20 秒刷新一次
            window.onload = refreshLiveQuotes;
        </script>
    </body></html>
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(base_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f: f.write(full_html)

















