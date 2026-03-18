import os
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
        if not Config.AI_API_KEY:
            logger.error("❌ 缺少 AI_API_KEY")
            return None
            
        # 修正 URL 拼接問題
        base_url = Config.AI_BASE_URL.rstrip('/')
        url = f"{base_url}/v1/chat/completions" # 確保包含 v1

        headers = {
            "Authorization": f"Bearer {Config.AI_API_KEY.strip()}", # 確保無空格
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DSA/1.0"
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
            # 打印更詳細的錯誤信息以便偵錯
            if res.status_code != 200:
                logger.error(f"⚠️ AI 服務器返回錯誤 {res.status_code}: {res.text}")
                return None
            return json.loads(res.json()['choices']['message']['content'])
        except Exception as e:
            logger.error(f"⚠️ 調用異常: {e}")
            return None

    def analyze_single(self, name, market_data):
        news_obj = self.nc.get_stock_context(name, market_data.get('code'))
        prompt = f"分析股票 {name} ({market_data.get('code')})。行情數據: {market_data}。新聞摘要: {news_obj['content']}。"
        
        ai_res = self._call_ai_api(prompt)
        if not ai_res:
            ai_res = {"insights": "AI 服務暫時不可用（403 Forbidden），請檢查 API Key 狀態。", "buy_point": "觀望", "trend_prediction": "維持現狀"}
        
        ai_res['news_snapshot'] = news_obj
        return ai_res

