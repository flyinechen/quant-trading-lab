"""
数据模块
Data Module

负责市场数据的采集、存储、处理和管理。
支持股票、期货、加密货币等多资产类别。
"""

from .sources.base import DataSource
from .storage.base import DataStorage

__all__ = [
    "DataSource",
    "DataStorage",
]
