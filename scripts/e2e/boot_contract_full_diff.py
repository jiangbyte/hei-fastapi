""" Author: Charlie

全量 OpenAPI 契约对比：hei-boot `/v3/api-docs` vs hei-fastapi（生成或在线）。

对比范围：路径+方法、query 参数、request body 字段、200 响应 data/records 字段（统一 snake_case）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

# Boot OpenAPI / MyBatis-Plus 分页扩展字段，不出现在 fastapi 契约中。
BOOT_PAGE_EXTRA_PROPS = frozenset(
    {
        "count_id",
        "max_limit",
        "optimize_count_sql",
        "optimize_join_of_count_sql",
        "orders",
        "search_count",
    }
)

# 实体内部字段，不作为对外契约。
IGNORE_PROPS = frozenset({"trans_map", "transMap"})

# FastAPI 虚拟展示字段（boot 无对应列，前端可用）。
FASTAPI_RESPONSE_EXTRA_OK = frozenset({"created_name", "updated_name"})

HTTP_METHODS = frozenset({"GET", "POST", "PUT", "DELETE", "PATCH"})


def to_snake(name: str) -> str:
    if not name:
        return name
    if "_" in name:
        return name
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _fetch_json(url: str, timeout: int = 60) -> dict[str, Any]:
    with urlopen(Request(url), timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"invalid JSON from {url}")
    return data


def fetch_boot_openapi(base: str) -> dict[str, Any]:
    root = base.rstrip("/")
    for path in ("/v3/api-docs", "/v3/api-docs/default"):
        doc = _fetch_json(root + path)
        if doc.get("paths"):
            return doc
    raise RuntimeError("boot openapi not found")


def fetch_fastapi_openapi(base: str | None = None) -> dict[str, Any]:
    if base:
        root = base.rstrip("/")
        for path in ("/openapi.json",):
            try:
                doc = _fetch_json(root + path)
                if doc.get("paths"):
                    return doc
            except Exception:
                continue
    # 避免 PYTHONPATH 中其他项目的 `app` 包抢占（如 acoj-worker）。
    project_root = Path(__file__).resolve().parents[2]
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    for mod in list(sys.modules):
        if mod == "app" or mod.startswith("app."):
            del sys.modules[mod]
    from app.factory import create_app

    return create_app().openapi()


def normalize_path(path: str) -> str:
    p = path.strip()
    if not p.startswith("/"):
        p = "/" + p
    if not p.startswith("/api"):
        p = "/api" + p
    return p.rstrip("/") or "/"


def resolve_ref(doc: dict[str, Any], node: Any, seen: set[str] | None = None) -> Any:
    if not isinstance(node, dict):
        return node
    seen = seen or set()
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        if ref in seen:
            return {"type": "object"}
        seen = set(seen)
        seen.add(ref)
        cur: Any = doc
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            cur = cur[part] if isinstance(cur, dict) else {}
        merged = resolve_ref(doc, cur, seen)
        extras = {k: v for k, v in node.items() if k != "$ref"}
        if extras and isinstance(merged, dict):
            out = dict(merged)
            for k, v in extras.items():
                out[k] = resolve_ref(doc, v, seen)
            return out
        return merged
    out: dict[str, Any] = {}
    for k, v in node.items():
        if k in ("allOf", "oneOf", "anyOf") and isinstance(v, list):
            # merge allOf object properties
            if k == "allOf":
                props: dict[str, Any] = {}
                for item in v:
                    resolved = resolve_ref(doc, item, seen)
                    if isinstance(resolved, dict) and "properties" in resolved:
                        props.update(resolved.get("properties") or {})
                if props:
                    out["properties"] = props
            else:
                out[k] = v
        elif isinstance(v, dict):
            out[k] = resolve_ref(doc, v, seen)
        elif isinstance(v, list):
            out[k] = [resolve_ref(doc, i, seen) if isinstance(i, dict) else i for i in v]
        else:
            out[k] = v
    return out


def schema_property_names(doc: dict[str, Any], schema: Any) -> set[str]:
    resolved = resolve_ref(doc, schema)
    if not isinstance(resolved, dict):
        return set()
    props = resolved.get("properties")
    if not isinstance(props, dict):
        return set()
    names: set[str] = set()
    for key in props:
        snake = to_snake(key)
        if snake in IGNORE_PROPS or snake in BOOT_PAGE_EXTRA_PROPS:
            continue
        names.add(snake)
    return names


def extract_body_props(doc: dict[str, Any], op: dict[str, Any]) -> set[str]:
    body = op.get("requestBody")
    if not isinstance(body, dict):
        return set()
    content = body.get("content") or {}
    names: set[str] = set()
    for media_type in ("application/json", "multipart/form-data"):
        schema = (content.get(media_type) or {}).get("schema")
        if schema:
            names.update(schema_property_names(doc, schema))
    return names


def extract_query_props(doc: dict[str, Any], op: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for param in op.get("parameters") or []:
        if not isinstance(param, dict) or param.get("in") != "query":
            continue
        name = str(param.get("name") or "")
        if name in ("param", "query"):
            schema = param.get("schema")
            names.update(schema_property_names(doc, schema))
        elif name:
            names.add(to_snake(name))
    return names


def extract_response_data_props(doc: dict[str, Any], op: dict[str, Any]) -> set[str]:
    responses = op.get("responses") or {}
    resp = responses.get("200") or responses.get("201") or {}
    content = resp.get("content") or {}
    schema = (content.get("application/json") or {}).get("schema")
    if not schema:
        return set()
    resolved = resolve_ref(doc, schema)
    if not isinstance(resolved, dict):
        return set()
    data_schema = (resolved.get("properties") or {}).get("data")
    if not data_schema:
        return schema_property_names(doc, resolved)
    data_resolved = resolve_ref(doc, data_schema)
    if not isinstance(data_resolved, dict):
        return set()
    # 分页：取 records 元素 schema
    records = (data_resolved.get("properties") or {}).get("records")
    if records:
        rec_resolved = resolve_ref(doc, records)
        if isinstance(rec_resolved, dict) and rec_resolved.get("type") == "array":
            items = rec_resolved.get("items")
            if items:
                return schema_property_names(doc, items)
        return schema_property_names(doc, data_resolved)
    return schema_property_names(doc, data_resolved)


@dataclass
class OpContract:
    method: str
    path: str
    query: set[str] = field(default_factory=set)
    body: set[str] = field(default_factory=set)
    response: set[str] = field(default_factory=set)


def collect_contracts(doc: dict[str, Any]) -> dict[tuple[str, str], OpContract]:
    out: dict[tuple[str, str], OpContract] = {}
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        norm = normalize_path(path)
        for method, op in item.items():
            m = method.upper()
            if m not in HTTP_METHODS or not isinstance(op, dict):
                continue
            key = (m, norm)
            out[key] = OpContract(
                method=m,
                path=norm,
                query=extract_query_props(doc, op),
                body=extract_body_props(doc, op),
                response=extract_response_data_props(doc, op),
            )
    return out


@dataclass
class FieldDiff:
    missing_in_fastapi: list[str] = field(default_factory=list)
    extra_in_fastapi: list[str] = field(default_factory=list)


@dataclass
class OpDiff:
    method: str
    path: str
    query: FieldDiff | None = None
    body: FieldDiff | None = None
    response: FieldDiff | None = None


def diff_fields(
    boot: set[str],
    fast: set[str],
    *,
    response: bool = False,
) -> FieldDiff | None:
    extra = fast - boot
    if response:
        extra = {x for x in extra if x not in FASTAPI_RESPONSE_EXTRA_OK}
    missing = sorted(boot - fast)
    extra_sorted = sorted(extra)
    if not missing and not extra_sorted:
        return None
    return FieldDiff(missing_in_fastapi=missing, extra_in_fastapi=extra_sorted)


def compare_contracts(
    boot: dict[tuple[str, str], OpContract],
    fast: dict[tuple[str, str], OpContract],
) -> dict[str, Any]:
    boot_keys = set(boot)
    fast_keys = set(fast)
    only_boot = sorted(f"{m} {p}" for m, p in boot_keys - fast_keys)
    only_fast = sorted(f"{m} {p}" for m, p in fast_keys - boot_keys)

    op_diffs: list[OpDiff] = []
    for key in sorted(boot_keys & fast_keys):
        b, f = boot[key], fast[key]
        od = OpDiff(method=b.method, path=b.path)
        od.query = diff_fields(b.query, f.query)
        od.body = diff_fields(b.body, f.body)
        od.response = diff_fields(b.response, f.response, response=True)
        if od.query or od.body or od.response:
            op_diffs.append(od)

    return {
        "summary": {
            "boot_operations": len(boot_keys),
            "fastapi_operations": len(fast_keys),
            "only_boot_count": len(only_boot),
            "only_fastapi_count": len(only_fast),
            "field_mismatch_count": len(op_diffs),
        },
        "only_boot": only_boot,
        "only_fastapi": only_fast,
        "field_mismatches": [
            {
                "method": d.method,
                "path": d.path,
                "query": (
                    {
                        "missing_in_fastapi": d.query.missing_in_fastapi,
                        "extra_in_fastapi": d.query.extra_in_fastapi,
                    }
                    if d.query
                    else None
                ),
                "body": (
                    {
                        "missing_in_fastapi": d.body.missing_in_fastapi,
                        "extra_in_fastapi": d.body.extra_in_fastapi,
                    }
                    if d.body
                    else None
                ),
                "response": (
                    {
                        "missing_in_fastapi": d.response.missing_in_fastapi,
                        "extra_in_fastapi": d.response.extra_in_fastapi,
                    }
                    if d.response
                    else None
                ),
            }
            for d in op_diffs
        ],
    }


def print_report(report: dict[str, Any]) -> None:
    s = report["summary"]
    print("=== Boot vs FastAPI full contract diff ===")
    print(f"Boot ops: {s['boot_operations']}, FastAPI ops: {s['fastapi_operations']}")
    print(f"Only Boot: {s['only_boot_count']}, Only FastAPI: {s['only_fastapi_count']}")
    print(f"Field mismatches: {s['field_mismatch_count']}")

    if report["only_boot"]:
        print("\n--- Only in Boot ---")
        for line in report["only_boot"][:50]:
            print(f"  {line}")
        if len(report["only_boot"]) > 50:
            print(f"  ... +{len(report['only_boot']) - 50} more")

    if report["only_fastapi"]:
        print("\n--- Only in FastAPI ---")
        for line in report["only_fastapi"][:50]:
            print(f"  {line}")
        if len(report["only_fastapi"]) > 50:
            print(f"  ... +{len(report['only_fastapi']) - 50} more")

    mismatches = report["field_mismatches"]
    if mismatches:
        print("\n--- Field mismatches (first 40) ---")
        for item in mismatches[:40]:
            print(f"\n{item['method']} {item['path']}")
            for kind in ("query", "body", "response"):
                block = item.get(kind)
                if not block:
                    continue
                miss = block.get("missing_in_fastapi") or []
                extra = block.get("extra_in_fastapi") or []
                if miss:
                    print(f"  {kind} missing in fastapi: {miss}")
                if extra:
                    print(f"  {kind} extra in fastapi: {extra}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Full OpenAPI contract diff boot vs fastapi")
    parser.add_argument("--boot", default="http://127.0.0.1:8000", help="hei-boot base URL")
    parser.add_argument("--fastapi", default="", help="fastapi URL (omit = generate from code)")
    parser.add_argument("--output", default="", help="write JSON report path")
    parser.add_argument("--json", action="store_true", help="print JSON only")
    args = parser.parse_args(argv)

    boot_doc = fetch_boot_openapi(args.boot)
    fast_doc = fetch_fastapi_openapi(args.fastapi or None)

    boot_contracts = collect_contracts(boot_doc)
    fast_contracts = collect_contracts(fast_doc)
    report = compare_contracts(boot_contracts, fast_contracts)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)
        if args.output:
            print(f"\nFull report: {args.output}")

    s = report["summary"]
    if s["only_boot_count"] or s["only_fastapi_count"] or s["field_mismatch_count"]:
        return 1
    print("\nAll endpoints and fields match (normalized snake_case)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
