"""
数据存储模块
Data Storage Module

支持多种存储后端：InfluxDB、TimescaleDB、PostgreSQL 等。
"""

from .base import DataStorage, StorageRegistry

try:
    from .influxdb_storage import InfluxDBStorage
except Exception:  # pragma: no cover - optional dependency
    InfluxDBStorage = None

try:
    from .timescaledb_storage import TimescaleDBStorage
except Exception:  # pragma: no cover - optional dependency
    TimescaleDBStorage = None

try:
    from .postgres_storage import PostgreSQLStorage
except Exception:  # pragma: no cover - optional dependency
    PostgreSQLStorage = None

__all__ = [
    "DataStorage",
    "StorageRegistry",
    "InfluxDBStorage",
    "TimescaleDBStorage",
    "PostgreSQLStorage",
]
