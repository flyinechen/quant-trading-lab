#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绩效分析模块
Performance Analysis Module

计算各种交易绩效指标。
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...utils.logger import get_logger


logger = get_logger("engine.backtest.performance")


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化绩效分析器
        
        Args:
            risk_free_rate: 无风险利率 (年化)
        """
        self.risk_free_rate = risk_free_rate
    
    def analyze(
        self,
        equity_curve: pd.Series,
        trades: Optional[List[Dict[str, Any]]] = None,
        benchmark: Optional[pd.Series] = None,
    ) -> Dict[str, Any]:
        """
        分析绩效
        
        Args:
            equity_curve: 权益曲线 (时间序列)
            trades: 交易记录列表
            benchmark: 基准指数 (可选)
            
        Returns:
            Dict[str, Any]: 绩效指标字典
        """
        metrics = {}
        
        # 计算收益率序列
        returns = equity_curve.pct_change().dropna()
        
        # 收益指标
        metrics.update(self._calculate_return_metrics(equity_curve, returns))
        
        # 风险指标
        metrics.update(self._calculate_risk_metrics(returns, equity_curve))
        
        # 风险调整收益指标
        metrics.update(self._calculate_risk_adjusted_metrics(returns))
        
        # 交易指标
        if trades:
            metrics.update(self._calculate_trade_metrics(trades))
        
        # 基准对比
        if benchmark is not None and len(benchmark) == len(equity_curve):
            metrics.update(self._calculate_benchmark_metrics(equity_curve, benchmark))
        
        return metrics
    
    def _calculate_return_metrics(
        self,
        equity_curve: pd.Series,
        returns: pd.Series,
    ) -> Dict[str, float]:
        """计算收益指标"""
        if len(returns) == 0:
            return {}
        
        # 累计收益率
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        
        # 年化收益率
        trading_days = len(returns)
        if trading_days > 0:
            annual_return = (1 + total_return) ** (252 / trading_days) - 1
        else:
            annual_return = 0.0
        
        # 日均收益率
        daily_return = returns.mean()
        
        # 月均收益率
        monthly_return = returns.mean() * 21
        
        # 盈利月份占比
        if len(equity_curve) > 21:
            monthly_equity = equity_curve.resample("M").last()
            monthly_returns = monthly_equity.pct_change().dropna()
            win_months = (monthly_returns > 0).sum()
            win_month_ratio = win_months / len(monthly_returns) if len(monthly_returns) > 0 else 0
        else:
            win_month_ratio = 0
        
        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": daily_return,
            "monthly_return": monthly_return,
            "win_month_ratio": win_month_ratio,
        }
    
    def _calculate_risk_metrics(
        self,
        returns: pd.Series,
        equity_curve: pd.Series,
    ) -> Dict[str, float]:
        """计算风险指标"""
        if len(returns) == 0:
            return {}
        
        # 波动率 (年化)
        volatility = returns.std() * np.sqrt(252)
        
        # 最大回撤
        rolling_max = equity_curve.expanding().max()
        drawdowns = (equity_curve - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # 最大回撤持续时间
        in_drawdown = drawdowns < 0
        if in_drawdown.any():
            drawdown_periods = in_drawdown.groupby((~in_drawdown).cumsum()).cumsum()
            max_drawdown_duration = drawdown_periods.max()
        else:
            max_drawdown_duration = 0
        
        # VaR (95% 置信水平)
        var_95 = returns.quantile(0.05)
        
        # CVaR (条件 VaR)
        cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95
        
        # 下行波动率
        negative_returns = returns[returns < 0]
        downside_volatility = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        
        return {
            "volatility": volatility,
            "max_drawdown": max_drawdown,
            "max_drawdown_duration": int(max_drawdown_duration),
            "var_95": var_95,
            "cvar_95": cvar_95,
            "downside_volatility": downside_volatility,
        }
    
    def _calculate_risk_adjusted_metrics(
        self,
        returns: pd.Series,
    ) -> Dict[str, float]:
        """计算风险调整收益指标"""
        if len(returns) == 0:
            return {}
        
        # 夏普比率
        excess_returns = returns - self.risk_free_rate / 252
        if returns.std() > 0:
            sharpe_ratio = (excess_returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 索提诺比率
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0 and negative_returns.std() > 0:
            sortino_ratio = (excess_returns.mean() / negative_returns.std()) * np.sqrt(252)
        else:
            sortino_ratio = 0
        
        # 卡尔马比率
        # 需要从外部传入最大回撤
        
        # 信息比率 (需要基准)
        
        return {
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
        }
    
    def _calculate_trade_metrics(
        self,
        trades: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """计算交易指标"""
        if not trades:
            return {}
        
        total_trades = len(trades)
        
        # 盈亏统计
        profits = []
        for trade in trades:
            pnl = trade.get("pnl", 0)
            profits.append(pnl)
        
        profits = np.array(profits)
        
        winning_trades = (profits > 0).sum()
        losing_trades = (profits < 0).sum()
        
        # 胜率
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 盈亏比
        avg_win = profits[profits > 0].mean() if winning_trades > 0 else 0
        avg_loss = abs(profits[profits < 0].mean()) if losing_trades > 0 else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # 平均盈亏
        avg_pnl = profits.mean()
        
        # 最大单笔盈利
        max_profit = profits.max()
        
        # 最大单笔亏损
        max_loss = profits.min()
        
        # 连续亏损次数
        max_consecutive_losses = 0
        current_losses = 0
        for pnl in profits:
            if pnl < 0:
                current_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
            else:
                current_losses = 0
        
        # 盈利因子
        gross_profit = profits[profits > 0].sum() if winning_trades > 0 else 0
        gross_loss = abs(profits[profits < 0].sum()) if losing_trades > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio,
            "avg_pnl": avg_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "max_consecutive_losses": max_consecutive_losses,
            "profit_factor": profit_factor,
        }
    
    def _calculate_benchmark_metrics(
        self,
        equity_curve: pd.Series,
        benchmark: pd.Series,
    ) -> Dict[str, float]:
        """计算基准对比指标"""
        if len(equity_curve) != len(benchmark):
            return {}
        
        # 策略收益率
        strategy_returns = equity_curve.pct_change().dropna()
        
        # 基准收益率
        benchmark_returns = benchmark.pct_change().dropna()
        
        # 超额收益
        excess_returns = strategy_returns - benchmark_returns
        
        # 年化超额收益
        annual_alpha = excess_returns.mean() * 252
        
        # Beta
        if benchmark_returns.var() > 0:
            beta = strategy_returns.cov(benchmark_returns) / benchmark_returns.var()
        else:
            beta = 0
        
        # Alpha (年化)
        strategy_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        benchmark_return = (benchmark.iloc[-1] / benchmark.iloc[0]) - 1
        alpha = strategy_return - beta * benchmark_return
        
        # 信息比率
        if excess_returns.std() > 0:
            information_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        else:
            information_ratio = 0
        
        # 跟踪误差
        tracking_error = excess_returns.std() * np.sqrt(252)
        
        return {
            "alpha": alpha,
            "beta": beta,
            "annual_alpha": annual_alpha,
            "information_ratio": information_ratio,
            "tracking_error": tracking_error,
        }
    
    def generate_report(
        self,
        metrics: Dict[str, Any],
        format: str = "text",
    ) -> str:
        """
        生成绩效报告
        
        Args:
            metrics: 绩效指标字典
            format: 输出格式 (text/html/markdown)
            
        Returns:
            str: 格式化的报告
        """
        if format == "text":
            return self._generate_text_report(metrics)
        elif format == "markdown":
            return self._generate_markdown_report(metrics)
        else:
            return str(metrics)
    
    def _generate_text_report(self, metrics: Dict[str, Any]) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("绩效分析报告")
        lines.append("=" * 60)
        
        # 收益指标
        lines.append("\n【收益指标】")
        lines.append(f"总收益率：     {metrics.get('total_return', 0):>10.2%}")
        lines.append(f"年化收益率：   {metrics.get('annual_return', 0):>10.2%}")
        lines.append(f"日均收益率：   {metrics.get('daily_return', 0):>10.4%}")
        lines.append(f"盈利月份占比： {metrics.get('win_month_ratio', 0):>10.2%}")
        
        # 风险指标
        lines.append("\n【风险指标】")
        lines.append(f"波动率：       {metrics.get('volatility', 0):>10.2%}")
        lines.append(f"最大回撤：     {metrics.get('max_drawdown', 0):>10.2%}")
        lines.append(f"VaR(95%):      {metrics.get('var_95', 0):>10.2%}")
        
        # 风险调整收益
        lines.append("\n【风险调整收益】")
        lines.append(f"夏普比率：     {metrics.get('sharpe_ratio', 0):>10.3f}")
        lines.append(f"索提诺比率：   {metrics.get('sortino_ratio', 0):>10.3f}")
        
        # 交易指标
        if "total_trades" in metrics:
            lines.append("\n【交易统计】")
            lines.append(f"总交易次数：   {metrics.get('total_trades', 0):>10d}")
            lines.append(f"胜率：         {metrics.get('win_rate', 0):>10.2%}")
            lines.append(f"盈亏比：       {metrics.get('profit_loss_ratio', 0):>10.2f}")
            lines.append(f"盈利因子：     {metrics.get('profit_factor', 0):>10.2f}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def _generate_markdown_report(self, metrics: Dict[str, Any]) -> str:
        """生成 Markdown 报告"""
        lines = []
        lines.append("# 绩效分析报告\n")
        
        # 收益指标
        lines.append("## 收益指标\n")
        lines.append("| 指标 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| 总收益率 | {metrics.get('total_return', 0):.2%} |")
        lines.append(f"| 年化收益率 | {metrics.get('annual_return', 0):.2%} |")
        lines.append(f"| 夏普比率 | {metrics.get('sharpe_ratio', 0):.3f} |")
        lines.append(f"| 最大回撤 | {metrics.get('max_drawdown', 0):.2%} |")
        
        return "\n".join(lines)


# 便捷函数
def calculate_performance(
    equity_curve: pd.Series,
    trades: Optional[List[Dict[str, Any]]] = None,
    benchmark: Optional[pd.Series] = None,
) -> Dict[str, Any]:
    """
    计算绩效指标的便捷函数
    
    Args:
        equity_curve: 权益曲线
        trades: 交易记录
        benchmark: 基准指数
        
    Returns:
        Dict[str, Any]: 绩效指标
    """
    analyzer = PerformanceAnalyzer()
    return analyzer.analyze(equity_curve, trades, benchmark)


__all__ = [
    "PerformanceAnalyzer",
    "calculate_performance",
]
