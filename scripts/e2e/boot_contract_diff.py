""" Author: Charlie

跨栈 OpenAPI 对比：hei-boot `/v3/api-docs` vs hei-fastapi `/openapi.json`。

输出路径/方法差异，供 CI 或本地对齐验收。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


def _fetch_json(url: str, timeout: int = 60) -> dict[str, Any]:
    with urlopen(Request(url), timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"invalid JSON document from {url}")
    return data


def fetch_boot_openapi(base: str) -> dict[str, Any]:
    root = base.rstrip("/")
    for path in ("/v3/api-docs", "/v3/api-docs/default"):
        doc = _fetch_json(root + path)
        if doc.get("paths"):
            return doc
    raise RuntimeError("boot openapi not found")


def fetch_fastapi_openapi(base: str | None = None) -> dict[str, Any]:
    """优先从运行中的服务拉取；未提供 base 或拉取失败时从应用代码生成。"""
    if base:
        root = base.rstrip("/")
        for path in ("/openapi.json",):
            try:
                doc = _fetch_json(root + path)
                if doc.get("paths"):
                    return doc
            except Exception:
                continue
    project_root = Path(__file__).resolve().parents[2]
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    for mod in list(sys.modules):
        if mod == "app" or mod.startswith("app."):
            del sys.modules[mod]
    from app.factory import create_app

    return create_app().openapi()


def _normalize_path(path: str) -> str:
    p = path.strip()
    if not p.startswith("/"):
        p = "/" + p
    if not p.startswith("/api"):
        p = "/api" + p
    # Spring `{id}` vs FastAPI `{id}` — already compatible for set compare.
    return p.rstrip("/") or "/"


def collect_operations(doc: dict[str, Any]) -> set[tuple[str, str]]:
    ops: set[tuple[str, str]] = set()
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        norm_path = _normalize_path(path)
        for method, spec in item.items():
            m = method.upper()
            if m not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            if isinstance(spec, dict):
                ops.add((m, norm_path))
    return ops


def diff_openapi(boot_doc: dict[str, Any], fast_doc: dict[str, Any]) -> dict[str, list[str]]:
    boot_ops = collect_operations(boot_doc)
    fast_ops = collect_operations(fast_doc)
    only_boot = sorted(f"{m} {p}" for m, p in boot_ops - fast_ops)
    only_fast = sorted(f"{m} {p}" for m, p in fast_ops - boot_ops)
    return {"only_boot": only_boot, "only_fastapi": only_fast}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare boot vs fastapi OpenAPI paths")
    parser.add_argument("--boot", default="http://127.0.0.1:8000", help="hei-boot base URL")
    parser.add_argument(
        "--fastapi",
        default="",
        help="hei-fastapi base URL (optional; omit to diff from generated OpenAPI)",
    )
    parser.add_argument("--json", action="store_true", help="print JSON diff only")
    args = parser.parse_args(argv)

    boot_doc = fetch_boot_openapi(args.boot)
    fast_doc = fetch_fastapi_openapi(args.fastapi or None)
    result = diff_openapi(boot_doc, fast_doc)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"only in boot ({len(result['only_boot'])}):")
        for line in result["only_boot"]:
            print(f"  {line}")
        print(f"only in fastapi ({len(result['only_fastapi'])}):")
        for line in result["only_fastapi"]:
            print(f"  {line}")

    if result["only_boot"] or result["only_fastapi"]:
        return 1
    print("OpenAPI path/method sets match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
