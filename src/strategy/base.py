#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略基类
Base Strategy Class

所有交易策略的抽象基类。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class Signal(Enum):
    """交易信号"""
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class Position:
    """持仓数据类"""
    symbol: str
    quantity: float
    avg_price: float
    entry_date: datetime
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    
    def update_market_value(self, current_price: float) -> None:
        """更新市值"""
        self.market_value = current_price * self.quantity
        self.unrealized_pnl = (current_price - self.avg_price) * self.quantity


@dataclass
class Trade:
    """交易记录类"""
    trade_id: str
    symbol: str
    direction: Signal
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0.0
    slippage: float = 0.0
    
    @property
    def total_cost(self) -> float:
        """总成本"""
        return self.quantity * self.price + self.commission + self.slippage


class BaseStrategy(ABC):
    """策略抽象基类"""
    
    def __init__(
        self,
        name: str,
        initial_capital: float = 1000000.0,
        **kwargs
    ):
        """
        初始化策略
        
        Args:
            name: 策略名称
            initial_capital: 初始资金
            **kwargs: 策略参数
        """
        self.name = name
        self.initial_capital = initial_capital
        self.params = kwargs
        
        # 状态变量
        self.capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.cash_history: List[float] = [initial_capital]
        self.equity_history: List[float] = [initial_capital]
        
        # 数据缓存
        self._data_cache: Dict[str, pd.DataFrame] = {}
    
    @abstractmethod
    def initialize(self) -> None:
        """
        策略初始化
        
        在此处设置指标、参数等。
        """
        pass
    
    @abstractmethod
    def on_bar(self, symbol: str, bar: pd.Series) -> Optional[Signal]:
        """
        K 线数据更新回调
        
        Args:
            symbol: 标的代码
            bar: K 线数据 (包含 open, high, low, close, volume)
            
        Returns:
            Signal: 交易信号
        """
        pass
    
    def on_tick(self, symbol: str, tick: pd.Series) -> None:
        """
        Tick 数据更新回调 (可选实现)
        
        Args:
            symbol: 标的代码
            tick: Tick 数据
        """
        pass
    
    def generate_trade_id(self) -> str:
        """生成交易 ID"""
        import uuid
        return f"T{uuid.uuid4().hex[:8].upper()}"
    
    def buy(
        self,
        symbol: str,
        quantity: float,
        price: float,
        timestamp: datetime,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> Optional[Trade]:
        """
        买入
        
        Args:
            symbol: 标的代码
            quantity: 数量
            price: 价格
            timestamp: 时间戳
            commission: 手续费
            slippage: 滑点
            
        Returns:
            Trade: 交易记录，如果资金不足返回 None
        """
        cost = quantity * price + commission + slippage
        
        if cost > self.capital:
            return None
        
        # 更新资金
        self.capital -= cost
        
        # 更新或创建持仓
        if symbol in self.positions:
            pos = self.positions[symbol]
            total_cost = pos.avg_price * pos.quantity + cost
            pos.quantity += quantity
            pos.avg_price = total_cost / pos.quantity
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                entry_date=timestamp,
            )
        
        # 记录交易
        trade = Trade(
            trade_id=self.generate_trade_id(),
            symbol=symbol,
            direction=Signal.BUY,
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            commission=commission,
            slippage=slippage,
        )
        self.trades.append(trade)
        
        return trade
    
    def sell(
        self,
        symbol: str,
        quantity: Optional[float] = None,
        price: float = 0.0,
        timestamp: Optional[datetime] = None,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> Optional[Trade]:
        """
        卖出
        
        Args:
            symbol: 标的代码
            quantity: 数量 (None 表示全部卖出)
            price: 价格
            timestamp: 时间戳
            commission: 手续费
            slippage: 滑点
            
        Returns:
            Trade: 交易记录，如果持仓不足返回 None
        """
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        
        if quantity is None:
            quantity = pos.quantity
        
        if quantity > pos.quantity:
            return None
        
        # 计算收入
        revenue = quantity * price - commission - slippage
        
        # 更新资金
        self.capital += revenue
        
        # 更新持仓
        pos.quantity -= quantity
        
        if pos.quantity <= 0:
            del self.positions[symbol]
        
        # 记录交易
        trade = Trade(
            trade_id=self.generate_trade_id(),
            symbol=symbol,
            direction=Signal.SELL,
            quantity=quantity,
            price=price,
            timestamp=timestamp or datetime.now(),
            commission=commission,
            slippage=slippage,
        )
        self.trades.append(trade)
        
        return trade
    
    def update_equity(self, current_prices: Dict[str, float]) -> float:
        """
        更新权益
        
        Args:
            current_prices: 当前价格字典
            
        Returns:
            float: 总权益
        """
        # 计算持仓市值
        market_value = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.avg_price)
            for pos in self.positions.values()
        )
        
        # 总权益 = 现金 + 持仓市值
        total_equity = self.capital + market_value
        
        # 更新持仓市值
        for pos in self.positions.values():
            pos.update_market_value(current_prices.get(pos.symbol, pos.avg_price))
        
        # 记录历史
        self.cash_history.append(self.capital)
        self.equity_history.append(total_equity)
        
        return total_equity
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取绩效指标
        
        Returns:
            Dict[str, Any]: 绩效指标字典
        """
        if len(self.equity_history) < 2:
            return {}
        
        equity_series = pd.Series(self.equity_history)
        returns = equity_series.pct_change().dropna()
        
        # 总收益率
        total_return = (equity_series.iloc[-1] - equity_series.iloc[0]) / equity_series.iloc[0]
        
        # 年化收益率 (假设 252 个交易日)
        trading_days = len(returns)
        annual_return = (1 + total_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0
        
        # 夏普比率 (假设无风险利率为 3%)
        risk_free_rate = 0.03
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * (252 ** 0.5) if len(returns) > 1 else 0
        
        # 最大回撤
        rolling_max = equity_series.expanding().max()
        drawdowns = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # 胜率
        buy_trades = [t for t in self.trades if t.direction == Signal.BUY]
        sell_trades = [t for t in self.trades if t.direction == Signal.SELL]
        
        profitable_trades = 0
        total_trades = len(sell_trades)
        
        for sell_trade in sell_trades:
            # 找到对应的买入交易
            for buy_trade in buy_trades:
                if buy_trade.symbol == sell_trade.symbol and buy_trade.timestamp < sell_trade.timestamp:
                    if sell_trade.price > buy_trade.price:
                        profitable_trades += 1
                    break
        
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "final_equity": self.equity_history[-1],
            "initial_capital": self.initial_capital,
        }
    
    def reset(self) -> None:
        """重置策略状态"""
        self.capital = self.initial_capital
        self.positions.clear()
        self.trades.clear()
        self.cash_history = [self.initial_capital]
        self.equity_history = [self.initial_capital]
        self._data_cache.clear()
