"""GET route sweep from OpenAPI paths."""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen

from .assert_util import CaseBucket, CaseResult, truncate
from .client import do_raw


def fetch_openapi_routes(base: str) -> list[dict[str, str]]:
    req = Request(f"{base}/openapi.json")
    with urlopen(req, timeout=30) as resp:
        schema = json.loads(resp.read().decode("utf-8"))
    routes: list[dict[str, str]] = []
    for path, item in (schema.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method in item:
            m = method.upper()
            if m in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                routes.append({"method": m, "path": path})
    return routes


def skip_route_reason(method: str, path: str) -> str | None:
    if method in {"HEAD", "OPTIONS", "CONNECT"}:
        return "method"
    if path in {"/metrics", "/openapi.json", "/docs", "/redoc"}:
        return "docs"
    if "/oauth/" in path:
        return "oauth"
    if path.endswith("/login") or path.endswith("/captcha") or path.endswith("/password-key"):
        return "auth-bootstrap"
    if "/cancel" in path or "/logout" in path:
        return "session-destructive"
    if "/upload" in path or "/avatar" in path or "/download" in path:
        return "storage"
    return None


def materialize_path(path: str) -> str:
    return (
        path.replace("{provider}", "github")
        .replace("{id}", "1")
        .replace("{account_id}", "1")
    )


def enrich_get_query(path: str) -> str:
    if path.endswith("/page") or path.endswith("/list") or path.endswith("/tree"):
        if "?" in path:
            return ""
        return "current=1&size=5"
    return ""


def pick_token(path: str, admin: str, portal: str) -> str:
    if "/portal/" in path:
        return portal
    if "/internal/" in path:
        return ""
    return admin


def is_sql_suspect(body: str, error: str = "") -> bool:
    low = (body + " " + error).lower()
    keys = ("sql", "dialect", "pq:", "mysql", "ilike", "jsonb", "syntax error", "operationalerror")
    return any(k in low for k in keys)


def run_get_sweep(
    base: str,
    admin_tok: str,
    portal_tok: str,
    routes: list[dict[str, str]],
    bucket: CaseBucket,
    skipped: list[CaseResult],
    results: list[dict[str, Any]],
) -> tuple[int, int]:
    """Sweep GET routes. Returns (ok_2xx_4xx, fail_5xx)."""
    ok_count = 0
    fail_5xx = 0
    seen: set[str] = set()
    for r in routes:
        if r["method"] != "GET":
            continue
        path = r["path"]
        if path in seen:
            continue
        seen.add(path)
        reason = skip_route_reason("GET", path)
        if reason:
            skipped.append(CaseResult(name=f"GET {path}", ok=True, error=reason))
            continue
        path_m = materialize_path(path)
        q = enrich_get_query(path_m)
        full = path_m
        if q:
            full = f"{path_m}&{q}" if "?" in path_m else f"{path_m}?{q}"
        url = base + full
        tok = pick_token(path_m, admin_tok, portal_tok)
        cr = CaseResult(name=f"GET {full}", url=url)
        try:
            status, raw, ar = do_raw("GET", url, tok)
            body = truncate(raw.decode("utf-8", "replace"), 280)
            cr.status, cr.biz_code, cr.body = status, ar.code, body
            entry = {
                "method": "GET",
                "path": full,
                "url": url,
                "status": status,
                "biz_code": ar.code,
                "body": body,
                "is_5xx": status >= 500 or ar.code >= 500,
                "sql_suspect": is_sql_suspect(body),
            }
            results.append(entry)
            if entry["is_5xx"] or entry["sql_suspect"]:
                cr.error = "5xx" if entry["is_5xx"] else "sql_suspect"
                fail_5xx += 1
                bucket.add(cr)
            else:
                cr.ok = True
                ok_count += 1
                bucket.add(cr)
        except Exception as exc:  # noqa: BLE001
            cr.error = str(exc)
            fail_5xx += 1
            bucket.add(cr)
            results.append(
                {
                    "method": "GET",
                    "path": full,
                    "url": url,
                    "error": str(exc),
                    "is_5xx": True,
                    "sql_suspect": is_sql_suspect("", str(exc)),
                }
            )
    return ok_count, fail_5xx
