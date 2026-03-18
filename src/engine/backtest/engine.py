#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件驱动回测引擎
Event-Driven Backtest Engine

核心回测引擎，支持多策略并行回测。
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List, Type
from collections import deque

from .event import (
    Event,
    EventType,
    BarEvent,
    OrderEvent,
    FillEvent,
    SignalEvent,
)
from .order import Order, OrderManager, Direction, Offset, OrderType, OrderStatus
from .performance import PerformanceAnalyzer
from ...strategy.base import BaseStrategy, Signal
from ...data import DataSource, DataCleaner
from ...utils.logger import get_logger, BacktestLogger


logger = get_logger("engine.backtest")


class BacktestEngine:
    """回测引擎类"""
    
    def __init__(
        self,
        initial_capital: float = 1000000.0,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001,
        risk_free_rate: float = 0.03,
    ):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage_rate: 滑点率
            risk_free_rate: 无风险利率
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.risk_free_rate = risk_free_rate
        
        self.logger = logger
        
        # 核心组件
        self.order_manager = OrderManager()
        self.performance_analyzer = PerformanceAnalyzer(risk_free_rate)
        
        # 策略实例
        self.strategies: Dict[str, BaseStrategy] = {}
        
        # 事件队列
        self.events_queue: deque = deque()
        
        # 市场数据
        self._market_data: Dict[str, pd.DataFrame] = {}
        self._current_prices: Dict[str, float] = {}
        
        # 回测结果
        self._equity_curve: List[float] = [initial_capital]
        self._cash_curve: List[float] = [initial_capital]
        self._datetime_index: List[datetime] = []
        self._results: Dict[str, Dict] = {}
        
        # 当前时间
        self._current_datetime: Optional[datetime] = None
    
    def add_strategy(
        self,
        strategy: BaseStrategy,
        symbols: List[str],
        strategy_id: Optional[str] = None,
    ) -> None:
        """
        添加策略
        
        Args:
            strategy: 策略实例
            symbols: 交易标的列表
            strategy_id: 策略 ID
        """
        if strategy_id is None:
            strategy_id = strategy.name
        
        strategy.strategy_id = strategy_id
        strategy.symbols = symbols
        strategy.initialize()
        
        self.strategies[strategy_id] = strategy
        
        self.logger.info(f"Added strategy: {strategy_id} for {symbols}")
    
    def load_data(
        self,
        symbol: str,
        data: pd.DataFrame,
        clean: bool = True,
    ) -> None:
        """
        加载市场数据
        
        Args:
            symbol: 标的代码
            data: 市场数据
            clean: 是否清洗数据
        """
        if clean:
            # 数据清洗
            cleaner = DataCleaner()
            data, report = cleaner.clean(data, symbol)
            
            completeness = report.get("completeness", 0)
            if completeness < 95:
                self.logger.warning(
                    f"Data completeness for {symbol} is {completeness}%"
                )
        
        # 验证数据
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Missing required columns: {required_columns}")
        
        # 确保时间戳为 datetime 类型
        if not pd.api.types.is_datetime64_any_dtype(data["timestamp"]):
            data["timestamp"] = pd.to_datetime(data["timestamp"])
        
        # 按时间排序
        data = data.sort_values("timestamp").reset_index(drop=True)
        
        self._market_data[symbol] = data
        
        self.logger.info(f"Loaded {len(data)} bars for {symbol}")
    
    def run(self) -> Dict[str, Dict]:
        """
        运行回测
        
        Returns:
            Dict[str, Dict]: 各策略的回测结果
        """
        if not self.strategies:
            raise ValueError("No strategies added")
        
        if not self._market_data:
            raise ValueError("No market data loaded")
        
        self.logger.info("Starting backtest...")
        
        # 构建统一时间索引
        self._build_datetime_index()
        
        # 记录开始日志
        BacktestLogger.start(
            strategy_name=list(self.strategies.keys())[0],
            start_date=self._datetime_index[0].strftime("%Y-%m-%d"),
            end_date=self._datetime_index[-1].strftime("%Y-%m-%d"),
            initial_capital=self.initial_capital,
        )
        
        # 主回测循环
        for dt in self._datetime_index:
            self._current_datetime = dt
            self._process_bar(dt)
        
        # 计算最终结果
        self._calculate_results()
        
        # 记录结束日志
        BacktestLogger.end(**self._results.get(list(self._results.keys())[0], {}))
        
        self.logger.info("Backtest completed")
        
        return self._results
    
    def _build_datetime_index(self) -> None:
        """构建统一的时间索引"""
        all_timestamps = set()
        
        for data in self._market_data.values():
            all_timestamps.update(data["timestamp"].tolist())
        
        self._datetime_index = sorted(list(all_timestamps))
        
        self.logger.info(f"Built datetime index with {len(self._datetime_index)} bars")
    
    def _process_bar(self, dt: datetime) -> None:
        """
        处理单个时间点的 bars
        
        Args:
            dt: 时间点
        """
        # 获取当前时刻所有标的的数据
        current_bars: Dict[str, pd.Series] = {}
        
        for symbol, data in self._market_data.items():
            bar = data[data["timestamp"] == dt]
            if not bar.empty:
                bar_series = bar.iloc[0]
                current_bars[symbol] = bar_series
                self._current_prices[symbol] = bar_series["close"]
        
        if not current_bars:
            return
        
        # 对每个策略执行
        for strategy_id, strategy in self.strategies.items():
            self._execute_strategy(strategy_id, strategy, current_bars)
        
        # 更新权益
        self._update_equity()
    
    def _execute_strategy(
        self,
        strategy_id: str,
        strategy: BaseStrategy,
        bars: Dict[str, pd.Series],
    ) -> None:
        """
        执行策略
        
        Args:
            strategy_id: 策略 ID
            strategy: 策略实例
            bars: 当前时刻的 bars
        """
        # 只在策略的标的上执行
        for symbol in strategy.symbols:
            if symbol not in bars:
                continue
            
            bar = bars[symbol]
            
            # 调用策略的 on_bar 方法
            try:
                signal = strategy.on_bar(symbol, bar)
                
                if signal is None:
                    continue
                
                # 生成订单
                self._generate_order(strategy_id, symbol, signal, bar["close"])
                
            except Exception as e:
                self.logger.error(f"Strategy {strategy_id} error on {symbol}: {e}")
    
    def _generate_order(
        self,
        strategy_id: str,
        symbol: str,
        signal: Signal,
        price: float,
    ) -> None:
        """
        生成订单
        
        Args:
            strategy_id: 策略 ID
            symbol: 标的代码
            signal: 交易信号
            price: 当前价格
        """
        # 获取当前持仓
        position = self._get_position(symbol)
        
        if signal == Signal.BUY:
            # 买入逻辑
            if position is None or position["direction"] == "short":
                # 开仓
                quantity = self._calculate_quantity(symbol, price)
                
                if quantity > 0:
                    order = self.order_manager.create_order(
                        symbol=symbol,
                        direction=Direction.BUY,
                        quantity=quantity,
                        offset=Offset.OPEN,
                        order_type=OrderType.MARKET,
                        price=price,
                        strategy_id=strategy_id,
                    )
                    
                    self.order_manager.submit_order(order.order_id)
                    self._process_order(order)
        
        elif signal == Signal.SELL:
            # 卖出逻辑
            if position is not None and position["direction"] == "long":
                # 平仓
                quantity = position["quantity"]
                
                order = self.order_manager.create_order(
                    symbol=symbol,
                    direction=Direction.SELL,
                    quantity=quantity,
                    offset=Offset.CLOSE,
                    order_type=OrderType.MARKET,
                    price=price,
                    strategy_id=strategy_id,
                )
                
                self.order_manager.submit_order(order.order_id)
                self._process_order(order)
    
    def _process_order(self, order: Order) -> None:
        """
        处理订单
        
        Args:
            order: 订单对象
        """
        if not order.is_active:
            return
        
        # 模拟撮合 (市价单立即成交)
        if order.order_type == OrderType.MARKET:
            price = order.price
            
            # 计算滑点
            slippage = price * self.slippage_rate
            
            # 计算手续费
            commission = order.quantity * price * self.commission_rate
            
            # 成交订单
            trade = self.order_manager.fill_order(
                order.order_id,
                order.quantity,
                price,
                commission,
                slippage,
            )
            
            if trade:
                # 更新策略持仓
                self._update_position(trade)
    
    def _update_position(self, trade) -> None:
        """更新持仓"""
        # 这里简化处理，实际应该维护完整的持仓系统
        pass
    
    def _get_position(self, symbol: str) -> Optional[Dict]:
        """获取持仓"""
        # 简化实现
        return None
    
    def _calculate_quantity(
        self,
        symbol: str,
        price: float,
    ) -> int:
        """
        计算买入数量
        
        Args:
            symbol: 标的代码
            price: 当前价格
            
        Returns:
            int: 买入数量
        """
        # 简单实现：使用 10% 资金
        position_size = self.initial_capital * 0.1
        quantity = position_size / price
        
        # 取整 (股票为 100 的倍数)
        quantity = int(quantity // 100) * 100
        
        return max(quantity, 100)
    
    def _update_equity(self) -> None:
        """更新权益"""
        # 计算持仓市值
        market_value = self._calculate_market_value()
        
        # 当前现金
        cash = self._calculate_cash()
        
        # 总权益
        total_equity = cash + market_value
        
        self._equity_curve.append(total_equity)
        self._cash_curve.append(cash)
    
    def _calculate_market_value(self) -> float:
        """计算持仓市值"""
        # 简化实现
        return 0
    
    def _calculate_cash(self) -> float:
        """计算现金"""
        # 简化实现
        return self.initial_capital
    
    def _calculate_results(self) -> None:
        """计算回测结果"""
        for strategy_id, strategy in self.strategies.items():
            # 获取权益曲线
            equity_curve = pd.Series(self._equity_curve)
            
            # 获取交易记录
            trades = [
                trade.to_dict()
                for trade in self.order_manager.get_trades()
            ]
            
            # 计算绩效指标
            metrics = self.performance_analyzer.analyze(equity_curve, trades)
            
            self._results[strategy_id] = metrics
    
    def get_results(self) -> Dict[str, Dict]:
        """获取回测结果"""
        return self._results
    
    def get_equity_curve(self) -> pd.Series:
        """获取权益曲线"""
        return pd.Series(
            self._equity_curve,
            index=self._datetime_index[:len(self._equity_curve)]
        )
    
    def get_trades(self) -> List:
        """获取交易记录"""
        return self.order_manager.get_trades()


__all__ = ["BacktestEngine"]
