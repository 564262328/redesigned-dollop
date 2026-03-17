import os
import sys
import pandas as pd
import akshare as ak
from datetime import datetime

# --- 核心配置 ---
TARGET_STOCKS = ["上证指数", "沪深300", "创业板指", "宁德时代", "贵州茅台"] # 你想分析的名称
BIAS_LIMIT = 0.05  # 5% 乖离率风险预警

def get_full_code(name_or_code):
    """自动将名称/简码转换为带市场前缀的全码"""
    try:
        df = ak.stock_zh_a_spot_em()
        match = df[df['名称'].str.contains(name_or_code)]
        if not match.empty:
            code = match.iloc[0]['代码']
            name = match.iloc[0]['名称']
            full_code = ('sh' + code) if code.startswith(('60', '68')) else ('sz' + code)
            return full_code, name
        return "sh000001", "上证指数" # 默认回退
    except:
        return "sh000001", "上证指数"

def analyze_logic(symbol, name):
    """三段复盘核心逻辑"""
    try:
        # 获取日线 (支持指数和个股)
        if 'sh000' in symbol or 'sz399' in symbol:
            df = ak.stock_zh_index_daily(symbol=symbol).tail(30)
        else:
            df = ak.stock_zh_a_hist(symbol=symbol[2:], period="daily", adjust="qfq").tail(30)
        
        df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'outstanding'] if len(df.columns)==8 else df.columns
        df['close'] = pd.to_numeric(df['close'])
        
        # 计算指标
        ma5, ma10, ma20 = df['close'].rolling(5).mean().iloc[-1], df['close'].rolling(10).mean().iloc[-1], df['close'].rolling(20).mean().iloc[-1]
        last_p = df['close'].iloc[-1]
        
        # 1. 技术面 (多头排列)
        is_bull = ma5 > ma10 > ma20
        # 2. 乖离率 (Bias)
        bias = (last_p - ma20) / ma20
        # 3. 精确买卖点 (支撑位)
        buy_p, stop_p = round(ma20 * 0.99, 2), round(ma20 * 0.95, 2)
        
        status = "🟢 投入进攻" if is_bull and abs(bias) < BIAS_LIMIT else "⚖️ 均衡/防御"
        
        return f"""
## 🔍 分析目标: {name} ({symbol})
- **当前结论**: {status}
- **技术面 (MA5/10/20)**: {'满足多头' if is_bull else '趋势整理'}
- **乖离风险**: {'安全' if abs(bias)<BIAS_LIMIT else '风险(过高)'} (当前: {bias:.2%})
### 🎯 操作清单
- **建议买入点**: `{buy_p}` | **止损点**: `{stop_p}`
- **检查项**: [趋势:{'✅' if is_bull else '❌'}] [乖离:{'✅' if abs(bias)<BIAS_LIMIT else '⚠️'}]
"""
    except Exception as e:
        return f"## ❌ {name} 分析失败\n原因: {str(e)}\n"

def run():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    report = f"# 📊 A股工业级量化看板 v7.0\n> 更新时间: {now}\n\n"
    
    # 遍历目标
    for item in TARGET_STOCKS:
        code, name = get_full_code(item)
        report += analyze_logic(code, name)
    
    report += "\n---\n*投资者参考，不构成投资建议。*\n"
    
    # --- 强制生成文件 (防止 Action 报错) ---
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
# Create the formatted content first
    formatted_report = report.replace('# ', '<h1>').replace('## ', '<h2>').replace('\n', '<br>')
    
# --- 1. 数据预处理 (确保这行最左侧没有空格) ---
content = report.replace('#', '<h1 class="text-xl font-bold text-blue-400 mt-6 mb-2 flex items-center border-l-4 border-blue-600 pl-3">')
content = content.replace('##', '<h2 class="text-lg font-semibold text-slate-300 mt-4 border-b border-slate-700 pb-1">')

# 自动为关键指标着色
content = content.replace('✅', '<span class="px-2 py-0.5 bg-green-900/50 text-green-400 rounded text-xs border border-green-700/50">优势 ✅</span>')
content = content.replace('❌', '<span class="px-2 py-0.5 bg-red-900/50 text-red-400 rounded text-xs border border-red-700/50">风险 ❌</span>')
content = content.replace('⚖️', '<span class="px-2 py-0.5 bg-slate-700/50 text-slate-300 rounded text-xs border border-slate-600/50">中性 ⚖️</span>')

# 处理换行
formatted_report = content.replace('\n', '<br>')

# --- 2. 定义高级 Web 模板 ---
html_tpl = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: radial-gradient(circle at top, #1e293b 0%, #0f172a 100%); min-height: 100vh; color: #e2e8f0; font-family: system-ui, -apple-system, sans-serif; }}
        .glass-card {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; box-shadow: 0 8px 32px 0 rgba(0,0,0,0.3); }}
        br {{ content: ""; margin: 0.5rem 0; display: block; }}
    </style>
</head>
<body class="p-4 md:p-10">
    <div class="max-w-3xl mx-auto">
        <div class="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
            <div>
                <h1 class="text-3xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                    QUANT DASHBOARD
                </h1>
                <p class="text-slate-500 text-sm mt-1 font-medium italic">A股工业级量化看板 v7.0</p>
            </div>
            <div class="text-right">
                <span class="text-xs bg-slate-800 text-slate-400 px-3 py-1 rounded-full border border-slate-700">
                    🕒 {report.split('> 更新时间:')[1].split('\\n')[0] if '> 更新时间:' in report else 'Real-time'}
                </span>
            </div>
        </div>

        <div class="glass-card p-6 md:p-8 leading-relaxed">
            <div class="prose prose-invert max-w-none">
                {formatted_report}
            </div>
        </div>

        <div class="mt-8 text-center text-slate-600 text-xs tracking-widest uppercase">
            Automated Strategy Execution • No Investment Advice
        </div>
    </div>
</body>
</html>
"""

# --- 3. 写入文件 (确保这行与上面对齐，最左侧无空格) ---
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_tpl)

    print("✅ 分析完成，文件已保存。")

if __name__ == "__main__":
    run()


