#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 数据存储
PostgreSQL Data Storage

用于存储交易记录、用户数据、策略配置等结构化数据。
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, text
from ..storage.base import DataStorage
from ...utils.logger import get_logger
from ...utils.config import get_config


class PostgreSQLStorage(DataStorage):
    """PostgreSQL 数据存储类"""
    
    def __init__(self, **kwargs):
        """
        初始化 PostgreSQL 存储
        
        Args:
            **kwargs: 配置参数
                - host: 数据库主机
                - port: 数据库端口
                - database: 数据库名称
                - user: 用户名
                - password: 密码
        """
        super().__init__("postgres", **kwargs)
        
        # 配置
        self.host = kwargs.get("host") or get_config("database.postgres.host", "localhost")
        self.port = kwargs.get("port") or get_config("database.postgres.port", 5432)
        self.database = kwargs.get("database") or get_config("database.postgres.database", "quant_lab")
        self.user = kwargs.get("user") or get_config("database.postgres.user", "quant_user")
        self.password = kwargs.get("password") or get_config("database.postgres.password", "quant_password")
        
        self.engine = None
        self.logger = get_logger("data.storage.postgres")
    
    def connect(self) -> bool:
        """连接数据库"""
        try:
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
            self.logger.info(f"PostgreSQL connected: {self.host}:{self.port}/{self.database}")
            return True
            
        except Exception as e:
            self.logger.error(f"PostgreSQL connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        if self.engine:
            self.engine.dispose()
        self.connected = False
        self.logger.info("PostgreSQL disconnected")
    
    def save_trades(self, trades: List[Dict[str, Any]]) -> int:
        """
        保存交易记录
        
        Args:
            trades: 交易记录列表
            
        Returns:
            int: 保存的记录数
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("PostgreSQL not connected")
        
        if not trades:
            return 0
        
        try:
            df = pd.DataFrame(trades)
            rows = df.to_sql(
                "trades",
                self.engine,
                if_exists="append",
                index=False,
                method="multi",
            )
            
            self.logger.info(f"Saved {rows} trade records")
            return rows
            
        except Exception as e:
            self.logger.error(f"Save trades failed: {e}")
            return 0
    
    def save_orders(self, orders: List[Dict[str, Any]]) -> int:
        """保存订单记录"""
        if not self.connected:
            if not self.connect():
                raise ConnectionError("PostgreSQL not connected")
        
        if not orders:
            return 0
        
        try:
            df = pd.DataFrame(orders)
            rows = df.to_sql(
                "orders",
                self.engine,
                if_exists="append",
                index=False,
            )
            
            self.logger.info(f"Saved {rows} order records")
            return rows
            
        except Exception as e:
            self.logger.error(f"Save orders failed: {e}")
            return 0
    
    def save_positions(self, positions: List[Dict[str, Any]]) -> int:
        """保存持仓记录"""
        if not self.connected:
            if not self.connect():
                raise ConnectionError("PostgreSQL not connected")
        
        try:
            df = pd.DataFrame(positions)
            rows = df.to_sql(
                "positions",
                self.engine,
                if_exists="replace",
                index=False,
            )
            
            self.logger.info(f"Saved {rows} position records")
            return rows
            
        except Exception as e:
            self.logger.error(f"Save positions failed: {e}")
            return 0
    
    def load_trades(
        self,
        user_id: Optional[int] = None,
        strategy_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """加载交易记录"""
        if not self.connected:
            if not self.connect():
                raise ConnectionError("PostgreSQL not connected")
        
        try:
            conditions = ["1=1"]
            params = {}
            
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = user_id
            
            if strategy_id:
                conditions.append("strategy_id = :strategy_id")
                params["strategy_id"] = strategy_id
            
            if start_date:
                conditions.append("created_at >= :start_date")
                params["start_date"] = start_date
            
            if end_date:
                conditions.append("created_at <= :end_date")
                params["end_date"] = end_date
            
            where_clause = " AND ".join(conditions)
            
            query = text(f"""
                SELECT * FROM trades
                WHERE {where_clause}
                ORDER BY created_at DESC
            """)
            
            df = pd.read_sql_query(query, self.engine, params=params)
            return df
            
        except Exception as e:
            self.logger.error(f"Load trades failed: {e}")
            return pd.DataFrame()
    
    def save_kline(
        self,
        symbol: str,
        data: pd.DataFrame,
        interval: str = "1d",
    ) -> int:
        """保存 K 线数据 (不推荐，建议使用 TimescaleDB)"""
        self.logger.warning("Kline data should be stored in TimescaleDB")
        return 0
    
    def load_kline(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """加载 K 线数据 (不推荐，建议使用 TimescaleDB)"""
        self.logger.warning("Kline data should be loaded from TimescaleDB")
        return pd.DataFrame()
    
    def save_tick(self, symbol: str, data: pd.DataFrame) -> int:
        """保存 Tick 数据 (不推荐，建议使用 InfluxDB)"""
        self.logger.warning("Tick data should be stored in InfluxDB")
        return 0
    
    def load_tick(self, symbol: str, date: datetime) -> pd.DataFrame:
        """加载 Tick 数据 (不推荐，建议使用 InfluxDB)"""
        self.logger.warning("Tick data should be loaded from InfluxDB")
        return pd.DataFrame()
    
    def delete_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """删除数据"""
        self.logger.warning("Delete not implemented for PostgreSQL storage")
        return 0
    
    def list_symbols(self) -> List[str]:
        """列出所有标的"""
        return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        if not self.connected:
            if not self.connect():
                raise ConnectionError("PostgreSQL not connected")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        (SELECT COUNT(*) FROM trades) as trades_count,
                        (SELECT COUNT(*) FROM orders) as orders_count,
                        (SELECT COUNT(*) FROM positions) as positions_count
                """))
                row = result.fetchone()
                
                return {
                    "trades_count": row[0],
                    "orders_count": row[1],
                    "positions_count": row[2],
                    "database": "PostgreSQL",
                }
                
        except Exception as e:
            self.logger.error(f"Get storage stats failed: {e}")
            return {}


# 注册存储
from ..storage.base import StorageRegistry
StorageRegistry.register("postgres", PostgreSQLStorage)
