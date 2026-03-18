#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎
Backtest Engine

事件驱动的回测框架，支持多策略、多标的并行回测。
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Type
from collections import defaultdict

from ..base import BaseStrategy, Signal, Trade
from ...utils.logger import get_logger, BacktestLogger


class BacktestEngine:
    """回测引擎类"""
    
    def __init__(
        self,
        initial_capital: float = 1000000.0,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001,
    ):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage_rate: 滑点率
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        self.logger = get_logger("backtest.engine")
        
        # 策略实例
        self.strategies: Dict[str, BaseStrategy] = {}
        
        # 数据
        self._market_data: Dict[str, pd.DataFrame] = {}
        
        # 回测结果
        self._results: Dict[str, dict] = {}
        
        # 时间线
        self._current_datetime: Optional[datetime] = None
        self._datetime_index: List[datetime] = []
    
    def add_strategy(
        self,
        strategy_class: Type[BaseStrategy],
        strategy_name: str,
        symbols: List[str],
        **kwargs
    ) -> None:
        """
        添加策略
        
        Args:
            strategy_class: 策略类
            strategy_name: 策略名称
            symbols: 交易标的列表
            **kwargs: 策略参数
        """
        strategy = strategy_class(
            name=strategy_name,
            initial_capital=self.initial_capital,
            **kwargs
        )
        strategy.symbols = symbols
        strategy.initialize()
        
        self.strategies[strategy_name] = strategy
        self.logger.info(f"Added strategy: {strategy_name} for {symbols}")
    
    def load_data(
        self,
        symbol: str,
        data: pd.DataFrame,
    ) -> None:
        """
        加载市场数据
        
        Args:
            symbol: 标的代码
            data: 市场数据 DataFrame
                必须包含 columns: timestamp, open, high, low, close, volume
        """
        # 验证数据
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Missing required columns. Required: {required_columns}")
        
        # 确保时间戳为 datetime 类型
        if not pd.api.types.is_datetime64_any_dtype(data["timestamp"]):
            data["timestamp"] = pd.to_datetime(data["timestamp"])
        
        # 按时间排序
        data = data.sort_values("timestamp").reset_index(drop=True)
        
        self._market_data[symbol] = data
        self.logger.info(f"Loaded data for {symbol}: {len(data)} bars")
    
    def run(self) -> Dict[str, dict]:
        """
        运行回测
        
        Returns:
            Dict[str, dict]: 各策略的回测结果
        """
        if not self.strategies:
            raise ValueError("No strategies added")
        
        if not self._market_data:
            raise ValueError("No market data loaded")
        
        # 获取统一的时间索引
        self._build_datetime_index()
        
        self.logger.info(f"Starting backtest from {self._datetime_index[0]} to {self._datetime_index[-1]}")
        BacktestLogger.start(
            strategy_name=list(self.strategies.keys())[0],
            start_date=str(self._datetime_index[0].date()),
            end_date=str(self._datetime_index[-1].date()),
            initial_capital=self.initial_capital,
        )
        
        # 初始化策略
        for strategy in self.strategies.values():
            strategy.reset()
        
        # 主回测循环
        for dt in self._datetime_index:
            self._current_datetime = dt
            self._process_bar(dt)
        
        # 计算最终结果
        for name, strategy in self.strategies.items():
            self._results[name] = strategy.get_performance_metrics()
        
        BacktestLogger.end(**self._results[list(self._results.keys())[0]])
        self.logger.info("Backtest completed")
        
        return self._results
    
    def _build_datetime_index(self) -> None:
        """构建统一的时间索引"""
        all_timestamps = set()
        
        for data in self._market_data.values():
            all_timestamps.update(data["timestamp"].tolist())
        
        self._datetime_index = sorted(list(all_timestamps))
    
    def _process_bar(self, dt: datetime) -> None:
        """
        处理单个时间点的 bars
        
        Args:
            dt: 时间点
        """
        # 获取当前时刻所有标的的数据
        current_bars: Dict[str, pd.Series] = {}
        current_prices: Dict[str, float] = {}
        
        for symbol, data in self._market_data.items():
            bar = data[data["timestamp"] == dt]
            if not bar.empty:
                bar_series = bar.iloc[0]
                current_bars[symbol] = bar_series
                current_prices[symbol] = bar_series["close"]
        
        if not current_bars:
            return
        
        # 对每个策略执行
        for strategy in self.strategies.values():
            self._execute_strategy(strategy, current_bars, current_prices)
    
    def _execute_strategy(
        self,
        strategy: BaseStrategy,
        bars: Dict[str, pd.Series],
        prices: Dict[str, float],
    ) -> None:
        """
        执行策略
        
        Args:
            strategy: 策略实例
            bars: 当前时刻的 bars
            prices: 当前价格
        """
        # 只在策略的标的上执行
        for symbol in strategy.symbols:
            if symbol not in bars:
                continue
            
            bar = bars[symbol]
            
            # 调用策略的 on_bar 方法
            signal = strategy.on_bar(symbol, bar)
            
            if signal is None:
                continue
            
            # 执行交易
            if signal == Signal.BUY:
                # 买入逻辑
                if symbol not in strategy.positions:
                    # 开仓
                    quantity = self._calculate_quantity(strategy, symbol, prices[symbol])
                    commission = quantity * prices[symbol] * self.commission_rate
                    slippage = quantity * prices[symbol] * self.slippage_rate
                    
                    strategy.buy(
                        symbol=symbol,
                        quantity=quantity,
                        price=prices[symbol],
                        timestamp=self._current_datetime,
                        commission=commission,
                        slippage=slippage,
                    )
            
            elif signal == Signal.SELL:
                # 卖出逻辑
                if symbol in strategy.positions:
                    commission = strategy.positions[symbol].quantity * prices[symbol] * self.commission_rate
                    slippage = strategy.positions[symbol].quantity * prices[symbol] * self.slippage_rate
                    
                    strategy.sell(
                        symbol=symbol,
                        price=prices[symbol],
                        timestamp=self._current_datetime,
                        commission=commission,
                        slippage=slippage,
                    )
        
        # 更新权益
        strategy.update_equity(prices)
    
    def _calculate_quantity(
        self,
        strategy: BaseStrategy,
        symbol: str,
        price: float,
    ) -> float:
        """
        计算买入数量
        
        Args:
            strategy: 策略实例
            symbol: 标的代码
            price: 当前价格
            
        Returns:
            float: 买入数量
        """
        # 简单实现：使用 10% 资金
        position_size = self.initial_capital * 0.1
        quantity = position_size / price
        
        # 取整 (股票为 100 的倍数)
        quantity = int(quantity // 100) * 100
        
        return max(quantity, 100)  # 至少买 100 股
    
    def get_results(self) -> Dict[str, dict]:
        """
        获取回测结果
        
        Returns:
            Dict[str, dict]: 各策略的绩效指标
        """
        return self._results
    
    def get_equity_curve(self, strategy_name: str) -> pd.Series:
        """
        获取权益曲线
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            pd.Series: 权益曲线
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return pd.Series(
            self.strategies[strategy_name].equity_history,
            index=self._datetime_index[:len(self.strategies[strategy_name].equity_history)]
        )
    
    def get_trades(self, strategy_name: str) -> List[Trade]:
        """
        获取交易记录
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            List[Trade]: 交易记录列表
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return self.strategies[strategy_name].trades
