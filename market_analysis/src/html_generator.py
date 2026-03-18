import os
from datetime import datetime

def format_val(val):
    """數值格式化引擎：自動轉化為『億』"""
    try:
        v = float(val)
        if v >= 1e8: return f"{v/1e8:.2f} 億"
        if v >= 1e4: return f"{v/1e4:.2f} 萬"
        return f"{v:.2f}"
    except: return "0"

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path, health_status):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. 頂部指數橫條
    index_html = ""
    for idx in indices[:4]:
        name = idx.get('名稱', 'N/A')
        price = idx.get('最新價', '0')
        chg = float(idx.get('漲跌幅', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        index_html += f"""
        <div class="index-item">
            <span class="index-name">{name}</span>
            <span class="index-val" style="color:{color}">{price} <small>{chg}%</small></span>
        </div>
        """

    # 2. 核心網格卡片渲染
    cards_html = ""
    for res in ai_results:
        chg = float(res.get('change', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        tag = res.get('market_tag', 'A股')
        
        # 根據市場類型分配標籤顏色
        tag_bg = "#1890ff" if tag == "A股" else "#eb2f96" if tag == "港股" else "#722ed1"
        
        cards_html += f"""
        <div class="stock-card">
            <div class="card-header">
                <div class="stock-title">
                    <span class="market-tag" style="background:{tag_bg}">{tag}</span>
                    <span class="stock-name">{res.get('name')}</span>
                    <span class="stock-code">{res.get('code')}</span>
                </div>
                <div class="stock-price" style="color:{color}">
                    <div class="price-val">{res.get('price')}</div>
                    <div class="price-chg">{"↑" if chg > 0 else "↓"} {chg}%</div>
                </div>
            </div>
            
            <div class="stats-bar">
                <div class="stat-item">PE: <b>{res.get('pe', 0)}</b></div>
                <div class="stat-item">換手: <b>{res.get('turnover', 0)}%</b></div>
                <div class="stat-item">市值: <b>{format_val(res.get('total_mv', 0))}</b></div>
            </div>

            <div class="ai-insight-box">
                <div class="ai-label">🤖 AI 深度解析</div>
                <div class="ai-content">{res.get('insights')}</div>
            </div>

            <div class="card-footer">
                <span class="strategy-tag">🎯 {res.get('buy_point')}</span>
                <span class="trend-tag">📈 {res.get('trend_prediction')}</span>
                <span class="rsi-tag">RSI: {res.get('rsi', 50)}</span>
            </div>
        </div>
        """

    # 3. 完整 CSS + HTML 模板
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT PRO 終端系統</title>
        <style>
            :root {{
                --bg-color: #0b0e11;
                --card-bg: #151a21;
                --border-color: #2b2f36;
                --text-main: #eaecef;
                --text-muted: #848e9c;
                --primary: #c99400;
            }}
            body {{
                background-color: var(--bg-color);
                color: var(--text-main);
                font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif;
                margin: 0;
                display: flex;
                height: 100vh;
            }}
            /* 側邊欄 */
            .sidebar {{
                width: 240px;
                background: #151a21;
                border-right: 1px solid var(--border-color);
                padding: 25px;
                display: flex;
                flex-direction: column;
            }}
            .logo {{ font-size: 20px; font-weight: bold; color: var(--primary); margin-bottom: 30px; display: flex; align-items: center; gap: 8px; }}
            .status-lamp {{ font-size: 12px; color: var(--text-muted); line-height: 2; margin-top: auto; padding-top: 20px; border-top: 1px solid var(--border-color); }}

            /* 主內容區 */
            .main {{ flex: 1; overflow-y: auto; padding: 25px; }}
            
            /* 頂部指數條 */
            .index-bar {{
                display: flex; gap: 15px; margin-bottom: 30px; 
                background: #1e2329; padding: 12px; border-radius: 8px; border: 1px solid var(--border-color);
            }}
            .index-item {{ flex: 1; display: flex; justify-content: space-between; padding: 0 15px; border-right: 1px solid #2b2f36; }}
            .index-name {{ color: var(--text-muted); font-size: 12px; }}
            .index-val {{ font-weight: bold; font-size: 14px; }}

            /* 網格系統 */
            .grid-container {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: 20px;
            }}

            /* 股票卡片樣式 */
            .stock-card {{
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 20px;
                transition: transform 0.2s, border-color 0.2s;
            }}
            .stock-card:hover {{ transform: translateY(-3px); border-color: var(--primary); }}
            
            .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }}
            .market-tag {{ font-size: 10px; color: white; padding: 1px 5px; border-radius: 3px; vertical-align: middle; margin-right: 5px; }}
            .stock-name {{ font-size: 18px; font-weight: bold; }}
            .stock-code {{ font-size: 12px; color: var(--text-muted); margin-left: 5px; }}
            
            .stock-price {{ text-align: right; }}
            .price-val {{ font-size: 20px; font-weight: bold; }}
            .price-chg {{ font-size: 13px; font-weight: 500; }}

            .stats-bar {{
                display: flex; justify-content: space-between; 
                background: #1e2329; padding: 8px 12px; border-radius: 6px;
                font-size: 11px; color: var(--text-muted); margin-bottom: 15px;
            }}
            .stats-bar b {{ color: var(--text-main); }}

            .ai-insight-box {{
                background: rgba(201, 148, 0, 0.05);
                border-left: 3px solid var(--primary);
                padding: 12px;
                border-radius: 0 4px 4px 0;
                margin-bottom: 15px;
            }}
            .ai-label {{ font-size: 11px; font-weight: bold; color: var(--primary); margin-bottom: 5px; }}
            .ai-content {{ font-size: 13px; line-height: 1.6; color: #d1d4dc; }}

            .card-footer {{ display: flex; gap: 10px; border-top: 1px solid #2b2f36; padding-top: 12px; font-size: 12px; }}
            .strategy-tag {{ color: #ff9d00; font-weight: bold; }}
            .trend-tag {{ color: #1890ff; font-weight: bold; }}

            ::-webkit-scrollbar {{ width: 6px; }}
            ::-webkit-scrollbar-thumb {{ background: #2b2f36; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="logo">⚡ QUANT PRO</div>
            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 40px;">
                更新: {update_time}<br>模式: {source_name}
            </div>
            
            <div style="margin-bottom: 20px;">
                <div style="font-size: 13px; color: var(--primary); margin-bottom: 15px;">📊 市場情緒熱度</div>
                <div style="background:#1e2329; height:8px; border-radius:4px; overflow:hidden;">
                    <div style="width:68%; background:var(--primary); height:100%;"></div>
                </div>
                <div style="text-align: center; margin-top: 10px; font-weight: bold;">68 - 貪婪</div>
            </div>

            <div class="status-lamp">
                TX: {health_status.get('TX', '🟢')}<br>
                Sina: {health_status.get('Sina', '🟢')}<br>
                Cache: {health_status.get('Cache', '🔵')}
            </div>
        </div>

        <div class="main">
            <div class="index-bar">{index_html}</div>
            <h2 style="font-size: 20px; margin-bottom: 25px;">今日精選深度分析 (共 {len(ai_results)} 檔)</h2>
            <div class="grid-container">
                {cards_html}
            </div>
        </div>
    </body>
    </html>
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)

























