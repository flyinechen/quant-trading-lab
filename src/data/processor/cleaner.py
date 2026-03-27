#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗模块
Data Cleaner Module

负责数据质量检查、缺失值处理、异常值检测、复权调整等。
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from ...utils.logger import get_logger


class DataCleaner:
    """数据清洗类"""
    
    def __init__(self):
        """初始化数据清洗器"""
        self.logger = get_logger("data.processor.cleaner")
        self.quality_report = {}
    
    def clean(
        self,
        df: pd.DataFrame,
        symbol: str = "",
        **kwargs
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        执行数据清洗
        
        Args:
            df: 原始数据
            symbol: 标的代码
            **kwargs: 清洗参数
            
        Returns:
            Tuple[pd.DataFrame, Dict]: (清洗后的数据，质量报告)
        """
        self.quality_report = {
            "symbol": symbol,
            "start_time": datetime.now().isoformat(),
            "original_rows": len(df),
            "issues": [],
        }
        
        if df.empty:
            self.quality_report["status"] = "empty"
            return df, self.quality_report
        
        # 1. 检查缺失值
        df = self._handle_missing_values(df, **kwargs)
        
        # 2. 检测异常值
        df = self._detect_outliers(df, **kwargs)
        
        # 3. 检查价格逻辑
        df = self._validate_price_logic(df, **kwargs)
        
        # 4. 去重
        df = self._remove_duplicates(df, **kwargs)
        
        # 5. 排序
        df = self._sort_by_time(df, **kwargs)
        
        # 完成报告
        self.quality_report["end_time"] = datetime.now().isoformat()
        self.quality_report["final_rows"] = len(df)
        self.quality_report["removed_rows"] = self.quality_report["original_rows"] - len(df)
        self.quality_report["status"] = "completed"
        self.quality_report["completeness"] = self._calculate_completeness(df)
        self.quality_report["accuracy"] = self._calculate_accuracy(df)
        
        return df, self.quality_report
    
    def _handle_missing_values(
        self,
        df: pd.DataFrame,
        fill_method: str = "forward",
        max_consecutive: int = 3,
        **kwargs
    ) -> pd.DataFrame:
        """
        处理缺失值
        
        Args:
            df: 数据
            fill_method: 填充方法 (forward/backward/mean/drop)
            max_consecutive: 最大连续缺失数
        """
        missing_cols = df.columns[df.isnull().any()].tolist()
        
        if not missing_cols:
            return df
        
        self.quality_report["issues"].append({
            "type": "missing_values",
            "columns": missing_cols,
            "count": df.isnull().sum().to_dict(),
        })
        
        # 检查连续缺失
        for col in missing_cols:
            is_null = df[col].isnull()
            consecutive = is_null.ne(is_null.shift()).cumsum()
            max_consecutive_missing = is_null.groupby(consecutive).sum().max()
            
            if max_consecutive_missing > max_consecutive:
                self.logger.warning(
                    f"Column {col} has {max_consecutive_missing} consecutive missing values"
                )
                # 标记为无效数据
                self.quality_report["issues"].append({
                    "type": "consecutive_missing",
                    "column": col,
                    "count": max_consecutive_missing,
                })
        
        # 填充缺失值
        if fill_method == "forward":
            df = df.fillna(method="ffill")
        elif fill_method == "backward":
            df = df.fillna(method="bfill")
        elif fill_method == "mean":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        elif fill_method == "drop":
            df = df.dropna()
        
        # 剩余的缺失值直接删除
        df = df.dropna()
        
        return df
    
    def _detect_outliers(
        self,
        df: pd.DataFrame,
        method: str = "zscore",
        threshold: float = 3.0,
        price_change_limit: float = 0.10,
        **kwargs
    ) -> pd.DataFrame:
        """
        检测异常值
        
        Args:
            df: 数据
            method: 检测方法 (zscore/iqr/percentile)
            threshold: 阈值
            price_change_limit: 价格涨跌幅限制 (默认 10%)
        """
        if "close" not in df.columns:
            return df
        
        # 1. 检测价格涨跌幅异常
        df["price_change"] = df["close"].pct_change()
        
        outlier_mask = df["price_change"].abs() > price_change_limit
        
        if outlier_mask.any():
            outlier_count = outlier_mask.sum()
            self.quality_report["issues"].append({
                "type": "price_change_outlier",
                "count": int(outlier_count),
                "threshold": price_change_limit,
                "indices": df.index[outlier_mask].tolist()[:10],  # 前 10 个
            })
            self.logger.warning(f"Detected {outlier_count} price change outliers")
            
            # 标记异常值 (不删除，保留原始数据)
            df["is_outlier"] = outlier_mask
        
        # 2. Z-Score 检测
        if method == "zscore":
            from scipy import stats
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                if col == "is_outlier":
                    continue
                    
                z_scores = np.abs(stats.zscore(df[col].dropna()))
                outlier_mask = z_scores > threshold
                
                if outlier_mask.any():
                    self.quality_report["issues"].append({
                        "type": "zscore_outlier",
                        "column": col,
                        "count": int(outlier_mask.sum()),
                        "threshold": threshold,
                    })
        
        # 3. IQR 检测
        elif method == "iqr":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                if col == "is_outlier":
                    continue
                
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                outlier_mask = (df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)
                
                if outlier_mask.any():
                    self.quality_report["issues"].append({
                        "type": "iqr_outlier",
                        "column": col,
                        "count": int(outlier_mask.sum()),
                    })
        
        # 删除 is_outlier 列
        if "is_outlier" in df.columns:
            df = df.drop(columns=["is_outlier"])
        
        # 删除 price_change 辅助列
        if "price_change" in df.columns:
            df = df.drop(columns=["price_change"])
        
        return df
    
    def _validate_price_logic(
        self,
        df: pd.DataFrame,
        **kwargs
    ) -> pd.DataFrame:
        """
        验证价格逻辑
        
        检查:
        - high >= low
        - high >= open, high >= close
        - low <= open, low <= close
        - 价格为正数
        """
        issues = []
        
        # 检查必需列
        required_cols = ["open", "high", "low", "close"]
        if not all(col in df.columns for col in required_cols):
            return df
        
        # 1. high >= low
        invalid_hl = df["high"] < df["low"]
        if invalid_hl.any():
            issues.append({
                "type": "invalid_high_low",
                "count": int(invalid_hl.sum()),
            })
            # 修正：交换 high 和 low
            df.loc[invalid_hl, ["high", "low"]] = df.loc[invalid_hl, ["low", "high"]].values
        
        # 2. high >= open 且 high >= close
        invalid_high = (df["high"] < df["open"]) | (df["high"] < df["close"])
        if invalid_high.any():
            issues.append({
                "type": "invalid_high",
                "count": int(invalid_high.sum()),
            })
            # 修正：high 取最大值
            df.loc[invalid_high, "high"] = df.loc[invalid_high, ["open", "close"]].max(axis=1)
        
        # 3. low <= open 且 low <= close
        invalid_low = (df["low"] > df["open"]) | (df["low"] > df["close"])
        if invalid_low.any():
            issues.append({
                "type": "invalid_low",
                "count": int(invalid_low.sum()),
            })
            # 修正：low 取最小值
            df.loc[invalid_low, "low"] = df.loc[invalid_low, ["open", "close"]].min(axis=1)
        
        # 4. 价格为正数
        price_cols = ["open", "high", "low", "close"]
        negative_price = (df[price_cols] <= 0).any(axis=1)
        if negative_price.any():
            issues.append({
                "type": "negative_price",
                "count": int(negative_price.sum()),
            })
            # 删除负价格行
            df = df[~negative_price]
        
        if issues:
            self.quality_report["issues"].extend(issues)
            self.logger.warning(f"Price logic validation found {len(issues)} issues")
        
        return df
    
    def _remove_duplicates(
        self,
        df: pd.DataFrame,
        subset: Optional[list] = None,
        keep: str = "first",
        **kwargs
    ) -> pd.DataFrame:
        """删除重复行"""
        if subset is None:
            subset = ["timestamp"] if "timestamp" in df.columns else None
        
        original_len = len(df)
        df = df.drop_duplicates(subset=subset, keep=keep)
        removed = original_len - len(df)
        
        if removed > 0:
            self.quality_report["issues"].append({
                "type": "duplicates_removed",
                "count": removed,
            })
            self.logger.info(f"Removed {removed} duplicate rows")
        
        return df
    
    def _sort_by_time(
        self,
        df: pd.DataFrame,
        **kwargs
    ) -> pd.DataFrame:
        """按时间排序"""
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        return df
    
    def _calculate_completeness(self, df: pd.DataFrame) -> float:
        """计算数据完整性"""
        if df.empty:
            return 0.0
        
        total_cells = df.size
        non_null_cells = df.notnull().sum().sum()
        
        return round(non_null_cells / total_cells * 100, 2) if total_cells > 0 else 0.0
    
    def _calculate_accuracy(self, df: pd.DataFrame) -> float:
        """计算数据准确性"""
        if df.empty:
            return 0.0
        
        # 检查价格逻辑正确的比例
        if all(col in df.columns for col in ["open", "high", "low", "close"]):
            valid = (
                (df["high"] >= df["low"]) &
                (df["high"] >= df["open"]) &
                (df["high"] >= df["close"]) &
                (df["low"] <= df["open"]) &
                (df["low"] <= df["close"]) &
                (df["close"] > 0)
            )
            return round(valid.sum() / len(df) * 100, 2)
        
        return 100.0
    
    def generate_report(self) -> Dict[str, Any]:
        """生成数据质量报告"""
        return self.quality_report


# 便捷函数
def clean_data(df: pd.DataFrame, symbol: str = "", **kwargs) -> Tuple[pd.DataFrame, Dict]:
    """
    清洗数据的便捷函数
    
    Args:
        df: 原始数据
        symbol: 标的代码
        **kwargs: 清洗参数
        
    Returns:
        Tuple[pd.DataFrame, Dict]: (清洗后的数据，质量报告)
    """
    cleaner = DataCleaner()
    return cleaner.clean(df, symbol, **kwargs)
