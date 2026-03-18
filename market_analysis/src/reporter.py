class ReportGenerator:
    def get_sentiment_config(self, score):
        """根據熱度值 (0-100) 分配標籤與色彩"""
        score = float(score)
        if score <= 20:
            return {"label": "極度恐懼", "color": "#52c41a", "desc": "市場情緒低迷，關注築底機會"}
        elif score <= 40:
            return {"label": "恐懼", "color": "#73d13d", "desc": "市場謹慎，建議輕倉觀察"}
        elif score <= 60:
            return {"label": "中性", "color": "#faad14", "desc": "多空博弈中，關注趨勢方向"}
        elif score <= 80:
            return {"label": "貪婪", "color": "#ff7a45", "desc": "情緒升溫，注意防範追高風險"}
        else:
            return {"label": "極度貪婪", "color": "#ff4d4f", "desc": "情緒過熱，應考慮分批止盈"}

    def render(self, ai_results, source_name, indices, output_path, health_status, sentiment_score=65):
        # 獲取情緒配置
        s_cfg = self.get_sentiment_config(sentiment_score)
        
        # ... 前面 HTML 代碼 ...
        
        # 側邊欄情緒條更新
        sentiment_html = f"""
        <div class="sentiment-container" style="margin-bottom: 35px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span class="sidebar-label">Market Heat</span>
                <span style="color: {s_cfg['color']}; font-weight: 800; font-size: 11px;">{s_cfg['label']}</span>
            </div>
            <div style="background: #1e2329; height: 12px; border-radius: 6px; overflow: hidden; border: 1px solid #2b2f36;">
                <div style="width: {sentiment_score}%; 
                            background: linear-gradient(90deg, #52c41a 0%, {s_cfg['color']} 100%); 
                            height: 100%; transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);">
                </div>
            </div>
            <div style="text-align: center; margin-top: 12px;">
                <div style="font-size: 24px; font-weight: 900; color: {s_cfg['color']};">{int(sentiment_score)}</div>
                <div style="font-size: 10px; color: #4a515c; margin-top: 4px; line-height: 1.4;">{s_cfg['desc']}</div>
            </div>
        </div>
        """
        # ... 後續渲染 ...


