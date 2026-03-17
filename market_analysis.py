import os
import sys
import time
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# --- Dependencies Check ---
try:
    import akshare as ak
except ImportError:
    print("❌ Dependency missing: akshare. Please check your YAML file.")
    sys.exit(1)

# --- configuration & helpers ---
def smart_rename(df):
    """Adapt column names to avoid KeyError"""
    if df is None or df.empty: return df
    mapping = {
        '涨跌幅': 'pct', 'changepercent': 'pct', '涨跌百分比': 'pct',
        '最新价': 'price', 'trade': 'price', '最新': 'price',
        '名称': 'name', '代码': 'code', 'symbol': 'code'
    }
    current_map = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=current_map)

@retry(
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception)
)
def tenacity_fetch(func, *args, **kwargs):
    time.sleep(random.uniform(2, 4))
    return func(*args, **kwargs)

def create_sentiment_bar(ratio):
    length = 15
    up_len = int(ratio * length)
    down_len = length - up_len
    return f"🟢{'█' * up_len}{'░' * down_len}🔴"

def send_push(content):
    sckey = os.getenv("SCKEY")
    if not sckey: return
    try:
        url = f"https://{sckey}://" if sckey.startswith("sctp") else f"https://sctapi.ftqq.com{sckey}.send"
        requests.post(url, json={"title": "📊 A股 AI 决策仪表盘", "desp": content}, timeout=15)
        print("✅ Push notification sent.")
    except Exception as e: print(f"❌ Push error: {e}")

# --- Core Analysis Logic ---
def run():
    now = datetime.now()
    print(f"🚀 Starting Engine at: {now}")
    
    # Initialize default report in case of API failure
    report = f"# 📊 A-Share AI Dashboard\n> Updated: {now.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    try:
        # 1. Fetch Market Data
        df = tenacity_fetch(ak.stock_zh_a_spot_em)
        df = smart_rename(df)
        df['pct'] = pd.to_numeric(df.get('pct', 0), errors='coerce').fillna(0)
        
        # 2. Basic Stats
        total_count = len(df)
        up_count = len(df[df['pct'] > 0])
        down_count = total_count - up_count
        up_ratio = up_count / total_count if total_count > 0 else 0.5
        market_score = round(up_ratio * 100, 1)
        
        # 3. Build Markdown Report
        report += f"### 🌡️ Market Sentiment\n"
        report += f"**Score**: `{market_score}` / 100\n"
        report += f"**Ratio**: {create_sentiment_bar(up_ratio)}\n"
        report += f"- 🟢 Up: **{up_count}** | 🔴 Down: **{down_count}**\n\n"
        
        # 4. Strategy Advice
        report += "### 🎯 AI Strategy\n"
        if market_score > 65: report += "✅ **Bullish**: Strong momentum. Hold positions."
        elif market_score < 35: report += "💀 **Oversold**: Extreme panic. Avoid panic selling."
        else: report += "⚖️ **Neutral**: Sideways market. Keep 50% position."

    except Exception as e:
        print(f"⚠️ Data Fetch Error: {e}")
        report += f"⚠️ **Data Error**: Failed to fetch live market data. (Source: AkShare)\nError details: `{str(e)}`"

    # --- HTML Generator (Fixed for f-string backslash) ---
    # First, handle characters that break f-strings or need formatting
    html_body = report.replace('\n', '<br>').replace('**', '<b>').replace('**', '</b>')
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>A-Share Dashboard</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; line-height: 1.6; padding: 40px; max-width: 800px; margin: auto; background: #f9f9f9; }}
            .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <div class="card">
            {html_body}
        </div>
    </body>
    </html>
    """

    # --- FINAL STEP: Write Files ---
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    
    send_push(report)
    print("✅ All files generated: report.md and index.html")

# --- ENTRY POINT ---
if __name__ == "__main__":
    try:
        run()
    except Exception as fatal_e:
        # Emergency catch-all to prevent Action from failing without a file
        err_report = f"# ❌ System Crash\n{str(fatal_e)}"
        with open("report.md", "w", encoding="utf-8") as f:
            f.write(err_report)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"<html><body>{err_report}</body></html>")
        print(f"🔥 Fatal Error: {fatal_e}")

