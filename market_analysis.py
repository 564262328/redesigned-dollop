import os
import sys
import time
import random
import requests
import json
import traceback
from datetime import datetime, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- 环境自检 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 核心依赖缺失。")
    sys.exit(1)

# --- 字段自适应映射器 ---
def robust_mapping(df):
    """智能识别东财/新浪等不同源的字段名，防止 KeyError: 'pct'"""
    if df is None or df.empty: return df
    FIELD_MAP = {
        'code': ['代码', 'code', 'symbol'],
        'name': ['名称', 'name'],
        'price': ['最新价', 'trade', 'current_price'],
        'pct': ['涨跌幅', 'changepercent', '涨跌百分比', 'pct_change'],
        'turnover': ['换手率', 'turnoverratio', '换手'],
        'vol_ratio': ['量比', 'volume_ratio']
    }
    current_cols = df.columns.tolist()
    final_map = {}
    for std, choices in FIELD_MAP.items():
        for choice in choices:
            if choice in current_cols:
                final_map[choice] = std
                break
    return df.rename(columns=final_map)

# --- 熔断器 ---
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
                self.state = "CLOSED"; self.fail_count = 0
                return True
            return False
        return True

    def report_fail(self):
        self.fail_count += 1
        if self.fail_count >= self.fail_max:
            self.state = "OPEN"; self.last_fail_time = datetime.now()

    def report_success(self):
        self.fail_count = 0; self.state = "CLOSED"

cb = CircuitBreaker()

# --- Tenacity 指数退避 ---
@retry(
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: print(f"⏳ 连接波动，进行第 {rs.attempt_number} 次重试...")
)
def tenacity_fetch(func, *args, **kwargs):
    if not cb.can_request(): raise Exception("熔断保护中")
    time.sleep(random.uniform(2, 5))
    try:
        res = func(*args, **kwargs)
        cb.report_success()
        return res
    except Exception as e:
        cb.report_fail(); raise e

# --- 数据与推送逻辑 ---
def get_market_metrics():
    """获取增强行情"""
    try:
        df = tenacity_fetch(ak.stock_zh_a_spot_em)
        df = robust_mapping(df)
        return df, "东财增强源"
    except:
        df = ak.stock_zh_a_spot()
        df = robust_mapping(df)
        return df, "新浪保底源"

def get_news():
    """彻底移除 js_news，使用 2026 最稳新闻源"""
    try:
        # 使用百度财经接口替代已下线的 js_news
        df = tenacity_fetch(ak.news_economic_baidu)
        return df.head(3).values.tolist()
    except: return [["-", "新闻获取受限"]]

def create_github_issue(title, body):
    """【免费方案】利用 GitHub Issues 托管报告页面"""
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    if not token or not repo: return
    try:
        url = f"https://api.github.com/repos/{repo}/issues"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        res = requests.post(url, headers=headers, json={"title": title, "body": body}, timeout=15)
        if res.status_code == 201:
            print(f"✅ 免费报告页面已发布: {res.json()['html_url']}")
    except Exception as e: print(f"❌ 发布 Issue 失败: {e}")

def send_push(content):
    """Server酱推送逻辑"""
    sckey = os.getenv("SCKEY")
    if not sckey: return
    try:
        url = f"https://{sckey}.push.ft07.com/send" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com/{sckey}.send"
        requests.post(url, json={"title": "AI 早报推送", "desp": content}, timeout=15)
    except: pass

def run():
    now = datetime.now()
    print(f"🚀 系统启动: {now}")
    
    df, source = get_market_metrics()
    
    # 强制字段检查，防止 KeyError: 'pct'
    if 'pct' not in df.columns:
        print(f"⚠️ 字段映射异常，列名: {df.columns.tolist()}")
        df['pct'] = 0.0
    
    df['pct'] = pd.to_numeric(df['pct'], errors='coerce').fillna(0)
    up = len(df[df['pct'] > 0])
    total = len(df)
    score = round((up/total)*70 + 30, 1) if total > 0 else 50
    
    news = get_news()
    
    report = f"## 💎 A股 AI 工业级早报 ({now.strftime('%Y-%m-%d %H:%M')})\n\n"
    report += f"| 指标 | 数值 | 状态 |\n| :--- | :--- | :--- |\n"
    report += f"| **市场评分** | **{score}** | {'偏多' if score > 60 else '偏空'} |\n"
    report += f"| 涨跌统计 | 🟢{up} / 🔴{total-up} | 赚钱效应 {round(up/total*100, 1) if total>0 else 0}% |\n\n"
    
    report += "#### 📰 全球财经实时快讯\n"
    for n in news:
        report += f"- **[{str(n[0])[-5:]}]** {str(n[1])[:55]}...\n"
    
    report += "\n#### 🎯 AI 策略建议\n- 当前市场处于偏{'多' if score > 55 else '空'}状态，建议结合量比指标控制仓位。"

    # 执行发布
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    title = f"📈 每日市场分析报告 - {now.strftime('%Y-%m-%d')}"
    create_github_issue(title, report)
    send_push(report)
    print("✅ 全流程完成。")

if __name__ == "__main__":
    run()



