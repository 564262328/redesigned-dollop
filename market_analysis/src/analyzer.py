class StockAnalyzer:
    def analyze_single(self, name, market_data):
        # 1. 抓取實時新聞物件 (含 content 和 source)
        news_obj = self.nc.get_stock_context(name, market_data['code'])
        
        # 2. 執行 AI 分析
        prompt = f"分析股票 {name}... 新聞背景: {news_obj['content']} ..."
        analysis = self._call_ai_api(prompt)
        
        # 3. 合併結果：將新聞物件原樣保留
        analysis['news_snapshot'] = news_obj
        return analysis
