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
    
    html_tpl = f"<html><body style='font-family:sans-serif;padding:20px;'>{report.replace('# ', '<h1>').replace('## ', '<h2>').replace('\\n', '<br>')}</body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_tpl)
    print("✅ 分析完成，文件已保存。")

if __name__ == "__main__":
    run()


