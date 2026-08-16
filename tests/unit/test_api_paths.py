""" Author: Charlie

API 路径常量单测。
"""

from app.core.paths import API_ROOT_PREFIX, api_version_glob_prefix


def test_api_root_prefix():
    assert API_ROOT_PREFIX == "/api"


def test_api_version_glob_prefix():
    assert api_version_glob_prefix() == "/api/v*"
