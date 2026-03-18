# 在 html_generator.py 中
def generate_html(data):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background-color: #0b0e14; color: #e5e7eb; }}
            .card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }}
            .accent-green {{ color: #238636; }}
            .accent-red {{ color: #da3633; }}
        </style>
    </head>
    <body class="p-8">
        <div class="max-w-6xl mx-auto grid grid-cols-12 gap-6">
            
            <!-- 左侧历史记录 -->
            <div class="col-span-3 card p-4">
                <h2 class="text-gray-400 mb-4 text-sm">历史记录</h2>
                <div class="space-y-3">
                    <div class="p-2 hover:bg-gray-800 rounded">中国石油 <span class="float-right text-yellow-500">45</span></div>
                    <div class="p-2 hover:bg-gray-800 rounded text-gray-500">腾讯控股</div>
                </div>
            </div>

            <!-- 中间核心分析 -->
            <div class="col-span-6 space-y-6">
                <div class="card p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h1 class="text-2xl font-bold">中国石油 <span class="text-green-500">10.41 -1.42%</span></h1>
                    </div>
                    <div class="bg-blue-900/20 p-4 rounded border border-blue-500/30">
                        <h3 class="text-blue-400 text-xs font-bold mb-2">KEY INSIGHTS</h3>
                        <p class="text-sm leading-relaxed">{data['insights']}</p>
                    </div>
                </div>
                
                <!-- 策略点位 -->
                <div class="grid grid-cols-4 gap-4">
                    <div class="card p-3 text-center"><div class="text-xs text-gray-400">推荐买入</div><div class="text-green-500 font-bold">10.21</div></div>
                    <div class="card p-3 text-center"><div class="text-xs text-gray-400">止损价位</div><div class="text-red-500 font-bold">9.99</div></div>
                </div>
            </div>

            <!-- 右侧情绪仪表盘 -->
            <div class="col-span-3 card p-6 text-center">
                <h2 class="text-gray-400 text-sm mb-4">Market Sentiment</h2>
                <div class="relative pt-1">
                    <div class="text-4xl font-bold">48</div>
                    <div class="text-purple-400 text-sm">中性</div>
                </div>
            </div>

        </div>
    </body>
    </html>
    """
    # 强制保存到 market_analysis/src/index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

