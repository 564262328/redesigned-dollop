import os

def generate_report(data):
    """
    接收 AI 格式化的数据并生成 index.html
    data 字典结构应包含: stock_name, stock_code, price, change, insights, 
    buy_point, stop_loss, target_price, sentiment_score, history
    """
    
    # 根据涨跌幅正负决定颜色 (A股习惯：红涨绿跌)
    is_up = "-" not in str(data.get('change', ''))
    price_color = "text-red-500" if is_up else "text-green-500"
    
    # 动态生成历史记录 HTML
    history_items = data.get('history', [])
    history_html = ""
    for item in history_items:
        history_html += f"""
        <div class="flex justify-between items-center p-2 hover:bg-gray-800/50 rounded transition">
            <div class="text-sm font-medium">{item.get('name')}</div>
            <div class="text-xs text-yellow-500 font-mono">{item.get('score')}</div>
        </div>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI 市场研报 - {data.get('stock_name')}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background-color: #0d1117; color: #c9d1d9; }}
            .card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }}
            .glow-blue {{ box-shadow: 0 0 15px rgba(59, 130, 246, 0.1); }}
        </style>
    </head>
    <body class="p-4 md:p-8">
        <div class="max-w-7xl mx-auto grid grid-cols-12 gap-6">
            
            <!-- 左侧：任务与历史 (3列) -->
            <div class="col-span-12 md:col-span-3 space-y-6">
                <div class="card p-4 glow-blue">
                    <h2 class="text-xs font-bold text-gray-500 mb-4 tracking-widest uppercase">分析任务</h2>
                    <div class="flex items-center space-x-3 p-3 bg-blue-900/10 border border-blue-500/20 rounded-lg">
                        <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                        <span class="text-xs font-mono">{data.get('stock_code')} 分析已完成</span>
                    </div>
                </div>
                
                <div class="card p-4">
                    <h2 class="text-xs font-bold text-gray-500 mb-4 tracking-widest uppercase font-mono">历史记录</h2>
                    <div class="space-y-1">
                        {history_html if history_html else '<p class="text-gray-600 text-xs">暂无历史数据</p>'}
                    </div>
                </div>
            </div>

            <!-- 中间：核心分析 (6列) -->
            <div class="col-span-12 md:col-span-6 space-y-6">
                <div class="card p-8">
                    <div class="flex justify-between items-baseline mb-8">
                        <div>
                            <h1 class="text-3xl font-black tracking-tight">{data.get('stock_name')}</h1>
                            <p class="text-gray-500 font-mono text-sm mt-1">{data.get('stock_code')} · {data.get('date', '今日')}</p>
                        </div>
                        <div class="text-right">
                            <div class="text-3xl font-black font-mono {price_color}">{data.get('price')}</div>
                            <div class="text-sm font-bold {price_color} mt-1">{data.get('change')}</div>
                        </div>
                    </div>
                    
                    <div class="relative p-6 bg-blue-900/5 border border-blue-500/10 rounded-xl mb-8">
                        <div class="absolute -top-3 left-4 px-2 bg-[#161b22] text-blue-400 text-[10px] font-black tracking-widest">KEY INSIGHTS</div>
                        <p class="text-sm leading-relaxed text-gray-300 italic">
                            {data.get('insights', 'AI 正在深度解析市场大数据...')}
                        </p>
                    </div>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="card p-3 border-gray-800 text-center">
                            <p class="text-[10px] text-gray-500 mb-1">推荐买入</p>
                            <p class="text-lg font-bold text-green-500 font-mono">{data.get('buy_point', '--')}</p>
                        </div>
                        <div class="card p-3 border-gray-800 text-center">
                            <p class="text-[10px] text-gray-500 mb-1">止损价位</p>
                            <p class="text-lg font-bold text-red-500 font-mono">{data.get('stop_loss', '--')}</p>
                        </div>
                        <div class="card p-3 border-gray-800 text-center">
                            <p class="text-[10px] text-gray-500 mb-1">止盈目标</p>
                            <p class="text-lg font-bold text-blue-500 font-mono">{data.get('target_price', '--')}</p>
                        </div>
                        <div class="card p-3 border-gray-800 text-center">
                            <p class="text-[10px] text-gray-500 mb-1">趋势预测</p>
                            <p class="text-sm font-bold text-purple-400 mt-1">震荡上行</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 右侧：情绪仪表盘 (3列) -->
            <div class="col-span-12 md:col-span-3">
                <div class="card p-8 h-full flex flex-col items-center justify-center text-center">
                    <h2 class="text-xs font-bold text-gray-500 mb-12 tracking-widest uppercase">Market Sentiment</h2>
                    
                    <div class="relative w-40 h-40 flex items-center justify-center">
                        <!-- 简易仪表盘环形 -->
                        <svg class="absolute inset-0 w-full h-full -rotate-90">
                            <circle cx="80" cy="80" r="70" stroke="#1f2937" stroke-width="12" fill="transparent" />
                            <circle cx="80" cy="80" r="70" stroke="#8b5cf6" stroke-width="12" fill="transparent" 
                                stroke-dasharray="440" stroke-dashoffset="{440 - (440 * int(data.get('sentiment_score', 50)) / 100)}" 
                                stroke-linecap="round" />
                        </svg>
                        <div class="text-center">
                            <div class="text-5xl font-black text-white font-mono">{data.get('sentiment_score', 50)}</div>
                            <div class="text-purple-400 text-xs font-bold mt-1">中性偏强</div>
                        </div>
                    </div>
                    
                    <p class="text-[10px] text-gray-500 mt-12 italic">AI 综合全网情绪大数据计算所得</p>
                </div>
            </div>

        </div>
    </body>
    </html>
    """
    
    # 将文件保存到根目录，方便 GitHub Pages 识别
    output_path = os.path.join(os.getcwd(), "../../index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ 专业研报已生成至根目录: index.html")


