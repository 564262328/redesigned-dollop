import os
from datetime import datetime

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path, health_status):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 1. 指数看板渲染
    index_html = ""
    for idx in indices[:4]:
        chg = float(idx.get('漲跌幅', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        index_html += f"""
        <div style="background: #1e222d; padding: 10px 15px; border-radius: 8px; min-width: 140px; border: 1px solid #363c4e;">
            <div style="font-size: 12px; color: #848e9c;">{idx.get('名稱')}</div>
            <div style="font-size: 16px; font-weight: bold; color: {color}; margin-top: 4px;">{idx.get('最新價')} <small>{chg}%</small></div>
        </div>
        """

    # 2. 个股卡片渲染 (仿照图片中心布局)
    cards_html = ""
    for res in ai_results:
        chg = float(res.get('change', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        cards_html += f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h2 style="margin: 0; font-size: 20px;">{res.get('name')} <span style="color: #1890ff; font-size: 14px;">{res.get('code')}</span></h2>
                    <div style="font-size: 12px; color: #848e9c; margin-top: 5px;">更新時間: {update_time}</div>
                </div>
                <div style="text-align: right; color: {color}; font-size: 22px; font-weight: bold;">
                    {res.get('price')} <span style="font-size: 14px;">{chg}%</span>
                </div>
            </div>

            <div class="key-insights">
                <div style="color: #1890ff; font-size: 12px; font-weight: bold; text-align: center; margin-bottom: 10px; text-transform: uppercase;">Key Insights</div>
                {res.get('insights')}
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                <div class="info-box"><b>操作建議：</b> <span style="color: #ff9d00;">{res.get('buy_point', '觀望')}</span></div>
                <div class="info-box"><b>趨勢預測：</b> <span style="color: #1890ff;">震盪上行</span></div>
            </div>

            <div style="border-top: 1px solid #363c4e; padding-top: 15px;">
                <div style="font-size: 12px; color: #848e9c; margin-bottom: 10px; font-weight: bold;">NEWS FEED 相關資訊</div>
                <div class="news-item">【行業深度】洞察2026：{res.get('name')} 所屬板塊競爭格局及市場份額分析...</div>
                <div class="news-item">實時異動：{res.get('name')} 盤中快速拉升，成交量明顯放大，機構資金流入。</div>
            </div>
        </div>
        """

    # 3. 完整 HTML 模板
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT 終端系統</title>
        <style>
            body {{ background-color: #131722; color: #d1d4dc; font-family: 'PingFang SC', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }}
            .sidebar {{ width: 260px; background: #1e222d; border-right: 1px solid #363c4e; padding: 20px; overflow-y: auto; }}
            .main-content {{ flex: 1; padding: 20px; overflow-y: auto; position: relative; }}
            .search-bar {{ width: 100%; max-width: 600px; background: #2a2e39; border: 1px solid #363c4e; border-radius: 4px; padding: 10px 15px; color: #fff; margin-bottom: 25px; }}
            .mkt-grid {{ display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }}
            .card {{ background: #1e222d; border-radius: 12px; padding: 25px; border: 1px solid #363c4e; margin-bottom: 20px; }}
            .key-insights {{ background: rgba(24, 144, 255, 0.05); border: 1px dashed #1890ff; border-radius: 8px; padding: 15px; font-size: 14px; line-height: 1.8; color: #f0f3fa; margin: 20px 0; }}
            .info-box {{ background: #2a2e39; padding: 12px; border-radius: 6px; font-size: 13px; text-align: center; }}
            .news-item {{ font-size: 13px; color: #848e9c; padding: 8px 0; border-bottom: 1px solid #2a2e39; }}
            .sentiment-box {{ background: #1e222d; border: 1px solid #363c4e; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px; }}
            .gauge {{ width: 120px; height: 120px; border-radius: 50%; border: 8px solid #363c4e; border-top-color: #1890ff; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; }}
            ::-webkit-scrollbar {{ width: 6px; }}
            ::-webkit-scrollbar-thumb {{ background: #363c4e; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div style="font-weight: bold; font-size: 14px; margin-bottom: 20px; color: #1890ff;">🕒 分析任務歷史</div>
            <div style="font-size: 12px; color: #848e9c; line-height: 2.5;">
                <div style="background:#2a2e39; padding:5px 10px; border-radius:4px; margin-bottom:10px;">中国石油 (601857) <span style="float:right">45</span></div>
                <div style="padding:5px 10px;">腾讯控股 (00700) <span style="float:right">35</span></div>
                <div style="padding:5px 10px;">小米集团 (01810) <span style="float:right">35</span></div>
                <div style="padding:5px 10px;">华润三九 (000999) <span style="float:right">42</span></div>
            </div>
            <div style="margin-top: 40px;">
                <div style="font-weight: bold; font-size: 14px; margin-bottom: 20px; color: #1890ff;">📡 數據源健康</div>
                <div style="font-size: 11px;">
                    EM: {health_status.get('EM', '🟢')} <br> Sina: {health_status.get('Sina', '🟢')}
                </div>
            </div>
        </div>

        <div class="main-content">
            <div style="display: flex; gap: 20px; align-items: center; margin-bottom: 30px;">
                <input type="text" class="search-bar" placeholder="輸入股票代碼，如 600519, 00700, AAPL">
                <button style="background: #1890ff; color: white; border: none; padding: 10px 25px; border-radius: 4px; cursor: pointer; font-weight: bold;">分析</button>
            </div>

            <div style="display: flex; gap: 20px;">
                <div style="flex: 3;">
                    <div class="mkt-grid">{index_html}</div>
                    {cards_html}
                </div>
                
                <div style="flex: 1;">
                    <div class="sentiment-box">
                        <div style="font-size: 14px; margin-bottom: 15px;">Market Sentiment</div>
                        <div class="gauge">48</div>
                        <div style="font-size: 14px; color: #1890ff;">中性</div>
                        <div style="font-size: 11px; color: #848e9c; margin-top: 10px;">恐懼貪婪指數</div>
                    </div>
                    <div class="card" style="padding: 15px;">
                        <div style="font-size: 12px; color: #1890ff; font-weight: bold; margin-bottom: 10px;">數據源模式</div>
                        <div style="font-size: 12px;">{source_name}</div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)






















