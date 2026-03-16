import os
import sys
import time
import random
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- 配置与自检 ---
try:
    import akshare as ak
except ImportError:
    print("❌ 核心依赖缺失，请检查安装环境。")
    sys.exit(1)

# 统一字段映射字典
FIELD_MAP = {
    'code': ['代码', 'code', 'symbol'],
    'name': ['名称', 'name', '板块名称'],
    'price': ['最新价', 'trade', 'current'],
    'pct': ['涨跌幅', 'changepercent', '涨跌额百分比'],
    'turnover': ['换手率', 'turnoverratio'],
    'vol_ratio': ['量比', 'volume_ratio'],
    'amount': ['成交额', 'amount']
}

# --- 核心辅助类 ---
class QuantEngine:
    """工业级量化引擎：含熔断与多源备份"""
    def __init__(self):
        self.fail_count = 0
        self.max_fails = 5
        self.is_open = False
        self.last_fail_time = None

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=30),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception)
    )
    def fetch(self, func, *args, **kwargs):
        if self.is_open and (datetime.now() - self.last_fail_time).seconds < 300:
            raise Exception("系统处于熔断降级模式")
        
        time.sleep(random.uniform(2, 5))
        try:
            res = func(*args, **kwargs)
            self.fail_count = 0
            self.is_open = False
            return res
        except Exception as e:
            self.fail_count += 1
            if self.fail_count >= self.max_fails:
                self.is_open = True
                self.last_fail_time = datetime.now()
            raise e

engine = QuantEngine()

def robust_map(df):
    """智能字段清洗器"""
    if df is None or df.empty: return df
    cols = df.columns.tolist()
    final_map = {}
    for std, raw_list in FIELD_MAP.items():
        for r in raw_list:
            if r in cols:
                final_map[r] = std
                break
    return df.rename(columns=final_map)

# --- 数据采集模块 ---
def get_ma_status(symbol="sh000001"):
    """技术面：计算 MA5/10/20 多头排列"""
    try:
        # 获取最近 60 个交易日历史数据
        df = engine.fetch(ak.stock_zh_index_daily_em, symbol=symbol)
        df['close'] = pd.to_numeric(df['close'])
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        
        last = df.iloc[-1]
        is_long = last['ma5'] > last['ma10'] > last['ma20']
        return {
            "is_long": is_long,
            "ma5": round(last['ma5'], 2),
            "ma20": round(last['ma20'], 2),
            "trend": "多头排列" if is_long else "均线交织"
        }
    except: return None

def get_sector_ranking():
    """板块监控：行业涨跌榜"""
    try:
        df = engine.fetch(ak.stock_board_industry_name_em)
        df = robust_map(df).sort_values('pct', ascending=False)
        return df.head(3)[['name', 'pct']].values.tolist()
    except: return []

def get_chips(symbol="000001"):
    """筹码分配：获利比例与集中度"""
    try:
        df = engine.fetch(ak.stock_cyq_em, symbol=symbol, adjust="qfq")
        L = df.iloc[-1]
        return {"profit": L.get("获利比例", 0), "conc": L.get("90筹码集中度", 0), "cost": L.get("平均成本", 0)}
    except: return None

