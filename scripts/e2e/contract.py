""" Author: Charlie

OpenAPI 契约：解析 schema、生成最小入参、校验出参 JSON。
"""

from __future__ import annotations

import copy
import json
from typing import Any
from urllib.request import Request, urlopen

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


def fetch_openapi(base: str) -> dict[str, Any]:
    req = Request(f"{base.rstrip('/')}/openapi.json")
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_registry(openapi: dict[str, Any]) -> Registry:
    """把 components.schemas 挂到 Registry，供 Draft202012Validator 解析 $ref。"""
    schemas = (openapi.get("components") or {}).get("schemas") or {}
    resources: dict[str, Resource] = {}
    for name, schema in schemas.items():
        if isinstance(schema, dict):
            resources[f"#/components/schemas/{name}"] = Resource.from_contents(
                schema, default_specification=DRAFT202012
            )
    # 根文档本身也可引用
    resources[""] = Resource.from_contents(openapi, default_specification=DRAFT202012)
    registry: Registry = Registry()
    for uri, resource in resources.items():
        registry = registry.with_resource(uri, resource)
    return registry


def resolve_ref(openapi: dict[str, Any], node: Any, *, _seen: set[str] | None = None) -> Any:
    """递归展开 $ref，供入参生成与出参校验（避免 Registry 相对指针失败）。"""
    if not isinstance(node, dict):
        if isinstance(node, list):
            return [resolve_ref(openapi, i, _seen=_seen) for i in node]
        return node
    seen = set() if _seen is None else _seen
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        if ref in seen:
            return {"type": "object"}
        seen = set(seen)
        seen.add(ref)
        cur: Any = openapi
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(cur, dict) or part not in cur:
                return {"type": "object"}
            cur = cur[part]
        merged = resolve_ref(openapi, copy.deepcopy(cur), _seen=seen)
        extras = {k: v for k, v in node.items() if k != "$ref"}
        if extras and isinstance(merged, dict):
            out = copy.deepcopy(merged) if isinstance(merged, dict) else {"type": "object"}
            # extras 里也可能含嵌套结构
            for ek, ev in extras.items():
                out[ek] = resolve_ref(openapi, ev, _seen=seen)
            return out
        return merged

    out: dict[str, Any] = {}
    for k, v in node.items():
        if k in {"allOf", "oneOf", "anyOf"} and isinstance(v, list):
            out[k] = [resolve_ref(openapi, i, _seen=seen) for i in v]
        elif k == "properties" and isinstance(v, dict):
            out[k] = {pk: resolve_ref(openapi, pv, _seen=seen) for pk, pv in v.items()}
        elif k == "items":
            out[k] = resolve_ref(openapi, v, _seen=seen)
        elif k == "additionalProperties" and isinstance(v, dict):
            out[k] = resolve_ref(openapi, v, _seen=seen)
        else:
            out[k] = resolve_ref(openapi, v, _seen=seen) if isinstance(v, (dict, list)) else v
    return out


def _string_for_schema(schema: dict[str, Any]) -> str:
    """按 format / pattern / minLength 生成合法字符串入参。"""
    if schema.get("format") == "date-time":
        return "2026-01-01T00:00:00Z"
    if schema.get("format") == "email":
        return "e2e@example.com"
    if schema.get("format") == "uri":
        return "https://example.com"
    pattern = str(schema.get("pattern") or "")
    min_len = int(schema.get("minLength") or 1)
    max_len = schema.get("maxLength")
    if pattern in {r"^[A-Z0-9_]+$", "^[A-Z0-9_]+$"}:
        base = "E2ECODE1"
    elif "A-Z" in pattern and "0-9" in pattern:
        base = "E2ECODE1"
    elif pattern.startswith("^") and pattern.endswith("$") and "[" not in pattern:
        base = pattern[1:-1] or "x"
    else:
        base = "x" * max(min_len, 1)
    if max_len is not None:
        base = base[: int(max_len)]
    if len(base) < min_len:
        base = (base + ("1" * min_len))[:min_len]
    return base


def _first_type(schema: dict[str, Any]) -> str | None:
    t = schema.get("type")
    if isinstance(t, list):
        for item in t:
            if item != "null":
                return str(item)
        return str(t[0]) if t else None
    if isinstance(t, str):
        return t
    if "properties" in schema or schema.get("additionalProperties") is not None:
        return "object"
    if "items" in schema:
        return "array"
    if "enum" in schema and schema["enum"]:
        sample = schema["enum"][0]
        if isinstance(sample, bool):
            return "boolean"
        if isinstance(sample, int) and not isinstance(sample, bool):
            return "integer"
        if isinstance(sample, float):
            return "number"
        if isinstance(sample, str):
            return "string"
    return None


