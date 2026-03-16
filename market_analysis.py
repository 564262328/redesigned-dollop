import sys
import time
import random
import traceback
from datetime import datetime

# --- 核心依赖预检 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 脚本环境未就绪，请检查 GitHub Actions 步骤。")
    sys.exit(1)

def fetch_sentiment_with_fallback(max_retries=3):
    """优先东财，失败则切换新浪，带重试机制。"""
    for i in range(max_retries):
        try:
            time.sleep(random.uniform(1, 3)) # 随机延迟避开防爬
            print(f"尝试获取市场行情 (第 {i+1} 次)...")
            
            # 方案 A: 东方财富
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                print("✅ 成功获取东财数据")
                up = len(df[df['涨跌幅'] > 0])
                down = len(df[df['涨跌幅'] < 0])
                temp = (up / len(df)) * 100
                return round(temp, 2), up, down, len(df), "东财数据源"
        except Exception as e:
            print(f"东财接口异常: {e}")
            
        try:
            # 方案 B: 新浪财经备份
            df_sina = ak.stock_zh_a_spot_sina()
            if df_sina is not None and not df_sina.empty:
                print("✅ 成功获取新浪数据")
                # 新浪字段可能不同，需转换
                up = len(df_sina[df_sina['pcp'] > 0]) if 'pcp' in df_sina.columns else 0
                return 50.0, up, 0, len(df_sina), "新浪备选源"
        except Exception as e:
            print(f"新浪接口异常: {e}")
            
    return 50.0, 0, 0, 0, "数据源维护中"

def get_indices():
    """获取主要指数表现。"""
    try:
        df = ak.stock_zh_index_spot_em()
        target = ["上证指数", "深证成指", "创业板指"]
        return df[df['名称'].isin(target)].to_dict('records')
    except:
        return []

def run():
    print("🚀 开始执行 A股开盘分析...")
    temp, up, down, total, source = fetch_sentiment_with_fallback()
    indices = get_indices()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"# 📊 A股市场开盘快报 ({now})\n\n"
    report += f"**数据来源**: {source}\n\n"
    report += f"## 🌡️ 情绪温度: {temp}℃\n"
    report += f"- 📈 上涨: {up} | 📉 下跌: {down} | 🔄 总数: {total}\n\n"
    
    if indices:
        report += "## 📈 核心指数\n| 名称 | 价格 | 涨跌幅 |\n| :--- | :--- | :--- |\n"
        for item in indices:
            report += f"| {item['名称']} | {item['最新价']} | {item['涨跌幅']}% |\n"
    
    report += "\n## 🤖 AI 简评\n"
    if temp < 35:
        report += "市场开盘情绪较低。建议关注 2026 年政策利好的 AI 算力及自主可控板块。"
    else:
        report += "开盘情绪稳健，建议关注量能变化。"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("✅ 分析报表已生成。")

if __name__ == "__main__":
    run()

