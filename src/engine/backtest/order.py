#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单模块
Order Module

定义订单类型和订单管理系统。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid


class OrderStatus(Enum):
    """订单状态"""
    
    PENDING = "pending"  # 待提交
    SUBMITTED = "submitted"  # 已提交
    ACCEPTED = "accepted"  # 已接受
    REJECTED = "rejected"  # 已拒绝
    PARTIALLY_FILLED = "partially_filled"  # 部分成交
    FILLED = "filled"  # 全部成交
    CANCELLED = "cancelled"  # 已撤销


class OrderType(Enum):
    """订单类型"""
    
    MARKET = "market"  # 市价单
    LIMIT = "limit"  # 限价单
    STOP = "stop"  # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单


class Direction(Enum):
    """交易方向"""
    
    BUY = "buy"
    SELL = "sell"


class Offset(Enum):
    """开平标志"""
    
    OPEN = "open"
    CLOSE = "close"
    CLOSE_TODAY = "close_today"


@dataclass
class Order:
    """订单类"""
    
    # 基本信息
    order_id: str = field(default_factory=lambda: f"ORD{uuid.uuid4().hex[:12].upper()}")
    symbol: str = ""
    direction: Direction = Direction.BUY
    offset: Offset = Offset.OPEN
    order_type: OrderType = OrderType.MARKET
    
    # 价格和数量
    price: float = 0.0
    quantity: int = 0
    filled_quantity: int = 0
    filled_price: float = 0.0
    
    # 状态
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # 费用
    commission: float = 0.0
    slippage: float = 0.0
    
    # 其他
    strategy_id: str = ""
    exchange_order_id: str = ""
    error_message: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def unfilled_quantity(self) -> int:
        """未成交数量"""
        return self.quantity - self.filled_quantity
    
    @property
    def is_active(self) -> bool:
        """是否活跃订单"""
        return self.status in [
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED,
        ]
    
    @property
    def is_filled(self) -> bool:
        """是否已完全成交"""
        return self.status == OrderStatus.FILLED
    
    @property
    def fill_rate(self) -> float:
        """成交率"""
        if self.quantity == 0:
            return 0.0
        return self.filled_quantity / self.quantity
    
    def submit(self) -> None:
        """提交订单"""
        self.status = OrderStatus.SUBMITTED
        self.submitted_at = datetime.now()
        self.updated_at = datetime.now()
    
    def accept(self) -> None:
        """接受订单"""
        self.status = OrderStatus.ACCEPTED
        self.updated_at = datetime.now()
    
    def reject(self, reason: str) -> None:
        """拒绝订单"""
        self.status = OrderStatus.REJECTED
        self.error_message = reason
        self.updated_at = datetime.now()
    
    def fill(
        self,
        quantity: int,
        price: float,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> None:
        """
        成交订单
        
        Args:
            quantity: 成交数量
            price: 成交价格
            commission: 手续费
            slippage: 滑点
        """
        self.filled_quantity += quantity
        self.commission += commission
        self.slippage += slippage
        
        # 计算成交均价
        if self.filled_quantity > 0:
            total_cost = self.filled_price * (self.filled_quantity - quantity) + price * quantity
            self.filled_price = total_cost / self.filled_quantity
        
        # 更新状态
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
            self.filled_at = datetime.now()
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
        
        self.updated_at = datetime.now()
    
    def cancel(self) -> None:
        """撤销订单"""
        if self.is_active:
            self.status = OrderStatus.CANCELLED
            self.cancelled_at = datetime.now()
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "direction": self.direction.value,
            "offset": self.offset.value,
            "order_type": self.order_type.value,
            "price": self.price,
            "quantity": self.quantity,
            "filled_quantity": self.filled_quantity,
            "filled_price": self.filled_price,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "commission": self.commission,
            "slippage": self.slippage,
            "strategy_id": self.strategy_id,
        }


@dataclass
class Trade:
    """成交记录类"""
    
    trade_id: str = field(default_factory=lambda: f"TRD{uuid.uuid4().hex[:12].upper()}")
    order_id: str = ""
    symbol: str = ""
    direction: Direction = Direction.BUY
    price: float = 0.0
    quantity: int = 0
    commission: float = 0.0
    slippage: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def cost(self) -> float:
        """总成本"""
        return self.quantity * self.price + self.commission + self.slippage
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trade_id": self.trade_id,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "direction": self.direction.value,
            "price": self.price,
            "quantity": self.quantity,
            "commission": self.commission,
            "slippage": self.slippage,
            "timestamp": self.timestamp.isoformat(),
        }


