#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据 API 服务
Data API Service

提供 RESTful API 接口，用于数据查询和管理。
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd

from ...utils.logger import get_logger
from ...utils.config import get_config


logger = get_logger("data.api")

# 创建 FastAPI 应用
app = FastAPI(
    title="Quantitative Trading Lab - Data API",
    description="量化交易实验室数据接口服务",
    version="0.1.0",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 数据模型 ====================

class KlineRequest(BaseModel):
    """K 线数据请求"""
    symbol: str = Field(..., description="标的代码")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    interval: str = Field(default="1d", description="K 线周期")


class KlineResponse(BaseModel):
    """K 线数据响应"""
    symbol: str
    interval: str
    count: int
    data: List[Dict[str, Any]]


class QualityReport(BaseModel):
    """数据质量报告"""
    symbol: str
    completeness: float
    accuracy: float
    issues: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: datetime
    version: str


# ==================== 依赖注入 ====================

def get_data_source():
    """获取数据源实例"""
    from ..sources import DataSourceRegistry
    
    # 从配置获取默认数据源
    default_source = get_config("data.default_source", "akshare")
    return DataSourceRegistry.get(default_source)


def get_storage():
    """获取存储实例"""
    from ..storage import StorageRegistry
    
    # 从配置获取默认存储
    default_storage = get_config("data.default_storage", "timescaledb")
    return StorageRegistry.get(default_storage)


# ==================== API 路由 ====================

@app.get("/", response_model=Dict[str, str])
async def root():
    """API 根路径"""
    return {
        "name": "Quantitative Trading Lab - Data API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="0.1.0",
    )


@app.get("/data/kline", response_model=KlineResponse)
async def get_kline(
    symbol: str = Query(..., description="标的代码"),
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    interval: str = Query(default="1d", description="K 线周期"),
    source: Optional[str] = Query(default=None, description="数据源"),
):
    """
    获取 K 线数据
    
    - **symbol**: 标的代码 (如 000001.SZ)
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **interval**: K 线周期 (1d, 1w, 1M, 1m, 5m 等)
    - **source**: 数据源 (tushare, akshare)
    """
    try:
        # 获取数据源
        if source:
            from ..sources import DataSourceRegistry
            data_source = DataSourceRegistry.get(source)
        else:
            data_source = get_data_source()
        
        # 连接数据源
        if not data_source.connected:
            data_source.connect()
        
        # 获取数据
        df = data_source.get_kline(symbol, start_date, end_date, interval)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # 转换为字典列表
        data = df.to_dict(orient="records")
        
        # 序列化时间戳
        for row in data:
            if "timestamp" in row and isinstance(row["timestamp"], pd.Timestamp):
                row["timestamp"] = row["timestamp"].isoformat()
        
        return KlineResponse(
            symbol=symbol,
            interval=interval,
            count=len(data),
            data=data,
        )
        
    except Exception as e:
        logger.error(f"Get kline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/symbols")
async def get_symbols(
    market: Optional[str] = Query(default=None, description="市场代码"),
    source: Optional[str] = Query(default=None, description="数据源"),
):
    """
    获取标的列表
    
    - **market**: 市场代码 (SSE, SZSE)
    - **source**: 数据源
    """
    try:
        if source:
            from ..sources import DataSourceRegistry
            data_source = DataSourceRegistry.get(source)
        else:
            data_source = get_data_source()
        
        if not data_source.connected:
            data_source.connect()
        
        symbols = data_source.get_symbols(market)
        
        return {
            "count": len(symbols),
            "symbols": symbols,
        }
        
    except Exception as e:
        logger.error(f"Get symbols failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/data/clean")
async def clean_data(
    data: List[Dict[str, Any]],
    symbol: str = Query(..., description="标的代码"),
    fill_method: str = Query(default="forward", description="缺失值填充方法"),
):
    """
    清洗数据
    
    - **data**: 原始数据
    - **symbol**: 标的代码
    - **fill_method**: 填充方法 (forward, backward, mean, drop)
    """
    try:
        from ..processor import DataCleaner
        
        # 转换为 DataFrame
        df = pd.DataFrame(data)
        
        # 清洗数据
        cleaner = DataCleaner()
        clean_df, report = cleaner.clean(df, symbol, fill_method=fill_method)
        
        # 转换为字典列表
        cleaned_data = clean_df.to_dict(orient="records")
        
        # 序列化时间戳
        for row in cleaned_data:
            if "timestamp" in row and isinstance(row["timestamp"], pd.Timestamp):
                row["timestamp"] = row["timestamp"].isoformat()
        
        return {
            "symbol": symbol,
            "original_rows": report["original_rows"],
            "cleaned_rows": report["final_rows"],
            "completeness": report["completeness"],
            "accuracy": report["accuracy"],
            "issues": report["issues"],
            "data": cleaned_data,
        }
        
    except Exception as e:
        logger.error(f"Clean data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/storage/stats")
async def get_storage_stats(
    storage_type: str = Query(default="timescaledb", description="存储类型"),
):
    """
    获取存储统计信息
    
    - **storage_type**: 存储类型 (influxdb, timescaledb, postgres)
    """
    try:
        from ..storage import StorageRegistry
        
        storage = StorageRegistry.get(storage_type)
        
        if not storage.connected:
            storage.connect()
        
        stats = storage.get_storage_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Get storage stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sources")
async def list_sources():
    """列出所有可用的数据源"""
    from ..sources import DataSourceRegistry
    
    sources = DataSourceRegistry.list_sources()
    
    return {
        "count": len(sources),
        "sources": sources,
    }


@app.get("/storages")
async def list_storages():
    """列出所有可用的存储"""
    from ..storage import StorageRegistry
    
    storages = StorageRegistry.list_storages()
    
    return {
        "count": len(storages),
        "storages": storages,
    }


# ==================== 主程序 ====================

def create_app() -> FastAPI:
    """创建应用实例"""
    return app


if __name__ == "__main__":
    import uvicorn
    
    # 启动服务
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
