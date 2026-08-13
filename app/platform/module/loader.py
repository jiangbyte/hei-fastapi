""" Author: Charlie

模块加载器：按清单导入模块声明的模型与 SnailJob 任务。
"""

from __future__ import annotations

import importlib
import logging

from app.platform.module.spec import ModuleSpec

logger = logging.getLogger(__name__)


def import_modules(module_paths: tuple[str, ...] | list[str]) -> None:
    """逐个导入给定的模块路径。"""
    for module_path in module_paths:
        importlib.import_module(module_path)


def load_declared_models(module_specs: list[ModuleSpec]) -> None:
    """导入各模块声明的 ORM 模型，确保元数据注册。"""
    for module_spec in module_specs:
        import_modules(module_spec.models)


def load_declared_tasks(module_specs: list[ModuleSpec]) -> None:
    """导入各模块声明的 SnailJob 任务执行器。"""
    for module_spec in module_specs:
        import_modules(module_spec.tasks)
