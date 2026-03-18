import os
from datetime import datetime

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    index_html = ""
    for idx in indices:
        chg = float(idx.get('漲跌幅', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        index_html += f"<div style='margin-right:20px; color:{color}'><b>{idx.get('名稱')}</b>: {idx.get('最新價')} ({chg}%)</div>"

    cards_html = ""
    for res in ai_results:
        chg = float(res.get('change', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        cards_html += f"""
        <div style="border:1px solid #eee; border-radius:12px; padding:20px; margin-bottom:15px; background:#fff; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="margin:0;">{res.get('name')} <small style="color:#666; font-weight:normal;">{res.get('code')}</small></h3>
                <span style="font-size:1.2em; font-weight:bold; color:{color}">{chg}%</span>
            </div>
            <p style="color:#444; font-size:14px; margin:15px 0;"><b>💡 AI 分析:</b> {res.get('insights')}</p>
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; font-size:12px; background:#f5f5f5; padding:10px; border-radius:6px;">
                <span>🎯 買點: {res.get('buy_point')}</span>
                <span>🛡️ 止損: {res.get('stop_loss')}</span>
                <span>📊 籌碼: {res.get('chip_status')}</span>
            </div>
        </div>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT 智能復盤</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#fafafa; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .mkt-box {{ display: flex; overflow-x: auto; background: #fff; padding: 15px; border-radius: 12px; margin: 20px 0; border: 1px solid #eee; }}
            .header {{ border-left: 5px solid #1890ff; padding-left: 15px; margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin:0;">QUANT 智能復盤看板</h1>
            <p style="color:#999; margin:5px 0;">更新於: {update_time} | 數據源: {source_name} | 全市場: {total_count}</p>
        </div>
        <div class="mkt-box">{index_html}</div>
        <div>{cards_html}</div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)


















