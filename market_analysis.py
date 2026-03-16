import os
import sys
import time
import random
import requests
import traceback
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- 环境自检 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 核心依赖缺失，请检查 YAML 安装步骤。")
    sys.exit(1)

# --- 增强型网络会话 [2026 规范] ---
def get_robust_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Connection": "keep-alive"
    })
    return session

session = get_robust_session()

# --- 智能字段归一化 (解决 KeyError: 'pct') ---
def normalize_columns(df):
    """
    自适应识别不同接口返回的字段，统一映射为标准名称
    """
    if df is None or df.empty:
        return df
    
    col_map = {
        'pct': ['涨跌幅', 'changepercent', 'pct_change', '涨跌百分比', 'f3'],
        'price': ['最新价', 'trade', 'current_price', '最新', 'f2'],
        'code': ['代码', 'code', 'symbol', 'f12'],
        'name': ['名称', 'name', 'f14'],
        'turnover': ['换手率', 'turnoverratio', '换手', 'f8'],
        'vol_ratio': ['量比', 'volume_ratio', 'f10']
    }
    
    current_cols = df.columns.tolist()
    final_rename = {}
    
    for standard, candidates in col_map.items():
        for cand in candidates:
            if cand in current_cols:
                final_rename[cand] = standard
                break
    
    new_df = df.rename(columns=final_rename)
    # 强制转换数值类型
    if 'pct' in new_df.columns:
        new_df['pct'] = pd.to_numeric(new_df['pct'], errors='coerce').fillna(0)
    return new_df

# --- Tenacity 增强重试 ---
@retry(
    wait=wait_exponential(multiplier=2, min=5, max=60), # 增加等待时长
    stop=stop_after_attempt(5), # 增加重试次数
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: print(f"⏳ 网络波动 (RemoteDisconnected), 进行第 {rs.attempt_number} 次重试 (等待 {rs.upcoming_sleep}s)...")
)
def fetch_with_retry(func, *args, **kwargs):
    time.sleep(random.uniform(1, 3))
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"⚠️ 接口请求异常: {str(e)[:100]}")
        raise e

# --- 核心数据逻辑 ---
def get_market_metrics():
    """获取全市场行情并归一化"""
    try:
        print("🔍 正在通过东财源获取增强行情...")
        df = fetch_with_retry(ak.stock_zh_a_spot_em)
        df = normalize_columns(df)
        if 'pct' in df.columns:
            return df, "东财增强源"
        raise KeyError("无法识别涨跌幅列")
    except:
        print("⚠️ 东财源失效，切换至新浪备份源...")
        df = ak.stock_zh_a_spot()
        df = normalize_columns(df)
        return df, "新浪备份源"

def get_chip_data(symbol="000001"):
    """筹码分布深度分析"""
    try:
        df = fetch_with_retry(ak.stock_cyq_em, symbol=symbol, adjust="qfq")
        if df is not None and not df.empty:
            last = df.iloc[-1]
            return {"profit": last.get("获利比例", 0), "conc": last.get("90筹码集中度", 0)}
    except: return None

def get_news_v24():
    """彻底修复 AttributeError: 移除 js_news，改用 2026 稳定百度财经源"""
    try:
        # AKShare 1.18.40 推荐的新闻接口
        df = fetch_with_retry(ak.news_economic_baidu)
        return df.head(3).values.tolist() # 返回 [时间, 标题, 内容...]
    except:
        return [["-", "实时快讯获取失败，请关注盘面异动"]]

def send_push(content):
    """修复推送变量 Bug"""
    sckey = os.getenv("SCKEY")
    if not sckey: return
    try:
        url = f"https://{sckey}.push.ft07.com/send" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com/{sckey}.send"
        requests.post(url, json={"title": "A股 AI 决策终端 v2.4", "desp": content}, timeout=15)
        print("📡 Server酱推送已发出。")
    except: pass

def run():
    print(f"🚀 v2.4 工业级系统启动: {datetime.now()}")
    
    # 1. 获取行情并确保 pct 存在
    df, source = get_market_metrics()
    
    # 2. 深度分析
    chips = get_chip_data("000001")
    news = get_news_v24()
    
    # 3. 统计逻辑
    up_count = len(df[df['pct'] > 0])
    total_count = len(df)
    score = round((up_count/total_count)*70 + 30, 1) if total_count > 0 else 50
    
    # 4. 生成报告
    report = f"## 💎 A股 AI 工业级早报 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
    report += f"| 指标 | 当前值 | 状态 |\n| :--- | :--- | :--- |\n"
    report += f"| **市场评分** | **{score}** | {'多头活跃' if score > 60 else '空头占优'} |\n"
    report += f"| 涨跌分布 | 🟢{up_count} / 🔴{total_count - up_count} | 赚钱效应 {round(up_count/total_count*100, 1) if total_count>0 else 0}% |\n"
    
    if chips:
        report += f"| **沪指筹码** | **获利 {chips['profit']}%** | 集中度 {chips['conc']}% |\n"
    report += f"| 数据源 | {source} | 正常 |\n\n"

    report += "#### 📰 实时财经热点\n"
    for n in news:
        report += f"- **[{str(n[0])[-5:]}]** {str(n[1])[:55]}...\n"
    
    report += "\n#### 🎯 AI 策略量化建议\n"
    if chips and chips['profit'] > 85:
        report += "⚠️ **高位预警**：获利盘进入 85% 极高位区间，谨防开盘诱多回落。"
    elif chips and chips['profit'] < 15:
        report += "✅ **底部信号**：获利盘 < 15%，属于极度超跌，大盘具备较强反弹动能。"
    else:
        report += "⚖️ **中枢博弈**：筹码分布均衡，维持 5 成仓位滚动操作。"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    send_push(report)
    print("✅ 分析报表已就绪。")

if __name__ == "__main__":
    run()


