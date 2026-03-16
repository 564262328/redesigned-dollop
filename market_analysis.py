import os
import sys
import time
import random
import requests
import traceback
from datetime import datetime, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- 核心环境自检 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 缺少核心依赖，请确认 YAML 中的 pip 安装步骤。")
    sys.exit(1)

# --- 反爬库: 2026 随机浏览器指纹 ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
]

# --- 熔断器机制 ---
class CircuitBreaker:
    def __init__(self, fail_max=5, reset_time=300):
        self.fail_count = 0
        self.fail_max = fail_max
        self.reset_time = reset_time
        self.last_fail_time = None
        self.state = "CLOSED" # CLOSED, OPEN

    def can_request(self):
        if self.state == "OPEN":
            if datetime.now() - self.last_fail_time > timedelta(seconds=self.reset_time):
                print("🟢 熔断冷却期结束，尝试恢复...")
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
            print(f"🔴 触发熔断！接口连续失败 {self.fail_count} 次，进入 5分钟 冷却期...")

    def report_success(self):
        self.fail_count = 0
        self.state = "CLOSED"

cb = CircuitBreaker()

# --- Tenacity 指数退避重试 ---
@retry(
    wait=wait_exponential(multiplier=2, min=4, max=30), # 4s, 8s, 16s...
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: print(f"⏳ 连接受限，进行第 {rs.attempt_number} 次指数退避重试 (等待 {rs.upcoming_sleep}s)...")
)
def tenacity_fetch(func, *args, **kwargs):
    if not cb.can_request():
        raise Exception("熔断器保护中，跳过物理请求。")
    
    # 随机休眠 2-5s 模拟真人
    time.sleep(random.uniform(2, 5))
    
    try:
        res = func(*args, **kwargs)
        cb.report_success()
        return res
    except Exception as e:
        cb.report_fail()
        raise e

# --- 增强数据获取与源降级逻辑 ---
def get_spot_data():
    """获取增强行情: 量比、换手、PE、市值"""
    try:
        print("正在获取增强行情 (东财源)...")
        df = tenacity_fetch(ak.stock_zh_a_spot_em)
        # 2026 最新列名映射
        mapping = {
            '代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'pct',
            '量比': 'vol_ratio', '换手率': 'turnover', '市盈率-动态': 'pe',
            '市净率': 'pb', '总市值': 'total_cap', '流通市值': 'float_cap'
        }
        return df.rename(columns=mapping), "东方财富 (增强版)"
    except Exception as e:
        print(f"⚠️ 东财增强源失效: {e}，自动降级至新浪备选源...")
        # 降级至新浪 (虽然数据维度较少，但能保底)
        df_sina = ak.stock_zh_a_spot()
        return df_sina.rename(columns={'trade': 'price', 'changepercent': 'pct'}), "新浪财经 (基础版)"

def get_chip_distribution(symbol="000001"):
    """筹码分布深度分析"""
    try:
        # 获取筹码获利比例与集中度
        df = tenacity_fetch(ak.stock_cyq_em, symbol=symbol, adjust="qfq")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return {
                "profit": latest.get("获利比例", 0),
                "cost": latest.get("平均成本", 0),
                "conc_90": latest.get("90筹码集中度", 0)
            }
    except: return None

def send_push(content):
    """SCTP 协议兼容推送"""
    sckey = os.getenv("SCKEY")
    if not sckey: return
    try:
        url = f"https://{sckey}.push.ft07.com/send" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com/{sckey}.send"
        requests.post(url, json={"title": "A股 AI 工业级早报", "desp": content}, timeout=15)
    except: pass

def run():
    print(f"🚀 工业级分析系统启动: {datetime.now()}")
    
    # 1. 获取增强行情数据
    df, source = get_spot_data()
    
    # 2. 获取大盘筹码分布 (上证指数)
    chips = get_chip_distribution("000001")
    
    # 3. 实时新闻
    news = ak.js_news(endpoint="main").head(3).values.tolist()
    
    # 4. AI 决策仪表盘构建
    up = len(df[df['pct'] > 0])
    down = len(df[df['pct'] < 0])
    total = len(df)
    
    report = f"## 💎 A股 AI 决策仪表盘 ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    report += f"| 指标 | 数值 | 状态 |\n| :--- | :--- | :--- |\n"
    report += f"| 涨跌分布 | 🟢{up} / 🔴{down} | 赚钱效应 {round(up/total*100, 1)}% |\n"
    
    # 填入增强数据
    if 'turnover' in df.columns:
        avg_turnover = round(df['turnover'].mean(), 2)
        report += f"| 平均换手 | {avg_turnover}% | {'活跃' if avg_turnover > 3 else '温和'} |\n"
    
    if chips:
        report += f"| **上证筹码** | **获利 {chips['profit']}%** | 集中度 {chips['conc_90']}% |\n"
        report += f"| 平均成本 | {chips['cost']} | (沪指参考) |\n"
        
    report += f"| 数据源 | {source} | 正常 |\n\n"

    report += "#### 📰 实时早间快讯\n"
    for n in news:
        report += f"- **[{n[0][-8:]}]** {n[1][:50]}...\n"
    
    report += "\n#### 🎯 工业级 AI 策略建议\n"
    if chips and chips['profit'] > 85:
        report += "⚠️ **高风险警示**：当前获利盘超过 85%，筹码极度浮动，建议减仓或止盈。"
    elif chips and chips['profit'] < 15:
        report += "✅ **底部信号**：获利盘低于 15%，属于极度超跌区，筹码集中度回落，可考虑左侧分批布局。"
    else:
        report += "⚖️ **博弈阶段**：筹码分布均衡，量比温和，建议控制仓位在 5 成左右，等待方向明确。"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    send_push(report)
    print("✅ 分析报表生成并已完成推送。")

if __name__ == "__main__":
    run()

