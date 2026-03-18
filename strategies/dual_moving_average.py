#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线策略 (Dual Moving Average Strategy)

最简单的趋势跟踪策略之一：
- 短期均线上穿长期均线 -> 买入信号
- 短期均线下穿长期均线 -> 卖出信号

Author: flyinechen
Date: 2026-03-18
"""

import pandas as pd
import numpy as np


class DualMAStrategy:
    """双均线策略类"""
    
    def __init__(self, short_window=5, long_window=20):
        """
        初始化策略
        
        Args:
            short_window: 短期均线周期
            long_window: 长期均线周期
        """
        self.short_window = short_window
        self.long_window = long_window
        self.signals = None
    
    def generate_signals(self, prices):
        """
        生成交易信号
        
        Args:
            prices: 价格序列 (pandas Series)
            
        Returns:
            signals: 信号 DataFrame
        """
        self.signals = pd.DataFrame(index=prices.index)
        self.signals['price'] = prices
        
        # 计算均线
        self.signals['sma_short'] = prices.rolling(window=self.short_window).mean()
        self.signals['sma_long'] = prices.rolling(window=self.long_window).mean()
        
        # 生成信号 (1=多头，0=空仓)
        self.signals['signal'] = 0.0
        self.signals['signal'][self.short_window:] = np.where(
            self.signals['sma_short'][self.short_window:] > 
            self.signals['sma_long'][self.short_window:], 1.0, 0.0
        )
        
        # 生成交易信号 (1=买入，-1=卖出)
        self.signals['positions'] = self.signals['signal'].diff()
        
        return self.signals
    
    def get_current_signal(self, prices):
        """
        获取当前信号
        
        Args:
            prices: 最近的价格序列
            
        Returns:
            signal: 当前信号 (1=持有，0=空仓)
        """
        signals = self.generate_signals(prices)
        return signals['signal'].iloc[-1]


# 使用示例
if __name__ == "__main__":
    # 生成示例数据
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')
    prices = pd.Series(100 + np.cumsum(np.random.randn(100)), index=dates)
    
    # 初始化策略
    strategy = DualMAStrategy(short_window=5, long_window=20)
    
    # 生成信号
    signals = strategy.generate_signals(prices)
    
    # 打印结果
    print("双均线策略信号")
    print("=" * 50)
    print(signals.tail(10))
    print("=" * 50)
    print(f"当前信号：{'持有' if signals['signal'].iloc[-1] == 1 else '空仓'}")
