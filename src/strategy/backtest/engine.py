#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容层：统一复用标准回测引擎实现。

请优先从 src.engine.backtest 导入 BacktestEngine。
"""

from ...engine.backtest.engine import BacktestEngine

__all__ = ["BacktestEngine"]
