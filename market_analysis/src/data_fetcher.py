import time as _time
import random
import logging
import pandas as pd
import akshare as ak
from typing import Optional, List, Dict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QuantDataCenter")

class DataFetchError(Exception): pass
class RateLimitError(DataFetchError): pass

class OptimizedDataFetcher:
    def __init__(self):
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]
        # 熔断器：记录每个源的失效截至时间
        self._circuit_breaker: Dict[str, float] = {}
        # 标准列名映射表
        self._column_map = {
            "开盘": "open", "收盘": "close", "最高": "high", "最低": "low", 
            "成交量": "volume", "成交额": "amount", "日期": "date", "涨跌幅": "pct_chg",
            "open": "open", "close": "close", "high": "high", "low": "low", "volume": "volume", "amount": "amount"
        }

    def _get_headers(self) -> Dict[str, str]:
        return {"User-Agent": random.choice(self.ua_list)}

    def _enforce_rate_limit(self):
        """2026 防封禁策略：智能随机休眠"""
        _time.sleep(random.uniform(0.6, 1.4))

    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """统一数据清洗引擎"""
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 1. 列名标准化（模糊匹配）
        df.columns = [self._column_map.get(col, col) for col in df.columns]
        
        # 2. 日期格式统一
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
        # 3. 核心数值转换（确保float）
        numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 4. 计算涨跌幅 (若缺失)
        if 'pct_chg' not in df.columns and 'close' in df.columns:
            df['pct_chg'] = df['close'].pct_change() * 100
            
        return df.dropna(subset=['date', 'close'])

    def _check_circuit(self, source_name: str) -> bool:
        """检查熔断状态"""
        if source_name in self._circuit_breaker:
            if _time.time() < self._circuit_breaker[source_name]:
                logger.warning(f"⚠️ [熔断] {source_name} 处于冷却期，自动跳过")
                return False
        return True

    def _trigger_circuit(self, source_name: str):
        """激活熔断 (冷却10分钟)"""
        self._circuit_breaker[source_name] = _time.time() + 600
        logger.error(f"🚨 [熔断激活] {source_name} 响应异常，已关断10分钟")

    def fetch_stock_hist(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """策略模式：A股历史数据获取（含Fallback逻辑）"""
        strategies = [
            (self._fetch_em_hist, "东方财富"),
            (self._fetch_sina_hist, "新浪财经"),
            (self._fetch_tx_hist, "腾讯财经")
        ]

        last_error = None
        for strategy_func, source_name in strategies:
            if not self._check_circuit(source_name):
                continue

            try:
                logger.info(f"🌐 [数据源] 正在尝试: {source_name} (代码: {stock_code})")
                df = strategy_func(stock_code, start_date, end_date)
                
                if df is not None and not df.empty:
                    logger.info(f"✅ [成功] 数据源: {source_name}")
                    return self._normalize_data(df)
                    
            except Exception as e:
                last_error = e
                logger.warning(f"❌ [失败] {source_name}: {str(e)}")
                # 如果检测到被限制，触发熔断
                if "limit" in str(e).lower() or "banned" in str(e).lower():
                    self._trigger_circuit(source_name)
                continue

        raise DataFetchError(f"所有渠道均无法获取数据。最后错误: {last_error}")

    # --- 具体实现部分 ---

    def _fetch_em_hist(self, code: str, start: str, end: str):
        self._enforce_rate_limit()
        return ak.stock_zh_a_hist(
            symbol=code, period="daily",
            start_date=start.replace('-', ''), end_date=end.replace('-', ''),
            adjust="qfq"
        )

    def _fetch_sina_hist(self, code: str, start: str, end: str):
        symbol = self._to_sina_tx_symbol(code)
        self._enforce_rate_limit()
        return ak.stock_zh_a_daily(
            symbol=symbol,
            start_date=start.replace('-', ''), end_date=end.replace('-', ''),
            adjust="qfq"
        )

    def _fetch_tx_hist(self, code: str, start: str, end: str):
        symbol = self._to_sina_tx_symbol(code)
        self._enforce_rate_limit()
        return ak.stock_zh_a_hist_tx(
            symbol=symbol,
            start_date=start.replace('-', ''), end_date=end.replace('-', ''),
            adjust="qfq"
        )

    def fetch_etf_hist(self, code: str, start: str, end: str):
        """获取ETF历史数据 (优化版)"""
        try:
            self._enforce_rate_limit()
            df = ak.fund_etf_hist_em(
                symbol=code, period="daily",
                start_date=start.replace('-', ''), end_date=end.replace('-', ''),
                adjustment="qfq"
            )
            return self._normalize_data(df)
        except Exception as e:
            logger.error(f"ETF获取异常: {e}")
            return pd.DataFrame()

    def fetch_us_hist(self, code: str, start: str, end: str):
        """获取美股历史数据 (EM源, 比腾讯更稳定)"""
        try:
            self._enforce_rate_limit()
            df = ak.stock_us_hist(
                symbol=code, period="daily",
                start_date=start.replace('-', ''), end_date=end.replace('-', ''),
                adjust="qfq"
            )
            return self._normalize_data(df)
        except Exception as e:
            logger.error(f"美股获取异常: {e}")
            return pd.DataFrame()

    @staticmethod
    def _to_sina_tx_symbol(code: str) -> str:
        """代码格式智能转换"""
        if code.startswith('6'): return f"sh{code}"
        if code.startswith('0') or code.startswith('3'): return f"sz{code}"
        if code.startswith('4') or code.startswith('8'): return f"bj{code}"
        return code














