"""Envelope / page assertions for e2e reports."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApiResp:
    code: int = 0
    message: str = ""
    data: Any = None


@dataclass
class CaseResult:
    name: str
    ok: bool = False
    error: str = ""
    url: str = ""
    status: int = 0
    biz_code: int = 0
    body: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"name": self.name, "ok": self.ok}
        if self.error:
            d["error"] = self.error
        if self.url:
            d["url"] = self.url
        if self.status:
            d["status"] = self.status
        if self.biz_code:
            d["biz_code"] = self.biz_code
        if self.body:
            d["body"] = self.body
        return d


@dataclass
class CaseBucket:
    total: int = 0
    pass_: int = 0
    fail: list[CaseResult] = field(default_factory=list)

    def add(self, cr: CaseResult) -> None:
        self.total += 1
        if cr.ok:
            self.pass_ += 1
            print("PASS", cr.name, flush=True)
        else:
            self.fail.append(cr)
            err = (cr.error or "").encode("utf-8", "replace").decode("utf-8", "replace")
            print("FAIL", cr.name, err[:240], flush=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "pass": self.pass_,
            "fail": [f.to_dict() for f in self.fail],
        }


def truncate(s: str, n: int) -> str:
    if len(s) <= n:
        return s
    return s[:n] + "..."


def parse_code(raw: Any) -> int:
    if raw is None:
        return 0
    if isinstance(raw, bool):
        return 0
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return 0
        return int(text)
    return 0


def parse_loose(body: bytes | str) -> tuple[ApiResp, Any]:
    """Parse unified envelope; code may be int or string."""
    if isinstance(body, bytes):
        text = body.decode("utf-8", "replace")
    else:
        text = body
    if not text.strip():
        return ApiResp(), None
    obj = json.loads(text)
    if not isinstance(obj, dict):
        return ApiResp(), None
    ar = ApiResp(
        code=parse_code(obj.get("code")),
        message=str(obj.get("message") or ""),
        data=obj.get("data"),
    )
    return ar, ar.data


def parse_envelope(body: bytes | str) -> tuple[ApiResp, dict[str, Any] | None]:
    ar, data = parse_loose(body)
    if isinstance(data, dict):
        return ar, data
    return ar, None


def assert_biz_ok(status: int, code: int) -> None:
    if status < 200 or status >= 300:
        raise AssertionError(f"http status {status}")
    if code not in (0, 200):
        raise AssertionError(f"biz code {code}")


def assert_keys(m: dict[str, Any] | None, *keys: str) -> None:
    if m is None:
        raise AssertionError("data is nil")
    missing = [k for k in keys if k not in m]
    if missing:
        raise AssertionError(f"missing keys: {','.join(missing)}")


def assert_page(m: dict[str, Any] | None) -> list[dict[str, Any]]:
    assert_keys(m, "size", "current", "total", "pages", "records")
    assert m is not None
    raw = m["records"]
    if not isinstance(raw, list):
        raise AssertionError("records not array")
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(item)
    return out


def as_string(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, float):
        return f"{v:.0f}"
    return str(v)


def find_id_by_field(records: list[dict[str, Any]], field: str, want: str) -> str:
    for rec in records:
        if as_string(rec.get(field)) == want:
            return as_string(rec.get("id"))
    return ""
