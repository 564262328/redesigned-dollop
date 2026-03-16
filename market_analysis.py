import sys
import time
import random
import traceback
from datetime import datetime

# --- 依赖项自检 ---
try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("❌ 环境异常，请确认 GitHub Actions 依赖安装步骤。")
    sys.exit(1)

def fetch_a_share_spot():
    """三级容错获取全 A 股行情数据。"""
    # 方案 1: 东方财富 (标准)
    try:
        print("Step 1: 尝试从东方财富获取行情...")
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            return df, "东方财富"
    except Exception as e:
        print(f"东财接口异常: {e}")

    time.sleep(random.uniform(1, 2))

    # 方案 2: 新浪财经 (备份) - 接口名为 stock_zh_a_spot
    try:
        print("Step 2: 尝试从新浪财经获取行情...")
        df = ak.stock_zh_a_spot() # 注意：不是 stock_zh_a_spot_sina
        if df is not None and not df.empty:
            # 统一字段名以适配后续分析逻辑
            df = df.rename(columns={'trade': '最新价', 'pricechange': '涨跌额', 'changepercent': '涨跌幅'})
            return df, "新浪财经"
    except Exception as e:
        print(f"新浪接口异常: {e}")

    time.sleep(random.uniform(1, 2))

    # 方案 3: 分交易所抓取 (最后的防线)
    try:
        print("Step 3: 尝试分交易所获取行情...")
        sh = ak.stock_sh_a_spot_em()
        sz = ak.stock_sz_a_spot_em()
        bj = ak.stock_bj_a_spot_em()
        df = pd.concat([sh, sz, bj], ignore_index=True)
        if not df.empty:
            return df, "分交易所合并"
    except Exception as e:
        print(f"分交易所接口异常: {e}")

    return None, None

def fetch_indices():
    """双源获取核心指数。"""
    try:
        # 方案 1: 东财
        df = ak.stock_zh_index_spot_em()
        if df is not None and not df.empty:
            return df, "东财"
    except:
        pass
    
    try:
        # 方案 2: 新浪
        df = ak.stock_zh_index_spot()
        if df is not None and not df.empty:
            return df.rename(columns={'last': '最新价', 'pct_chg': '涨跌幅'}), "新浪"
    except:
        return None, None

def run():
    print(f"🚀 开始执行 A股早报分析 (当前时间: {datetime.now()})")
    
    df_spot, source_spot = fetch_a_share_spot()
    df_index, source_index = fetch_indices()
    
    if df_spot is None:
        print("❌ 所有行情接口均失效，请检查网络或 AKShare 版本。")
        sys.exit(1)

    # 计算情绪温度
    total = len(df_spot)
    up = len(df_spot[df_spot['涨跌幅'] > 0])
    down = len(df_spot[df_spot['涨跌幅'] < 0])
    temp = round((up / total) * 100, 2) if total > 0 else 50.0

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"# 📊 A股开盘快报 ({now})\n\n"
    report += f"- **行情源**: {source_spot} | **指数源**: {source_index}\n"
    report += f"## 🌡️ 情绪温度: {temp}℃\n"
    report += f"- 📈 上涨: {up} | 📉 下跌: {down} | 🔄 样本: {total}\n\n"

    if df_index is not None:
        report += "## 📈 核心指数\n| 指数名称 | 最新价 | 涨跌幅 |\n| :--- | :--- | :--- |\n"
        target = ["上证指数", "深证成指", "创业板指"]
        for name in target:
            row = df_index[df_index['名称'] == name]
            if not row.empty:
                report += f"| {name} | {row.iloc[0]['最新价']} | {row.iloc[0]['涨跌幅']}% |\n"

    report += "\n## 🤖 AI 简评 (2026 版)\n"
    report += "根据最新宏观展望，2026 年亚洲市场将进入宽松周期后半程。"
    if temp > 60:
        report += "市场情绪过热，建议保持警惕，关注 AI 基础设施板块回调机会。"
    elif temp < 40:
        report += "开盘情绪低迷，可关注高股息蓝筹股的避险价值。"
    else:
        report += "情绪处于中性区间，建议观察量能是否有效放大。"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("✅ 报告已生成。")

if __name__ == "__main__":
    run()

