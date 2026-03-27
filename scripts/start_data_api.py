#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 Data API 前执行依赖自检。
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.runtime_checks import print_missing_modules


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start Quant Trading Lab data API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    required_modules = ["fastapi", "uvicorn", "pandas"]

    if not print_missing_modules(required_modules):
        raise SystemExit(1)

    import uvicorn

    uvicorn.run("src.api.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
