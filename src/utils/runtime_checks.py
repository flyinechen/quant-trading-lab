#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行时依赖检查工具。
"""

from importlib.util import find_spec
from typing import Iterable, List


def find_missing_modules(modules: Iterable[str]) -> List[str]:
    """Return a list of missing module names."""
    missing: List[str] = []
    for module in modules:
        if find_spec(module) is None:
            missing.append(module)
    return missing


def print_missing_modules(modules: Iterable[str]) -> bool:
    """Print friendly message for missing modules. Return True if all present."""
    missing = find_missing_modules(modules)
    if not missing:
        return True

    print("缺少运行依赖，无法启动。")
    print("缺失模块:", ", ".join(missing))
    print("可执行: pip install -r requirements.txt")
    return False