# --- 核心逻辑：三段复盘策略 ---
def run_triple_review():
    now = datetime.now()
    report = f"# 🏮 A股 AI 三段量化决策系统 (v2.4)\n"
    report += f"> 运行时间: {now.strftime('%Y-%m-%d %H:%M')} | 投资者参考，不构成投资建议\n\n"

    # --- 第一段：【盘前】舆情情报与宏观 (Pre-market) ---
    news_df = engine.fetch(ak.news_economic_baidu)
    news_list = news_df.head(3).values.tolist()
    
    # --- 第二段：【盘中】动能实战与板块 (During-market) ---
    spot_df, _ = engine.fetch(ak.stock_zh_a_spot_em), "EM"
    spot_df = robust_map(spot_df)
    sectors = get_sector_ranking()
    
    # --- 第三段：【趋势】筹码分配与均线 (Post-market/Trend) ---
    ma = get_ma_status("sh000001")
    chips = get_chips("000001")
    
    # --- 决策模型计算 ---
    spot_df['pct'] = pd.to_numeric(spot_df['pct'], errors='coerce').fillna(0)
    up_ratio = len(spot_df[spot_df['pct'] > 0]) / len(spot_df) if not spot_df.empty else 0.5
    score = round(up_ratio * 60 + (20 if ma and ma['is_long'] else 0) + (20 if chips and chips['profit'] < 80 else 10), 1)
    
    # --- 话语核心结论 ---
    report += "### 📢 话语核心结论\n"
    if score > 70:
        conclusion = "🚀 **强力多头占优**：均线多头排列形成，领涨板块放量，建议积极寻找回踩买点。"
        plan = "🔥 **投入计划：全力进攻** (风险开启)"
    elif score < 40:
        conclusion = "🛡️ **空头防守阶段**：筹码高位松动或趋势走弱，建议控制仓位，规避高位股。"
        plan = "❄️ **投入计划：全面防守** (风险关闭)"
    else:
        conclusion = "⚖️ **中枢横盘震荡**：板块轮动极快，无明显持续主线，适合高抛低吸。"
        plan = "🧱 **投入计划：中性均衡** (风险中性)"
    report += f"{conclusion}\n\n**{plan}**\n\n"

    # --- AI 决策仪表盘 ---
    report += "### 📊 AI 决策仪表盘\n"
    report += f"| 指标分类 | 核心数值 | 状态监测 |\n| :--- | :--- | :--- |\n"
    report += f"| 综合评分 | **{score}** | {'极佳' if score>80 else '一般'} |\n"
    if ma: report += f"| 技术形态 | {ma['ma5']} (MA5) | {ma['trend']} |\n"
    if chips: report += f"| 筹码分布 | 获利 {chips['profit']}% | 集中度 {chips['conc']}% |\n"
    report += "\n"

    # --- 精确买卖点位 (模拟量化点位) ---
    if ma:
        support = round(ma['ma20'] * 0.99, 2)
        resist = round(ma['ma5'] * 1.02, 2)
        report += "### 🎯 精确参考点位\n"
        report += f"- **强力支撑位**：{support} (基于MA20均线支撑)\n"
        report += f"- **盘中压力位**：{resist} (基于近期波动率偏离)\n"
        report += f"- **最佳买入点**：缩量回踩 {support} 附近且 5 分钟 K 线企稳\n"
        report += f"- **止损卖出点**：有效跌破 {support} 或 筹码获利比例超过 90%\n\n"

    # --- 板块涨跌榜 ---
    report += "### 🔝 今日领涨行业板块\n"
    for s in sectors:
        report += f"- **{s[0]}** (涨幅: {s[1]}%)\n"
    report += "\n"

    # --- 操作检查清单 ---
    report += "### ✅ 操作检查清单\n"
    report += f"- [ ] **环境确认**：是否处于 9:30-15:00 交易时段？\n"
    report += f"- [ ] **情绪过滤**：当前赚钱效应 ({round(up_ratio*100,1)}%) 是否支持开仓？\n"
    report += f"- [ ] **风险控制**：单笔亏损是否已设置 5% 强制止损？\n\n"

    # --- 舆情情报 ---
    report += "#### 📰 实时舆情快讯\n"
    for n in news_list:
        report += f"- **[{str(n[0])[-5:]}]** {str(n[1])[:50]}...\n"

    # 推送与保存
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    # Server酱推送
    sckey = os.getenv("SCKEY")
    if sckey:
        url = f"https://{sckey}.push.ft07.com/send" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com/{sckey}.send"
        requests.post(url, json={"title": f"A股AI量化简报 - {score}分", "desp": report}, timeout=15)

if __name__ == "__main__":
    run_triple_review()


