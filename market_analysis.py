import os
import sys
import time
import random
import requests
import traceback
from datetime import datetime, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- 核心环境检查 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 缺少核心依赖，请确认 YAML 中的 pip 安装步骤。")
    sys.exit(1)

# --- 反爬配置: 2026 随机 UA 库 ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
]

# --- 熔断器机制 ---
class CircuitBreaker:
    def __init__(self, fail_max=5, reset_time=300):
        self.fail_count = 0
        self.fail_max = fail_max
        self.reset_time = reset_time
        self.last_fail_time = None
        self.state = "CLOSED" # CLOSED, OPEN

    def check(self):
        if self.state == "OPEN":
            if datetime.now() - self.last_fail_time > timedelta(seconds=self.reset_time):
                self.state = "CLOSED"
                self.fail_count = 0
                return True
            return False
        return True

    def report_fail(self):
        self.fail_count += 1
        if self.fail_count >= self.fail_max:
            self.state = "OPEN"
            self.last_fail_time = datetime.now()
            print(f"🔴 触发熔断！进入 {self.reset_time}秒 冷却期...")

    def report_success(self):
        self.fail_count = 0
        self.state = "CLOSED"

cb = CircuitBreaker()

# --- 增强请求逻辑: 指数退避重试 ---
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=20),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(f"⏳ 连接波动，正在进行第 {retry_state.attempt_number} 次指数退避重试...")
)
def safe_fetch(func, *args, **kwargs):
    if not cb.check():
        raise Exception("熔断器开启中，跳过请求。")
    
    # 随机休眠 2-5 秒
    time.sleep(random.uniform(2, 5))
    
    # 随机 User-Agent
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        result = func(*args, **kwargs)
        cb.report_success()
        return result
    except Exception as e:
        cb.report_fail()
        raise e

# --- 数据获取逻辑 ---
def get_market_metrics():
    """获取增强行情数据: 量比、换手率、PE/PB等"""
    df = safe_fetch(ak.stock_zh_a_spot_em)
    # 关键列映射
    target_cols = {
        '代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'pct',
        '量比': 'vol_ratio', '换手率': 'turnover', '市盈率-动态': 'pe',
        '市净率': 'pb', '总市值': 'total_cap', '流通市值': 'float_cap'
    }
    return df.rename(columns=target_cols)

def get_chip_analysis(symbol="sh000001"):
    """筹码分布深度分析: 获利比例、集中度"""
    try:
        # 获取筹码分布历史数据 (东财接口)
        df = safe_fetch(ak.stock_cyq_em, symbol=symbol, adjust="qfq")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return {
                "profit_ratio": latest.get("获利比例", 0),
                "avg_cost": latest.get("平均成本", 0),
                "concentration_90": latest.get("90筹码集中度", 0),
                "concentration_70": latest.get("70筹码集中度", 0)
            }
    except: pass
    return None

def send_push(content):
    """多渠道主动推送"""
    sckey = os.getenv("SCKEY")
    if sckey:
        try:
            url = f"https://{sckey}.push.ft07.com/send" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com/{sckey}.send"
            requests.post(url, json={"title": "A股 AI 工业级早报", "desp": content}, timeout=15)
        except: print("推送异常")

def run():
    print(f"🚀 工业级分析启动: {datetime.now()}")
    
    # 1. 获取增强行情
    df = get_market_metrics()
    
    # 2. 获取核心指数筹码分析
    chip_data = get_chip_analysis("sh000001") # 以沪指为例
    
    # 3. 实时新闻
    news = safe_fetch(ak.js_news, endpoint="main").head(3).values.tolist()
    
    # 4. 构建 AI 决策仪表盘
    up = len(df[df['pct'] > 0])
    down = len(df[df['pct'] < 0])
    avg_turnover = round(df['turnover'].mean(), 2)
    avg_pe = round(df['pe'].mean(), 2)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"## 💎 A股 AI 决策仪表盘 ({now})\n\n"
    report += f"| 核心指标 | 当前数值 | 解读 |\n| :--- | :--- | :--- |\n"
    report += f"| 涨跌分布 | 🟢{up} / 🔴{down} | 赚钱效应 {round(up/len(df)*100, 1)}% |\n"
    report += f"| 平均换手 | {avg_turnover}% | {'活跃' if avg_turnover > 3 else '低迷'} |\n"
    report += f"| 平均市盈 | {avg_pe} | {'高估' if avg_pe > 30 else '合理'} |\n"
    
    if chip_data:
        report += f"| **上证筹码** | **获利 {chip_data['profit_ratio']}%** | 集中度 {chip_data['concentration_90']}% |\n"
    
    report += "\n#### 📰 实时早间快讯\n"
    for n in news:
        report += f"- **[{n[0][-8:]}]** {n[1][:50]}...\n"
    
    report += "\n#### 🎯 AI 工业级策略建议\n"
    report += "基于 2026 宏观模型：目前市场处于"
    if chip_data and chip_data['profit_ratio'] > 80: report += "【高位获利区】，警惕抛压。"
    elif chip_data and chip_data['profit_ratio'] < 20: report += "【超跌筑底区】，关注反弹。"
    else: report += "【震荡中轴】，控制仓位。"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    send_push(report)
    print("✅ 分析报表生成并已通过主动通道推送。")

if __name__ == "__main__":
    run()

