class ReportGenerator:
    def get_source_style(self, source):
        """為不同搜尋引擎分配專屬色彩"""
        styles = {
            "BOCHA": {"color": "#1890ff", "label": "博查 AI 摘要"},     # 科技藍
            "TAVILLY": {"color": "#52c41a", "label": "Tavilly 檢索"},  # 森林綠
            "SERPAPI": {"color": "#fa8c16", "label": "SerpAPI 谷歌"},   # 活力橙
            "SEARXNG": {"color": "#722ed1", "label": "SearXNG 自建"},   # 皇家紫
            "SYSTEM": {"color": "#8c8c8c", "label": "系統保底"}         # 中性灰
        }
        return styles.get(source, styles["SYSTEM"])

    def render(self, ai_results, source_name, indices, output_path, health_status):
        # ... 前面邏輯不變 ...
        
        cards_html = ""
        for res in ai_results:
            # 獲取新聞來源與樣式
            news_obj = res.get('news_snapshot', {"content": "無數據", "source": "SYSTEM"})
            style = self.get_source_style(news_obj['source'])
            
            cards_html += f"""
            <div class="stock-card">
                <!-- ... 原有的股票頭部與技術指標 ... -->

                <div class="news-section" style="margin-top: 15px; border-top: 1px dashed #2b2f36; padding-top: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 10px; font-weight: 800; color: var(--text-muted); letter-spacing: 1px;">
                            LATEST NEWS / 實時資訊
                        </span>
                        <span style="font-size: 9px; padding: 1px 6px; border-radius: 4px; 
                                     background: {style['color']}20; color: {style['color']}; 
                                     border: 1px solid {style['color']}50;">
                            {style['label']}
                        </span>
                    </div>
                    <div style="font-size: 13px; line-height: 1.6; color: #d1d4dc;">
                        {news_obj['content']}
                    </div>
                </div>

                <!-- ... 原有的 AI 深度解析與 Footer ... -->
            </div>
            """
        # ... 後續渲染 ...

