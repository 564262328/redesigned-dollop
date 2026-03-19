import os
from datetime import datetime

class ReportGenerator:
    def get_sentiment_config(self, score):
        score = float(score)
        if score <= 40:
            return {"label": "恐慌", "color": "#52c41a", "desc": "市场处于低位。"}
        elif score <= 60:
            return {"label": "中性", "color": "#faad14", "desc": "横盘整理中。"}
        else:
            return {"label": "贪婪", "color": "#ff4d4f", "desc": "警惕冲高回落。"}

    def render(self, ai_results, source_name, indices, output_path, health_status, sentiment_score=65):
        """生成最终的 HTML 仪表盘"""
        s_cfg = self.get_sentiment_config(sentiment_score)
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. 渲染顶部指数
        index_html = ""
        for idx in indices:
            name = idx.get('名稱', '---')
            price = idx.get('最新價', '0')
            chg = float(idx.get('漲跌幅', 0))
            color = "#ff4d4f" if chg >= 0 else "#52c41a"
            index_html += f"""
            <div style="margin: 0 20px; text-align: left; border-right: 1px solid #2b2f36; padding-right: 20px;">
                <div style="font-size: 12px; color: #848e9c;">{name}</div>
                <div style="font-size: 18px; font-weight: bold; color: {color};">{price}</div>
            </div>"""

        # 2. 渲染股票分析卡片
        cards_html = ""
        for res in ai_results:
            chg = float(res.get('change', 0))
            color = "#ff4d4f" if chg >= 0 else "#52c41a"
            cards_html += f"""
            <div style="background: #151a21; border: 1px solid #2b2f36; border-radius: 12px; padding: 20px; margin: 10px; width: 340px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: bold; font-size: 20px;">{res.get('name')}</span>
                    <span style="color: {color}; font-size: 20px; font-weight: 800;">{res.get('price')}</span>
                </div>
                <div style="color: #848e9c; font-size: 13px; margin-bottom: 15px;">{res.get('code')} | {res.get('market_tag')} | 涨跌: {res.get('change')}%</div>
                
                <div style="background: rgba(201, 148, 0, 0.05); border-left: 4px solid #c99400; padding: 12px; border-radius: 4px; margin-bottom: 15px;">
                    <div style="color: #c99400; font-size: 11px; font-weight: bold; margin-bottom: 5px; letter-spacing: 1px;">🤖 AI QUANT ANALYSIS</div>
                    <div style="font-size: 14px; line-height: 1.6; color: #eaecef;">{res.get('insights')}</div>
                </div>

                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <span style="color: #ff9d00; font-weight: bold;">🎯 {res.get('buy_point')}</span>
                    <span style="color: #1890ff; font-weight: bold;">📈 {res.get('trend_prediction')}</span>
                </div>
            </div>"""

        # 3. 完整网页模板
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>QUANT PRO V15.8</title>
            <style>
                body {{ background-color: #0b0e11; color: #eaecef; font-family: -apple-system, "微软雅黑", sans-serif; margin: 0; padding: 25px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid #2b2f36; padding-bottom: 15px; margin-bottom: 25px; }}
                .index-bar {{ display: flex; background: #1e2329; padding: 20px; border-radius: 10px; margin-bottom: 30px; border: 1px solid #2b2f36; overflow-x: auto; }}
                .grid {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div>
                        <div style="font-size: 26px; font-weight: 900; color: #c99400; letter-spacing: 1px;">QUANT PRO V15.8</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: {s_cfg['color']}; font-weight: bold; font-size: 16px;">市场热度: {int(sentiment_score)} ({s_cfg['label']})</div>
                        <div style="font-size: 12px; color: #848e9c; margin-top: 5px;">最后更新: {update_time} | 来源: {source_name}</div>
                    </div>
                </div>
                <div class="index-bar">{index_html}</div>
                <div class="grid">{cards_html}</div>
            </div>
        </body>
        </html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)




