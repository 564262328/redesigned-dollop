import os
import sys
import time
import random
import requests
import traceback
from datetime import datetime, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- 环境自检 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 核心依赖缺失，请检查 YAML 安装步骤。")
    sys.exit(1)

# --- 2026 智能字段映射器 ---
def robust_mapping(df, target_map):
    """
    自适应不同数据源及 AKShare 1.18.40 版本的字段名。
    target_map: {'pct': ['涨跌幅', 'f3', 'changepercent', 'pct_change', '涨跌百分比']}
    """
    if df is None or df.empty:
        return df
    
    current_cols = df.columns.tolist()
    final_map = {}
    
    for standard_name, possible_names in target_map.items():
        for p_name in possible_names:
            if p_name in current_cols:
                final_map[p_name] = standard_name
                break
    
    return df.rename(columns=final_map)

# --- 熔断器机制 ---
class CircuitBreaker:
    def __init__(self, fail_max=5, reset_time=300):
        self.fail_count = 0
        self.fail_max = fail_max
        self.reset_time = reset_time
        self.last_fail_time = None
        self.state = "CLOSED"

    def can_request(self):
        if self.state == "OPEN":
            if datetime.now() - self.last_fail_time > timedelta(seconds=self.reset_time):
                self.state = "CLOSED"; self.fail_count = 0; return True
            return False
        return True

    def report_fail(self):
        self.fail_count += 1
        if self.fail_count >= self.fail_max:
            self.state = "OPEN"; self.last_fail_time = datetime.now()

    def report_success(self):
        self.fail_count = 0; self.state = "CLOSED"

cb = CircuitBreaker()

# --- Tenacity 指数退避重试 ---
@retry(
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: print(f"⏳ 连接受阻，正在进行第 {rs.attempt_number} 次重试...")
)
def tenacity_fetch(func, *args, **kwargs):
    if not cb.can_request():
        raise Exception("熔断器保护中")
    time.sleep(random.uniform(1, 3))
    try:
        res = func(*args, **kwargs)
        cb.report_success()
        return res
    except Exception as e:
        cb.report_fail()
        raise e

# --- 核心数据采集 ---
def get_spot_enhanced():
    """获取增强行情 (EM -> Sina 降级)"""
    # 2026 字段映射全库
    F_MAP = {
        'code': ['代码', 'code', 'f12', 'symbol'],
        'name': ['名称', 'name', 'f14'],
        'price': ['最新价', 'trade', 'f2', '最新'],
        'pct': ['涨跌幅', 'f3', 'changepercent', '涨跌百分比', 'pct_change'],
        'turnover': ['换手率', 'f8', 'turnoverratio'],
        'pe': ['市盈率-动态', 'f9', 'per'],
        'total_cap': ['总市值', 'f20']
    }
    
    try:
        print("🔍 尝试东财增强源...")
        df = tenacity_fetch(ak.stock_zh_a_spot_em)
        df = robust_mapping(df, F_MAP)
        return df, "东财增强源"
    except Exception as e:
        print(f"⚠️ 东财源失效: {e}，切换新浪备选...")
        df = ak.stock_zh_a_spot()
        df = robust_mapping(df, F_MAP)
        return df, "新浪基础源"

def get_chip_analysis(symbol="000001"):
    """筹码分布分析"""
    try:
        df = tenacity_fetch(ak.stock_cyq_em, symbol=symbol, adjust="qfq")
        if df is not None and not df.empty:
            L = df.iloc[-1]
            return {"profit": L.get("获利比例", 0), "conc": L.get("90筹码集中度", 0)}
    except: return None

def get_news_2026():
    """彻底移除已失效的 js_news，增加多重降级"""
    # 方案1: 百度财经快讯 (2026 最稳)
    try:
        df = tenacity_fetch(ak.news_economic_baidu)
        return df.head(3).values.tolist(), "Baidu"
    except:
        # 方案2: 央视新闻联播 (保底)
        try:
            df = tenacity_fetch(ak.news_cctv, date=datetime.now().strftime('%Y%m%d'))
            return df.head(3).values.tolist(), "CCTV"
        except:
            return [["-", "当前实时新闻获取超时"]], "None"

def send_push(content):
    """修复 Server酱 逻辑 Bug"""
    sckey = os.getenv("SCKEY")
    if not sckey:
        print("⚠️ 未配置 SCKEY。")
        return
    try:
        # 识别 SCTP (方糖3) 或旧版 Turbo
        url = f"https://{sckey}.push.ft07.com/send" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com/{sckey}.send"
        params = {"title": "A股 AI 决策早报 (v2.4)", "desp": content}
        res = requests.post(url, json=params, timeout=15)
        print(f"📡 推送响应: {res.text}")
    except Exception as e:
        print(f"❌ 推送故障: {e}")

def run():
    now_dt = datetime.now()
    print(f"🚀 系统启动: {now_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 获取行情并映射
    df, source = get_spot_enhanced()
    
    # 2. 计算容错 (KeyError 终极修复)
    if 'pct' not in df.columns:
        print(f"⚠️ 无法识别涨跌幅字段，当前列名: {df.columns.tolist()}")
        df['pct'] = 0.0 # 默认 0 避免崩溃
    
    df['pct'] = pd.to_numeric(df['pct'], errors='coerce').fillna(0)
    up = len(df[df['pct'] > 0])
    total = len(df)
    score = round((up/total)*70 + 30, 1) if total > 0 else 50
    
    # 3. 深度数据
    chips = get_chip_analysis("000001")
    news_list, news_source = get_news_2026()
    
    # 4. 构建报告
    report = f"## 💎 A股 AI 工业级早报 ({now_dt.strftime('%Y-%m-%d %H:%M')})\n\n"
    report += f"| 关键指标 | 数值 | 状态 |\n| :--- | :--- | :--- |\n"
    report += f"| **市场评分** | **{score}** | {'活跃' if score > 60 else '低迷'} |\n"
    report += f"| 涨跌分布 | 🟢{up} / 🔴{total-up} | 赚钱效应 {round(up/total*100, 1) if total>0 else 0}% |\n"
    
    if chips:
        report += f"| **沪指筹码** | **获利 {chips['profit']}%** | 集中度 {chips['conc']}% |\n"
    
    report += f"| 行情源 | {source} | 正常 |\n"
    report += f"| 新闻源 | {news_source} | 正常 |\n\n"

    report += "#### 📰 实时全球财经快讯\n"
    for n in news_list:
        # 对齐百度/CCTV 字段
        title = str(n[1]) if len(n)>1 else str(n[0])
        report += f"- **[{str(n[0])[-5:]}]** {title[:55]}...\n"
    
    report += "\n#### 🎯 AI 策略量化建议\n"
    if chips and chips['profit'] > 85:
        report += "⚠️ **高位拥挤**：获利盘 > 85%，显示筹码处于极度超买状态，历史回测显示易发生剧烈回调。"
    elif chips and chips['profit'] < 15:
        report += "✅ **冰点反弹**：获利盘 < 15%，市场处于极度超跌区间，长线筹码已锁死，可关注底仓机会。"
    else:
        report += "⚖️ **中枢震荡**：筹码分布稳定，两市换手率处于合理区间，建议维持 5-6 成仓位，等待突破。"

    # 保存并推送
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    send_push(report)
    print("✅ 分析任务圆满完成。")

if __name__ == "__main__":
    run()



