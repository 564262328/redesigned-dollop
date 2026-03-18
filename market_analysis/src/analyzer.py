import requests, json, time
from src.config import Config

class StockAnalyzer:
    def batch_process(self, df, dc):
        # 筛选 20 档分析目标
        top_10 = df.sort_values(by='change', ascending=False).head(10)
        others = df[~df['code'].isin(top_10['code'])].sample(n=min(10, len(df)-10))
        target_df = pd.concat([top_10, others])

        results = []
        for _, row in target_df.iterrows():
            print(f"🤖 正在分析: {row['name']}...")
            chips = dc.get_chips(row['code'])
            combined = {**row.to_dict(), **chips}
            
            # AI 请求
            ai_res = self._call_ai(row['name'], combined) or {"insights":"數據同步中","buy_point":"觀望","trend":"橫盤"}
            ai_res.update(combined)
            results.append(ai_res)
            time.sleep(0.5)
        return results

    def _call_ai(self, name, data):
        try:
            res = requests.post(f"{Config.AI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {Config.AI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini", 
                    "messages": [{"role": "user", "content": f"分析股票 {name}: {data}。繁體中文回傳 JSON: insights, buy_point, trend。"}],
                    "response_format": {"type": "json_object"}, "temperature": 0.2
                }, timeout=30)
            return json.loads(res.json()['choices']['message']['content'])
        except: return None
