import akshare as ak
import pandas as pd
from datetime import datetime
import os

def fetch_market_sentiment():
    """Calculates market sentiment temperature based on A-share advance/decline ratio."""
    try:
        # Fetch real-time snapshot of all A-shares
        df = ak.stock_zh_a_spot_em()
        total_stocks = len(df)
        up_stocks = len(df[df['涨跌幅'] > 0])
        down_stocks = len(df[df['涨跌幅'] < 0])
        
        # Sentiment formula: (Up / Total) * 100
        temperature = (up_stocks / total_stocks) * 100 if total_stocks > 0 else 50
        return round(temperature, 2), up_stocks, down_stocks, total_stocks
    except Exception as e:
        print(f"Error fetching sentiment: {e}")
        return 50.0, 0, 0, 0

def get_index_data():
    """Fetches key index performance (SSE, SZSE, ChiNext)."""
    try:
        df_index = ak.stock_zh_index_spot_em()
        indices = {
            "上证指数": "000001",
            "深证成指": "399001",
            "创业板指": "399006"
        }
        report_data = []
        for name, code in indices.items():
            row = df_index[df_index['名称'] == name].iloc[0]
            report_data.append({
                "name": name,
                "price": row['最新价'],
                "change_pct": row['涨跌幅']
            })
        return report_data
    except Exception as e:
        print(f"Error fetching indices: {e}")
        return []

def generate_ai_insights(temp, indices):
    """Generates rule-based AI insights based on 2026 market themes."""
    # 2026 Themes: Anti-involution, AI Capex, and GDP 4.3% stability
    if temp > 70:
        mood = "极度亢奋 (Extreme Greed)"
        advice = "警惕短期回调，避免追高。当前市场情绪已触及情绪高位。"
    elif temp < 30:
        mood = "恐慌探底 (Fear)"
        advice = "分批布局优质蓝筹。2026年'反内卷'政策利好行业龙头利润修复。"
    else:
        mood = "中性震荡"
        advice = "持股观望，关注成交量变化。目前处于宽幅震荡区间。"

    insights = f"**当前市场情绪状态**: {mood}\n\n"
    insights += f"**2026 宏观背景分析**: \n"
    insights += "- 关注国内'反内卷'政策对制造行业毛利的修复进度。\n"
    insights += "- AI 算力基建（预计2026年投入超$700亿）仍是核心驱动力。\n\n"
    insights += f"**AI 操作建议**: {advice}"
    return insights

def create_report():
    temp, up, down, total = fetch_market_sentiment()
    indices = get_index_data()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"# 🚀 A股市场 9:25 开盘早报 ({now_str})\n\n"
    report += "## 🌡️ 市场情绪温度\n"
    report += f"**当前温度: {temp}℃**\n"
    report += f"- 🟢 上涨家数: {up} | 🔴 下跌家数: {down} | ⚪ 总数: {total}\n"
    report += f"- 情绪参考: < 25 (冰点期) | > 75 (过热期)\n\n"
    
    report += "## 📈 大盘核心指数\n"
    report += "| 指数名称 | 最新价 | 涨跌幅 |\n| :--- | :--- | :--- |\n"
    for idx in indices:
        report += f"| {idx['name']} | {idx['price']} | {idx['change_pct']}% |\n"
    
    report += "\n## 🤖 AI 智能分析与建议\n"
    report += generate_ai_insights(temp, indices)
    
    report += "\n\n---\n*数据来源: AKShare (开源金融数据库) | 分析引擎: Rule-based AI Engine 2026*"
    
    # Save to file
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Report generated successfully.")

if __name__ == "__main__":
    create_report()

