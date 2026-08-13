""" Author: Charlie

配置值类型转换：将 DB 中存为字符串的配置值按 settings 字段声明的注解强制转换。

支持 str/bool/int/float 与 list/dict（JSON），以及 Optional 与枚举类型。
"""

from __future__ import annotations

import json
from types import UnionType
from typing import Any, Union, get_args, get_origin


def coerce_config_value(value: Any, annotation: Any) -> Any:
    """将 DB 字符串配置值强制转换为 settings 字段声明的类型。"""
    if value is None:
        return None

    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (UnionType, Union):
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return coerce_config_value(value, non_none_args[0])

    if annotation is str:
        return str(value)
    if annotation is bool:
        return _coerce_bool(value)
    if annotation is int:
        return _coerce_int(value)
    if annotation is float:
        return _coerce_float(value)
    if origin is list:
        return _coerce_json(value, list)
    if origin is dict or annotation is dict:
        return _coerce_json(value, dict)

    try:
        return annotation(value)
    except Exception:
        return value


def _coerce_bool(value: Any) -> bool:
    """把字符串解析为布尔（识别 true/1/yes/y/on 等）。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def _coerce_int(value: Any) -> int | None:
    """把值解析为整数，失败返回 None。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    """把值解析为浮点数，失败返回 None。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_json(value: Any, expected_type: type) -> Any:
    """把字符串按 JSON 解析并校验目标容器类型，失败返回 None。"""
    if isinstance(value, expected_type):
        return value
    try:
        parsed = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, expected_type) else None
