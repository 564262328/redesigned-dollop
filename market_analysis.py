import sys
import traceback
from datetime import datetime

# --- 依赖项自检 (Dependency Self-Check) ---
# 2026 年 AKShare 核心运行环境需求
required = ["akshare", "pandas", "requests", "bs4", "lxml", "html5lib", "py_mini_racer"]
missing = []

for mod in required:
    try:
        __import__(mod)
    except ImportError:
        missing.append(mod)

if missing:
    print(f"❌ 运行失败！缺少必要组件: {', '.join(missing)}")
    print("提示：请检查 GitHub Actions 中的 'Install Dependencies' 步骤是否成功。")
    sys.exit(1)

import akshare as ak
import pandas as pd

def fetch_market_sentiment():
    """获取全市场涨跌家数，计算情绪温度。"""
    try:
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return 50.0, 0, 0, 0
        total = len(df)
        up = len(df[df['涨跌幅'] > 0])
        down = len(df[df['涨跌幅'] < 0])
        temp = (up / total) * 100 if total > 0 else 50
        return round(temp, 2), up, down, total
    except Exception as e:
        print(f"获取情绪失败: {e}")
        return 50.0, 0, 0, 0

def get_index_data():
    """获取核心指数表现。"""
    try:
        df_index = ak.stock_zh_index_spot_em()
        indices = {"上证指数": "000001", "深证成指": "399001", "创业板指": "399006"}
        res = []
        for name in indices.keys():
            row = df_index[df_index['名称'] == name]
            if not row.empty:
                res.append({
                    "name": name, 
                    "price": row.iloc[0]['最新价'], 
                    "change": row.iloc[0]['涨跌幅']
                })
        return res
    except Exception as e:
        print(f"获取指数失败: {e}")
        return []

def create_report():
    """生成并保存报告文件。"""
    try:
        temp, up, down, total = fetch_market_sentiment()
        indices = get_index_data()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        report = f"# 🚀 A股开盘早报 ({now})\n\n"
        report += f"## 🌡️ 情绪温度: {temp}℃\n"
        report += f"- 🟢 上涨: {up} | 🔴 下跌: {down} | ⚪ 总数: {total}\n\n"
        
        report += "## 📈 指数概览\n"
        report += "| 指数 | 最新价 | 涨跌幅 |\n| :--- | :--- | :--- |\n"
        for i in indices:
            report += f"| {i['name']} | {i['price']} | {i['change']}% |\n"
        
        report += "\n## 🤖 AI 简评 (2026 版)\n"
        if temp < 30:
            report += "市场处于超卖区间。2026 年政策导向聚焦核心资产，建议关注'反内卷'受益行业。"
        else:
            report += "市场情绪平稳。建议关注 AI 基础设施与算力板块的持续性。"

        with open("report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("✅ 报告生成成功: report.md")
    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_report()

