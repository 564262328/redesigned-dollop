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
    print("❌ 缺失核心依赖。")
    sys.exit(1)

# --- 2026 随机浏览器指纹库 ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]

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

    def report_success(self):
        self.fail_count = 0
        self.state = "CLOSED"

cb = CircuitBreaker()

# --- Tenacity 指数退避重试 ---
@retry(
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: print(f"⏳ 连接波动，进行第 {rs.attempt_number} 次重试...")
)
def tenacity_fetch(func, *args, **kwargs):
    if not cb.can_request():
        raise Exception("熔断器保护中")
    time.sleep(random.uniform(2, 5))
    try:
        res = func(*args, **kwargs)
        cb.report_success()
        return res
    except Exception as e:
        cb.report_fail()
        raise e

# --- 数据接口适配 ---
def get_spot_data():
    """获取量比、换手、市值等"""
    try:
        df = tenacity_fetch(ak.stock_zh_a_spot_em)
        mapping = {
            '代码': 'code', '名称': 'name', '最新价': 'price', '涨跌幅': 'pct',
            '量比': 'vol_ratio', '换手率': 'turnover', '市盈率-动态': 'pe',
            '总市值': 'total_cap'
        }
        return df.rename(columns=mapping), "东财增强源"
    except:
        df = ak.stock_zh_a_spot()
        return df.rename(columns={'trade': 'price', 'changepercent': 'pct'}), "新浪基础源"

def get_chip_info(symbol="000001"):
    """筹码分布深度分析"""
    try:
        df = tenacity_fetch(ak.stock_cyq_em, symbol=symbol, adjust="qfq")
        if df is not None and not df.empty:
            L = df.iloc[-1]
            return {"profit": L.get("获利比例", 0), "conc": L.get("90筹码集中度", 0)}
    except: return None

def get_news_2026():
    """修复 AttributeError: 使用 2026 最新财经新闻接口"""
    try:
        # 百度财经全球快讯：2026年最稳接口
        df = tenacity_fetch(ak.news_economic_baidu)
        # 提取前3条，确保字段对齐
        return df.head(3).values.tolist()
    except Exception as e:
        print(f"⚠️ 新闻获取失败: {e}")
        return [["-", "实时新闻获取超时"]]

def send_push(content):
    """修复推送 Bug & 增加响应日志"""
    key = os.getenv("SCKEY")
    if not key:
        print("⚠️ 未检测到 SCKEY，跳过推送。")
        return
    try:
        # 自动切换 SCTP (Server酱3) 或 Turbo 地址
        if key.startswith("sctp"):
            url = f"https://{key}.push.ft07.com/send"
        else:
            url = f"https://sctapi.ftqq.com/{key}.send"
            
        params = {"title": "A股 AI 工业级早报", "desp": content}
        res = requests.post(url, json=params, timeout=15)
        print(f"📡 Server酱 响应: {res.text}")
    except Exception as e:
        print(f"❌ 推送异常: {e}")

def run():
    now = datetime.now()
    print(f"🚀 工业级系统启动: {now}")
    
    df, source = get_spot_data()
    chips = get_chip_info("000001")
    news = get_news_2026()
    
    up = len(df[df['pct'] > 0])
    total = len(df)
    score = round((up/total)*70 + 30, 1) if total > 0 else 50
    
    report = f"## 💎 A股 AI 决策仪表盘 ({now.strftime('%Y-%m-%d %H:%M')})\n\n"
    report += f"| 指标 | 数值 | 状态 |\n| :--- | :--- | :--- |\n"
    report += f"| **市场评分** | **{score}** | {'偏多' if score > 60 else '偏空'} |\n"
    report += f"| 涨跌分布 | 🟢{up} / 🔴{total-up} | 赚钱效应 {round(up/total*100, 1)}% |\n"
    
    if chips:
        report += f"| **上证筹码** | **获利 {chips['profit']}%** | 集中度 {chips['conc']}% |\n"
        
    report += f"| 数据源 | {source} | 正常 |\n\n"

    report += "#### 📰 实时全球财经快讯\n"
    for n in news:
        # 百度新闻接口字段通常为 [时间, 标题, 内容...]
        report += f"- **[{str(n[0])[-5:]}]** {str(n[1])[:50]}...\n"
    
    report += "\n#### 🎯 AI 策略建议\n"
    if chips and chips['profit'] > 85:
        report += "⚠️ **高位预警**：获利盘 > 85%，筹码极度松动，谨防开盘杀跌。"
    elif chips and chips['profit'] < 15:
        report += "✅ **冰点信号**：获利盘 < 15%，历史超跌区间，可关注分批建仓机会。"
    else:
        report += "⚖️ **震荡博弈**：筹码分布正常，换手率平稳，建议维持 5 成仓位。"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    send_push(report)
    print("✅ 分析完成。")

if __name__ == "__main__":
    run()

