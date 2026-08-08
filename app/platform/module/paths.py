""" Author: Charlie

与路由装饰器约定对齐的路径常量（非“改一处升全库版本”）。

项目约定（见 RouteSpec）：全局挂 ``/api``，完整路径写在装饰器上，例如
``/v1/admin/sys/positions/create``。升 API 版本需同步改装饰器（或全库替换 ``/v1/``）。

此处只放：
- ``API_ROOT_PREFIX``：模块挂载用
- ``DEFAULT_FILES_PUBLIC_PATH``：与当前公开文件路由一致的默认值，避免三处字面量漂移
- ``api_version_glob_prefix``：白名单 fnmatch 用 ``/api/v*``，匹配时不绑死某一版
"""
from __future__ import annotations

API_ROOT_PREFIX = "/api"

# 与装饰器里的 /v1/... 及公开文件路由保持一致；不是全库版本开关。
DEFAULT_FILES_PUBLIC_PATH = f"{API_ROOT_PREFIX}/v1/files"


def api_version_glob_prefix() -> str:
    """供 fnmatch 使用的版本通配前缀：/api/v*。"""
    return f"{API_ROOT_PREFIX}/v*"
