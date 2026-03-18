import os
from datetime import datetime

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices):
    """
    生成可视化 HTML 报告
    """
    # 获取当前时间
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 构造指数看板 HTML
    index_html = ""
    for idx in indices:
        name = idx.get('名称', '未知')
        price = idx.get('最新价', '0')
        chg = idx.get('涨跌幅', '0%')
        color = "red" if "+" in str(chg) or (isinstance(chg, (int, float)) and chg > 0) else "green"
        index_html += f"<div style='margin-right:20px; color:{color}'><b>{name}</b>: {price} ({chg}%)</div>"

    # 构造个股卡片 HTML
    cards_html = ""
    for res in ai_results:
        color = "red" if float(str(res.get('change', 0)).replace('%','')) > 0 else "green"
        cards_html += f"""
        <div style="border:1px solid #ddd; border-radius:8px; padding:15px; margin-bottom:15px; background:#f9f9f9;">
            <h3 style="margin-top:0;">{res.get('stock_name')} ({res.get('stock_code')}) <span style="color:{color}">{res.get('change')}%</span></h3>
            <p><b>🤖 AI 洞察:</b> {res.get('insights')}</p>
            <div style="display:flex; justify-content:space-between; font-size:0.9em; color:#666;">
                <span>🎯 买点: {res.get('buy_point')}</span>
                <span>🛡️ 止损: {res.get('stop_loss')}</span>
                <span>📊 筹码: {res.get('chip_status', '未知')}</span>
            </div>
        </div>
        """

    # 完整 HTML 模版
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>QUANT 终端行情报告</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; color: #333; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .mkt-summary {{ display: flex; background: #eee; padding: 10px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ font-size: 0.8em; color: #999; text-align: center; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 QUANT 智能看板</h1>
            <div style="text-align:right">
                <div>更新: {update_time}</div>
                <div>来源: {source_name} | 总数: {total_count}</div>
            </div>
        </div>

        <div class="mkt-summary">
            {index_html}
        </div>

        <div>
            <h2>🔥 热门个股 AI 分析 (Top {len(ai_results)})</h2>
            {cards_html}
        </div>

        <div class="footer">
            数据由 AkShare 提供 | AI 生成分析仅供参考，不构成投资建议。
        </div>
    </body>
    </html>
    """

    # 写入文件
    report_path = "index.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"📄 报告已生成至: {os.path.abspath(report_path)}")















