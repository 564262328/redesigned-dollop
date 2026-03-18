import os
from datetime import datetime

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. 處理指數看板 (橫向排列)
    index_html = ""
    for idx in indices[:4]: # 取前4個核心指數
        chg = float(idx.get('漲跌幅', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        index_html += f"""
        <div style='flex: 1; min-width: 120px; padding: 10px; border-right: 1px solid #f0f0f0;'>
            <div style='font-size: 12px; color: #8c8c8c;'>{idx.get('名稱')}</div>
            <div style='font-size: 16px; font-weight: bold; color: {color};'>{idx.get('最新價')} <small>{chg}%</small></div>
        </div>
        """

    # 2. 按行業分組數據
    grouped_data = {}
    for res in ai_results:
        ind = res.get('industry', '其他板塊')
        if ind not in grouped_data:
            grouped_data[ind] = []
        grouped_data[ind].append(res)

    # 3. 渲染分組卡片
    sections_html = ""
    for industry, stocks in grouped_data.items():
        # 每個行業一個大區塊
        sections_html += f"""
        <div style="margin-bottom: 30px;">
            <h2 style="font-size: 18px; color: #001529; border-left: 4px solid #1890ff; padding-left: 10px; margin-bottom: 15px;">
                {industry} <span style="font-size: 12px; font-weight: normal; color: #999;">({len(stocks)} 檔追蹤)</span>
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 15px;">
        """
        
        for res in stocks:
            chg = float(res.get('change', 0))
            color = "#ff4d4f" if chg > 0 else "#52c41a"
            sections_html += f"""
            <div style="background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <b style="font-size: 16px;">{res.get('name')} <small style="color:#bfbfbf; font-weight:normal;">{res.get('code')}</small></b>
                    <span style="color: {color}; font-weight: bold; font-size: 16px;">{chg}%</span>
                </div>
                <div style="background: #fafafa; padding: 10px; border-radius: 4px; font-size: 13px; line-height: 1.5; color: #595959; margin-bottom: 10px;">
                    <b>🤖 AI 洞察:</b> {res.get('insights')}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #8c8c8c;">
                    <span>🎯 買點: <b style="color:#ff4d4f;">{res.get('buy_point')}</b></span>
                    <span>🛡️ 止損: <b style="color:#52c41a;">{res.get('stop_loss')}</b></span>
                    <span>📊 RSI: {res.get('rsi')}</span>
                </div>
            </div>
            """
        sections_html += "</div></div>"

    # 4. 最終 HTML 模板
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT 核心資產看板</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang TC", sans-serif; background: #f7f8fa; margin: 0; padding: 20px; color: #262626; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ background: #001529; color: #fff; padding: 20px; border-radius: 12px 12px 0 0; display: flex; justify-content: space-between; align-items: center; }}
            .mkt-bar {{ background: #fff; display: flex; flex-wrap: wrap; border-radius: 0 0 12px 12px; margin-bottom: 25px; border: 1px solid #f0f0f0; border-top: none; }}
            .footer {{ margin-top: 40px; padding: 20px; border-top: 1px solid #e8e8e8; font-size: 12px; color: #8c8c8c; line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1 style="margin: 0; font-size: 22px;">🚀 QUANT 智能復盤終端 <span style="font-weight: normal; font-size: 14px; opacity: 0.8;">V15.8</span></h1>
                    <div style="font-size: 12px; margin-top: 5px; opacity: 0.7;">📡 模式: {source_name} | 更新: {update_time}</div>
                </div>
                <div style="text-align: right;">
                    <div style="background: #1890ff; padding: 4px 10px; border-radius: 4px; font-size: 12px;">核心資產監控中</div>
                </div>
            </div>

            <div class="mkt-bar">{index_html}</div>

            {sections_html}

            <div class="footer">
                <b>⚠️ 風險提示：</b><br>
                本報告由 AI 量化機器人自動生成。數據源已切換至「核心資產歷史模擬接口」以確保 GitHub 環境運行穩定。
                AI 洞察基於技術指標與情緒模型，不代表具體買賣建議。市場波動劇烈，投資請務必保持理性，自負盈虧。
                <br><br>
                📡 數據驅動：AkShare & Tencent Finance Service
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)



















