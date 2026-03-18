"""
回测引擎模块
Backtest Engine Module

事件驱动的回测框架。
"""

from .event import (
    EventType,
    Event,
    MarketEvent,
    TickEvent,
    BarEvent,
    OrderEvent,
    FillEvent,
    SignalEvent,
)
from .order import (
    OrderStatus,
    OrderType,
    Direction,
    Offset,
    Order,
    Trade,
    OrderManager,
)
from .performance import (
    PerformanceAnalyzer,
    calculate_performance,
)
from .engine import BacktestEngine

__all__ = [
    # 事件
    "EventType",
    "Event",
    "MarketEvent",
    "TickEvent",
    "BarEvent",
    "OrderEvent",
    "FillEvent",
    "SignalEvent",
    
    # 订单
    "OrderStatus",
    "OrderType",
    "Direction",
    "Offset",
    "Order",
    "Trade",
    "OrderManager",
    
    # 绩效
    "PerformanceAnalyzer",
    "calculate_performance",
    
    # 引擎
    "BacktestEngine",
]
