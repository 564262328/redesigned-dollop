import sys
import traceback
from datetime import datetime

# --- 显式依赖检查器 (Dependency Checker) ---
required_modules = ["akshare", "pandas", "requests", "bs4", "lxml", "html5lib", "py_mini_racer"]
missing_modules = []

for mod in required_modules:
    try:
        __import__(mod)
        print(f"Check: {mod} ... OK")
    except ImportError:
        missing_modules.append(mod)

if missing_modules:
    print(f"\n❌ 关键依赖缺失: {', '.join(missing_modules)}")
    print("请确认您的 requirements.txt 已正确上传并包含这些库。")
    sys.exit(1)

import akshare as ak
import pandas as pd

def fetch_market_sentiment():
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
        print(f"Sentiment Error: {e}")
        return 50.0, 0, 0, 0

def get_index_data():
    try:
        df_index = ak.stock_zh_index_spot_em()
        indices = {"上证指数": "000001", "深证成指": "399001", "创业板指": "399006"}
        res = []
        for name in indices.keys():
            row = df_index[df_index['名称'] == name]
            if not row.empty:
                res.append({"name": name, "price": row.iloc[0]['最新价'], "change": row.iloc[0]['涨跌幅']})
        return res
    except Exception as e:
        print(f"Index Error: {e}")
        return []

def create_report():
    try:
        temp, up, down, total = fetch_market_sentiment()
        indices = get_index_data()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        report = f"# 🚀 A股开盘早报 ({now})\n\n"
        report += f"## 🌡️ 情绪温度: {temp}℃\n- 🟢 {up} | 🔴 {down} | ⚪ {total}\n\n"
        report += "## 📈 指数概览\n| 指数 | 价格 | 涨跌幅 |\n| :--- | :--- | :--- |\n"
        for i in indices:
            report += f"| {i['name']} | {i['price']} | {i['change']}% |\n"
            
        with open("report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("Done: Report generated.")
    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_report()

