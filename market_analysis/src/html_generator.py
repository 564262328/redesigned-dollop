import os
from datetime import datetime

def format_mkt_val(val):
    """將大額數值轉換為『億』格式"""
    try:
        val = float(val)
        if val >= 100000000:
            return f"{val / 100000000:.2f} 億"
        elif val >= 10000:
            return f"{val / 10000:.2f} 萬"
        return str(val)
    except: return "0"

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path, health_status):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    cards_html = ""
    for res in ai_results:
        chg = float(res.get('change', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        tag_color = "#1890ff" if res.get('market_tag') == "A股" else "#eb2f96" if res.get('market_tag') == "港股" else "#722ed1"
        
        cards_html += f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <h2 style="margin: 0; font-size: 20px;">
                        {res.get('name')} <small style="color:#848e9c; font-size:12px;">({res.get('code')})</small>
                        <span style="background:{tag_color}; color:white; font-size:10px; padding:1px 4px; border-radius:3px;">{res.get('market_tag')}</span>
                    </h2>
                    <div style="font-size: 11px; color: #1890ff; margin-top: 6px;">
                        PE: {res.get('pe')} | 換手: {res.get('turnover')}% | 量比: {res.get('vol_ratio')} | 市值: {format_mkt_val(res.get('total_mv'))}
                    </div>
                </div>
                <div style="text-align: right; color: {color};">
                    <div style="font-size: 22px; font-weight: bold;">{res.get('price')}</div>
                    <div style="font-size: 13px;">{"+" if chg > 0 else ""}{chg}%</div>
                </div>
            </div>
            <div class="chip-bar">
                獲利比例: <b>{res.get('profit_ratio')}</b> | 平均成本: <b>{res.get('avg_cost')}</b> | 集中度: <b>{res.get('chip_concentrate')}</b>
            </div>
            <div class="insights"><b>AI 洞察:</b> {res.get('insights')}</div>
            <div style="display: flex; gap: 10px; font-size: 12px; margin-top: 10px;">
                <div class="tag">策略: {res.get('buy_point')}</div>
                <div class="tag">預測: {res.get('trend_prediction')}</div>
            </div>
        </div>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>QUANT 2026 PRO 終端</title>
        <style>
            body {{ background: #131722; color: #d1d4dc; font-family: sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }}
            .sidebar {{ width: 250px; background: #1e222d; border-right: 1px solid #363c4e; padding: 20px; }}
            .main {{ flex: 1; padding: 25px; overflow-y: auto; }}
            .search-bar {{ background: #2a2e39; border: 1px solid #363c4e; border-radius: 4px; padding: 12px; width: 400px; color: white; margin-bottom: 30px; }}
            .card {{ background: #1e222d; border-radius: 12px; padding: 20px; border: 1px solid #363c4e; margin-bottom: 20px; }}
            .chip-bar {{ background: #2a2e39; padding: 8px 12px; border-radius: 6px; font-size: 11px; margin: 12px 0; color: #848e9c; }}
            .insights {{ background: rgba(24,144,255,0.05); border-left: 3px solid #1890ff; padding: 12px; font-size: 13px; line-height: 1.6; color: #f0f3fa; }}
            .tag {{ background: #2a2e39; padding: 4px 10px; border-radius: 4px; color: #1890ff; }}
            .heat-bg {{ background: #2a2e39; height: 10px; border-radius: 5px; margin: 15px 0; overflow: hidden; }}
            .heat-fill {{ background: #1890ff; height: 100%; width: 68%; }}
            ::-webkit-scrollbar {{ width: 5px; }}
            ::-webkit-scrollbar-thumb {{ background: #363c4e; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2 style="color: #1890ff; font-size: 18px;">🚀 QUANT 終端</h2>
            <div style="font-size: 12px; color: #848e9c;">更新: {update_time}</div>
            <div style="margin-top: 40px;">
                <div style="font-size: 13px; color: #1890ff;">🔥 市場情緒熱度</div>
                <div class="heat-bg"><div class="heat-fill"></div></div>
                <div style="text-align: center; color: #ff4d4f; font-weight: bold; font-size: 20px;">68 (貪婪)</div>
            </div>
            <div style="margin-top: 40px; font-size: 12px; color: #595959;">
                數據源: {source_name}<br>掃描範圍: {total_count} 標的
            </div>
        </div>
        <div class="main">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <input type="text" class="search-bar" placeholder="🔍 輸入代碼分析 (如 00700, 600519)...">
                <div style="background:#1e222d; padding:8px 15px; border-radius:8px; border:1px solid #363c4e; color:#52c41a;">多市場監控: Online</div>
            </div>
            <h3 style="color:#1890ff; border-bottom: 1px solid #363c4e; padding-bottom: 10px;">今日焦點批量分析 (20 檔)</h3>
            {cards_html}
        </div>
    </body>
    </html>
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
























