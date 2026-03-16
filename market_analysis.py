import os
import sys
import time
import random
import requests
import traceback
from datetime import datetime

# --- 核心依赖预检 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 环境异常，请确认 GitHub Actions 依赖安装步骤。")
    sys.exit(1)

def send_notification(content):
    """多渠道主动推送逻辑"""
    # 1. Telegram 推送
    tg_token = os.getenv("TELEGRAM_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat_id:
        url = f"https://api.telegram.org{tg_token}/sendMessage"
        requests.post(url, data={"chat_id": tg_chat_id, "text": content, "parse_mode": "Markdown"})

    # 2. 钉钉推送
    dd_token = os.getenv("DINGTALK_ACCESS_TOKEN")
    if dd_token:
        url = f"https://oapi.dingtalk.com{dd_token}"
        data = {"msgtype": "markdown", "markdown": {"title": "A股开盘早报", "text": content}}
        requests.post(url, json=data)

    # 3. Server酱 (微信推送)
    sckey = os.getenv("SCKEY")
    if sckey:
        url = f"https://sctapi.ftqq.com{sckey}.send"
        requests.post(url, data={"title": "A股开盘早报", "desp": content})

def fetch_a_share_spot():
    """三级行情源冗余机制"""
    # 1. 东财接口
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            return df, "东方财富"
    except: pass
    
    # 2. 新浪接口 (备份)
    try:
        df = ak.stock_zh_a_spot()
        if df is not None and not df.empty:
            df = df.rename(columns={'trade': '最新价', 'changepercent': '涨跌幅'})
            return df, "新浪财经"
    except: pass

    # 3. 腾讯接口 (备选)
    try:
        df = ak.stock_zh_a_spot_qq()
        if df is not None and not df.empty:
            return df, "腾讯财经"
    except: pass
    return None, None

def fetch_latest_news():
    """获取金十实时快讯"""
    try:
        df = ak.js_news(endpoint="main") # 获取主流快讯
        news_list = df.head(5)[['datetime', 'content']].values.tolist()
        return news_list
    except:
        return [["-", "无法获取实时新闻，请检查接口"]]

def calculate_dashboard(df_spot, df_index):
    """AI 决策仪表盘逻辑"""
    up = len(df_spot[df_spot['涨跌幅'] > 0])
    down = len(df_spot[df_spot['涨跌幅'] < 0])
    ratio = round((up / len(df_spot)) * 100, 2)
    
    # 简单的 AI 评分模型 (0-100)
    score = ratio * 0.6 + 40 # 基础分
    if ratio > 60: status, color = "极度乐观", "🚀"
    elif ratio < 40: status, color = "情绪低迷", "⚠️"
    else: status, color = "中性震荡", "⚖️"
    
    return score, status, color, up, down

def run():
    print(f"🚀 系统启动: {datetime.now()}")
    df_spot, source = fetch_a_share_spot()
    news = fetch_latest_news()
    
    if df_spot is None:
        sys.exit(1)

    df_index = ak.stock_zh_index_spot_em()
    score, status, color, up, down = calculate_dashboard(df_spot, df_index)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"### {color} A股 AI 决策仪表盘 ({now})\n\n"
    report += f"| 指标 | 当前值 | 状态 |\n| :--- | :--- | :--- |\n"
    report += f"| **市场评分** | **{score}** | {status} |\n"
    report += f"| 涨跌家数 | 🟢{up} / 🔴{down} | 占比 {round(up/(up+down)*100,1)}% |\n\n"
    
    report += "#### 📰 实时早间头条\n"
    for n in news:
        report += f"- **[{n[0][-8:]}]** {n[1][:60]}...\n"
    
    report += "\n#### 🎯 AI 策略建议\n"
    report += "基于 2026 年宏观环境，建议重点配置 AI 基础设施与高股息蓝筹。"
    if score > 70: report += "当前过热，建议分批减仓。"
    else: report += "维持定投计划，关注核心资产。"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    # 执行多渠道主动推送
    send_notification(report)
    print("✅ 报告已生成并发送推送。")

if __name__ == "__main__":
    run()