def generate_example(openapi: dict[str, Any], schema: dict[str, Any] | None, *, depth: int = 0) -> Any:
    """从 JSON Schema 生成最小可序列化示例（偏 wire：标量优先字符串）。"""
    if schema is None or depth > 8:
        return None
    schema = resolve_ref(openapi, schema)
    if not isinstance(schema, dict):
        return None

    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if "const" in schema:
        return schema["const"]
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]

    for key in ("anyOf", "oneOf"):
        opts = schema.get(key)
        if isinstance(opts, list) and opts:
            non_null = [
                o
                for o in opts
                if not (isinstance(o, dict) and o.get("type") == "null")
            ]
            return generate_example(openapi, non_null[0] if non_null else opts[0], depth=depth + 1)

    all_of = schema.get("allOf")
    if isinstance(all_of, list) and all_of:
        merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
        for part in all_of:
            part_r = resolve_ref(openapi, part) if isinstance(part, dict) else {}
            if not isinstance(part_r, dict):
                continue
            props = part_r.get("properties") or {}
            if isinstance(props, dict):
                merged["properties"].update(props)
            req = part_r.get("required") or []
            if isinstance(req, list):
                merged["required"] = list(dict.fromkeys([*merged["required"], *req]))
            for k, v in part_r.items():
                if k not in {"properties", "required"}:
                    merged.setdefault(k, v)
        return generate_example(openapi, merged, depth=depth + 1)

    t = _first_type(schema)
    if t == "object" or (t is None and "properties" in schema):
        props = schema.get("properties") or {}
        required = list(schema.get("required") or [])
        obj: dict[str, Any] = {}
        if isinstance(props, dict):
            keys = required if required else list(props.keys())[:8]
            for name in keys:
                if name in props:
                    obj[name] = generate_example(openapi, props[name], depth=depth + 1)
        return obj
    if t == "array":
        items = schema.get("items")
        if isinstance(items, dict):
            return [generate_example(openapi, items, depth=depth + 1)]
        return []
    if t == "boolean":
        return True
    if t == "integer":
        return int(schema.get("minimum") or 1)
    if t == "number":
        return float(schema.get("minimum") or 1)
    if t == "string" or t is None:
        return _string_for_schema(schema)
    return None


def response_json_schema(openapi: dict[str, Any], op: dict[str, Any], status: str) -> dict[str, Any] | None:
    responses = op.get("responses") or {}
    resp = responses.get(status) or responses.get(str(int(status))) if status.isdigit() else None
    if not isinstance(resp, dict):
        return None
    content = resp.get("content") or {}
    app_json = content.get("application/json")
    if not isinstance(app_json, dict):
        return None
    schema = app_json.get("schema")
    if not isinstance(schema, dict):
        return None
    return schema


def request_body_schema(openapi: dict[str, Any], op: dict[str, Any]) -> dict[str, Any] | None:
    body = op.get("requestBody")
    if not isinstance(body, dict):
        return None
    content = body.get("content") or {}
    for ctype in ("application/json", "multipart/form-data", "application/x-www-form-urlencoded"):
        block = content.get(ctype)
        if isinstance(block, dict) and isinstance(block.get("schema"), dict):
            return block["schema"]
    return None


def has_json_200(openapi: dict[str, Any], op: dict[str, Any]) -> bool:
    return response_json_schema(openapi, op, "200") is not None


def validate_against_schema(
    openapi: dict[str, Any],
    registry: Registry | None,
    schema: dict[str, Any],
    instance: Any,
) -> str | None:
    """校验失败返回错误摘要，成功返回 None。"""
    _ = registry  # 保留参数兼容；实际用全量 dereference，避免相对 $ref 失败
    try:
        resolved = resolve_ref(openapi, schema)
        # 去掉 OpenAPI 扩展字段，降低 Draft202012 噪音
        if isinstance(resolved, dict):
            resolved = {k: v for k, v in resolved.items() if not str(k).startswith("x-")}
        validator = Draft202012Validator(resolved)
        errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
        if not errors:
            return None
        err = errors[0]
        path = ".".join(str(p) for p in err.path) or "$"
        return f"{path}: {err.message}"
    except Exception as exc:  # noqa: BLE001 — 契约层收集错误
        return f"validator_error: {exc}"


def iter_operations(openapi: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    paths = openapi.get("paths") or {}
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            m = str(method).upper()
            if m not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            if not isinstance(op, dict):
                continue
            out.append(
                {
                    "method": m,
                    "path": path,
                    "operation": op,
                    "operationId": op.get("operationId") or f"{m} {path}",
                }
            )
    return out
