import os
import sys
import time
import random
import requests
import pandas as pd
from datetime import datetime
from tenacity import retry, wait_exponential, stop_after_attempt

# --- 1. Dependencies Check ---
try:
    import akshare as ak
except ImportError:
    print("❌ Dependency missing: akshare.")
    sys.exit(1)

# --- 2. Robust Data Fetching ---
def smart_rename(df):
    if df is None or df.empty: return df
    mapping = {
        '涨跌幅': 'pct', 'changepercent': 'pct', '涨跌百分比': 'pct',
        '最新价': 'price', 'trade': 'price', '最新': 'price',
        '名称': 'name', '代码': 'code', 'symbol': 'code'
    }
    current_map = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=current_map)

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def fetch_with_retry(func):
    """Adds a small random delay to avoid anti-crawler detection"""
    time.sleep(random.uniform(1, 3))
    return func()

def get_market_data():
    """Tries EastMoney first, then falls back to Sina"""
    # Attempt 1: EastMoney (EM)
    try:
        print("🔄 Fetching from EastMoney...")
        df = fetch_with_retry(ak.stock_zh_a_spot_em)
        if df is not None and not df.empty:
            return smart_rename(df), "EastMoney"
    except Exception as e:
        print(f"⚠️ EastMoney failed: {e}")

    # Attempt 2: Sina Fallback
    try:
        print("🔄 Falling back to Sina...")
        df = fetch_with_retry(ak.stock_zh_a_spot)
        if df is not None and not df.empty:
            return smart_rename(df), "Sina"
    except Exception as e:
        print(f"❌ Sina failed: {e}")
    
    raise Exception("All data sources are currently unreachable.")

# --- 3. Core Logic ---
def run():
    now = datetime.now()
    report = f"# 📊 A-Share AI Dashboard\n> Time: {now.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    try:
        df, source = get_market_data()
        df['pct'] = pd.to_numeric(df.get('pct', 0), errors='coerce').fillna(0)
        
        # Stats
        total = len(df)
        up = len(df[df['pct'] > 0])
        down = total - up
        ratio = up / total if total > 0 else 0.5
        score = round(ratio * 100, 1)
        
        # Build Report
        report += f"**Data Source**: `{source}`\n\n"
        report += f"### 🌡️ Market Sentiment\n"
        report += f"**Score**: `{score}` / 100\n"
        bar = f"🟢{'█' * int(ratio*15)}{'░' * (15-int(ratio*15))}🔴"
        report += f"**Ratio**: {bar}\n"
        report += f"- 🟢 Up: **{up}** | 🔴 Down: **{down}**\n\n"
        
        # Strategy
        report += "### 🎯 AI Strategy\n"
        if score > 60: report += "✅ **Bullish**: Strong market. Hold positions."
        elif score < 40: report += "💀 **Weak**: High pressure. Stay cautious."
        else: report += "⚖️ **Neutral**: Sideways. Maintain 50% position."

    except Exception as e:
        report += f"## ❌ Error\nFailed to fetch data: `{str(e)}`"

    # --- 4. File Generation (Fixed for GitHub Actions) ---
    # Prepare HTML content separately to avoid f-string backslash error
    html_body = report.replace('\n', '<br>').replace('**', '<b>').replace('**', '</b>')
    
    html_template = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
    <style>body{{font-family:sans-serif;padding:30px;line-height:1.6;max-width:700px;margin:auto;background:#f4f4f9;}}
    .box{{background:white;padding:25px;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.1);}}</style>
    </head><body><div class="box">{html_body}</div></body></html>"""

    with open("report.md", "w", encoding="utf-8") as f: f.write(report)
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_template)
    
    # Push to ServerChan if SCKEY exists
    sckey = os.getenv("SCKEY")
    if sckey:
        try:
            url = f"https://sctapi.ftqq.com{sckey}.send"
            requests.post(url, json={"title": "📊 A-Share Report", "desp": report}, timeout=10)
        except: pass
    print("✅ Done.")

if __name__ == "__main__":
    run()

