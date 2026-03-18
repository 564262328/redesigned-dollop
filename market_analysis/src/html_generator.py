import os
from datetime import datetime

def format_val(val):
    """數值格式化引擎：自動轉化為『億/萬』格式"""
    try:
        v = float(val)
        if v >= 1e8: return f"{v/1e8:.2f} 億"
        if v >= 1e4: return f"{v/1e4:.2f} 萬"
        return f"{v:.2f}"
    except: return "0"

def get_market_style(tag):
    """動態色彩配置：根據市場標籤回傳顏色"""
    styles = {
        "A股": {"bg": "rgba(24, 144, 255, 0.1)", "border": "#1890ff", "text": "#1890ff"},
        "港股": {"bg": "rgba(235, 47, 150, 0.1)", "border": "#eb2f96", "text": "#eb2f96"},
        "ETF": {"bg": "rgba(114, 46, 209, 0.1)", "border": "#722ed1", "text": "#722ed1"}
    }
    return styles.get(tag, {"bg": "rgba(140, 140, 140, 0.1)", "border": "#8c8c8c", "text": "#8c8c8c"})

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path, health_status):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. 頂部指數橫條渲染
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

    # 2. 核心網格卡片渲染 (解決重複，展示動態標籤)
    cards_html = ""
    for res in ai_results:
        chg = float(res.get('change', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        tag = res.get('market_tag', 'A股')
        m_style = get_market_style(tag)
        
        cards_html += f"""
        <div class="stock-card">
            <div class="card-header">
                <div class="stock-title">
                    <span class="market-badge" style="background:{m_style['bg']}; border:1px solid {m_style['border']}; color:{m_style}">{tag}</span>
                    <span class="stock-name">{res.get('name')}</span>
                    <span class="stock-code">{res.get('code')}</span>
                </div>
                <div class="stock-price" style="color:{color}">
                    <div class="price-val">{res.get('price')}</div>
                    <div class="price-chg">{"▲" if chg > 0 else "▼"} {chg}%</div>
                </div>
            </div>
            
            <div class="stats-bar">
                <div class="stat-item">PE: <b>{res.get('pe', 0)}</b></div>
                <div class="stat-item">換手: <b>{res.get('turnover', 0)}%</b></div>
                <div class="stat-item">市值: <b>{format_val(res.get('total_mv', 0))}</b></div>
            </div>

            <div class="ai-insight-box">
                <div class="ai-label">🤖 AI QUANT ANALYSIS</div>
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
        <title>QUANT PRO | 跨市場復盤終端</title>
        <style>
            :root {{
                --bg-color: #0b0e11;
                --card-bg: #151a21;
                --border-color: #2b2f36;
                --text-main: #eaecef;
                --text-muted: #848e9c;
                --primary: #c99400;
                --accent: #1890ff;
            }}
            body {{
                background-color: var(--bg-color);
                color: var(--text-main);
                font-family: 'Inter', 'PingFang TC', sans-serif;
                margin: 0;
                display: flex;
                height: 100vh;
            }}
            /* 側邊欄 */
            .sidebar {{
                width: 260px;
                background: #151a21;
                border-right: 1px solid var(--border-color);
                padding: 30px 20px;
                display: flex;
                flex-direction: column;
            }}
            .logo {{ font-size: 22px; font-weight: 800; color: var(--primary); margin-bottom: 35px; letter-spacing: 1px; }}
            .sidebar-label {{ font-size: 12px; color: var(--text-muted); margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }}

            /* 主內容區 */
            .main {{ flex: 1; overflow-y: auto; padding: 30px; }}
            
            /* 搜索區 */
            .search-section {{ display: flex; gap: 15px; margin-bottom: 30px; align-items: center; }}
            .search-bar {{ 
                flex: 1; max-width: 500px; background: #1e2329; border: 1px solid var(--border-color);
                border-radius: 6px; padding: 12px 15px; color: white; outline: none; font-size: 14px;
            }}
            .search-bar:focus {{ border-color: var(--accent); }}
            .analyze-btn {{ background: var(--accent); color: white; border: none; padding: 10px 25px; border-radius: 6px; font-weight: bold; cursor: pointer; }}

            /* 頂部指數條 */
            .index-bar {{
                display: flex; gap: 15px; margin-bottom: 35px; 
                background: #1e2329; padding: 15px; border-radius: 10px; border: 1px solid var(--border-color);
            }}
            .index-item {{ flex: 1; display: flex; justify-content: space-between; padding: 0 15px; border-right: 1px solid #2b2f36; }}
            .index-item:last-child {{ border-right: none; }}
            .index-name {{ color: var(--text-muted); font-size: 12px; }}
            .index-val {{ font-weight: bold; font-size: 15px; }}

            /* 網格系統 */
            .grid-container {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 25px;
            }}

            /* 股票卡片 */
            .stock-card {{
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 22px;
                position: relative;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            .stock-card:hover {{ transform: translateY(-5px); border-color: var(--accent); box-shadow: 0 10px 20px rgba(0,0,0,0.4); }}
            
            .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; }}
            .market-badge {{ font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }}
            .stock-name {{ font-size: 19px; font-weight: bold; margin-left: 8px; }}
            .stock-code {{ font-size: 13px; color: var(--text-muted); margin-left: 6px; }}
            
            .stock-price {{ text-align: right; }}
            .price-val {{ font-size: 22px; font-weight: 800; }}
            .price-chg {{ font-size: 14px; margin-top: 2px; }}

            .stats-bar {{
                display: flex; justify-content: space-between; 
                background: #1e2329; padding: 10px 15px; border-radius: 8px;
                font-size: 12px; color: var(--text-muted); margin-bottom: 20px;
            }}
            .stats-bar b {{ color: var(--text-main); }}

            .ai-insight-box {{
                background: rgba(24, 144, 255, 0.03);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid rgba(24, 144, 255, 0.1);
            }}
            .ai-label {{ font-size: 10px; font-weight: 800; color: var(--accent); margin-bottom: 8px; letter-spacing: 1.5px; }}
            .ai-content {{ font-size: 14px; line-height: 1.7; color: #d1d4dc; }}

            .card-footer {{ display: flex; justify-content: space-between; border-top: 1px solid #2b2f36; padding-top: 15px; font-size: 13px; }}
            .strategy-tag {{ color: #ff9d00; font-weight: bold; }}
            .trend-tag {{ color: #1890ff; font-weight: bold; }}
            .rsi-tag {{ color: var(--text-muted); font-family: monospace; }}

            /* 情緒條 */
            .heat-bg {{ background: #1e2329; height: 10px; border-radius: 5px; margin: 15px 0; overflow: hidden; }}
            .heat-fill {{ 
                background: linear-gradient(90deg, #52c41a 0%, #c99400 50%, #ff4d4f 100%); 
                height: 100%; width: 68%; transition: width 1s;
            }}

            .status-lamp {{ margin-top: auto; font-size: 11px; color: #4a515c; border-top: 1px solid var(--border-color); padding-top: 20px; }}

            ::-webkit-scrollbar {{ width: 6px; }}
            ::-webkit-scrollbar-thumb {{ background: #363c4e; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="logo">⚡ QUANT PRO</div>
            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 40px;">
                {update_time}<br>NODE: {source_name}
            </div>
            
            <div class="sidebar-label">Market Sentiment</div>
            <div style="margin-bottom: 30px;">
                <div class="heat-bg"><div class="heat-fill"></div></div>
                <div style="text-align: center; color: #ff4d4f; font-weight: bold; font-size: 20px;">68 - 貪婪</div>
            </div>

            <div class="sidebar-label">System Health</div>
            <div class="status-lamp">
                TENCENT_API: {health_status.get('TX', '🟢')}<br>
                SINA_DATA: {health_status.get('Sina', '🟢')}<br>
                CACHE_SYNC: {health_status.get('Cache', '🔵')}
            </div>
        </div>

        <div class="main">
            <div class="search-section">
                <input type="text" class="search-bar" placeholder="🔍 搜尋股票代碼或名稱分析...">
                <button class="analyze-btn">即時分析</button>
                <div style="flex:1"></div>
                <div style="font-size: 12px; color:var(--text-muted)">全市場標本: {total_count} 檔</div>
            </div>

            <div class="index-bar">{index_html}</div>
            
            <h2 style="font-size: 22px; margin-bottom: 30px; letter-spacing: 0.5px;">今日精選跨市場深度分析 <small style="color:var(--text-muted); font-weight:normal; font-size:14px;">(20 檔權重股)</small></h2>
            
            <div class="grid-container">
                {cards_html}
            </div>
            
            <div style="margin-top: 60px; text-align: center; color: #363c4e; font-size: 12px; border-top: 1px solid #1e2329; padding-top: 30px;">
                © 2026 QUANT Terminal PRO v15.8. Data provided by Mixed Cloud Sources.
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)

























