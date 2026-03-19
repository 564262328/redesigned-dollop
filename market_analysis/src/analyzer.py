import json
import requests
import logging
from src.config import Config

logger = logging.getLogger("StockAnalyzer")

class StockAnalyzer:
    def _call_ai_api(self, prompt):
        if not Config.AI_API_KEY:
            logger.error("❌ 未配置 AI_API_KEY")
            return None
        
        # 核心修正：处理 Base URL 的斜杠与 /v1 路径
        base_url = Config.AI_BASE_URL.rstrip('/')
        if base_url.endswith('/v1'):
            url = f"{base_url}/chat/completions"
        else:
            url = f"{base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {Config.AI_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是一位量化分析师。请使用简体中文对股票数据进行深度分析，并输出 JSON 格式。"},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }

        try:
            logger.info(f"📡 正在请求 AI 接口: {url}")
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if res.status_code != 200:
                logger.error(f"⚠️ AI 接口返回异常 {res.status_code}: {res.text}")
                return None
            
            content = res.json()['choices']['message']['content']
            return json.loads(content)
        except Exception as e:
            logger.error(f"⚠️ AI 请求异常: {e}")
            return None

    def analyze_single(self, name, market_data):
        prompt = f"""
        请分析股票: {name} ({market_data.get('code')})。
        数据: 现价 {market_data.get('price')}, 涨跌幅 {market_data.get('change')}%, 换手率 {market_data.get('turnover')}%。
        技术指标: MA5/10/20 排列为 {market_data.get('bullish')}, RSI 为 {market_data.get('rsi')}。
        
        输出格式 JSON:
        - insights: 核心观点
        - buy_point: 建议动作 (积极买入/观望/减仓)
        - trend_prediction: 趋势预测 (看多/震荡/看空)
        """
        
        ai_res = self._call_ai_api(prompt)
        if not ai_res:
            ai_res = {"insights": "AI 服务暂时不可用。", "buy_point": "风险规避", "trend_prediction": "盘整"}
        
        return ai_res




