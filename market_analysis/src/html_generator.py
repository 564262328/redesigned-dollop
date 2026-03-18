import os
from datetime import datetime

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path, health_status):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 指數看板
    index_html = ""
    for idx in indices[:1]:
        index_html += f"""
        <div style="background: #1e222d; padding: 12px 20px; border-radius: 8px; border: 1px solid #363c4e;">
            <div style="font-size: 12px; color: #848e9c;">{idx.get('名稱')}</div>
            <div style="font-size: 18px; font-weight: bold; color: #1890ff; margin-top: 4px;">多市場監控系統 <small>Online</small></div>
        </div>
        """

    # 個股卡片
    cards_html = ""
    for res in ai_results:
        chg = float(res.get('change', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        tag_color = "#1890ff" if res.get('market_tag') == "A股" else "#eb2f96" if res.get('market_tag') == "港股" else "#722ed1"
        
        cards_html += f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; font-size: 20px; color: #f0f3fa;">
                        {res.get('name')} <span style="font-size:13px; color:#848e9c;">{res.get('code')}</span>
                        <span style="font-size:10px; background:{tag_color}; color:white; padding:1px 5px; border-radius:3px; margin-left:8px;">{res.get('market_tag')}</span>
                    </h2>
                    <div style="font-size: 11px; color: #1890ff; margin-top: 6px;">
                        PE: {res.get('pe')} | 換手: {res.get('turnover')}% | 量比: {res.get('vol_ratio')}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 22px; font-weight: bold; color: {color};">{res.get('price')}</div>
                    <div style="font-size: 13px; color: {color};">{"+" if chg > 0 else ""}{chg}%</div>
                </div>
            </div>

            <div class="chip-grid">
                <div>獲利比例: <b style="color:#fff;">{res.get('profit_ratio')}</b></div>
                <div>平均成本: <b style="color:#fff;">{res.get('avg_cost')}</b></div>
                <div>籌碼集中度: <b style="color:#fff;">{res.get('chip_concentrate')}</b></div>
            </div>

            <div class="key-insights">
                <div style="color: #1890ff; font-size: 10px; font-weight: bold; margin-bottom: 8px;">AI DEEP ANALYTICS</div>
                {res.get('insights')}
            </div>
            
            <div style="display: flex; gap: 10px; font-size: 12px;">
                <div style="flex:1; background:#2a2e39; padding:8px; border-radius:4px; text-align:center;">策略: <span style="color:#ff9d00;">{res.get('buy_point')}</span></div>
                <div style="flex:1; background:#2a2e39; padding:8px; border-radius:4px; text-align:center;">預測: <span style="color:#1890ff;">{res.get('trend_prediction', '震盪')}</span></div>
            </div>
        </div>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>QUANT 2026 專業終端</title>
        <style>
            body {{ background-color: #131722; color: #d1d4dc; font-family: sans-serif; margin: 0; padding: 20px; display: flex; height: 100vh; overflow: hidden; }}
            .sidebar {{ width: 240px; background: #1e222d; border-right: 1px solid #363c4e; padding: 20px; }}
            .main-content {{ flex: 1; padding-left: 25px; overflow-y: auto; }}
            .search-bar {{ width: 100%; max-width: 500px; background: #2a2e39; border: 1px solid #363c4e; border-radius: 4px; padding: 12px; color: #fff; margin-bottom: 30px; }}
            .card {{ background: #1e222d; border-radius: 12px; padding: 20px; border: 1px solid #363c4e; margin-bottom: 20px; }}
            .chip-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); background: #2a2e39; padding: 10px; border-radius: 6px; font-size: 11px; margin: 15px 0; color: #848e9c; }}
            .key-insights {{ background: rgba(24,144,255,0.05); border-left: 3px solid #1890ff; padding: 12px; font-size: 13px; line-height: 1.6; margin-bottom: 15px; color: #f0f3fa; }}
            ::-webkit-scrollbar {{ width: 5px; }}
            ::-webkit-scrollbar-thumb {{ background: #363c4e; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div style="color: #1890ff; font-weight: bold; margin-bottom: 25px;">🚀 智能復盤終端</div>
            <div style="font-size: 12px; color: #848e9c; margin-bottom: 10px;">🕒 更新時間: {update_time}</div>
            <div style="font-size: 12px; color: #848e9c; margin-bottom: 30px;">📡 模式: {source_name}</div>
            <div style="color: #1890ff; font-size: 13px; margin-bottom: 15px;">📊 市場情緒熱度</div>
            <div style="background:#2a2e39; height:10px; border-radius:5px; margin-bottom:10px;"><div style="width:65%; background:#1890ff; height:100%; border-radius:5px;"></div></div>
            <div style="text-align:center; color:#ff4d4f; font-weight:bold; font-size:20px;">65 (中性偏貪婪)</div>
        </div>
        <div class="main-content">
            <div style="display:flex; gap:15px; align-items:center; margin-bottom:25px;">
                <input type="text" class="search-bar" placeholder="🔍 搜尋股票代碼分析 (如 00700, 600519, 510300)...">
                {index_html}
            </div>
            <div style="max-width: 800px;">
                <h3 style="color:#1890ff; border-bottom: 1px solid #363c4e; padding-bottom: 10px; margin-bottom: 20px;">🔥 AI 批量分析結果 (今日焦點)</h3>
                {cards_html}
            </div>
        </div>
    </body>
    </html>
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)























