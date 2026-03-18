import requests
import random
import logging
from src.config import Config

logger = logging.getLogger("NewsCenter")

class NewsCenter:
    def __init__(self):
        # 初始化搜索鏈條
        self.bocha_url = "https://api.bochaai.com"
        self.tavilly_url = "https://api.tavilly.com"
        self.serp_url = "https://serpapi.com"
        self.bocha_keys = [k for k in Config.BOCHA_API_KEYS if k]
        self.current_key_idx = 0

    def _get_bocha_key(self):
        if not self.bocha_keys: return None
        key = self.bocha_keys[self.current_key_idx % len(self.bocha_keys)]
        self.current_key_idx += 1
        return key

    def get_stock_context(self, name, code):
        """核心降級檢索邏輯：返回包含內容與來源的字典"""
        query = f"{name} {code} 股票 2026 最新利好利空 財報異動"
        
        # 1. 優先嘗試博查 (中文優化 + AI 摘要)
        context = self._search_bocha(query)
        if context: return {"content": context, "source": "BOCHA"}
        
        # 2. 備選：Tavilly (AI 原生搜索)
        context = self._search_tavilly(query)
        if context: return {"content": context, "source": "TAVILLY"}
        
        # 3. 備選：SerpAPI (Google News)
        context = self._search_serpapi(query)
        if context: return {"content": context, "source": "SERPAPI"}
        
        # 4. 終極保底：SearXNG (自建實例，無損耗)
        context = self._search_searxng(query)
        if context: return {"content": context, "source": "SEARXNG"}
        
        return {"content": "近期公開市場無重大消息。建議關注盤中成交量變化。", "source": "SYSTEM"}

    def _search_bocha(self, query):
        key = self._get_bocha_key()
        if not key: return None
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {"query": query, "freshness": "oneWeek", "summary": True, "count": 3}
        try:
            res = requests.post(self.bocha_url, headers=headers, json=payload, timeout=10)
            data = res.json()
            # 優先提取博查自動生成的 AI 摘要
            return data.get("data", {}).get("summary") or data.get("data", {}).get("webPages", {}).get("value", [{}])[0].get("summary")
        except: return None

    def _search_tavilly(self, query):
        if not Config.TAVILLY_API_KEY: return None
        payload = {"api_key": Config.TAVILLY_API_KEY, "query": query, "search_depth": "smart", "include_answer": True}
        try:
            res = requests.post(self.tavilly_url, json=payload, timeout=10)
            return res.json().get("answer")
        except: return None

    def _search_serpapi(self, query):
        if not Config.SERP_API_KEY: return None
        params = {"q": query, "tbm": "nws", "api_key": Config.SERP_API_KEY, "num": 3}
        try:
            res = requests.get(self.serp_url, params=params, timeout=10)
            snippets = [n.get('snippet', '') for n in res.json().get('news_results', [])]
            return " ".join(snippets) if snippets else None
        except: return None

    def _search_searxng(self, query):
        if not Config.SEARXNG_URL: return None
        params = {"q": query, "format": "json", "categories": "news", "language": "zh-TW"}
        try:
            res = requests.get(f"{Config.SEARXNG_URL}/search", params=params, timeout=5)
            results = res.json().get("results", [])
            return results[0].get("content") if results else None
        except: return None
