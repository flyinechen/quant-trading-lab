"""
数据存储模块
Data Storage Module

支持多种存储后端：InfluxDB、TimescaleDB、PostgreSQL 等。
"""

from .base import DataStorage, StorageRegistry

__all__ = [
    "DataStorage",
    "StorageRegistry",
]
