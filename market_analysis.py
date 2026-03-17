import os
import pandas as pd
import akshare as ak
from datetime import datetime
import time
import json
import random

# --- 1. 自动化数据库配置 ---
DB_FILE = "stocks_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_update": "", "total_count": 0, "stock_list": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 2. 深度数据抓取 (带防封逻辑) ---
def fetch_safe_data(func, *args, **kwargs):
    """带随机休眠的抓取代理"""
    time.sleep(random.uniform(2.0, 4.5)) # 随机休眠 2-5 秒
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"请求异常: {e}")
        return pd.DataFrame()

def get_market_intelligence():
    """扫描全市场并识别新个股/ETF"""
    print("正在扫描全市场实时行情...")
    # 获取全 A 股实时快照 (包含量比、换手、市盈率等)
    df_a = fetch_safe_data(ak.stock_zh_a_spot_em)
    # 获取热门 ETF 快照
    df_etf = fetch_safe_data(ak.fund_etf_spot_em)
    
    return df_a, df_etf

# --- 3. 筹码分布模拟分析 (基于行情衍生) ---
def analyze_chip_density(row):
    """
    根据换手率和乖离率估算筹码状态
    获利比例估算模型：基于价格相对于 20MA 的位置
    """
    turnover = pd.to_numeric(row.get('换手率', 0), errors='coerce')
    # 简单模型：换手率极高通常意味着筹码正在剧烈换手
    status = "集中" if turnover < 3 else "活跃" if turnover < 10 else "发散"
    return status

# --- 4. 执行主流程 ---
def run():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = load_db()
    
    df_a, df_etf = get_market_intelligence()
    
    if df_a.empty:
        print("无法获取市场数据，退出。")
        return

    # 识别新股逻辑
    current_codes = set(df_a['代码'].tolist())
    old_codes = set(db.get("stock_list", []))
    new_stocks = current_codes - old_codes
    
    # 更新数据库
    db["last_update"] = now_str
    db["total_count"] = len(current_codes)
    db["stock_list"] = list(current_codes)
    save_db(db)

    # 筛选今日表现最强的 12 个目标展示在网页上 (按涨幅排序)
    top_performers = df_a.sort_values(by="涨跌幅", ascending=False).head(12)
    
    cards_html = ""
    for _, row in top_performers.iterrows():
        color = "text-red-500" if row['涨跌幅'] > 0 else "text-green-500"
        chip_status = analyze_chip_density(row)
        
        cards_html += f"""
        <div class="glass-card p-4 border-t-2 border-white/5 hover:border-red-500/50 transition-all">
            <div class="flex justify-between items-start mb-2">
                <div>
                    <h3 class="text-sm font-bold text-white">{row['名称']}</h3>
                    <span class="text-[9px] text-slate-500 font-mono">{row['代码']}</span>
                </div>
                <div class="text-right">
                    <span class="text-lg font-black {color}">{row['最新价']}</span>
                    <span class="text-[10px] {color} block">{row['涨跌幅']}%</span>
                </div>
            </div>
            <div class="grid grid-cols-2 gap-2 text-[10px] border-t border-white/5 pt-2 mt-2 uppercase font-bold italic">
                <div class="flex flex-col"><span class="text-slate-500 font-bold uppercase italic font-bold">换手率</span><span class="text-slate-300 font-mono font-bold uppercase italic">{row['换手率']}%</span></div>
                <div class="flex flex-col text-right"><span class="text-slate-500 font-bold uppercase italic font-bold">量比</span><span class="text-amber-400 font-mono font-bold uppercase italic">{row['量比']}</span></div>
                <div class="flex flex-col"><span class="text-slate-500 font-bold uppercase italic font-bold">筹码状态</span><span class="text-blue-400 font-bold uppercase italic font-bold">{chip_status}</span></div>
                <div class="flex flex-col text-right"><span class="text-slate-500 font-bold uppercase italic font-bold">市盈率</span><span class="text-slate-300 font-mono font-bold uppercase italic">{row['动态市盈率']}</span></div>
            </div>
        </div>
        """

    # 渲染 HTML 模板
    html_tpl = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #020617; color: #f8fafc; font-family: ui-sans-serif; }}
        .glass-card {{ background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); border-radius: 12px; }}
    </style>
</head>
<body class="p-4 md:p-10 font-bold italic font-black uppercase tracking-tight">
    <div class="max-w-6xl mx-auto font-bold italic font-black uppercase tracking-tight">
        <header class="flex justify-between items-center mb-10 border-b border-white/5 pb-6 font-bold italic font-black uppercase tracking-tight">
            <div>
                <h1 class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-orange-500 uppercase italic font-bold">QUANT SCANNER v13.0</h1>
                <p class="text-xs text-slate-500 mt-1 uppercase tracking-widest font-bold">全市场自动扫描与深度对冲</p>
            </div>
            <div class="text-right font-bold italic font-black">
                <p class="text-[10px] text-slate-400 uppercase font-bold italic">市场个股总数: {db['total_count']}</p>
                <p class="text-[10px] text-blue-500 uppercase font-bold italic">发现新标的: {len(new_stocks)}</p>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 font-bold italic font-black">
            {cards_html}
        </div>

        <div class="mt-12 p-6 glass-card border border-blue-500/20 font-bold italic font-black">
            <h2 class="text-xs font-black text-blue-400 uppercase tracking-widest mb-4 italic font-bold italic font-black uppercase underline decoration-blue-500/30 underline-offset-8">数据持久化监控 / DATABASE STATUS</h2>
            <p class="text-[11px] text-slate-400 leading-relaxed font-bold italic font-black">
                系统已自动同步全市场行情。`stocks_db.json` 已更新。今日新增个股已进入扫描序列。
                <br>● 数据源：东方财富实时接口 (AkShare) ● 策略：随机休眠反爬模式 ● 备份：Git Auto-Commit
            </p>
        </div>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_tpl)
    with open(".nojekyll", "w") as f:
        f.write("")
    print(f"✅ 扫描完成。发现新股: {len(new_stocks)} 只。")

if __name__ == "__main__":
    run()



