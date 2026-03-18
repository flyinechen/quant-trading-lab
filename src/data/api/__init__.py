"""
数据 API 模块
Data API Module

提供 RESTful API 服务。
"""

from .routes import app, create_app

__all__ = [
    "app",
    "create_app",
]
