""" Author: Charlie

模块发现：运行时 enable 过滤 vs 迁移 include_disabled。
"""
from __future__ import annotations

import os

import pytest

from app.platform.module.discovery import clear_module_specs_cache, load_module_specs

CG_TEST_ACTIVITY = "biz.cg_test_activity"


@pytest.fixture(autouse=True)
def _clear_discovery_cache():
    clear_module_specs_cache()
    previous = {
        "HEI_ENABLED_MODULES": os.environ.pop("HEI_ENABLED_MODULES", None),
        "HEI_DISABLED_MODULES": os.environ.pop("HEI_DISABLED_MODULES", None),
    }
    try:
        yield
    finally:
        clear_module_specs_cache()
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_runtime_specs_include_codegen_example_modules():
    names = {spec.name for spec in load_module_specs()}
    assert CG_TEST_ACTIVITY in names


def test_include_disabled_still_loads_codegen_test_modules():
    names = {spec.name for spec in load_module_specs(include_disabled=True)}
    assert CG_TEST_ACTIVITY in names


def test_hei_disabled_modules_excludes_example_module_at_runtime():
    os.environ["HEI_DISABLED_MODULES"] = CG_TEST_ACTIVITY
    clear_module_specs_cache()
    runtime_names = {spec.name for spec in load_module_specs()}
    assert CG_TEST_ACTIVITY not in runtime_names

    migrate_names = {spec.name for spec in load_module_specs(include_disabled=True)}
    assert CG_TEST_ACTIVITY in migrate_names


def test_hei_disabled_modules_excludes_even_when_include_disabled_false():
    # banner 通常启用；仅运行时强制禁用
    os.environ["HEI_DISABLED_MODULES"] = "sys.banner"
    clear_module_specs_cache()
    runtime_names = {spec.name for spec in load_module_specs()}
    assert "sys.banner" not in runtime_names

    migrate_names = {spec.name for spec in load_module_specs(include_disabled=True)}
    assert "sys.banner" in migrate_names
