from data_provider.fundamental_center import FundamentalCenter

class StockAnalyzer:
    def __init__(self):
        self.fc = FundamentalCenter()

    def analyze_single(self, row):
        code = row['code']
        # 獲取基本面聚合數據
        fundamental_res = self.fc.get_stock_fundamentals(code)
        
        # 構建 AI 提示詞
        fundamental_info = ""
        if fundamental_res['status'] != "not_supported":
            fundamental_info = f"基本面數據: {fundamental_res['data']}"
        else:
            fundamental_info = "基本面分析: 當前模式未啟用"

        prompt = f"""
        分析股票: {row['name']} ({code})
        即時行情: 價格 {row['price']}, 漲跌 {row['change']}%
        技術指標: MA5={row.get('ma5')}, 多頭排列={row.get('bullish')}
        {fundamental_info}
        
        請給出深度投資洞察。
        """
        # ... 調用 AI 接口邏輯 ...