class OrderManager:
    """订单管理器"""
    
    def __init__(self):
        """初始化订单管理器"""
        self._orders: Dict[str, Order] = {}
        self._trades: Dict[str, Trade] = {}
        self._active_orders: Dict[str, Order] = {}
    
    def create_order(
        self,
        symbol: str,
        direction: Direction,
        quantity: int,
        offset: Offset = Offset.OPEN,
        order_type: OrderType = OrderType.MARKET,
        price: float = 0.0,
        strategy_id: str = "",
        **kwargs,
    ) -> Order:
        """
        创建订单
        
        Args:
            symbol: 标的代码
            direction: 交易方向
            quantity: 数量
            offset: 开平标志
            order_type: 订单类型
            price: 价格 (限价单需要)
            strategy_id: 策略 ID
            
        Returns:
            Order: 订单对象
        """
        order = Order(
            symbol=symbol,
            direction=direction,
            offset=offset,
            order_type=order_type,
            price=price,
            quantity=quantity,
            strategy_id=strategy_id,
            extra_data=kwargs,
        )
        
        self._orders[order.order_id] = order
        self._active_orders[order.order_id] = order
        
        return order
    
    def submit_order(self, order_id: str) -> bool:
        """
        提交订单
        
        Args:
            order_id: 订单 ID
            
        Returns:
            bool: 是否成功提交
        """
        if order_id not in self._orders:
            return False
        
        order = self._orders[order_id]
        order.submit()
        
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """
        撤销订单
        
        Args:
            order_id: 订单 ID
            
        Returns:
            bool: 是否成功撤销
        """
        if order_id not in self._orders:
            return False
        
        order = self._orders[order_id]
        
        if not order.is_active:
            return False
        
        order.cancel()
        
        if order_id in self._active_orders:
            del self._active_orders[order_id]
        
        return True
    
    def fill_order(
        self,
        order_id: str,
        quantity: int,
        price: float,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> Optional[Trade]:
        """
        成交订单
        
        Args:
            order_id: 订单 ID
            quantity: 成交数量
            price: 成交价格
            commission: 手续费
            slippage: 滑点
            
        Returns:
            Trade: 成交记录
        """
        if order_id not in self._orders:
            return None
        
        order = self._orders[order_id]
        
        if not order.is_active:
            return None
        
        # 更新订单
        order.fill(quantity, price, commission, slippage)
        
        # 创建成交记录
        trade = Trade(
            order_id=order_id,
            symbol=order.symbol,
            direction=order.direction,
            price=price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
        )
        
        self._trades[trade.trade_id] = trade
        
        # 如果订单已完成，从活跃订单中移除
        if order.is_filled and order_id in self._active_orders:
            del self._active_orders[order_id]
        
        return trade
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self._orders.get(order_id)
    
    def get_active_orders(self, symbol: Optional[str] = None) -> list:
        """
        获取活跃订单
        
        Args:
            symbol: 标的代码 (可选)
            
        Returns:
            list: 活跃订单列表
        """
        orders = list(self._active_orders.values())
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        return orders
    
    def get_orders(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        strategy_id: Optional[str] = None,
    ) -> list:
        """
        获取订单列表
        
        Args:
            symbol: 标的代码
            status: 订单状态
            strategy_id: 策略 ID
            
        Returns:
            list: 订单列表
        """
        orders = list(self._orders.values())
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        if status:
            orders = [o for o in orders if o.status == status]
        
        if strategy_id:
            orders = [o for o in orders if o.strategy_id == strategy_id]
        
        return orders
    
    def get_trades(
        self,
        symbol: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> list:
        """
        获取成交记录
        
        Args:
            symbol: 标的代码
            order_id: 订单 ID
            
        Returns:
            list: 成交记录列表
        """
        trades = list(self._trades.values())
        
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        
        if order_id:
            trades = [t for t in trades if t.order_id == order_id]
        
        return trades
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取订单统计信息"""
        total_orders = len(self._orders)
        active_orders = len(self._active_orders)
        filled_orders = len([o for o in self._orders.values() if o.is_filled])
        cancelled_orders = len([o for o in self._orders.values() if o.status == OrderStatus.CANCELLED])
        rejected_orders = len([o for o in self._orders.values() if o.status == OrderStatus.REJECTED])
        
        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "filled_orders": filled_orders,
            "cancelled_orders": cancelled_orders,
            "rejected_orders": rejected_orders,
            "total_trades": len(self._trades),
        }


__all__ = [
    "OrderStatus",
    "OrderType",
    "Direction",
    "Offset",
    "Order",
    "Trade",
    "OrderManager",
]
