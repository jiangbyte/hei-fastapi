"""HTTP helpers for e2e against a running uvicorn."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .assert_util import ApiResp, parse_loose, truncate

_TIMEOUT = 60


def do_raw(
    method: str,
    url: str,
    token: str = "",
    body: str = "",
) -> tuple[int, bytes, ApiResp]:
    """Perform HTTP call; returns (status, raw_body, parsed envelope)."""
    data = body.encode("utf-8") if body else None
    req = Request(url, data=data, method=method.upper())
    if body:
        req.add_header("Content-Type", "application/json")
    if token:
        # Match hei-fastapi tests: raw token, no Bearer prefix.
        req.add_header("Authorization", token)
    try:
        with urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read()
            status = int(getattr(resp, "status", 200))
    except HTTPError as exc:
        raw = exc.read() if exc.fp else b""
        status = int(exc.code)
    except URLError as exc:
        raise RuntimeError(f"{method} {url}: {exc}") from exc
    ar, _ = parse_loose(raw)
    return status, raw, ar


def get_json(url: str) -> dict[str, Any]:
    status, raw, _ = do_raw("GET", url)
    if status >= 500:
        raise RuntimeError(f"GET {url} status {status}: {truncate(raw.decode('utf-8', 'replace'), 200)}")
    return json.loads(raw)


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    _, raw, _ = do_raw("POST", url, body=json.dumps(payload, ensure_ascii=False))
    return json.loads(raw)
