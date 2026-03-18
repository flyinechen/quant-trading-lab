#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件模块
Event Module

定义回测引擎中的各种事件类型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class EventType(Enum):
    """事件类型枚举"""
    
    # 市场事件
    MARKET = "market"
    TICK = "tick"
    BAR = "bar"
    
    # 订单事件
    ORDER = "order"
    ORDER_CREATED = "order_created"
    ORDER_SUBMITTED = "order_submitted"
    ORDER_ACCEPTED = "order_accepted"
    ORDER_REJECTED = "order_rejected"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    
    # 账户事件
    ACCOUNT = "account"
    POSITION = "position"
    FILL = "fill"
    
    # 系统事件
    SYSTEM = "system"
    TIMER = "timer"
    LOG = "log"


@dataclass
class Event:
    """事件基类"""
    
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not isinstance(self.event_type, EventType):
            raise ValueError(f"Invalid event type: {self.event_type}")


@dataclass
class MarketEvent(Event):
    """市场事件"""
    
    event_type: EventType = EventType.MARKET
    symbol: str = ""
    exchange: str = ""


@dataclass
class TickEvent(MarketEvent):
    """Tick 事件"""
    
    event_type: EventType = EventType.TICK
    price: float = 0.0
    volume: int = 0
    bid_price: float = 0.0
    ask_price: float = 0.0
    bid_volume: int = 0
    ask_volume: int = 0


@dataclass
class BarEvent(MarketEvent):
    """K 线事件"""
    
    event_type: EventType = EventType.BAR
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    amount: float = 0.0
    interval: str = "1d"


@dataclass
class OrderEvent(Event):
    """订单事件"""
    
    event_type: EventType = EventType.ORDER
    order_id: str = ""
    symbol: str = ""
    direction: str = ""  # buy/sell
    offset: str = ""  # open/close
    order_type: str = ""  # limit/market
    price: float = 0.0
    quantity: int = 0
    filled_quantity: int = 0
    status: str = "pending"


@dataclass
class FillEvent(Event):
    """成交事件"""
    
    event_type: EventType = EventType.FILL
    fill_id: str = ""
    order_id: str = ""
    symbol: str = ""
    direction: str = ""
    price: float = 0.0
    quantity: int = 0
    commission: float = 0.0
    slippage: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def cost(self) -> float:
        """总成本"""
        return self.quantity * self.price + self.commission + self.slippage


@dataclass
class PositionEvent(Event):
    """持仓事件"""
    
    event_type: EventType = EventType.POSITION
    symbol: str = ""
    direction: str = ""  # long/short
    quantity: int = 0
    avg_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass
class SignalEvent(Event):
    """交易信号事件"""
    
    event_type: EventType = EventType.ORDER
    signal_id: str = ""
    symbol: str = ""
    signal_type: str = ""  # BUY/SELL/HOLD
    strength: float = 0.0  # 信号强度 0-1
    price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0


@dataclass
class TimerEvent(Event):
    """定时器事件"""
    
    event_type: EventType = EventType.TIMER
    timer_id: str = ""
    interval: float = 0.0  # 秒


@dataclass
class LogEvent(Event):
    """日志事件"""
    
    event_type: EventType = EventType.LOG
    level: str = "INFO"  # DEBUG/INFO/WARNING/ERROR
    message: str = ""
    source: str = ""


__all__ = [
    "EventType",
    "Event",
    "MarketEvent",
    "TickEvent",
    "BarEvent",
    "OrderEvent",
    "FillEvent",
    "PositionEvent",
    "SignalEvent",
    "TimerEvent",
    "LogEvent",
]
