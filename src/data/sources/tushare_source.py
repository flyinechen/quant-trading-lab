#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare 数据源
Tushare Data Source

接入 Tushare Pro 金融数据接口，获取股票、期货、基金等市场数据。
https://tushare.pro/
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from ..sources.base import DataSource
from ...utils.logger import get_logger
from ...utils.config import get_config


class TushareSource(DataSource):
    """Tushare 数据源类"""
    
    def __init__(self, **kwargs):
        """
        初始化 Tushare 数据源
        
        Args:
            **kwargs: 配置参数，包含 token 等
        """
        super().__init__("tushare", **kwargs)
        self.token = kwargs.get("token") or get_config("data_sources.tushare.token")
        self.base_url = "https://api.tushare.pro"
        self.logger = get_logger("data.sources.tushare")
        
        # Tushare 接口映射
        self._api_mapping = {
            "daily": "daily",  # 日线行情
            "weekly": "weekly",  # 周线行情
            "monthly": "monthly",  # 月线行情
            "min": "mins",  # 分钟线
            "tick": "tick",  # Tick 数据
        }
    
    def connect(self) -> bool:
        """
        连接到 Tushare
        
        Returns:
            bool: 连接是否成功
        """
        if not self.token:
            self.logger.error("Tushare token not configured")
            return False
        
        # 测试连接
        try:
            # 获取交易日历测试连接
            data = self._api_request("trade_cal", {
                "exchange": "SSE",
                "start_date": datetime.now().strftime("%Y%m%d"),
                "end_date": datetime.now().strftime("%Y%m%d"),
            })
            
            if data is not None:
                self.connected = True
                self.logger.info("Tushare connected successfully")
                return True
        except Exception as e:
            self.logger.error(f"Tushare connection failed: {e}")
        
        return False
    
    def disconnect(self) -> None:
        """断开连接"""
        self.connected = False
        self.logger.info("Tushare disconnected")
    
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
            symbol: 标的代码 (如 000001.SZ)
            start_date: 开始日期
            end_date: 结束日期
            interval: K 线周期 (1m, 5m, 1h, 1d, 1w, 1M)
            
        Returns:
            pd.DataFrame: K 线数据
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("Tushare not connected")
        
        # 转换时间格式
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        # 根据周期选择接口
        if interval in ["1d", "d"]:
            api_name = "daily"
        elif interval in ["1w", "w"]:
            api_name = "weekly"
        elif interval in ["1M", "M"]:
            api_name = "monthly"
        elif interval in ["1m", "5m", "15m", "30m", "60m"]:
            api_name = "mins"
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        # 构建请求参数
        params = {
            "ts_code": symbol,
            "start_date": start_str,
            "end_date": end_str,
        }
        
        # 分钟线需要额外参数
        if api_name == "mins":
            freq_map = {
                "1m": "1min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "60m": "60min",
            }
            params["freq"] = freq_map.get(interval, "1min")
        
        # 请求数据
        data = self._api_request(api_name, params)
        
        if data is None or data.empty:
            self.logger.warning(f"No data returned for {symbol} from {start_str} to {end_str}")
            return pd.DataFrame()
        
        # 数据清洗和格式化
        df = self._process_kline_data(data, interval)
        
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
                raise ConnectionError("Tushare not connected")
        
        date_str = date.strftime("%Y%m%d")
        
        # Tushare Tick 数据接口
        data = self._api_request("tick", {
            "ts_code": symbol,
            "trade_date": date_str,
        })
        
        if data is None or data.empty:
            return pd.DataFrame()
        
        # 格式化 Tick 数据
        df = self._process_tick_data(data)
        
        return df
    
    def get_symbols(self, market: Optional[str] = None) -> List[str]:
        """
        获取标的列表
        
        Args:
            market: 市场代码 (SSE/ SZSE/ BSE)
            
        Returns:
            List[str]: 标的代码列表
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("Tushare not connected")
        
        # 获取股票列表
        data = self._api_request("stock_basic", {
            "exchange": market or "",
            "list_status": "L",  # 正常上市
        })
        
        if data is None or data.empty:
            return []
        
        # 返回 ts_code 列表
        return data["ts_code"].tolist()
    
    def _api_request(self, api_name: str, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        调用 Tushare API
        
        Args:
            api_name: API 名称
            params: 请求参数
            
        Returns:
            Optional[pd.DataFrame]: 返回的数据
        """
        url = f"{self.base_url}"
        
        payload = {
            "api_name": api_name,
            "token": self.token,
            "params": params,
            "fields": ""  # 返回所有字段
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # 检查返回码
            if result.get("code") != 0:
                error_msg = result.get("msg", "Unknown error")
                self.logger.error(f"Tushare API error: {error_msg}")
                return None
            
            # 解析数据
            data = result.get("data", {})
            fields = data.get("fields", [])
            items = data.get("items", [])
            
            if not items:
                return pd.DataFrame()
            
            # 转换为 DataFrame
            df = pd.DataFrame(items, columns=fields)
            
            return df
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Tushare API request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Tushare API error: {e}")
            return None
    
    def _process_kline_data(self, df: pd.DataFrame, interval: str) -> pd.DataFrame:
        """
        处理 K 线数据
        
        Args:
            df: 原始数据
            interval: K 线周期
            
        Returns:
            pd.DataFrame: 处理后的数据
        """
        if df.empty:
            return df
        
        # 重命名列
        rename_map = {
            "trade_date": "timestamp",
            "trade_time": "timestamp",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "vol": "volume",
            "amount": "amount",
        }
        
        # 只保留存在的列
        existing_cols = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        # 转换时间戳
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # 选择标准列
        standard_cols = ["timestamp", "open", "high", "low", "close", "volume"]
        available_cols = [col for col in standard_cols if col in df.columns]
        df = df[available_cols]
        
        # 按时间排序
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        # 验证数据
        if not self.validate_data(df):
            self.logger.warning("Data validation failed")
        
        return df
    
    def _process_tick_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理 Tick 数据
        
        Args:
            df: 原始数据
            
        Returns:
            pd.DataFrame: 处理后的数据
        """
        if df.empty:
            return df
        
        # 重命名列
        rename_map = {
            "trade_time": "timestamp",
            "price": "price",
            "vol": "volume",
            "bs_type": "bs_type",  # 买卖类型
        }
        
        existing_cols = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        # 转换时间戳
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # 按时间排序
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        return df


# 注册数据源
from ..sources.base import DataSourceRegistry
DataSourceRegistry.register("tushare", TushareSource)
