import os
import sys
import time
import random
import requests
from datetime import datetime, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- 核心环境检查 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 运行环境缺少 akshare 或 pandas，请检查 YAML 中的安装步骤。")
    sys.exit(1)

# --- 2026 工业级防封禁配置 ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]

class CircuitBreaker:
    """智能熔断器：连续失败后自动冷却，防止 IP 被永久封禁"""
    def __init__(self, fail_max=5, reset_time=300):
        self.fail_count = 0
        self.fail_max = fail_max
        self.reset_time = reset_time
        self.last_fail_time = None
        self.state = "CLOSED"

    def can_request(self):
        if self.state == "OPEN":
            if datetime.now() - self.last_fail_time > timedelta(seconds=self.reset_time):
                print("🟢 熔断冷却期结束，尝试恢复请求...")
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
            print(f"🔴 触发熔断保护！进入 {self.reset_time}s 冷却期...")

    def report_success(self):
        self.fail_count = 0
        self.state = "CLOSED"

cb = CircuitBreaker()

@retry(
    wait=wait_exponential(multiplier=2, min=4, max=30), # 指数退避重试
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: print(f"⏳ 连接波动，进行第 {rs.attempt_number} 次重试...")
)
def tenacity_fetch(func, *args, **kwargs):
    if not cb.can_request():
        raise Exception("熔断器开启中，跳过此请求")
    
    # 随机休眠模拟真人访问
    time.sleep(random.uniform(2, 5))
    
    try:
        res = func(*args, **kwargs)
        cb.report_success()
        return res
    except Exception as e:
        cb.report_fail()
        raise e

# --- 智能字段映射器 ---
def robust_mapping(df, field_dict):
    """自动匹配不同接口的列名，彻底消除 KeyError"""
    if df is None or df.empty:
        return df
    cols = df.columns.tolist()
    final_map = {}
    for standard_name, aliases in field_dict.items():
        for alias in aliases:
            if alias in cols:
                final_map[alias] = standard_name
                break
    return df.rename(columns=final_map)

# --- 数据采集模块 ---
def get_market_metrics():
    """获取增强行情：量比、换手率、PE、PB、市值"""
    FIELD_MAP = {
        'pct': ['涨跌幅', 'changepercent', '涨跌百分比', 'pct_change'],
        'price': ['最新价', 'trade', '最新'],
        'vol_ratio': ['量比', 'volume_ratio'],
        'turnover': ['换手率', 'turnoverratio'],
        'pe': ['市盈率-动态', 'per'],
        'pb': ['市净率', 'pb'],
        'total_cap': ['总市值', 'mktcap'],
        'float_cap': ['流通市值', 'nmc']
    }
    
    try:
        print("🔍 获取东财增强行情数据...")
        df = tenacity_fetch(ak.stock_zh_a_spot_em)
        df = robust_mapping(df, FIELD_MAP)
        return df, "东财源"
    except Exception as e:
        print(f"⚠️ 东财接口异常: {e}，自动降级至新浪备选源...")
        df = ak.stock_zh_a_spot() # 新浪保底源
        df = robust_mapping(df, FIELD_MAP)
        return df, "新浪源"

def get_chip_analysis(symbol="000001"):
    """筹码分布分析：获利比例、平均成本、集中度"""
    try:
        df = tenacity_fetch(ak.stock_cyq_em, symbol=symbol, adjust="qfq")
        if df is not None and not df.empty:
            last = df.iloc[-1]
            return {
                "profit": round(last.get("获利比例", 0), 2),
                "cost": round(last.get("平均成本", 0), 2),
                "conc": round(last.get("90筹码集中度", 0), 2)
            }
    except: return None

def get_realtime_news():
    """获取 2026 最新的百度财经快讯"""
    try:
        df = tenacity_fetch(ak.news_economic_baidu)
        # 返回字段对齐 [日期, 标题, 内容...]
        return df.head(5).values.tolist()
    except:
        return [["-", "实时快讯接口连接超时"]]

def send_push(content):
    """Server酱 (SCTP/Turbo) 多协议自动适配推送"""
    sckey = os.getenv("SCKEY")
    if not sckey:
        print("⚠️ 未配置 SCKEY，跳过消息推送。")
        return
    try:
        # SCTP (方糖07) 与旧版 Turbo 接口适配
        url = f"https://{sckey}.push.ft07.com/send" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com/{sckey}.send"
        res = requests.post(url, json={"title": "A股 AI 决策早报", "desp": content}, timeout=15)
        print(f"📡 推送响应: {res.text}")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

# --- 主运行引擎 ---
def run():
    now = datetime.now()
    print(f"🚀 工业级分析系统启动: {now}")
    
    # 1. 基础行情与多源容错
    df, source = get_market_metrics()
    
    # 2. 字段防御逻辑：确保 pct 列存在
    if 'pct' not in df.columns:
        df['pct'] = 0.0 # 兜底逻辑防止 KeyError
    df['pct'] = pd.to_numeric(df['pct'], errors='coerce').fillna(0)

    # 3. AI 量化决策模型
    up = len(df[df['pct'] > 0])
    total = len(df)
    score = round((up/total)*70 + 30, 1) if total > 0 else 50
    
    # 4. 深度筹码与新闻
    chips = get_chip_analysis("000001")
    news = get_realtime_news()
    
    # 5. 构建分析报告
    report = f"## 💎 A股 AI 工业级早报 ({now.strftime('%Y-%m-%d %H:%M')})\n\n"
    report += f"| 指标 | 实时数值 | 评估状态 |\n| :--- | :--- | :--- |\n"
    report += f"| **市场综合分** | **{score}** | {'偏多' if score > 60 else '偏空'} |\n"
    report += f"| 涨跌分布 | 🟢{up} / 🔴{total-up} | 赚钱效应 {round(up/total*100, 1)}% |\n"
    
    if chips:
        report += f"| **沪指筹码** | **获利 {chips['profit']}%** | 集中度 {chips['conc']}% |\n"
        report += f"| 平均成本 | {chips['cost']} | (指数参考) |\n"
    
    if 'turnover' in df.columns:
        report += f"| 全市换手 | {round(df['turnover'].mean(), 2)}% | {'活跃' if df['turnover'].mean() > 3 else '平淡'} |\n"
        
    report += f"| 数据源 | {source} | 正常 |\n\n"

    report += "#### 📰 全球财经实时快讯 (Baidu)\n"
    for n in news:
        # 百度快讯：[时间, 标题, ...]
        report += f"- **[{str(n[0])[-5:]}]** {str(n[1])[:55]}...\n"
    
    report += "\n#### 🎯 AI 策略量化建议\n"
    if chips and chips['profit'] > 85:
        report += "⚠️ **警惕风险**：获利盘处于极高位 (>85%)，显示筹码极度松动，谨防大幅波动。"
    elif chips and chips['profit'] < 15:
        report += "✅ **底部信号**：获利盘进入极低区间 (<15%)，历史经验显示为超跌反弹前兆。"
    else:
        report += "⚖️ **震荡博弈**：筹码分布均衡，换手率平稳。操作建议：维持 5 成仓位，动态跟随趋势。"

    # 输出与推送
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    send_push(report)
    print("✅ 自动化分析报表已生成并发送。")

if __name__ == "__main__":
    run()


