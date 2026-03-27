#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一 FastAPI 应用入口。

为了兼容 Docker/Compose 的 `src.api.main:app` 启动方式，
这里复用数据层 API 的应用实例。
"""

from src.data.api.routes import create_app

app = create_app()
