#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据存储基类
Data Storage Base Class

所有数据存储接口的抽象基类。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime


class DataStorage(ABC):
    """数据存储抽象基类"""
    
    def __init__(self, name: str, **kwargs):
        """
        初始化数据存储
        
        Args:
            name: 存储名称
            **kwargs: 配置参数
        """
        self.name = name
        self.config = kwargs
        self.connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接到存储
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    def save_kline(
        self,
        symbol: str,
        data: pd.DataFrame,
        interval: str = "1d",
    ) -> int:
        """
        保存 K 线数据
        
        Args:
            symbol: 标的代码
            data: K 线数据
            interval: K 线周期
            
        Returns:
            int: 保存的记录数
        """
        pass
    
    @abstractmethod
    def load_kline(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        加载 K 线数据
        
        Args:
            symbol: 标的代码
            start_date: 开始日期
            end_date: 结束日期
            interval: K 线周期
            
        Returns:
            pd.DataFrame: K 线数据
        """
        pass
    
    @abstractmethod
    def save_tick(
        self,
        symbol: str,
        data: pd.DataFrame,
    ) -> int:
        """
        保存 Tick 数据
        
        Args:
            symbol: 标的代码
            data: Tick 数据
            
        Returns:
            int: 保存的记录数
        """
        pass
    
    @abstractmethod
    def load_tick(
        self,
        symbol: str,
        date: datetime,
    ) -> pd.DataFrame:
        """
        加载 Tick 数据
        
        Args:
            symbol: 标的代码
            date: 日期
            
        Returns:
            pd.DataFrame: Tick 数据
        """
        pass
    
    @abstractmethod
    def delete_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        删除数据
        
        Args:
            symbol: 标的代码
            start_date: 开始日期 (可选，删除该日期之后的数据)
            end_date: 结束日期 (可选，删除该日期之前的数据)
            
        Returns:
            int: 删除的记录数
        """
        pass
    
    @abstractmethod
    def list_symbols(self) -> List[str]:
        """
        列出所有标的
        
        Returns:
            List[str]: 标的代码列表
        """
        pass
    
    @abstractmethod
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            Dict[str, Any]: 统计信息，包含:
                - total_records: 总记录数
                - total_size_bytes: 总大小 (字节)
                - symbols_count: 标的数量
                - date_range: 日期范围
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证数据
        
        Args:
            df: 数据 DataFrame
            
        Returns:
            bool: 数据是否有效
        """
        if df.empty:
            return False
        
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        return all(col in df.columns for col in required_columns)
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


class StorageRegistry:
    """存储注册表"""
    
    _storages: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, storage_class: type) -> None:
        """
        注册存储
        
        Args:
            name: 存储名称
            storage_class: 存储类
        """
        cls._storages[name] = storage_class
    
    @classmethod
    def get(cls, name: str, **kwargs) -> DataStorage:
        """
        获取存储实例
        
        Args:
            name: 存储名称
            **kwargs: 配置参数
            
        Returns:
            DataStorage: 存储实例
        """
        if name not in cls._storages:
            raise ValueError(f"Unknown storage: {name}")
        
        return cls._storages[name](**kwargs)
    
    @classmethod
    def list_storages(cls) -> List[str]:
        """
        列出已注册的存储
        
        Returns:
            List[str]: 存储名称列表
        """
        return list(cls._storages.keys())
