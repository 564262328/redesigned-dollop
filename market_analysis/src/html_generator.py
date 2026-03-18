import os
from datetime import datetime

def generate_report(ai_results, new_count, total_count, source_name, industry_data, indices, output_path, health_status):
    """
    生成專業級 QUANT 復盤報告
    :param ai_results: AI 分析結果清單
    :param new_count: 新股數量
    :param total_count: 掃描總數
    :param source_name: 當前主力數據源名稱
    :param industry_data: 行業熱力圖數據
    :param indices: 大盤指數數據
    :param output_path: HTML 輸出絕對路徑
    :param health_status: 數據源熔斷監控狀態字典
    """
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. 構建數據源健康狀態燈 HTML
    health_html = ""
    for name, status in health_status.items():
        # 根據狀態標籤判斷顏色
        if "🟢" in status: color, bg = "#52c41a", "#f6ffed"  # 正常-綠
        elif "🔴" in status: color, bg = "#ff4d4f", "#fff2f0" # 熔斷-紅
        else: color, bg = "#faad14", "#fffbe6"               # 恢復-黃
        
        health_html += f"""
        <span style="display:inline-block; margin-right:8px; padding:2px 10px; border-radius:4px; 
                     border:1px solid {color}; color:{color}; background:{bg}; font-size:11px; font-weight:bold;">
            {name} {status}
        </span>
        """

    # 2. 處理大盤指數看板
    index_html = ""
    for idx in indices[:4]:
        name = idx.get('名稱', '未知')
        price = idx.get('最新價', '0.00')
        chg = float(idx.get('漲跌幅', 0))
        color = "#ff4d4f" if chg > 0 else "#52c41a"
        symbol = "+" if chg > 0 else ""
        index_html += f"""
        <div style='flex: 1; min-width: 140px; padding: 10px 15px; border-right: 1px solid #f0f0f0;'>
            <div style='font-size: 12px; color: #8c8c8c; margin-bottom:4px;'>{name}</div>
            <div style='font-size: 18px; font-weight: bold; color: {color};'>{price} <small style='font-size:12px;'>{symbol}{chg}%</small></div>
        </div>
        """

    # 3. 按行業分組 AI 分析數據
    grouped_data = {}
    for res in ai_results:
        ind = res.get('industry', '其他板塊')
        if ind not in grouped_data:
            grouped_data[ind] = []
        grouped_data[ind].append(res)

    # 4. 渲染行業分組個股卡片
    sections_html = ""
    for industry, stocks in grouped_data.items():
        sections_html += f"""
        <div style="margin-bottom: 35px;">
            <h2 style="font-size: 18px; color: #001529; border-left: 5px solid #1890ff; padding-left: 12px; margin-bottom: 20px; display:flex; align-items:center;">
                {industry} <span style="font-size: 12px; font-weight: normal; color: #999; margin-left:10px;">(追蹤 {len(stocks)} 檔核心標的)</span>
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 20px;">
        """
        
        for res in stocks:
            chg = float(res.get('change', 0))
            price = res.get('price', '0.00')
            color = "#ff4d4f" if chg > 0 else "#52c41a"
            symbol = "+" if chg > 0 else ""
            
            sections_html += f"""
            <div style="background: #fff; border: 1px solid #e8e8e8; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); transition: transform 0.2s;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div>
                        <b style="font-size: 18px; color:#1a1a1a;">{res.get('name')}</b>
                        <code style="background:#f5f5f5; color:#666; padding:2px 6px; border-radius:4px; font-size:12px; margin-left:5px;">{res.get('code')}</code>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: {color}; font-weight: bold; font-size: 20px;">{symbol}{chg}%</div>
                        <div style="font-size: 12px; color: #bfbfbf;">Price: {price}</div>
                    </div>
                </div>
                <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6; color: #333; margin-bottom: 15px; border: 1px solid #f0f0f0;">
                    <b style="color:#1890ff;">🤖 AI 洞察:</b> {res.get('insights')}
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
                    <div style="color:#ff4d4f;">🎯 買點: <b>{res.get('buy_point')}</b></div>
                    <div style="color:#52c41a;">🛡️ 止損: <b>{res.get('stop_loss')}</b></div>
                    <div style="color:#8c8c8c;">📊 籌碼: {res.get('chip_status', '穩定')}</div>
                    <div style="color:#8c8c8c;">📈 RSI: {res.get('rsi', '--')}</div>
                </div>
            </div>
            """
        sections_html += "</div></div>"

    # 5. 構建完整 HTML 模板
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QUANT 智能復盤終端</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang TC", sans-serif; background: #f4f7f9; margin: 0; padding: 25px; color: #262626; }}
            .container {{ max-width: 1100px; margin: 0 auto; }}
            .header {{ background: #001529; color: #fff; padding: 30px; border-radius: 16px 16px 0 0; box-shadow: 0 4px 20px rgba(0,21,41,0.15); }}
            .mkt-bar {{ background: #fff; display: flex; flex-wrap: wrap; border-radius: 0 0 16px 16px; margin-bottom: 30px; border: 1px solid #e8e8e8; border-top: none; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .tencent-tag {{ background: #0052d9; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; letter-spacing: 0.5px; }}
            .footer {{ margin-top: 50px; padding: 30px; background: #fff; border-radius: 12px; border: 1px solid #e8e8e8; font-size: 13px; color: #595959; line-height: 1.8; }}
            @media (max-width: 600px) {{ .mkt-bar {{ flex-direction: column; }} .mkt-bar > div {{ border-right: none; border-bottom: 1px solid #f0f0f0; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h1 style="margin: 0; font-size: 26px; letter-spacing: 1px;">🚀 QUANT 智能復盤終端 <span style="font-weight: normal; font-size: 14px; opacity: 0.6;">v15.8 PRO</span></h1>
                        <div style="margin-top: 15px;">{health_html}</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="tencent-tag">TENCENT CLOUD DATA</div>
                        <div style="font-size: 12px; margin-top: 8px; opacity: 0.7;">更新時間: {update_time}</div>
                    </div>
                </div>
                <div style="margin-top: 20px; font-size: 13px; color: rgba(255,255,255,0.7); display: flex; gap: 20px;">
                    <span>📡 主力數據源: <b style="color:#fff;">{source_name}</b></span>
                    <span>🔍 掃描樣本: {total_count} 檔標的</span>
                </div>
            </div>

            <div class="mkt-bar">{index_html}</div>

            {sections_html}

            <div class="footer">
                <b style="color: #ff4d4f; font-size: 15px;">⚠️ 專業風險提示與聲明：</b><br>
                1. <b>數據說明</b>：本報告數據整合自東方財富爬蟲、新浪財經 API 及騰訊財經數據雲。當前系統已激活熔斷保護機制，確保在高頻監控下的連線穩定性。<br>
                2. <b>AI 算法</b>：報告中「AI 洞察」內容由 GPT-4o-mini 模型基於實時 K 線、技術指標（RSI/籌碼分布）及板塊聯動性自動生成，不代表人工審核意見。<br>
                3. <b>免責聲明</b>：量化分析結果僅供科研與模擬盤參考，<b>不構成任何形式的投資建議、要約或保證</b>。金融市場具備高度不可預測性，請務必根據自身財務狀況及風險承受能力獨立決策，自負盈虧。
                <br><br>
                <div style="text-align: center; border-top: 1px solid #f0f0f0; padding-top: 20px; color: #bfbfbf;">
                    © 2026 QUANT Deployment Engine. Powered by AkShare Open Data.
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # 安全地寫入文件
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        print(f"✅ 成功生成復盤報告: {output_path}")
    except Exception as e:
        print(f"❌ 報告寫入失敗: {e}")





















