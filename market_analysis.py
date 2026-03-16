import akshare as ak
import pandas as pd
from datetime import datetime
import traceback
import sys

def fetch_market_sentiment():
    """Calculates market sentiment with safety checks."""
    try:
        # Fetch real-time snapshot
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            print("Warning: stock_zh_a_spot_em returned empty data.")
            return 50.0, 0, 0, 0
            
        total_stocks = len(df)
        up_stocks = len(df[df['涨跌幅'] > 0])
        down_stocks = len(df[df['涨跌幅'] < 0])
        
        temperature = (up_stocks / total_stocks) * 100 if total_stocks > 0 else 50
        return round(temperature, 2), up_stocks, down_stocks, total_stocks
    except Exception as e:
        print(f"Error fetching sentiment: {e}")
        return 50.0, 0, 0, 0

def get_index_data():
    """Fetches index performance with individual error handling."""
    try:
        df_index = ak.stock_zh_index_spot_em()
        if df_index is None or df_index.empty:
            print("Warning: Index data is empty.")
            return []
            
        indices = {
            "上证指数": "000001",
            "深证成指": "399001",
            "创业板指": "399006"
        }
        report_data = []
        for name, code in indices.items():
            try:
                # Use flexible matching to avoid IndexError
                row_match = df_index[df_index['名称'] == name]
                if not row_match.empty:
                    row = row_match.iloc[0]
                    report_data.append({
                        "name": name,
                        "price": row['最新价'],
                        "change_pct": row['涨跌幅']
                    })
            except Exception as inner_e:
                print(f"Skipping index {name} due to: {inner_e}")
        return report_data
    except Exception as e:
        print(f"General Index Error: {e}")
        return []

def generate_ai_insights(temp):
    """Generates insights for 2026 market themes."""
    # 2026 Macro Context
    if temp > 75:
        mood, advice = "情绪过热", "策略：分批减仓，防范高位震荡风险。"
    elif temp < 25:
        mood, advice = "极度冰点", "策略：寻找低估值蓝筹，2026年反内卷政策将提升核心资产溢价。"
    else:
        mood, advice = "平稳运行", "策略：精选板块，关注 AI 算力与电力基建的协同效应。"

    insights = f"**市场氛围**: {mood}\n"
    insights += f"**2026 核心逻辑**: 随着国内 GDP 增速稳定在 4.3% 左右，市场正从'增量竞争'转向'存量优化'。\n"
    insights += f"**操作建议**: {advice}"
    return insights

def create_report():
    try:
        temp, up, down, total = fetch_market_sentiment()
        indices = get_index_data()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        report = f"# 🚀 A股市场 9:25 开盘早报 ({now_str})\n\n"
        report += "## 🌡️ 市场情绪温度\n"
        report += f"**当前温度: {temp}℃**\n"
        report += f"- 🟢 上涨: {up} | 🔴 下跌: {down} | ⚪ 总数: {total}\n\n"
        
        report += "## 📈 指数表现\n"
        if indices:
            report += "| 指数名称 | 最新价 | 涨跌幅 |\n| :--- | :--- | :--- |\n"
            for idx in indices:
                report += f"| {idx['name']} | {idx['price']} | {idx['change_pct']}% |\n"
        else:
            report += "*指数数据获取失败，请检查 API 连通性。*\n"
        
        report += "\n## 🤖 AI 智能分析\n"
        report += generate_ai_insights(temp)
        
        with open("report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("Success: report.md created.")
        
    except Exception:
        print("Critical Error during report generation:")
        traceback.print_exc() # This will show the exact line of failure in GH Actions logs
        sys.exit(1) # Signal failure to GitHub Actions

if __name__ == "__main__":
    create_report()

