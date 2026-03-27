#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目 CLI 入口。
"""

import argparse

from src import __version__
from src.utils.runtime_checks import print_missing_modules


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quant-lab",
        description="Quant Trading Lab command line interface",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("version", help="Print package version")

    serve_parser = subparsers.add_parser("serve-data-api", help="Start FastAPI data service")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", default=8000, type=int)
    serve_parser.add_argument("--reload", action="store_true")

    return parser


def main() -> None:
    """CLI root command."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "version":
        print(__version__)
        return

    if args.command == "serve-data-api":
        required_modules = ["fastapi", "uvicorn", "pandas"]
        if not print_missing_modules(required_modules):
            raise SystemExit(1)

        import uvicorn

        uvicorn.run("src.api.main:app", host=args.host, port=args.port, reload=args.reload)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
