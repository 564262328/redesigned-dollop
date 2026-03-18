import os
from datetime import datetime

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path, health_status):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 指數看板
    index_html = ""
    for idx in indices[:4]:
        chg = float(idx.get('漲跌幅', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        index_html += f"""
        <div style="background: #1e222d; padding: 12px; border-radius: 8px; min-width: 150px; border: 1px solid #363c4e;">
            <div style="font-size: 11px; color: #848e9c;">{idx.get('名稱')}</div>
            <div style="font-size: 16px; font-weight: bold; color: {color}; margin-top: 4px;">{idx.get('最新價')} <small>{chg}%</small></div>
        </div>
        """

    # 個股卡片
    cards_html = ""
    for res in ai_results:
        chg = float(res.get('change', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        cards_html += f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2a2e39; padding-bottom: 15px;">
                <div>
                    <h2 style="margin: 0; font-size: 20px; color: #f0f3fa;">{res.get('name')} <span style="color: #1890ff; font-size: 14px;">({res.get('code')})</span></h2>
                    <div style="font-size: 11px; color: #848e9c; margin-top: 4px;">Sector: {res.get('industry')} | RSI: {res.get('rsi')}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 22px; font-weight: bold; color: {color};">{res.get('price')}</div>
                    <div style="font-size: 13px; color: {color};">{"+" if chg > 0 else ""}{chg}%</div>
                </div>
            </div>
            <div class="key-insights">
                <div style="color: #1890ff; font-size: 10px; font-weight: bold; margin-bottom: 8px;">AI DEEP ANALYSIS</div>
                {res.get('insights')}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                <div class="info-box">策略：<span style="color: #ff9d00;">{res.get('buy_point')}</span></div>
                <div class="info-box">狀態：<span style="color: #1890ff;">{res.get('chip_status')}</span></div>
            </div>
            <div style="font-size: 11px; color: #595959; border-top: 1px solid #2a2e39; pt: 10px;">
                【資訊】盤中異動：{res.get('name')} 成交量能溫和放大，關注支撐位表現。
            </div>
        </div>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT 專業終端</title>
        <style>
            body {{ background-color: #131722; color: #d1d4dc; font-family: sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }}
            .sidebar {{ width: 240px; background: #1e222d; border-right: 1px solid #363c4e; padding: 20px; overflow-y: auto; }}
            .main-content {{ flex: 1; padding: 25px; overflow-y: auto; }}
            .search-bar {{ width: 100%; max-width: 450px; background: #2a2e39; border: 1px solid #363c4e; border-radius: 4px; padding: 10px; color: #fff; margin-bottom: 30px; }}
            .card {{ background: #1e222d; border-radius: 12px; padding: 20px; border: 1px solid #363c4e; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
            .key-insights {{ background: rgba(24,144,255,0.05); border-left: 3px solid #1890ff; padding: 12px; font-size: 13px; line-height: 1.6; margin: 15px 0; color: #f0f3fa; }}
            .info-box {{ background: #2a2e39; padding: 8px; border-radius: 4px; font-size: 12px; text-align: center; }}
            .sentiment-box {{ background: #1e222d; border: 1px solid #363c4e; border-radius: 12px; padding: 20px; text-align: center; }}
            ::-webkit-scrollbar {{ width: 5px; }}
            ::-webkit-scrollbar-thumb {{ background: #363c4e; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div style="color: #1890ff; font-weight: bold; margin-bottom: 20px;">🕒 分析歷史</div>
            <div style="font-size: 12px; color: #848e9c; line-height: 2.5;">
                <div>貴州茅台 (600519)</div>
                <div>騰訊控股 (00700)</div>
                <div>寧德時代 (300750)</div>
            </div>
            <div style="margin-top: 40px; border-top: 1px solid #363c4e; padding-top: 20px;">
                <div style="color: #1890ff; font-weight: bold; margin-bottom: 15px;">📡 系統健康</div>
                <div style="font-size: 11px;">TX: {health_status.get('TX')} | Sina: {health_status.get('Sina')} | EM: {health_status.get('EM')}</div>
            </div>
        </div>
        <div class="main-content">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                <input type="text" class="search-bar" placeholder="輸入股票代碼分析...">
                <div style="text-align: right; font-size: 12px; color: #848e9c;">更新時間: {update_time}</div>
            </div>
            <div style="display: flex; gap: 20px;">
                <div style="flex: 2.5;">
                    <div style="display: flex; gap: 10px; margin-bottom: 20px;">{index_html}</div>
                    {cards_html}
                </div>
                <div style="flex: 1;">
                    <div class="sentiment-box">
                        <div style="font-size: 13px; color: #848e9c;">市場情緒熱度</div>
                        <div style="font-size: 32px; font-weight: bold; color: #1890ff; margin: 15px 0;">65</div>
                        <div style="color: #ff4d4f; font-weight: bold;">貪婪模式</div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)






















