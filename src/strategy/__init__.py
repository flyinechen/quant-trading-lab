"""
策略模块
Strategy Module

提供策略开发、回测和执行的完整框架。
"""

from .base import BaseStrategy, Signal, Position, Trade
from ..engine.backtest import BacktestEngine

__all__ = [
    "BaseStrategy",
    "Signal",
    "Position",
    "Trade",
    "BacktestEngine",
]
