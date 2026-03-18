from datetime import datetime
from src.config import Config

class ReportGenerator:
    def format_val(self, v):
        return f"{float(v)/1e8:.2f} 億" if float(v) >= 1e8 else f"{v:.2f}"

    def render(self, results, source):
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        cards_html = ""
        for res in results:
            color = "#ff4d4f" if float(res.get('change',0)) > 0 else "#52c41a"
            tag_color = "#1890ff" if res.get('market_tag') == "A股" else "#eb2f96" if res.get('market_tag') == "港股" else "#722ed1"
            
            cards_html += f"""
            <div class="card">
                <div style="display:flex;justify-content:space-between">
                    <b>{res.get('name')} <small style="color:#848e9c">({res.get('code')})</small> <span class="tag" style="background:{tag_color}">{res.get('market_tag')}</span></b>
                    <span style="color:{color};font-weight:bold">{res.get('price')} ({res.get('change')}%)</span>
                </div>
                <div class="stats">PE:{res.get('pe')} | 換手:{res.get('turnover')}% | 市值:{self.format_val(res.get('total_mv'))}</div>
                <div class="insights"><b>🤖 AI:</b> {res.get('insights')}</div>
                <div class="footer">獲利:{res.get('profit')} | 集中度:超高 | 🎯 {res.get('buy_point')}</div>
            </div>"""

        # 完整 HTML 模板 (此处组合之前的专业 Dark Mode 样式)
        html = f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8"><title>QUANT PRO</title>
        <style>
            body {{ background:#0b0e11; color:#d1d4dc; font-family:sans-serif; display:flex; margin:0; height:100vh; overflow:hidden; }}
            .sidebar {{ width:240px; background:#151a21; border-right:1px solid #2b2f36; padding:20px; }}
            .main {{ flex:1; padding:20px; overflow-y:auto; }}
            .grid {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap:20px; }}
            .card {{ background:#151a21; border:1px solid #2b2f36; border-radius:12px; padding:15px; }}
            .tag {{ font-size:10px; color:white; padding:1px 4px; border-radius:3px; margin-left:5px; }}
            .stats {{ font-size:11px; color:#1890ff; margin:10px 0; }}
            .insights {{ background:rgba(24,144,255,0.05); padding:10px; border-left:3px solid #1890ff; font-size:13px; border-radius:4px; }}
            .search-bar {{ width:100%; max-width:400px; background:#1e2329; border:1px solid #2b2f36; padding:10px; color:white; border-radius:4px; margin-bottom:20px; }}
        </style></head><body>
        <div class="sidebar">
            <h3>⚡ QUANT PRO</h3>
            <div style="font-size:12px;color:#848e9c">更新:{update_time}<br>源:{source}</div>
            <div style="margin-top:30px">
                <div style="font-size:13px;color:#c99400">🔥 市場情緒</div>
                <div style="background:#1e2329;height:8px;border-radius:4px;margin:10px 0"><div style="width:68%;background:#c99400;height:100%"></div></div>
                <div style="text-align:center;font-weight:bold">68 - {Config.SENTIMENT_LABEL}</div>
            </div>
        </div>
        <div class="main">
            <input class="search-bar" placeholder="🔍 搜尋股票代碼分析 (如 00700)...">
            <div class="grid">{cards_html}</div>
        </div></body></html>"""
        
        with open(Config.REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(html)
