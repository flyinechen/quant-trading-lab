"""
数据存储模块
Data Storage Module

支持多种存储后端：InfluxDB、TimescaleDB、PostgreSQL 等。
"""

from .base import DataStorage, StorageRegistry
from .influxdb_storage import InfluxDBStorage
from .timescaledb_storage import TimescaleDBStorage
from .postgres_storage import PostgreSQLStorage

__all__ = [
    "DataStorage",
    "StorageRegistry",
    "InfluxDBStorage",
    "TimescaleDBStorage",
    "PostgreSQLStorage",
]
