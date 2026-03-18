#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKShare 数据源
AKShare Data Source

免费开源的金融数据接口，支持股票、期货、基金、债券等。
https://akshare.xyz/
"""

import pandas as pd
from datetime import datetime
from typing import List, Optional
from ..sources.base import DataSource
from ...utils.logger import get_logger


class AKShareSource(DataSource):
    """AKShare 数据源类"""
    
    def __init__(self, **kwargs):
        """
        初始化 AKShare 数据源
        
        Args:
            **kwargs: 配置参数
        """
        super().__init__("akshare", **kwargs)
        self.logger = get_logger("data.sources.akshare")
        self.ak = None
    
    def connect(self) -> bool:
        """
        连接到 AKShare
        
        Returns:
            bool: 连接是否成功
        """
        try:
            import akshare as ak
            self.ak = ak
            self.connected = True
            self.logger.info("AKShare connected successfully")
            return True
        except ImportError:
            self.logger.error("AKShare not installed. Run: pip install akshare")
            return False
        except Exception as e:
            self.logger.error(f"AKShare connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        self.connected = False
        self.ak = None
        self.logger.info("AKShare disconnected")
    
    def get_kline(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        获取 K 线数据
        
        Args:
            symbol: 标的代码 (如 000001 或 000001.SZ)
            start_date: 开始日期
            end_date: 结束日期
            interval: K 线周期 (1d, 1w, 1M, 1m, 5m 等)
            
        Returns:
            pd.DataFrame: K 线数据
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("AKShare not connected")
        
        # 解析标的代码
        ts_code = self._parse_symbol(symbol)
        
        # 根据周期选择接口
        if interval in ["1d", "d"]:
            df = self._get_daily_kline(ts_code, start_date, end_date)
        elif interval in ["1w", "w"]:
            df = self._get_weekly_kline(ts_code, start_date, end_date)
        elif interval in ["1M", "M"]:
            df = self._get_monthly_kline(ts_code, start_date, end_date)
        elif interval in ["1m", "5m", "15m", "30m", "60m"]:
            df = self._get_minute_kline(ts_code, start_date, end_date, interval)
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 格式化数据
        df = self._process_kline_data(df, interval)
        
        return df
    
    def get_tick(
        self,
        symbol: str,
        date: datetime,
    ) -> pd.DataFrame:
        """
        获取 Tick 数据
        
        Args:
            symbol: 标的代码
            date: 日期
            
        Returns:
            pd.DataFrame: Tick 数据
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("AKShare not connected")
        
        try:
            ts_code = self._parse_symbol(symbol)
            date_str = date.strftime("%Y%m%d")
            
            # AKShare Tick 数据接口
            df = self.ak.stock_tick(ts_code)
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # 格式化
            df = self._process_tick_data(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Get tick data failed: {e}")
            return pd.DataFrame()
    
    def get_symbols(self, market: Optional[str] = None) -> List[str]:
        """
        获取标的列表
        
        Args:
            market: 市场代码 (SSE/SZSE)
            
        Returns:
            List[str]: 标的代码列表
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("AKShare not connected")
        
        try:
            # 获取 A 股列表
            if market == "SSE":
                df = self.ak.stock_info_a_code_name()
            elif market == "SZSE":
                df = self.ak.stock_info_a_code_name()
            else:
                df = self.ak.stock_info_a_code_name()
            
            if df is None or df.empty:
                return []
            
            # 返回代码列表
            if "code" in df.columns:
                return df["code"].tolist()
            elif "symbol" in df.columns:
                return df["symbol"].tolist()
            
            return []
            
        except Exception as e:
            self.logger.error(f"Get symbols failed: {e}")
            return []
    
    def _parse_symbol(self, symbol: str) -> str:
        """
        解析标的代码
        
        Args:
            symbol: 标的代码
            
        Returns:
            str: 标准化代码
        """
        # 处理不同格式的代码
        if "." in symbol:
            # 000001.SZ -> 000001
            return symbol.split(".")[0]
        return symbol
    
    def _get_daily_kline(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[pd.DataFrame]:
        """获取日线数据"""
        try:
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")
            
            # AKShare 日线接口
            df = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq",  # 前复权
            )
            
            return df
        except Exception as e:
            self.logger.error(f"Get daily kline failed: {e}")
            return None
    
    def _get_weekly_kline(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[pd.DataFrame]:
        """获取周线数据"""
        try:
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")
            
            df = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="weekly",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq",
            )
            
            return df
        except Exception as e:
            self.logger.error(f"Get weekly kline failed: {e}")
            return None
    
    def _get_monthly_kline(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[pd.DataFrame]:
        """获取月线数据"""
        try:
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")
            
            df = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="monthly",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq",
            )
            
            return df
        except Exception as e:
            self.logger.error(f"Get monthly kline failed: {e}")
            return None
    
    def _get_minute_kline(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> Optional[pd.DataFrame]:
        """获取分钟线数据"""
        try:
            # 分钟线周期映射
            freq_map = {
                "1m": "1",
                "5m": "5",
                "15m": "15",
                "30m": "30",
                "60m": "60",
            }
            
            freq = freq_map.get(interval, "1")
            
            # AKShare 分钟线接口
            df = self.ak.stock_zh_a_hist_min_em(
                symbol=symbol,
                period=freq,
                adjust="qfq",
            )
            
            # 过滤日期范围
            df["datetime"] = pd.to_datetime(df["datetime"])
            mask = (df["datetime"] >= start_date) & (df["datetime"] <= end_date)
            df = df[mask]
            
            return df
        except Exception as e:
            self.logger.error(f"Get minute kline failed: {e}")
            return None
    
    def _process_kline_data(self, df: pd.DataFrame, interval: str) -> pd.DataFrame:
        """处理 K 线数据"""
        if df.empty:
            return df
        
        # AKShare 列名映射
        rename_map = {
            "datetime": "timestamp",
            "date": "timestamp",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "vol": "volume",
            "amount": "amount",
            "turnover": "amount",
        }
        
        # 重命名
        existing_cols = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        # 转换时间戳
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # 选择标准列
        standard_cols = ["timestamp", "open", "high", "low", "close", "volume"]
        available_cols = [col for col in standard_cols if col in df.columns]
        df = df[available_cols]
        
        # 排序
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        return df
    
    def _process_tick_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理 Tick 数据"""
        if df.empty:
            return df
        
        # 列名映射
        rename_map = {
            "time": "timestamp",
            "price": "price",
            "volume": "volume",
            "vol": "volume",
        }
        
        existing_cols = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        return df


# 注册数据源
from ..sources.base import DataSourceRegistry
DataSourceRegistry.register("akshare", AKShareSource)
