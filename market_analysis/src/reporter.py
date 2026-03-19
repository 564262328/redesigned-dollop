import os
from datetime import datetime

class ReportGenerator:
    def get_sentiment_config(self, score):
        """Map 0-100 score to labels and colors"""
        score = float(score)
        if score <= 40:
            return {"label": "Fear", "color": "#52c41a", "desc": "Market sentiment is low."}
        elif score <= 60:
            return {"label": "Neutral", "color": "#faad14", "desc": "Market is in sideways mode."}
        else:
            return {"label": "Greed", "color": "#ff4d4f", "desc": "Market sentiment is high."}

    def render(self, ai_results, source_name, indices, output_path, health_status, sentiment_score=65):
        """Main HTML rendering logic"""
        s_cfg = self.get_sentiment_config(sentiment_score)
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Generate Index HTML
        index_html = ""
        for idx in indices:
            name = idx.get('名稱', '---')
            price = idx.get('最新價', '0')
            chg = float(idx.get('漲跌幅', 0))
            color = "#ff4d4f" if chg > 0 else "#52c41a"
            index_html += f"""
            <div style="margin: 0 15px; text-align: center;">
                <div style="font-size: 12px; color: #848e9c;">{name}</div>
                <div style="font-size: 16px; font-weight: bold; color: {color};">{price}</div>
            </div>"""

        # 2. Generate Stock Cards HTML
        cards_html = ""
        for res in ai_results:
            chg = float(res.get('change', 0))
            color = "#ff4d4f" if chg > 0 else "#52c41a"
            cards_html += f"""
            <div style="background: #151a21; border: 1px solid #2b2f36; border-radius: 10px; padding: 20px; margin: 10px; width: 320px;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-weight: bold; font-size: 18px;">{res.get('name')}</span>
                    <span style="color: {color}; font-size: 18px; font-weight: bold;">{res.get('price')}</span>
                </div>
                <div style="color: #848e9c; font-size: 12px; margin-bottom: 10px;">{res.get('code')} | {res.get('market_tag')}</div>
                <div style="background: rgba(201, 148, 0, 0.1); border-left: 3px solid #c99400; padding: 10px; font-size: 13px; margin: 10px 0;">
                    <strong style="color: #c99400; display: block; margin-bottom: 5px;">🤖 AI ANALYSIS</strong>
                    {res.get('insights', 'No data available.')}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #ff9d00;">
                    <span>🎯 {res.get('buy_point', 'Observe')}</span>
                    <span>📈 {res.get('trend_prediction', 'Stable')}</span>
                </div>
            </div>"""

        # 3. Complete Dashboard Template
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>QUANT PRO | AI Terminal</title>
            <style>
                body {{ background: #0b0e11; color: #eaecef; font-family: sans-serif; margin: 0; padding: 20px; }}
                .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2b2f36; padding-bottom: 20px; margin-bottom: 20px; }}
                .index-bar {{ display: flex; background: #1e2329; padding: 15px; border-radius: 8px; margin-bottom: 30px; }}
                .grid {{ display: flex; flex-wrap: wrap; justify-content: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div style="font-size: 24px; font-weight: bold; color: #c99400;">QUANT PRO V15.8</div>
                <div style="text-align: right;">
                    <div style="color: {s_cfg['color']}; font-weight: bold;">Market Heat: {int(sentiment_score)} ({s_cfg['label']})</div>
                    <div style="font-size: 12px; color: #848e9c;">Last Update: {update_time}</div>
                </div>
            </div>
            <div class="index-bar">{index_html}</div>
            <div class="grid">{cards_html}</div>
        </body>
        </html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)



