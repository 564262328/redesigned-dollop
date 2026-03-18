import os
import json
import time
import requests
import logging
from src.config import Config
from data_provider.news_center import NewsCenter

logger = logging.getLogger("StockAnalyzer")

class StockAnalyzer:
    def __init__(self):
        # 初始化新聞引擎
        self.nc = NewsCenter()

    def _call_ai_api(self, prompt):
        """調用大模型接口 (GPT-4o-mini 或 DeepSeek)"""
        if not Config.AI_API_KEY:
            logger.error("❌ 未檢測到 AI_API_KEY，請在 GitHub Secrets 中配置。")
            return None
            
        headers = {
            "Authorization": f"Bearer {Config.AI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是一位擁有 20 年經驗的華爾街量化分析師，擅長結合實時消息面與技術指標給出精準判斷。"},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }

        try:
            res = requests.post(
                f"{Config.AI_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=45
            )
            res.raise_for_status()
            content = res.json()['choices']['message']['content']
            return json.loads(content)
        except Exception as e:
            logger.error(f"⚠️ AI 接口調用異常: {e}")
            return None

    def analyze_single(self, name, market_data):
        """
        核心分析方法：執行 RAG (檢索增強生成)
        :param name: 股票名稱
        :param market_data: 包含價格、漲跌、MA、RSI、籌碼的字典
        """
        # 1. 獲取實時新聞物件 (包含 {"content": ..., "source": ...})
        news_obj = self.nc.get_stock_context(name, market_data.get('code'))
        
        # 2. 構建深度 RAG Prompt
        prompt = f"""
        請針對股票 【{name} ({market_data.get('code')})】 進行深度復盤分析。
        
        【今日實時行情】:
        - 當前價格: {market_data.get('price')} (漲跌幅: {market_data.get('change')}%)
        - 市場板塊: {market_data.get('market_tag')}
        - 技術狀態: MA5/10/20 均線位置({market_data.get('ma5')}/{market_data.get('ma10')}/{market_data.get('ma20')})，形態: {market_data.get('bullish')}
        - 籌碼與指標: RSI={market_data.get('rsi')}, 獲利盤={market_data.get('profit_ratio')}
        
        【最新消息面 (來源: {news_obj['source']})】:
        {news_obj['content']}
        
        分析要求:
        1. insights: 結合上述消息面與技術形態，給出 150 字以內的深度洞察。
        2. buy_point: 給出具體的建議操作位（如：回踩 MA5 買入、觀望、或突破壓力位）。
        3. trend_prediction: 預測未來 3-5 個交易日的走勢（如：強勢上攻、震盪洗盤、走弱回調）。
        
        必須以繁體中文 JSON 格式返回，包含鍵: insights, buy_point, trend_prediction。
        """

        # 3. 執行 AI 分析
        ai_res = self._call_ai_api(prompt)
        
        # 4. 合併結果：確保返回的結果中包含新聞物件，以便 reporter.py 渲染顏色標籤
        if not ai_res:
            ai_res = {
                "insights": "數據源同步延遲，AI 正在重試分析中。請參考下方實時技術位與籌碼分佈。",
                "buy_point": "觀望",
                "trend_prediction": "不明"
            }
        
        # 【關鍵】將新聞物件注入分析結果，供 HTML 模板使用
        ai_res['news_snapshot'] = news_obj
        
        return ai_res
