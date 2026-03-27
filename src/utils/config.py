#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
Configuration Management Module

负责加载和管理系统配置，支持环境变量和配置文件。
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    def load_dotenv(*args, **kwargs):
        return False


class Config:
    """配置管理类"""
    
    _instance: Optional["Config"] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls) -> "Config":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置"""
        if self._config:
            return
        
        # 加载环境变量
        self._load_env()
        
        # 加载配置文件
        self._load_config_file()
    
    def _load_env(self) -> None:
        """加载环境变量"""
        # 查找 .env 文件
        env_paths = [
            Path(".env"),
            Path.home() / ".quant-lab" / ".env",
            Path(__file__).parent.parent / ".env",
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                break
        
        # 读取配置
        self._config["data_sources"] = {
            "tushare": {
                "token": os.getenv("TUSHARE_TOKEN", ""),
                "enabled": bool(os.getenv("TUSHARE_TOKEN")),
            },
            "akshare": {
                "enabled": os.getenv("AKSHARE_ENABLED", "true").lower() == "true",
            },
            "binance": {
                "api_key": os.getenv("BINANCE_API_KEY", ""),
                "api_secret": os.getenv("BINANCE_API_SECRET", ""),
                "testnet": os.getenv("BINANCE_TESTNET", "true").lower() == "true",
            },
        }
        
        self._config["database"] = {
            "influxdb": {
                "url": os.getenv("INFLUXDB_URL", "http://localhost:8086"),
                "token": os.getenv("INFLUXDB_TOKEN", ""),
                "org": os.getenv("INFLUXDB_ORG", "quant_lab"),
                "bucket": os.getenv("INFLUXDB_BUCKET", "market_data"),
            },
            "postgres": {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DB", "quant_lab"),
                "user": os.getenv("POSTGRES_USER", "quant_user"),
                "password": os.getenv("POSTGRES_PASSWORD", ""),
            },
        }
        
        self._config["trading"] = {
            "mode": os.getenv("TRADING_MODE", "paper"),
            "initial_capital": float(os.getenv("PAPER_TRADING_INITIAL_CAPITAL", "1000000")),
            "max_position_ratio": float(os.getenv("MAX_POSITION_RATIO", "0.3")),
            "max_daily_loss": float(os.getenv("MAX_DAILY_LOSS", "50000")),
            "stop_loss_percent": float(os.getenv("STOP_LOSS_PERCENT", "0.05")),
        }
        
        self._config["api"] = {
            "host": os.getenv("API_HOST", "0.0.0.0"),
            "port": int(os.getenv("API_PORT", "8000")),
            "debug": os.getenv("API_DEBUG", "false").lower() == "true",
        }
        
        self._config["logging"] = {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "file": os.getenv("LOG_FILE", "logs/quant_lab.log"),
        }
    
    def _load_config_file(self) -> None:
        """加载配置文件"""
        config_paths = [
            Path("configs/default.yaml"),
            Path.home() / ".quant-lab" / "configs" / "default.yaml",
            Path(__file__).parent.parent / "configs" / "default.yaml",
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
                    self._merge_config(file_config)
                break
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """合并配置"""
        for key, value in new_config.items():
            if key in self._config and isinstance(value, dict):
                self._config[key].update(value)
            else:
                self._config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def reload(self) -> None:
        """重新加载配置"""
        self._config = {}
        self._load_env()
        self._load_config_file()


# 全局配置实例
config = Config()


def get_config(key: Optional[str] = None, default: Any = None) -> Any:
    """获取配置的便捷函数"""
    if key is None:
        return config.all()
    return config.get(key, default)
