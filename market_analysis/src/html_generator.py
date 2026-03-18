import os
from datetime import datetime

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 指數看板渲染
    index_html = ""
    for idx in indices:
        chg = float(idx.get('漲跌幅', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        index_html += f"""
        <div style='flex: 1; min-width: 150px; border-right: 1px solid #eee; padding: 5px 15px;'>
            <div style='font-size: 12px; color: #666;'>{idx.get('名稱')}</div>
            <div style='font-size: 18px; font-weight: bold; color: {color};'>{idx.get('最新價')} <small>{chg}%</small></div>
        </div>
        """

    # AI 個股卡片渲染
    cards_html = ""
    for res in ai_results:
        chg = float(res.get('change', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        cards_html += f"""
        <div style="border: 1px solid #e8e8e8; border-radius: 8px; padding: 18px; margin-bottom: 15px; background: #fff;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <div>
                    <h3 style="margin: 0; font-size: 18px;">{res.get('name')} <span style="font-size: 12px; color: #999; font-weight: normal;">{res.get('code')}</span></h3>
                    <div style="font-size: 12px; color: #1890ff; margin-top: 4px;">📊 籌碼狀態: {res.get('chip_status', '未知')}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 20px; font-weight: bold; color: {color};">{chg}%</div>
                    <div style="font-size: 12px; color: #999;">最新價: {res.get('price')}</div>
                </div>
            </div>
            <div style="background: #f9f9f9; padding: 12px; border-radius: 6px; font-size: 14px; line-height: 1.6; color: #333;">
                <b>🤖 AI 深度洞察:</b> {res.get('insights')}
            </div>
            <div style="display: flex; gap: 15px; margin-top: 12px; font-size: 13px;">
                <span style="color: #ff4d4f;">🎯 建議買點: {res.get('buy_point')}</span>
                <span style="color: #52c41a;">🛡️ 止損參考: {res.get('stop_loss')}</span>
                <span style="color: #8c8c8c;">📈 RSI: {res.get('rsi')}</span>
            </div>
        </div>
        """

    # 完整 HTML 模板
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT 終端 | AI 盤後復盤</title>
        <style>
            body {{ font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif; background: #f0f2f5; color: #262626; max-width: 850px; margin: 0 auto; padding: 20px; }}
            .container {{ background: transparent; }}
            .header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; border-bottom: 2px solid #1890ff; padding-bottom: 10px; }}
            .mkt-panel {{ display: flex; flex-wrap: wrap; background: #fff; border-radius: 8px; margin-bottom: 20px; padding: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
            .data-source {{ font-size: 12px; color: #8c8c8c; display: flex; align-items: center; gap: 5px; }}
            .warning-box {{ background: #fff2f0; border: 1px solid #ffccc7; padding: 15px; border-radius: 8px; font-size: 13px; color: #ff4d4f; margin-top: 30px; line-height: 1.5; }}
            .tencent-tag {{ background: #0052d9; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; vertical-align: middle; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1 style="margin: 0; color: #001529; font-size: 24px;">🚀 QUANT 智能復盤終端 <small style="font-weight: normal; font-size: 14px; color: #666;">V15.8</small></h1>
                    <div class="data-source">
                        <span>📡 實時數據源: <b>{source_name}</b></span>
                        <span class="tencent-tag">Tencent Data Cloud</span>
                        <span>| 全市場掃描: {total_count} 檔</span>
                    </div>
                </div>
                <div style="text-align: right; font-size: 12px; color: #999;">
                    生成時間: {update_time}
                </div>
            </div>

            <div class="mkt-panel">{index_html}</div>

            <div>
                <h2 style="font-size: 18px; margin-bottom: 15px; display: flex; align-items: center;">🔥 AI 焦點個股 <span style="font-size: 12px; font-weight: normal; color: #8c8c8c; margin-left: 10px;">(基於漲幅與籌碼篩選)</span></h2>
                {cards_html}
            </div>

            <div class="warning-box">
                <b>⚠️ 投資風險提示：</b><br>
                本報告由 AI 自動生成，數據來源包括東方財富、新浪及騰訊財經。AI 分析僅供技術探討與數據整合參考，不構成具體的投資建議。市場有風險，投資需謹慎。請用戶務必結合自身風險承受能力進行獨立判斷。
            </div>
            
            <div style="text-align: center; margin-top: 40px; color: #bfbfbf; font-size: 12px;">
                © 2026 QUANT Terminal Deployment Bot. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)


















