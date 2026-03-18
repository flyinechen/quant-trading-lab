"""
数据模块
Data Module

负责市场数据的采集、存储、处理和管理。
支持股票、期货、加密货币等多资产类别。
"""

from .sources import (
    DataSource,
    DataSourceRegistry,
    TushareSource,
    AKShareSource,
)
from .storage import (
    DataStorage,
    StorageRegistry,
)
from .processor import (
    DataCleaner,
    clean_data,
)

__all__ = [
    # 数据源
    "DataSource",
    "DataSourceRegistry",
    "TushareSource",
    "AKShareSource",
    
    # 数据存储
    "DataStorage",
    "StorageRegistry",
    
    # 数据处理
    "DataCleaner",
    "clean_data",
]
