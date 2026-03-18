#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块
Logger Management Module

提供统一的日志管理功能，支持多级别日志、文件轮转、格式化输出。
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from .config import get_config


class QuantLogger:
    """量化交易日志类"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str = "quant_lab") -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(cls._get_log_level())
        
        # 避免重复添加 handler
        if not logger.handlers:
            # 控制台输出
            console_handler = cls._create_console_handler()
            logger.addHandler(console_handler)
            
            # 文件输出
            file_handler = cls._create_file_handler()
            if file_handler:
                logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def _get_log_level(cls) -> int:
        """获取日志级别"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        
        level_name = get_config("logging.level", "INFO")
        return level_map.get(level_name.upper(), logging.INFO)
    
    @classmethod
    def _create_console_handler(cls) -> logging.StreamHandler:
        """创建控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(cls._get_log_level())
        
        # 彩色格式 (使用 rich 库如果可用)
        try:
            from rich.logging import RichHandler
            return RichHandler(
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                markup=True,
            )
        except ImportError:
            # 普通格式
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(formatter)
            return console_handler
    
    @classmethod
    def _create_file_handler(cls) -> Optional[logging.Handler]:
        """创建文件处理器"""
        log_file = get_config("logging.file", "logs/quant_lab.log")
        log_path = Path(log_file)
        
        # 创建日志目录
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 按时间轮转 (每天一个文件)
        file_handler = TimedRotatingFileHandler(
            filename=log_path,
            when="D",
            interval=1,
            backupCount=30,  # 保留 30 天
            encoding="utf-8",
        )
        file_handler.setLevel(cls._get_log_level())
        
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        
        return file_handler


# 便捷函数
def get_logger(name: str = "quant_lab") -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志名称
        
    Returns:
        logging.Logger: 日志记录器
        
    Example:
        >>> logger = get_logger("data.source")
        >>> logger.info("Data loaded successfully")
    """
    return QuantLogger.get_logger(name)


# 模块级日志记录器
logger = get_logger()


# 交易专用日志
class TradingLogger:
    """交易日志类"""
    
    @staticmethod
    def order(order_id: str, action: str, symbol: str, **kwargs):
        """记录订单日志"""
        logger = get_logger("trading.orders")
        logger.info(
            f"ORDER | {order_id} | {action} | {symbol} | " + 
            " | ".join(f"{k}={v}" for k, v in kwargs.items())
        )
    
    @staticmethod
    def fill(order_id: str, symbol: str, price: float, quantity: float, **kwargs):
        """记录成交日志"""
        logger = get_logger("trading.fills")
        logger.info(
            f"FILL | {order_id} | {symbol} | price={price} | qty={quantity} | " +
            " | ".join(f"{k}={v}" for k, v in kwargs.items())
        )
    
    @staticmethod
    def position(symbol: str, quantity: float, avg_price: float, pnl: float = 0):
        """记录持仓日志"""
        logger = get_logger("trading.positions")
        logger.info(
            f"POSITION | {symbol} | qty={quantity} | avg_price={avg_price} | pnl={pnl}"
        )
    
    @staticmethod
    def risk_alert(alert_type: str, message: str, **kwargs):
        """记录风险预警"""
        logger = get_logger("trading.risk")
        logger.warning(
            f"RISK_ALERT | {alert_type} | {message} | " +
            " | ".join(f"{k}={v}" for k, v in kwargs.items())
        )
    
    @staticmethod
    def performance(date: str, daily_return: float, total_value: float, **kwargs):
        """记录绩效日志"""
        logger = get_logger("trading.performance")
        logger.info(
            f"PERFORMANCE | {date} | daily_return={daily_return:.4%} | " +
            f"total_value={total_value:.2f} | " +
            " | ".join(f"{k}={v}" for k, v in kwargs.items())
        )


# 回测专用日志
class BacktestLogger:
    """回测日志类"""
    
    @staticmethod
    def start(strategy_name: str, start_date: str, end_date: str, initial_capital: float):
        """记录回测开始"""
        logger = get_logger("backtest.engine")
        logger.info(
            f"BACKTEST_START | {strategy_name} | " +
            f"period={start_date} to {end_date} | " +
            f"initial_capital={initial_capital:.2f}"
        )
    
    @staticmethod
    def end(total_return: float, sharpe_ratio: float, max_drawdown: float, **kwargs):
        """记录回测结束"""
        logger = get_logger("backtest.engine")
        logger.info(
            f"BACKTEST_END | " +
            f"total_return={total_return:.4%} | " +
            f"sharpe={sharpe_ratio:.4f} | " +
            f"max_drawdown={max_drawdown:.4%} | " +
            " | ".join(f"{k}={v}" for k, v in kwargs.items())
        )
    
    @staticmethod
    def trade(trade_id: int, symbol: str, direction: str, entry_price: float, 
              exit_price: float, quantity: float, pnl: float):
        """记录回测交易"""
        logger = get_logger("backtest.trades")
        logger.info(
            f"TRADE | #{trade_id} | {symbol} | {direction} | " +
            f"entry={entry_price:.4f} | exit={exit_price:.4f} | " +
            f"qty={quantity} | pnl={pnl:.2f}"
        )
