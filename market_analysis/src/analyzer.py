import json
import requests
import logging
from src.config import Config

logger = logging.getLogger("StockAnalyzer")

class StockAnalyzer:
    def _call_ai_api(self, prompt):
        if not Config.AI_API_KEY:
            logger.error("❌ Missing AI_API_KEY")
            return None
        
        # Build the correct endpoint
        base_url = Config.AI_BASE_URL.rstrip('/')
        url = f"{base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {Config.AI_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是一位量化分析師，請使用簡體中文分析數據並輸出 JSON 格式。"},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code != 200:
                logger.error(f"⚠️ AI API Error {res.status_code}: {res.text}")
                return None
            
            content = res.json()['choices'][0]['message']['content']
            return json.loads(content)
        except Exception as e:
            logger.error(f"⚠️ AI Exception: {e}")
            return None

    def analyze_single(self, name, market_data):
        # Build prompt using market data
        prompt = f"""
        请分析股票: {name} ({market_data.get('code')})。
        实时数据: 现价 {market_data.get('price')}, 涨跌幅 {market_data.get('change')}%, 换手率 {market_data.get('turnover')}%。
        技术指标: MA5/10/20 排列 {market_data.get('bullish')}, RSI {market_data.get('rsi')}。
        
        请输出以下 JSON 字段:
        - insights: 简短的分析观点
        - buy_point: 建议动作 (积极买入/观望/减仓)
        - trend_prediction: 趋势预测 (看多/震荡/看空)
        """
        
        ai_res = self._call_ai_api(prompt)
        
        # Fallback if API fails
        if not ai_res:
            ai_res = {
                "insights": "AI 服务暂时不可用，请参考技术指标。", 
                "buy_point": "观望", 
                "trend_prediction": "盘整"
            }
        
        return ai_res


