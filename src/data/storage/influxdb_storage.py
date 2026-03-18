#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluxDB 数据存储
InfluxDB Data Storage

用于存储 Tick 数据和 K 线数据的时序数据库。
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from ..storage.base import DataStorage
from ...utils.logger import get_logger
from ...utils.config import get_config


class InfluxDBStorage(DataStorage):
    """InfluxDB 数据存储类"""
    
    def __init__(self, **kwargs):
        """
        初始化 InfluxDB 存储
        
        Args:
            **kwargs: 配置参数
                - url: InfluxDB URL
                - token: API Token
                - org: 组织名称
                - bucket: 桶名称
        """
        super().__init__("influxdb", **kwargs)
        
        # 配置
        self.url = kwargs.get("url") or get_config("database.influxdb.url")
        self.token = kwargs.get("token") or get_config("database.influxdb.token")
        self.org = kwargs.get("org") or get_config("database.influxdb.org")
        self.bucket = kwargs.get("bucket") or get_config("database.influxdb.bucket")
        
        self.client = None
        self.write_api = None
        self.query_api = None
        self.logger = get_logger("data.storage.influxdb")
    
    def connect(self) -> bool:
        """
        连接到 InfluxDB
        
        Returns:
            bool: 连接是否成功
        """
        try:
            from influxdb_client import InfluxDBClient, WriteOptions, QueryOptions
            
            # 创建客户端
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                write_options=WriteOptions(batch_size=1000),
                query_options=QueryOptions(),
            )
            
            # 创建写入 API
            self.write_api = self.client.write_api()
            
            # 创建查询 API
            self.query_api = self.client.query_api()
            
            # 测试连接
            health = self.client.health()
            if health.status == "pass":
                self.connected = True
                self.logger.info(f"InfluxDB connected: {self.url}")
                return True
            else:
                self.logger.error(f"InfluxDB health check failed: {health.message}")
                return False
                
        except ImportError:
            self.logger.error("influxdb-client not installed. Run: pip install influxdb-client")
            return False
        except Exception as e:
            self.logger.error(f"InfluxDB connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        if self.write_api:
            self.write_api.close()
        
        if self.client:
            self.client.close()
        
        self.connected = False
        self.logger.info("InfluxDB disconnected")
    
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
                raise ConnectionError("InfluxDB not connected")
        
        if data.empty:
            return 0
        
        try:
            from influxdb_client import Point
            
            # 准备数据点
            points = []
            
            for _, row in data.iterrows():
                # 创建 Point
                point = (
                    Point("kline")
                    .tag("symbol", symbol)
                    .tag("interval", interval)
                    .field("open", float(row["open"]))
                    .field("high", float(row["high"]))
                    .field("low", float(row["low"]))
                    .field("close", float(row["close"]))
                    .field("volume", float(row.get("volume", 0)))
                )
                
                # 添加时间戳
                if "timestamp" in row:
                    timestamp = row["timestamp"]
                    if isinstance(timestamp, pd.Timestamp):
                        timestamp = timestamp.to_pydatetime()
                    point = point.time(timestamp)
                
                points.append(point)
            
            # 批量写入
            self.write_api.write(bucket=self.bucket, record=points)
            
            self.logger.info(f"Saved {len(points)} kline records for {symbol}")
            return len(points)
            
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
                raise ConnectionError("InfluxDB not connected")
        
        try:
            # Flux 查询
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_date.isoformat()}, stop: {end_date.isoformat()})
              |> filter(fn: (r) => r["_measurement"] == "kline")
              |> filter(fn: (r) => r["symbol"] == "{symbol}")
              |> filter(fn: (r) => r["interval"] == "{interval}")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            # 执行查询
            result = self.query_api.query(query=query)
            
            # 解析结果
            records = []
            for table in result:
                for record in table.records:
                    records.append({
                        "timestamp": record.get_time(),
                        "open": record.get_value("open"),
                        "high": record.get_value("high"),
                        "low": record.get_value("low"),
                        "close": record.get_value("close"),
                        "volume": record.get_value("volume"),
                    })
            
            if not records:
                return pd.DataFrame()
            
            # 转换为 DataFrame
            df = pd.DataFrame(records)
            df = df.sort_values("timestamp").reset_index(drop=True)
            
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
        if not self.connected:
            if not self.connect():
                raise ConnectionError("InfluxDB not connected")
        
        if data.empty:
            return 0
        
        try:
            from influxdb_client import Point
            
            points = []
            
            for _, row in data.iterrows():
                point = (
                    Point("tick")
                    .tag("symbol", symbol)
                    .field("price", float(row.get("price", 0)))
                    .field("volume", float(row.get("volume", 0)))
                )
                
                if "timestamp" in row:
                    timestamp = row["timestamp"]
                    if isinstance(timestamp, pd.Timestamp):
                        timestamp = timestamp.to_pydatetime()
                    point = point.time(timestamp)
                
                points.append(point)
            
            # 批量写入
            self.write_api.write(bucket=self.bucket, record=points)
            
            self.logger.info(f"Saved {len(points)} tick records for {symbol}")
            return len(points)
            
        except Exception as e:
            self.logger.error(f"Save tick failed: {e}")
            return 0
    
    def load_tick(
        self,
        symbol: str,
        date: datetime,
    ) -> pd.DataFrame:
        """
        加载 Tick 数据
        
        Args:
            symbol: 标的代码
            date: 日期
            
        Returns:
            pd.DataFrame: Tick 数据
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("InfluxDB not connected")
        
        try:
            start_date = date.replace(hour=0, minute=0, second=0)
            end_date = date.replace(hour=23, minute=59, second=59)
            
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_date.isoformat()}, stop: {end_date.isoformat()})
              |> filter(fn: (r) => r["_measurement"] == "tick")
              |> filter(fn: (r) => r["symbol"] == "{symbol}")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(query=query)
            
            records = []
            for table in result:
                for record in table.records:
                    records.append({
                        "timestamp": record.get_time(),
                        "price": record.get_value("price"),
                        "volume": record.get_value("volume"),
                    })
            
            if not records:
                return pd.DataFrame()
            
            df = pd.DataFrame(records)
            df = df.sort_values("timestamp").reset_index(drop=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Load tick failed: {e}")
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
                raise ConnectionError("InfluxDB not connected")
        
        try:
            from influxdb_client import DeleteApi
            
            delete_api = self.client.delete_api()
            
            # 构建时间范围
            start = start_date.isoformat() if start_date else "1970-01-01T00:00:00Z"
            stop = end_date.isoformat() if end_date else datetime.now().isoformat()
            
            # 删除数据
            delete_api.delete(
                start=start,
                stop=stop,
                predicate=f'_measurement="kline" AND symbol="{symbol}"',
                bucket=self.bucket,
                org=self.org,
            )
            
            self.logger.info(f"Deleted data for {symbol} from {start} to {stop}")
            return -1  # InfluxDB 不返回删除行数
            
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
                raise ConnectionError("InfluxDB not connected")
        
        try:
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "kline")
              |> keep(columns: ["symbol"])
              |> distinct()
            '''
            
            result = self.query_api.query(query=query)
            
            symbols = []
            for table in result:
                for record in table.records:
                    symbols.append(record.get_value())
            
            return symbols
            
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
                raise ConnectionError("InfluxDB not connected")
        
        try:
            # 查询总记录数
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -365d)
              |> filter(fn: (r) => r["_measurement"] == "kline")
              |> count()
            '''
            
            result = self.query_api.query(query=query)
            
            total_records = 0
            for table in result:
                for record in table.records:
                    total_records += record.get_value()
            
            # 获取标的数量
            symbols = self.list_symbols()
            
            return {
                "total_records": total_records,
                "symbols_count": len(symbols),
                "database": "InfluxDB",
                "bucket": self.bucket,
            }
            
        except Exception as e:
            self.logger.error(f"Get storage stats failed: {e}")
            return {}


# 注册存储
from ..storage.base import StorageRegistry
StorageRegistry.register("influxdb", InfluxDBStorage)
