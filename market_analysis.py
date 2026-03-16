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
def robust_column_mapping(df, target_map):
    """
    智能映射不同数据源的列名，防止 KeyError
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
    if not cb.can_request():
        raise Exception("熔断器冷却中")
    time.sleep(random.uniform(2, 5))
    try:
        res = func(*args, **kwargs)
        cb.report_success()
        return res
    except Exception as e:
        cb.report_fail()
        raise e

# --- 核心数据接口 ---
def get_market_data():
    FIELD_MAP = {
        'code': ['代码', 'code', 'symbol'],
        'name': ['名称', 'name'],
        'price': ['最新价', 'trade', '最新'],
        'pct': ['涨跌幅', 'changepercent', '涨跌百分比'],
        'turnover': ['换手率', 'turnoverratio', '换手'],
        'vol_ratio': ['量比', 'volume_ratio']
    }
    try:
        df = tenacity_fetch(ak.stock_zh_a_spot_em)
        df = robust_column_mapping(df, FIELD_MAP)
        return df, "东财增强源"
    except:
        df = ak.stock_zh_a_spot()
        df = robust_column_mapping(df, FIELD_MAP)
        return df, "新浪基础源"

def get_chip_analysis(symbol="000001"):
    try:
        df = tenacity_fetch(ak.stock_cyq_em, symbol=symbol, adjust="qfq")
        if df is not None and not df.empty:
            L = df.iloc[-1]
            return {"profit": L.get("获利比例", 0), "conc": L.get("90筹码集中度", 0)}
    except: return None

def get_news_2026():
    """使用 2026 最新接口替代已下线的 js_news"""
    try:
        df = tenacity_fetch(ak.news_economic_baidu)
        return df.head(5).values.tolist()
    except:
        return [["-", "实时新闻通道拥堵"]]

def send_push(content):
    """修复 TypeError 与 变量名 Bug"""
    sckey = os.getenv("SCKEY")
    if not sckey:
        print("⚠️ 未配置 SCKEY，跳过推送。")
        return
    try:
        # 正确匹配 SCTP (Server酱3) 推送地址
        if sckey.startswith("sctp"):
            url = f"https://{sckey}.push.ft07.com/send"
        else:
            url = f"https://sctapi.ftqq.com/{sckey}.send"
            
        # 修正语法: 使用单层大括号 {} 定义字典
        payload = {"title": "A股 2026 AI 决策早报", "desp": content}
        res = requests.post(url, json=payload, timeout=15)
        print(f"📡 推送响应: {res.text}")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def run():
    now_dt = datetime.now()
    print(f"🚀 系统启动: {now_dt}")
    
    df, source = get_market_data()
    
    # 智能检查 pct 列
    if 'pct' not in df.columns:
        print(f"⚠️ 'pct' 列缺失，列名清单: {df.columns.tolist()}")
        df['pct'] = 0.0
    
    df['pct'] = pd.to_numeric(df['pct'], errors='coerce').fillna(0)
    up = len(df[df['pct'] > 0])
    total = len(df)
    score = round((up/total)*70 + 30, 1) if total > 0 else 50
    
    chips = get_chip_analysis("000001")
    news = get_news_2026()
    
    report = f"## 💎 A股 AI 工业级早报 ({now_dt.strftime('%Y-%m-%d %H:%M')})\n\n"
    report += f"| 指标 | 当前值 | 状态 |\n| :--- | :--- | :--- |\n"
    report += f"| **市场评分** | **{score}** | {'偏多' if score > 60 else '偏空'} |\n"
    report += f"| 涨跌分布 | 🟢{up} / 🔴{total-up} | 赚钱效应 {round(up/total*100, 1) if total>0 else 0}% |\n"
    
    if chips:
        report += f"| **沪指筹码** | **获利 {chips['profit']}%** | 集中度 {chips['conc']}% |\n"
    
    report += f"| 数据源 | {source} | 正常 |\n\n"

    report += "#### 📰 实时全球财经快讯\n"
    for n in news:
        report += f"- **[{str(n[0])[-5:]}]** {str(n[1])[:50]}...\n"
    
    report += "\n#### 🎯 AI 策略决策建议\n"
    if chips and chips['profit'] > 85:
        report += "⚠️ **高位风险**：获利盘 > 85%，谨防主力派发筹码。"
    elif chips and chips['profit'] < 15:
        report += "✅ **底部信号**：获利盘 < 15%，具备超跌反弹潜力。"
    else:
        report += "⚖️ **震荡整理**：建议维持中性仓位，关注开盘后量比变化。"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    send_push(report)
    print("✅ 任务完成。")

if __name__ == "__main__":
    run()



