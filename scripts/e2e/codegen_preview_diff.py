""" Author: Charlie

同一 codegen plan 下，对比 hei-boot 与 hei-fastapi 的 preview 产物（逐文件）。

用法::

    python scripts/e2e/codegen_preview_diff.py \\
        --boot http://127.0.0.1:8000 \\
        --fastapi http://127.0.0.1:8100 \\
        --plan-keyword cg_test \\
        --write-unified
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from redis import Redis

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.e2e.boot_fastapi_runtime_diff import login  # noqa: E402
from scripts.e2e.client import do_raw  # noqa: E402

BACKEND_BOOT_MARKER = "src/main/java/"


def canonical_key(path: str) -> str:
    """将 Boot/FastAPI 预览路径归一到可对比键。"""
    p = path.replace("\\", "/").strip()
    while p.startswith("../"):
        p = p[3:]
    for marker in ("src/views/", "src/api/"):
        if marker in p:
            return marker + p.split(marker, 1)[1]
    if BACKEND_BOOT_MARKER in p:
        return "backend/boot/" + p.split(BACKEND_BOOT_MARKER, 1)[1]
    idx = p.find("app/modules/")
    if idx >= 0:
        return "backend/fastapi/" + p[idx + len("app/modules/"):]
    return p


def normalize_content(content: str) -> str:
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for line in text.split("\n"):
        if re.match(r"^\s*(@generated|Generated on|生成时间|\* 生成时间)", line, re.I):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def classify_file(path: str) -> str:
    key = canonical_key(path)
    if key.startswith("src/views/") or key.startswith("src/api/"):
        return "frontend"
    if key.startswith("backend/"):
        return "backend"
    return "other"


def first_diff_line(boot: str, fast: str) -> str | None:
    boot_lines = boot.split("\n")
    fast_lines = fast.split("\n")
    for i, (a, b) in enumerate(zip(boot_lines, fast_lines, strict=False)):
        if a != b:
            return f"line {i + 1}: boot={a[:120]!r} fast={b[:120]!r}"
    if len(boot_lines) != len(fast_lines):
        return f"line count boot={len(boot_lines)} fast={len(fast_lines)}"
    return None


def fetch_preview(base_api: str, token: str, plan_id: str) -> dict[str, str]:
    url = f"{base_api}/v1/admin/sys/codegen/preview?id={plan_id}"
    _, _, ar = do_raw("GET", url, token)
    if ar.code not in (0, 200):
        raise RuntimeError(f"preview failed {url}: code={ar.code}")
    data = ar.data or {}
    files = data.get("files") or []
    out: dict[str, str] = {}
    for item in files:
        path = str(item.get("path") or "")
        content = str(item.get("content") or "")
        if path:
            out[canonical_key(path)] = content
    return out


def resolve_plan_id(
    base_api: str,
    token: str,
    plan_id: str | None,
    keyword: str | None,
) -> tuple[str, str]:
    if plan_id:
        return plan_id, plan_id
    url = f"{base_api}/v1/admin/sys/codegen/page?size=50&current=1"
    _, _, ar = do_raw("GET", url, token)
    records = (ar.data or {}).get("records") or []
    if keyword:
        kw = keyword.lower()
        for record in records:
            blob = json.dumps(record, ensure_ascii=False).lower()
            if kw in blob:
                return (
                    str(record["id"]),
                    str(record.get("entity_name") or record.get("module_name") or record["id"]),
                )
    if records:
        record = records[0]
        return (
            str(record["id"]),
            str(record.get("entity_name") or record.get("module_name") or record["id"]),
        )
    raise RuntimeError("no codegen plan found on page")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Codegen preview per-file diff boot vs fastapi")
    parser.add_argument("--boot", default="http://127.0.0.1:8000")
    parser.add_argument("--fastapi", default="http://127.0.0.1:8100")
    parser.add_argument("--redis", default="redis://:123456@127.0.0.1:6379/3")
    parser.add_argument("--redis-boot", default="redis://:123456@127.0.0.1:6379/0")
    parser.add_argument("--plan-id", default=None, help="Codegen plan id（共享库同一行）")
    parser.add_argument(
        "--plan-keyword",
        default="cg_test",
        help="未指定 plan-id 时从 page 记录中匹配",
    )
    parser.add_argument("--out", default="scripts/e2e/reports/codegen_preview_diff.json")
    parser.add_argument(
        "--write-unified",
        action="store_true",
        help="为不一致的前端文件写出 unified diff",
    )
    args = parser.parse_args(argv)

    boot_api = args.boot.rstrip("/") + "/api"
    fast_api = args.fastapi.rstrip("/") + "/api"
    rdb_fast = Redis.from_url(args.redis, decode_responses=False)
    rdb_boot = Redis.from_url(args.redis_boot, decode_responses=False)

    admin_boot = login(rdb_boot, boot_api, "/v1/admin", "superadmin")
    admin_fast = login(rdb_fast, fast_api, "/v1/admin", "superadmin")

    plan_id, label = resolve_plan_id(boot_api, admin_boot, args.plan_id, args.plan_keyword)
    print(f"Plan: {label} ({plan_id})")

    boot_files = fetch_preview(boot_api, admin_boot, plan_id)
    fast_files = fetch_preview(fast_api, admin_fast, plan_id)

    boot_keys = set(boot_files)
    fast_keys = set(fast_files)
    all_keys = sorted(boot_keys | fast_keys)

    file_results: list[dict[str, Any]] = []
    frontend_match = 0
    frontend_mismatch = 0
    backend_expected_diff = 0

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = _ROOT / out_path
    diff_dir = out_path.parent / "codegen_preview_unified"
    if args.write_unified:
        diff_dir.mkdir(parents=True, exist_ok=True)

    for key in all_keys:
        category = classify_file(key)
        if key not in boot_keys:
            file_results.append({"path": key, "category": category, "status": "fast_only"})
            continue
        if key not in fast_keys:
            file_results.append({"path": key, "category": category, "status": "boot_only"})
            continue

        norm_b = normalize_content(boot_files[key])
        norm_f = normalize_content(fast_files[key])
        if norm_b == norm_f:
            if category == "frontend":
                frontend_match += 1
            file_results.append({"path": key, "category": category, "status": "match"})
            continue

        detail = first_diff_line(norm_b, norm_f)
        if category == "frontend":
            frontend_mismatch += 1
            status = "frontend_mismatch"
        elif category == "backend":
            backend_expected_diff += 1
            status = "backend_diff"
        else:
            status = "content_mismatch"

        entry: dict[str, Any] = {
            "path": key,
            "category": category,
            "status": status,
            "first_diff": detail,
            "boot_lines": len(norm_b.split("\n")),
            "fast_lines": len(norm_f.split("\n")),
        }
        if args.write_unified and category == "frontend":
            unified = difflib.unified_diff(
                norm_b.splitlines(keepends=True),
                norm_f.splitlines(keepends=True),
                fromfile=f"boot/{key}",
                tofile=f"fastapi/{key}",
            )
            diff_file = diff_dir / key.replace("/", "__")
            diff_file.write_text("".join(unified), encoding="utf-8")
            entry["unified_diff"] = str(diff_file)
        file_results.append(entry)

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "plan_id": plan_id,
        "plan_label": label,
        "summary": {
            "boot_files": len(boot_files),
            "fast_files": len(fast_files),
            "frontend_match": frontend_match,
            "frontend_mismatch": frontend_mismatch,
            "backend_diff": backend_expected_diff,
            "boot_only": sum(1 for r in file_results if r["status"] == "boot_only"),
            "fast_only": sum(1 for r in file_results if r["status"] == "fast_only"),
        },
        "files": file_results,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== CODEGEN PREVIEW DIFF ===")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    print(f"Report: {out_path}")

    return 1 if frontend_mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
