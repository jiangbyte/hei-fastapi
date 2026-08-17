""" Author: Charlie

全量 OpenAPI 契约扫：GET 出参对照 response schema；POST 入参负向（缺必填 → 422 错误壳）。
写成功出参由 CRUD 用例覆盖。
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

from .assert_util import CaseBucket, CaseResult, truncate
from .client import do_raw
from .contract import (
    build_registry,
    fetch_openapi,
    generate_example,
    has_json_200,
    iter_operations,
    request_body_schema,
    response_json_schema,
    validate_against_schema,
)
from .sweep import is_sql_suspect, materialize_path, pick_token, skip_route_reason


def _enrich_get_query(path: str, op: dict[str, Any]) -> str:
    """按 OpenAPI parameters 补齐 GET query；分页类补 current/size。"""
    params = op.get("parameters") or []
    parts: list[str] = []
    names: set[str] = set()
    for p in params:
        if not isinstance(p, dict) or p.get("in") != "query":
            continue
        name = str(p.get("name") or "")
        if not name:
            continue
        names.add(name)
        schema = p.get("schema") if isinstance(p.get("schema"), dict) else {}
        # 仅补 required 或有 default/example 的；分页字段始终补
        required = bool(p.get("required"))
        if name in {"current", "size", "page", "pageSize"} or required:
            if "example" in (schema or {}):
                val = schema["example"]
            elif "default" in (schema or {}):
                val = schema["default"]
            elif name in {"current", "page"}:
                val = 1
            elif name in {"size", "pageSize"}:
                val = 5
            else:
                val = generate_example({}, schema or {"type": "string"})
            parts.append(f"{quote(name)}={quote(str(val))}")
    if path.rstrip("/").endswith(("/page", "/list", "/tree")):
        if "current" not in names:
            parts.append("current=1")
        if "size" not in names:
            parts.append("size=5")
    # 常见详情 id
    if "id" not in names and any(
        isinstance(p, dict) and p.get("in") == "query" and p.get("name") == "id" for p in params
    ):
        pass
    # 详情类缺省给种子 id=1
    for p in params:
        if isinstance(p, dict) and p.get("in") == "query" and p.get("name") == "id":
            if not any(x.startswith("id=") for x in parts):
                parts.append("id=1")
    return "&".join(parts)


def _skip_contract(method: str, path: str) -> str | None:
    reason = skip_route_reason(method, path)
    if reason:
        return reason
    # 契约扫额外跳过：会发短信/邮件、注册、改密、踢会话等副作用
    low = path.lower()
    if any(
        s in low
        for s in (
            "/send-login-code",
            "/register/send-code",
            "/register",
            "/forgot-password",
            "/reset-password",
            "/refresh",
            "/kick",
            "/force-logout",
            "/test-push",
            "/trigger",
            "/execute",
        )
    ):
        return "side-effect"
    return None


def _validate_response(
    openapi: dict[str, Any],
    registry: Any,
    op: dict[str, Any],
    status: int,
    raw: bytes,
) -> str | None:
    """按实际 HTTP status 匹配 OpenAPI responses；无 JSON schema 的二进制 200 跳过。"""
    text = raw.decode("utf-8", "replace")
    status_key = str(status)
    schema = response_json_schema(openapi, op, status_key)
    if schema is None and status == 200 and not has_json_200(openapi, op):
        # download 等非 JSON
        return None
    if schema is None:
        # 未声明该 status：允许 4xx 业务/校验，但仍要求是 envelope 形状的错误壳（若可解析）
        if 400 <= status < 500:
            try:
                obj = json.loads(text) if text.strip() else None
            except json.JSONDecodeError:
                return f"non-json error body status={status}"
            if isinstance(obj, dict) and "code" in obj and "message" in obj:
                return None
            return f"undeclared status={status} body not ApiError-shaped"
        if status >= 500:
            return f"undeclared 5xx status={status}"
        return f"no schema for status={status}"
    try:
        instance = json.loads(text) if text.strip() else None
    except json.JSONDecodeError:
        return f"response not json status={status}"
    return validate_against_schema(openapi, registry, schema, instance)


def run_contract_sweep(
    base: str,
    admin_tok: str,
    portal_tok: str,
    out_bucket: CaseBucket,
    in_bucket: CaseBucket,
    skipped: list[CaseResult],
    results: list[dict[str, Any]],
) -> dict[str, int]:
    """跑全量契约。返回计数摘要。"""
    openapi = fetch_openapi(base)
    registry = build_registry(openapi)
    ops = iter_operations(openapi)

    stats = {
        "ops_total": len(ops),
        "out_pass": 0,
        "out_fail": 0,
        "in_pass": 0,
        "in_fail": 0,
        "skipped": 0,
        "fail_5xx": 0,
        "sql_suspect": 0,
    }

    for item in ops:
        method = item["method"]
        path = item["path"]
        op = item["operation"]
        name = f"{method} {path}"

        skip = _skip_contract(method, path)
        if skip:
            skipped.append(CaseResult(name=name, ok=True, error=skip))
            stats["skipped"] += 1
            continue

        path_m = materialize_path(path)
        # 路径参数尽量用种子 id=1
        path_m = path_m.replace("/0", "/1") if path_m.endswith("/0") else path_m
        tok = pick_token(path_m, admin_tok, portal_tok)
        url = base + path_m

        # ---- 出参：仅 GET（写成功出参由 CRUD 覆盖；避免 exit/batch-save 等弄脏会话）----
        if method == "GET":
            q = _enrich_get_query(path_m, op)
            get_url = f"{url}&{q}" if q and "?" in url else (f"{url}?{q}" if q else url)
            cr_out = CaseResult(name=f"OUT {name}", url=get_url)
            try:
                status, raw, ar = do_raw(method, get_url, tok, "")
                text = raw.decode("utf-8", "replace")
                cr_out.status, cr_out.biz_code, cr_out.body = status, ar.code, truncate(text, 240)
                entry: dict[str, Any] = {
                    "phase": "out",
                    "method": method,
                    "path": path,
                    "url": get_url,
                    "status": status,
                    "biz_code": ar.code,
                    "body": truncate(text, 280),
                    "is_5xx": status >= 500 or ar.code >= 500,
                    "sql_suspect": is_sql_suspect(text),
                }
                err = _validate_response(openapi, registry, op, status, raw)
                if entry["is_5xx"] or entry["sql_suspect"]:
                    cr_out.error = "5xx" if entry["is_5xx"] else "sql_suspect"
                    stats["fail_5xx" if entry["is_5xx"] else "sql_suspect"] += 1
                    stats["out_fail"] += 1
                    out_bucket.add(cr_out)
                elif err:
                    cr_out.error = err
                    stats["out_fail"] += 1
                    out_bucket.add(cr_out)
                    entry["schema_error"] = err
                else:
                    cr_out.ok = True
                    stats["out_pass"] += 1
                    out_bucket.add(cr_out)
                results.append(entry)
            except Exception as exc:  # noqa: BLE001
                cr_out.error = str(exc)
                stats["out_fail"] += 1
                out_bucket.add(cr_out)
                results.append(
                    {
                        "phase": "out",
                        "method": method,
                        "path": path,
                        "url": get_url,
                        "error": str(exc),
                        "is_5xx": True,
                    }
                )

        # ---- 入参：有 JSON body 的 POST —— 缺必填应 422 且符合错误壳 ----
        if method != "POST":
            continue
        req_schema = request_body_schema(openapi, op)
        if req_schema is None:
            continue
        # reset url without GET query pollution
        url = base + path_m
        cr_in = CaseResult(name=f"IN {name}", url=url)
        try:
            st, raw, ar = do_raw("POST", url, tok, "{}")
            text = raw.decode("utf-8", "replace")
            cr_in.status, cr_in.biz_code, cr_in.body = st, ar.code, truncate(text, 240)
            entry_in: dict[str, Any] = {
                "phase": "in",
                "method": method,
                "path": path,
                "url": url,
                "status": st,
                "biz_code": ar.code,
                "body": truncate(text, 280),
                "is_5xx": st >= 500 or ar.code >= 500,
                "sql_suspect": is_sql_suspect(text),
            }
            if entry_in["is_5xx"] or entry_in["sql_suspect"]:
                cr_in.error = "5xx" if entry_in["is_5xx"] else "sql_suspect"
                stats["in_fail"] += 1
                stats["fail_5xx" if entry_in["is_5xx"] else "sql_suspect"] += 1
                in_bucket.add(cr_in)
            else:
                err = _validate_response(openapi, registry, op, st, raw)
                if err and st == 422:
                    cr_in.error = err
                    stats["in_fail"] += 1
                    in_bucket.add(cr_in)
                    entry_in["schema_error"] = err
                elif st >= 500:
                    cr_in.error = f"unexpected status {st}"
                    stats["in_fail"] += 1
                    in_bucket.add(cr_in)
                elif err and st < 400:
                    cr_in.error = err
                    stats["in_fail"] += 1
                    in_bucket.add(cr_in)
                    entry_in["schema_error"] = err
                else:
                    cr_in.ok = True
                    stats["in_pass"] += 1
                    in_bucket.add(cr_in)
            results.append(entry_in)
        except Exception as exc:  # noqa: BLE001
            cr_in.error = str(exc)
            stats["in_fail"] += 1
            in_bucket.add(cr_in)
            results.append(
                {
                    "phase": "in",
                    "method": method,
                    "path": path,
                    "url": url,
                    "error": str(exc),
                    "is_5xx": True,
                }
            )

    return stats
