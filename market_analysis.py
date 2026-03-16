import os
import sys
import time
import random
import requests
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
def robust_column_mapping(df, target_map):
    if df is None or df.empty: return df
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

# --- Tenacity 指数退避 ---
@retry(
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: print(f"⏳ 连接波动，进行第 {rs.attempt_number} 次重试...")
)
def tenacity_fetch(func, *args, **kwargs):
    if not cb.can_request(): raise Exception("熔断器保护中")
    time.sleep(random.uniform(2, 5))
    try:
        res = func(*args, **kwargs)
        cb.report_success()
        return res
    except Exception as e:
        cb.report_fail(); raise e

# --- 数据获取 ---
def get_market_data():
    FIELD_MAP = {
        'code': ['代码', 'code'], 'name': ['名称', 'name'],
        'price': ['最新价', 'trade'], 'pct': ['涨跌幅', 'changepercent'],
        'turnover': ['换手率', 'turnoverratio'], 'pe': ['市盈率-动态', 'pe']
    }
    try:
        df = tenacity_fetch(ak.stock_zh_a_spot_em)
        return robust_column_mapping(df, FIELD_MAP), "东财增强源"
    except:
        df = ak.stock_zh_a_spot()
        return robust_column_mapping(df, FIELD_MAP), "新浪基础源"

def get_news_2026():
    try:
        df = tenacity_fetch(ak.news_economic_baidu)
        return df.head(3).values.tolist()
    except: return [["-", "实时新闻通道拥堵"]]

def get_chip_analysis(symbol="000001"):
    try:
        df = tenacity_fetch(ak.stock_cyq_em, symbol=symbol, adjust="qfq")
        if df is not None and not df.empty:
            L = df.iloc[-1]
            return {"profit": L.get("获利比例", 0), "conc": L.get("90筹码集中度", 0)}
    except: return None

# --- 多渠道推送逻辑 ---
def send_bark(content):
    """Bark 推送 (iOS)"""
    bark_key = os.getenv("BARK_KEY")
    if not bark_key:
        print("⚠️ 未配置 BARK_KEY，跳过 iOS 推送。")
        return
    try:
        url = f"https://api.day.app/{bark_key}"
        # 配置 2026 常用参数：Markdown 支持、分组、铃声、中断级别
        params = {
            "title": "📈 A股 AI 决策早报",
            "body": content,
            "group": "StockAnalysis",
            "icon": "https://api.day.app",
            "sound": "minuet", # 可更换为 alarm, electronic 等
            "level": "active"  # 即使在勿扰模式下也可能提醒
        }
        res = requests.post(url, json=params, timeout=15)
        print(f"📡 Bark 响应: {res.text}")
    except Exception as e:
        print(f"❌ Bark 推送失败: {e}")

def send_serverchan(content):
    """Server酱推送 (微信)"""
    sckey = os.getenv("SCKEY")
    if not sckey: return
    try:
        url = f"https://{sckey}.push.ft07.com/send" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com/{sckey}.send"
        requests.post(url, json={"title": "A股 2026 AI 决策早报", "desp": content}, timeout=15)
    except: pass

def run():
    now = datetime.now()
    print(f"🚀 系统启动: {now}")
    
    df, source = get_market_data()
    chips = get_chip_analysis("000001")
    news = get_news_2026()
    
    df['pct'] = pd.to_numeric(df.get('pct', 0), errors='coerce').fillna(0)
    up = len(df[df['pct'] > 0])
    total = len(df)
    score = round((up/total)*70 + 30, 1) if total > 0 else 50
    
    report = f"## 💎 A股 AI 工业级早报 ({now.strftime('%m-%d %H:%M')})\n\n"
    report += f"| 指标 | 当前值 | 状态 |\n| :--- | :--- | :--- |\n"
    report += f"| **市场评分** | **{score}** | {'多头活跃' if score > 60 else '空头占优'} |\n"
    report += f"| 涨跌分布 | 🟢{up} / 🔴{total-up} | 赚钱效应 {round(up/total*100, 1)}% |\n"
    
    if chips:
        report += f"| **沪指筹码** | **获利 {chips['profit']}%** | 集中度 {chips['conc']}% |\n"
    
    report += f"| 数据源 | {source} | 正常 |\n\n"
    report += "#### 📰 实时全球财经快讯\n"
    for n in news:
        report += f"- **[{str(n[0])[-5:]}]** {str(n[1])[:50]}...\n"
    
    report += "\n#### 🎯 AI 策略决策建议\n"
    if chips and chips['profit'] > 85:
        report += "⚠️ **高位预警**：获利盘 > 85%，筹码极度浮躁，谨防冲高回落。"
    elif chips and chips['profit'] < 15:
        report += "✅ **底部信号**：获利盘 < 15%，属于极度超跌，长线资金可考虑入场。"
    else:
        report += "⚖️ **中枢博弈**：筹码分布均衡，建议关注 3300 点支撑表现。"

    # 执行推送
    send_bark(report)
    send_serverchan(report)
    
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("✅ 分析任务圆满完成。")

if __name__ == "__main__":
    run()


