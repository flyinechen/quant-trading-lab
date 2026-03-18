#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源基类
Data Source Base Class

所有数据源接口的抽象基类。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime


class DataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self, name: str, **kwargs):
        """
        初始化数据源
        
        Args:
            name: 数据源名称
            **kwargs: 配置参数
        """
        self.name = name
        self.config = kwargs
        self.connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接到数据源
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
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
            symbol: 标的代码 (如 000001.SZ, BTCUSDT)
            start_date: 开始日期
            end_date: 结束日期
            interval: K 线周期 (1m, 5m, 1h, 1d, 1w 等)
            
        Returns:
            pd.DataFrame: K 线数据，包含 columns:
                - timestamp: 时间戳
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_symbols(self, market: Optional[str] = None) -> List[str]:
        """
        获取标的列表
        
        Args:
            market: 市场代码 (可选)
            
        Returns:
            List[str]: 标的代码列表
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证数据质量
        
        Args:
            df: 数据 DataFrame
            
        Returns:
            bool: 数据是否有效
        """
        if df.empty:
            return False
        
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        if not all(col in df.columns for col in required_columns):
            return False
        
        # 检查价格是否为正
        price_cols = ["open", "high", "low", "close"]
        if (df[price_cols] <= 0).any().any():
            return False
        
        # 检查最高价不低于最低价
        if (df["high"] < df["low"]).any():
            return False
        
        return True
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


class DataSourceRegistry:
    """数据源注册表"""
    
    _sources: Dict[str, DataSource] = {}
    
    @classmethod
    def register(cls, name: str, source_class: type) -> None:
        """
        注册数据源
        
        Args:
            name: 数据源名称
            source_class: 数据源类
        """
        cls._sources[name] = source_class
    
    @classmethod
    def get(cls, name: str, **kwargs) -> DataSource:
        """
        获取数据源实例
        
        Args:
            name: 数据源名称
            **kwargs: 配置参数
            
        Returns:
            DataSource: 数据源实例
        """
        if name not in cls._sources:
            raise ValueError(f"Unknown data source: {name}")
        
        return cls._sources[name](name, **kwargs)
    
    @classmethod
    def list_sources(cls) -> List[str]:
        """
        列出已注册的数据源
        
        Returns:
            List[str]: 数据源名称列表
        """
        return list(cls._sources.keys())
