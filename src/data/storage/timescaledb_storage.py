#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimescaleDB 数据存储
TimescaleDB Data Storage

基于 PostgreSQL 的时序数据库，用于存储 K 线数据。
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, text, inspect
from ..storage.base import DataStorage
from ...utils.logger import get_logger
from ...utils.config import get_config


class TimescaleDBStorage(DataStorage):
    """TimescaleDB 数据存储类"""
    
    def __init__(self, **kwargs):
        """
        初始化 TimescaleDB 存储
        
        Args:
            **kwargs: 配置参数
                - host: 数据库主机
                - port: 数据库端口
                - database: 数据库名称
                - user: 用户名
                - password: 密码
        """
        super().__init__("timescaledb", **kwargs)
        
        # 配置
        self.host = kwargs.get("host") or get_config("database.timescaledb.host", "localhost")
        self.port = kwargs.get("port") or get_config("database.timescaledb.port", 5433)
        self.database = kwargs.get("database") or get_config("database.timescaledb.database", "market_data")
        self.user = kwargs.get("user") or get_config("database.timescaledb.user", "quant_user")
        self.password = kwargs.get("password") or get_config("database.timescaledb.password", "quant_password")
        
        self.engine = None
        self.logger = get_logger("data.storage.timescaledb")
    
    def connect(self) -> bool:
        """
        连接到 TimescaleDB
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 创建数据库连接
            connection_url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
            self.engine = create_engine(
                connection_url,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600,
            )
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.connected = True
            self.logger.info(f"TimescaleDB connected: {self.host}:{self.port}/{self.database}")
            
            # 初始化表结构
            self._init_tables()
            
            return True
            
        except ImportError:
            self.logger.error("SQLAlchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
            return False
        except Exception as e:
            self.logger.error(f"TimescaleDB connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        if self.engine:
            self.engine.dispose()
        
        self.connected = False
        self.logger.info("TimescaleDB disconnected")
    
    def _init_tables(self) -> None:
        """初始化表结构"""
        try:
            with self.engine.connect() as conn:
                # 创建 K 线表 (Hypertable)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS kline_data (
                        time TIMESTAMPTZ NOT NULL,
                        symbol VARCHAR(20) NOT NULL,
                        interval VARCHAR(10) NOT NULL,
                        open DECIMAL(10,4) NOT NULL,
                        high DECIMAL(10,4) NOT NULL,
                        low DECIMAL(10,4) NOT NULL,
                        close DECIMAL(10,4) NOT NULL,
                        volume BIGINT,
                        amount DECIMAL(15,4),
                        PRIMARY KEY (time, symbol, interval)
                    )
                """))
                
                # 转换为 Hypertable
                try:
                    conn.execute(text("""
                        SELECT create_hypertable('kline_data', 'time', if_not_exists => TRUE)
                    """))
                except:
                    pass  # 可能已经创建过了
                
                # 创建索引
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_kline_symbol 
                    ON kline_data (symbol, interval, time DESC)
                """))
                
                conn.commit()
                self.logger.info("TimescaleDB tables initialized")
                
        except Exception as e:
            self.logger.error(f"Init tables failed: {e}")
    
    def save_kline(
        self,
        symbol: str,
        data: pd.DataFrame,
        interval: str = "1d",
    ) -> int:
        """
        保存 K 线数据
        
        Args:
            symbol: 标的代码
            data: K 线数据
            interval: K 线周期
            
        Returns:
            int: 保存的记录数
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("TimescaleDB not connected")
        
        if data.empty:
            return 0
        
        try:
            # 准备数据
            df = data.copy()
            df["symbol"] = symbol
            df["interval"] = interval
            
            # 重命名列
            rename_map = {
                "timestamp": "time",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
            
            # 确保 time 列存在
            if "time" not in df.columns:
                self.logger.error("Missing 'time' column")
                return 0
            
            # 批量插入
            rows = df.to_sql(
                "kline_data",
                self.engine,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
            )
            
            self.logger.info(f"Saved {len(df)} kline records for {symbol}")
            return len(df)
            
        except Exception as e:
            self.logger.error(f"Save kline failed: {e}")
            return 0
    
    def load_kline(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        加载 K 线数据
        
        Args:
            symbol: 标的代码
            start_date: 开始日期
            end_date: 结束日期
            interval: K 线周期
            
        Returns:
            pd.DataFrame: K 线数据
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("TimescaleDB not connected")
        
        try:
            query = text("""
                SELECT time, open, high, low, close, volume, amount
                FROM kline_data
                WHERE symbol = :symbol
                  AND interval = :interval
                  AND time >= :start_date
                  AND time <= :end_date
                ORDER BY time ASC
            """)
            
            df = pd.read_sql_query(
                query,
                self.engine,
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                index_col="time",
            )
            
            if df.empty:
                return pd.DataFrame()
            
            # 重命名
            df = df.rename(columns={"time": "timestamp"})
            df = df.reset_index()
            
            self.logger.info(f"Loaded {len(df)} kline records for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Load kline failed: {e}")
            return pd.DataFrame()
    
    def save_tick(
        self,
        symbol: str,
        data: pd.DataFrame,
    ) -> int:
        """
        保存 Tick 数据
        
        Args:
            symbol: 标的代码
            data: Tick 数据
            
        Returns:
            int: 保存的记录数
        """
        # Tick 数据建议存储在 InfluxDB
        self.logger.warning("Tick data should be stored in InfluxDB, not TimescaleDB")
        return 0
    
    def load_tick(
        self,
        symbol: str,
        date: datetime,
    ) -> pd.DataFrame:
        """
        加载 Tick 数据
        
        Returns:
            pd.DataFrame: Tick 数据
        """
        self.logger.warning("Tick data should be loaded from InfluxDB, not TimescaleDB")
        return pd.DataFrame()
    
    def delete_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        删除数据
        
        Args:
            symbol: 标的代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            int: 删除的记录数
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("TimescaleDB not connected")
        
        try:
            with self.engine.connect() as conn:
                # 构建删除语句
                conditions = ["symbol = :symbol"]
                params = {"symbol": symbol}
                
                if start_date:
                    conditions.append("time >= :start_date")
                    params["start_date"] = start_date
                
                if end_date:
                    conditions.append("time <= :end_date")
                    params["end_date"] = end_date
                
                where_clause = " AND ".join(conditions)
                
                query = text(f"""
                    DELETE FROM kline_data
                    WHERE {where_clause}
                """)
                
                result = conn.execute(query, params)
                conn.commit()
                
                deleted = result.rowcount
                self.logger.info(f"Deleted {deleted} records for {symbol}")
                return deleted
                
        except Exception as e:
            self.logger.error(f"Delete data failed: {e}")
            return 0
    
    def list_symbols(self) -> List[str]:
        """
        列出所有标的
        
        Returns:
            List[str]: 标的代码列表
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("TimescaleDB not connected")
        
        try:
            query = text("""
                SELECT DISTINCT symbol
                FROM kline_data
                ORDER BY symbol
            """)
            
            df = pd.read_sql_query(query, self.engine)
            return df["symbol"].tolist()
            
        except Exception as e:
            self.logger.error(f"List symbols failed: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("TimescaleDB not connected")
        
        try:
            with self.engine.connect() as conn:
                # 总记录数
                result = conn.execute(text("""
                    SELECT COUNT(*) as total_records
                    FROM kline_data
                """))
                total_records = result.fetchone()[0]
                
                # 标的数量
                result = conn.execute(text("""
                    SELECT COUNT(DISTINCT symbol) as symbols_count
                    FROM kline_data
                """))
                symbols_count = result.fetchone()[0]
                
                # 表大小
                result = conn.execute(text("""
                    SELECT pg_size_pretty(pg_total_relation_size('kline_data')) as size
                """))
                size = result.fetchone()[0]
                
                return {
                    "total_records": total_records,
                    "symbols_count": symbols_count,
                    "size": size,
                    "database": "TimescaleDB",
                }
                
        except Exception as e:
            self.logger.error(f"Get storage stats failed: {e}")
            return {}


# 注册存储
from ..storage.base import StorageRegistry
StorageRegistry.register("timescaledb", TimescaleDBStorage)
