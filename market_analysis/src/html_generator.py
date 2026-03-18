import os
from datetime import datetime

def format_val(val):
    try:
        v = float(val)
        return f"{v/1e8:.2f} 億" if v >= 1e8 else f"{v:.2f}"
    except: return "0"

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path, health_status):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    cards_html = ""
    for res in ai_results:
        color = "#ff4d4f" if float(res.get('change',0)) > 0 else "#52c41a"
        cards_html += f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between;">
                <b>{res.get('name')} ({res.get('code')}) [{res.get('market_tag')}]</b>
                <span style="color:{color}; font-weight:bold;">{res.get('price')} ({res.get('change')}%)</span>
            </div>
            <div style="font-size:11px; color:#1890ff; margin:5px 0;">市值: {format_val(res.get('total_mv'))} | 換手: {res.get('turnover')}%</div>
            <div style="background:rgba(24,144,255,0.05); padding:10px; font-size:13px; margin:10px 0; border-left:3px solid #1890ff;">{res.get('insights')}</div>
            <div style="display:flex; gap:10px; font-size:12px;">
                <span class="tag">策略: {res.get('buy_point')}</span>
                <span class="tag">預測: {res.get('trend_prediction')}</span>
            </div>
        </div>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#131722; color:#d1d4dc; font-family:sans-serif; display:flex; }}
            .sidebar {{ width:220px; background:#1e222d; padding:20px; border-right:1px solid #363c4e; }}
            .main {{ flex:1; padding:20px; overflow-y:auto; }}
            .card {{ background:#1e222d; border-radius:8px; padding:15px; margin-bottom:15px; border:1px solid #363c4e; }}
            .tag {{ background:#2a2e39; padding:3px 8px; border-radius:4px; color:#1890ff; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h3>🚀 QUANT 終端</h3>
            <p style="font-size:12px;">更新: {update_time}<br>源: {source_name}</p>
        </div>
        <div class="main">
            <h3>今日焦點 (20 檔)</h3>
            {cards_html}
        </div>
    </body>
    </html>
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)

























