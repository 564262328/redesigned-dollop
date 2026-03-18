import json
import requests
import logging
from src.config import Config
from data_provider.news_center import NewsCenter

logger = logging.getLogger("StockAnalyzer")

class StockAnalyzer:
    def __init__(self):
        self.nc = NewsCenter()

    def _call_ai_api(self, prompt):
        if not Config.AI_API_KEY: return None
        
        # 修正：aihubmix 必須包含 /v1/chat/completions
        base_url = Config.AI_BASE_URL.rstrip('/')
        url = f"{base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {Config.AI_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是一位量化分析師，請輸出繁體中文 JSON。"},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code != 200:
                logger.error(f"⚠️ AI 錯誤 {res.status_code}: {res.text}")
                return None
            return json.loads(res.json()['choices']['message']['content'])
        except Exception as e:
            logger.error(f"⚠️ AI 異常: {e}")
            return None

    def analyze_single(self, name, market_data):
        # 獲取新聞物件
        news_obj = self.nc.get_stock_context(name, market_data.get('code'))
        prompt = f"分析股票 {name}({market_data.get('code')})。數據: {market_data}。新聞: {news_obj['content']}。"
        
        ai_res = self._call_ai_api(prompt)
        if not ai_res:
            ai_res = {"insights": "AI 服務暫不可用，請參考技術指標。", "buy_point": "觀望", "trend_prediction": "盤整"}
        
        ai_res['news_snapshot'] = news_obj
        return ai_res


