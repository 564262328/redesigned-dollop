import os
import sys
import time
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- 环境自检 ---
try:
    import akshare as ak
except ImportError:
    print("❌ 依赖缺失，请检查 YAML 文件。")
    sys.exit(1)

# --- 2026 智能字段映射器 ---
def smart_rename(df):
    """自适应不同源的列名，彻底解决 KeyError"""
    if df is None or df.empty: return df
    mapping = {
        '涨跌幅': 'pct', 'changepercent': 'pct', '涨跌百分比': 'pct',
        '最新价': 'price', 'trade': 'price', '最新': 'price',
        '名称': 'name', '代码': 'code', 'symbol': 'code'
    }
    current_map = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=current_map)

# --- 熔断器机制 ---
class CircuitBreaker:
    def __init__(self, fail_max=5, reset_time=300):
        self.fail_count, self.fail_max = 0, fail_max
        self.reset_time, self.last_fail_time = reset_time, None
        self.state = "CLOSED"

    def can_request(self):
        if self.state == "OPEN":
            if datetime.now() - self.last_fail_time > timedelta(seconds=self.reset_time):
                self.state, self.fail_count = "CLOSED", 0
                return True
            return False
        return True

    def report_fail(self):
        self.fail_count += 1
        if self.fail_count >= self.fail_max:
            self.state, self.last_fail_time = "OPEN", datetime.now()

cb = CircuitBreaker()

# --- Tenacity 指数退避 ---
@retry(
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: print(f"⏳ 接口波动，正在重试第 {rs.attempt_number} 次...")
)
def tenacity_fetch(func, *args, **kwargs):
    if not cb.can_request(): raise Exception("熔断保护中")
    time.sleep(random.uniform(2, 4))
    try:
        res = func(*args, **kwargs)
        cb.fail_count = 0
        return res
    except Exception as e:
        cb.report_fail()
        raise e

# --- 数据分析模块 ---
def get_market_data():
    """多维度行情抓取"""
    # 1. 基础行情
    try:
        df = tenacity_fetch(ak.stock_zh_a_spot_em)
        df = smart_rename(df)
        source = "东财增强源"
    except:
        df = ak.stock_zh_a_spot()
        df = smart_rename(df)
        source = "新浪基础源"
    
    # 2. 行业板块
    sectors = None
    try:
        sectors = tenacity_fetch(ak.stock_board_industry_name_em)
    except: pass

    # 3. 实时新闻
    news = []
    try:
        news_df = tenacity_fetch(ak.news_economic_baidu)
        news = news_df.head(3).values.tolist()
    except: pass

    return df, sectors, news, source

def create_sentiment_bar(ratio):
    """创建可视化的多空对比条"""
    length = 15
    up_len = int(ratio * length)
    down_len = length - up_len
    return f"🟢{'█' * up_len}{'░' * down_len}🔴"

def send_push(content):
    """工业级推送"""
    sckey = os.getenv("SCKEY")
    if not sckey: return
    try:
        url = f"https://{sckey}.push.ft07.com/send" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com/{sckey}.send"
        requests.post(url, json={"title": "📊 A股 AI 决策仪表盘", "desp": content}, timeout=15)
        print("✅ 推送成功")
    except Exception as e: print(f"❌ 推送异常: {e}")

def run():
    now = datetime.now()
    print(f"🚀 仪表盘系统启动: {now}")
    
    df, sectors, news, source = get_market_data()
    
    # 字段清洗
    df['pct'] = pd.to_numeric(df.get('pct', 0), errors='coerce').fillna(0)
    
    # 指标计算
    total_count = len(df)
    up_count = len(df[df['pct'] > 0])
    down_count = total_count - up_count
    up_ratio = up_count / total_count if total_count > 0 else 0.5
    market_score = round(up_ratio * 100, 1)
    
    # 构造 Markdown 报告
    report = f"# 📊 A股 AI 决策仪表盘\n"
    report += f"> **更新时间**: {now.strftime('%Y-%m-%d %H:%M')} | **数据源**: {source}\n\n"
    
    report += f"### 🌡️ 市场热度分析\n"
    report += f"**综合评分**: `{market_score}` / 100\n"
    report += f"**多空对比**: {create_sentiment_bar(up_ratio)}\n"
    report += f"- 🟢 上涨家数: **{up_count}**\n"
    report += f"- 🔴 下跌家数: **{down_count}**\n"
    report += f"- 📈 赚钱效应: **{round(up_ratio*100, 1)}%**\n\n"
    
    if sectors is not None and not sectors.empty:
        report += f"### 🏆 行业领涨榜 (TOP 3)\n"
        # 假设字段名为 '板块名称', '涨跌幅'
        sectors_sorted = sectors.sort_values(by='涨跌幅', ascending=False).head(3)
        for _, row in sectors_sorted.iterrows():
            report += f"- **{row['板块名称']}**: `{row['涨跌幅']}%` (领涨: {row['领涨股票']})\n"
        report += "\n"

    report += f"### 📰 全球实时快讯\n"
    if news:
        for n in news:
            report += f"- 🕒 **{str(n[0])[-5:]}** | {str(n[1])[:45]}...\n"
    else:
        report += "- ⚠️ 实时新闻通道暂时拥堵\n"
    
    report += f"\n---\n"
    report += f"### 🎯 AI 策略建议\n"
    if market_score > 65:
        report += "✅ **多头爆发**: 赚钱效应极佳，建议持股待涨，关注成交量是否持续放大。"
    elif market_score < 35:
        report += "💀 **冰点时刻**: 市场极度低迷，历史经验显示此时不宜杀跌，建议等待企稳。"
    else:
        report += "⚖️ **中位震荡**: 多空力量均衡，建议执行 5 成仓位策略，关注 3350 点支撑位。"

    # 输出 Summary 并推送
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    send_push(report)
    print("✅ 分析报表已生成。")
        # ... (Keep all your existing data fetching and report logic) ...

if __name__ == "__main__":
  def run():
    now = datetime.now()
    report = ""
    html_template = ""
    
    try:
        print(f"🚀 Starting Analysis: {now}")
        df, sectors, news, source = get_market_data()
        
        # ... [Your existing report generation logic here] ...
        # (Make sure 'report' and 'html_template' variables are fully built)
        
        # --- NEW: Safe HTML conversion logic ---
        html_content = report.replace('# ', '<h1>').replace('### ', '<h3>').replace('**', '<b>').replace('\n', '<br>')
        html_template = f"<html><body style='font-family:sans-serif;padding:20px;'>{html_content}</body></html>"

    except Exception as e:
        error_msg = f"❌ Analysis Failed at {now}: {str(e)}"
        print(error_msg)
        report = f"# ⚠️ Market Analysis Error\n\n{error_msg}"
        html_template = f"<html><body><h1>Error</h1><p>{error_msg}</p></body></html>"

    # --- CRITICAL: Always write files to avoid 'cat' error ---
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print("✅ Process complete. Files saved.")

# IMPORTANT: Ensure this is at the VERY BOTTOM of the file with NO indentation
if __name__ == "__main__":
    run()

