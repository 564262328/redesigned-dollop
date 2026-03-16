import os
import sys
import time
import random
import requests
import json
from datetime import datetime, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- 环境检查与 AKShare 1.18.40 适配 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 依赖缺失。")
    sys.exit(1)

# --- 2026 工业级防封锁逻辑 ---
def robust_mapping(df, mapping):
    if df is None or df.empty: return df
    c = df.columns.tolist()
    m = {p: s for s, ps in mapping.items() for p in ps if p in c}
    return df.rename(columns=m)

@retry(wait=wait_exponential(multiplier=2, min=4, max=30), stop=stop_after_attempt(3))
def fetch(func, *args, **kwargs):
    time.sleep(random.uniform(2, 5))
    return func(*args, **kwargs)

# --- 数据采集 ---
def get_data():
    FIELD_MAP = {
        'code': ['代码', 'code'], 'name': ['名称', 'name'],
        'price': ['最新价', 'trade'], 'pct': ['涨跌幅', 'changepercent'],
        'turnover': ['换手率', 'turnover'], 'vol_ratio': ['量比', 'volume_ratio']
    }
    try:
        df = fetch(ak.stock_zh_a_spot_em)
        df = robust_mapping(df, FIELD_MAP)
        return df, "Eastmoney"
    except:
        df = ak.stock_zh_a_spot()
        df = robust_mapping(df, FIELD_MAP)
        return df, "Sina"

def get_chips():
    try:
        df = fetch(ak.stock_cyq_em, symbol="000001", adjust="qfq")
        L = df.iloc[-1]
        return {"profit": round(float(L.get("获利比例", 0)), 2), "conc": round(float(L.get("90筹码集中度", 0)), 2)}
    except: return {"profit": 50, "conc": 15}

def get_news():
    try:
        df = fetch(ak.news_economic_baidu)
        return df.head(5).values.tolist()
    except: return [["-", "快讯通道暂不可用"]]

# --- Web 页面生成 (Tailwind v4 + Chart.js v4) ---
def generate_html(data_dict):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI 市场监控仪表盘</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"></script>
        <style>
            @theme {{ --color-primary: #10b981; --color-danger: #ef4444; }}
        </style>
    </head>
    <body class="bg-slate-50 text-slate-900 font-sans leading-relaxed">
        <div class="max-w-5xl mx-auto px-4 py-8">
            <header class="flex justify-between items-center mb-8 border-b border-slate-200 pb-6">
                <div>
                    <h1 class="text-3xl font-black text-slate-800 tracking-tight">AI 市场量化分析 <span class="text-primary">v3.0</span></h1>
                    <p class="text-slate-500 text-sm mt-1">更新时间: {data_dict['time']} | 数据源: {data_dict['source']}</p>
                </div>
                <div class="text-right">
                    <span class="px-4 py-2 bg-primary text-white rounded-full text-lg font-bold shadow-lg shadow-emerald-200">
                        评分: {data_dict['score']}
                    </span>
                </div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <!-- 市场情绪图表 -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-center">
                    <h3 class="text-slate-600 font-bold mb-4">市场情绪分布</h3>
                    <canvas id="sentimentChart" width="200" height="200"></canvas>
                </div>

                <!-- 核心指标 -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 col-span-2">
                    <h3 class="text-slate-600 font-bold mb-4">核心监控指标</h3>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-slate-50 p-4 rounded-xl">
                            <p class="text-xs text-slate-400 uppercase">赚钱效应</p>
                            <p class="text-2xl font-black text-primary">{data_dict['ratio']}%</p>
                        </div>
                        <div class="bg-slate-50 p-4 rounded-xl">
                            <p class="text-xs text-slate-400 uppercase">沪指获利盘</p>
                            <p class="text-2xl font-black text-danger">{data_dict['profit']}%</p>
                        </div>
                        <div class="bg-slate-50 p-4 rounded-xl">
                            <p class="text-xs text-slate-400 uppercase">筹码集中度</p>
                            <p class="text-2xl font-black text-slate-700">{data_dict['conc']}%</p>
                        </div>
                        <div class="bg-slate-50 p-4 rounded-xl">
                            <p class="text-xs text-slate-400 uppercase">上涨家数</p>
                            <p class="text-2xl font-black text-primary">{data_dict['up_count']}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 实时资讯 -->
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 mb-8">
                <h3 class="text-slate-600 font-bold mb-4 flex items-center">
                    <span class="w-2 h-2 bg-danger rounded-full animate-pulse mr-2"></span> 实时全球财经快讯
                </h3>
                <div class="space-y-4">
                    {" ".join([f'<div class="flex gap-4 border-l-2 border-slate-100 pl-4 py-1"><span class="text-slate-400 text-sm whitespace-nowrap">{str(n[0])[-5:]}</span><p class="text-slate-700 text-sm">{n[1]}</p></div>' for n in data_dict['news']])}
                </div>
            </div>

            <!-- 决策建议 -->
            <div class="bg-emerald-50 border border-emerald-100 p-6 rounded-2xl">
                <h3 class="text-emerald-800 font-bold mb-2">🎯 AI 策略决策建议</h3>
                <p class="text-emerald-700 text-sm leading-relaxed">{data_dict['advice']}</p>
            </div>
        </div>

        <script>
            new Chart(document.getElementById('sentimentChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['上涨', '下跌'],
                    datasets: [{{
                        data: [{data_dict['up_count']}, {data_dict['down_count']}],
                        backgroundColor: ['#10b981', '#ef4444'],
                        borderWidth: 0,
                        hoverOffset: 4
                    }}]
                }},
                options: {{ cutout: '70%', plugins: {{ legend: {{ display: false }} }} }}
            }});
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

def run():
    print("🚀 启动 Web 仪表盘引擎...")
    df, source = get_data()
    chips = get_chips()
    news = get_news()
    
    df['pct'] = pd.to_numeric(df['pct'], errors='coerce').fillna(0)
    up = len(df[df['pct'] > 0])
    total = len(df)
    score = round((up/total)*70 + 30, 1) if total > 0 else 50
    ratio = round(up/total*100, 1) if total > 0 else 0
    
    advice = "⚠️ 筹码过热" if chips['profit'] > 85 else "✅ 极度超跌" if chips['profit'] < 15 else "⚖️ 震荡市况"
    advice += "。建议密切关注开盘前 15 分钟量比变化，控制仓位在合理水平。"

    data_payload = {{
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": source, "score": score, "ratio": ratio,
        "up_count": up, "down_count": total - up,
        "profit": chips['profit'], "conc": chips['conc'],
        "news": news, "advice": advice
    }}
    
    generate_html(data_payload)
    print("✅ Web 仪表盘 index.html 已生成。")

if __name__ == "__main__":
    run()


