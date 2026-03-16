import os
import sys
import time
import random
import requests
import traceback
from datetime import datetime

# --- 核心环境检查 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 运行环境缺少依赖项，请检查 GitHub Actions 的 pip 安装步骤。")
    sys.exit(1)

def send_push(content):
    """多渠道主动推送逻辑"""
    # 1. Telegram 推送
    tg_token = os.getenv("TELEGRAM_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat_id:
        try:
            url = f"https://api.telegram.org{tg_token}/sendMessage"
            requests.post(url, data={"chat_id": tg_chat_id, "text": content, "parse_mode": "Markdown"}, timeout=10)
        except: print("TG 推送失败")

    # 2. 钉钉推送
    dd_token = os.getenv("DINGTALK_ACCESS_TOKEN")
    if dd_token:
        try:
            url = f"https://oapi.dingtalk.com{dd_token}"
            data = {"msgtype": "markdown", "markdown": {"title": "A股分析早报", "text": content}}
            requests.post(url, json=data, timeout=10)
        except: print("钉钉推送失败")

    # 3. Server酱 (微信通知)
    sckey = os.getenv("SCKEY")
    if sckey:
        try:
            url = f"https://sctapi.ftqq.com{sckey}.send"
            requests.post(url, data={"title": "A股分析早报", "desp": content}, timeout=10)
        except: print("Server酱推送失败")

def fetch_market_data():
    """三级行情源切换，彻底解决 RemoteDisconnected 问题"""
    # 方案 A: 东方财富
    try:
        print("尝试从东方财富获取行情...")
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            return df, "东方财富"
    except Exception as e:
        print(f"东财连接中断: {e}")

    time.sleep(random.uniform(1, 2))

    # 方案 B: 新浪财经
    try:
        print("尝试从新浪财经获取行情...")
        df = ak.stock_zh_a_spot() # 修正接口名
        if df is not None and not df.empty:
            df = df.rename(columns={'trade': '最新价', 'changepercent': '涨跌幅'})
            return df, "新浪财经"
    except Exception as e:
        print(f"新浪连接中断: {e}")

    # 方案 C: 腾讯财经
    try:
        print("尝试从腾讯财经获取行情...")
        df = ak.stock_zh_a_spot_qq()
        if df is not None and not df.empty:
            return df, "腾讯财经"
    except: pass
    
    return None, None

def get_live_news():
    """获取金十实时新闻快讯"""
    try:
        df = ak.js_news(endpoint="main")
        return df.head(5)[['datetime', 'content']].values.tolist()
    except:
        return [["-", "实时新闻获取受限"]]

def analyze_and_score(df_spot):
    """AI 决策仪表盘逻辑"""
    total = len(df_spot)
    up = len(df_spot[df_spot['涨跌幅'] > 0])
    down = len(df_spot[df_spot['涨跌幅'] < 0])
    up_ratio = (up / total) * 100 if total > 0 else 50
    
    # 简单的 AI 评分逻辑
    score = round(up_ratio * 0.7 + 30, 1)
    if up_ratio > 65: status, icon = "极其强劲", "🔥"
    elif up_ratio < 35: status, icon = "情绪恐慌", "❄️"
    else: status, icon = "多空博弈", "⚖️"
    
    return score, status, icon, up, down, total

def run():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"🚀 系统启动: {now_str}")
    
    df_spot, source = fetch_market_data()
    if df_spot is None:
        print("❌ 无法获取行情数据，系统退出。")
        sys.exit(1)

    score, status, icon, up, down, total = analyze_and_score(df_spot)
    news = get_live_news()
    
    # 构建 Markdown 报告
    report = f"## {icon} A股 AI 决策仪表盘 ({now_str})\n\n"
    report += f"| 指标 | 数值 | 状态 |\n| :--- | :--- | :--- |\n"
    report += f"| **市场评分** | **{score}** | {status} |\n"
    report += f"| 涨跌分布 | 🟢{up} / 🔴{down} | 赚钱效应 {round(up/total*100, 1)}% |\n"
    report += f"| 行情来源 | {source} | 正常 |\n\n"
    
    report += "#### 📰 实时早间快讯\n"
    for item in news:
        report += f"- **[{item[0][-8:]}]** {item[1][:60]}...\n"
    
    report += "\n#### 🎯 AI 投资建议 (2026版)\n"
    if score > 75:
        report += "当前情绪亢奋，建议分批锁定利润，关注科技成长股。"
    elif score < 35:
        report += "市场极度悲观，可分批布局高股息蓝筹或核心指数 ETF。"
    else:
        report += "震荡市操作难度大，建议轻仓观望，等待放量信号。"

    # 保存报告
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    # 主动推送
    send_push(report)
    print("✅ 分析完成，报告已发送推送。")

if __name__ == "__main__":
    run()


