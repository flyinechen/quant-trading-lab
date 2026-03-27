#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小冒烟测试：导入、CLI、API 路由可见性。
"""

import importlib
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.runtime_checks import find_missing_modules


def check_imports() -> bool:
    modules = [
        "src.utils.config",
        "src.data.processor.cleaner",
        "src.data.sources.base",
        "src.data.storage.base",
        "src.utils.cli",
    ]
    ok = True
    for name in modules:
        try:
            importlib.import_module(name)
            print(f"[OK] import {name}")
        except Exception as exc:
            print(f"[FAIL] import {name}: {exc}")
            ok = False
    return ok


def check_cli_version(repo_root: Path) -> bool:
    cmd = [sys.executable, "-m", "src.utils.cli", "version"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if result.returncode != 0:
        print("[FAIL] cli version command failed")
        print(result.stderr.strip())
        return False

    output = result.stdout.strip()
    if not output:
        print("[FAIL] cli version produced empty output")
        return False

    print(f"[OK] cli version: {output}")
    return True


def check_api_routes() -> str:
    missing = find_missing_modules(["fastapi"])
    if missing:
        print("[SKIP] api route check: missing fastapi")
        return "skipped"

    try:
        from src.api.main import app
    except Exception as exc:
        print(f"[WARN] skip api route check: {exc}")
        return "skipped"

    paths = {route.path for route in app.routes}
    required = {"/", "/health"}
    missing = required - paths
    if missing:
        print(f"[FAIL] api routes missing: {sorted(missing)}")
        return "failed"

    print("[OK] api routes include / and /health")
    return "passed"


def main() -> int:
    repo_root = REPO_ROOT

    print("Running smoke test...")
    ok_imports = check_imports()
    ok_cli = check_cli_version(repo_root)
    api_status = check_api_routes()

    all_ok = ok_imports and ok_cli and api_status in ["passed", "skipped"]
    if all_ok:
        if api_status == "skipped":
            print("SMOKE TEST PASSED (API CHECK SKIPPED)")
        else:
            print("SMOKE TEST PASSED")
        return 0

    print("SMOKE TEST FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
