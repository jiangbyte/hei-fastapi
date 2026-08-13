""" Author: Charlie

模块钩子执行：按模块清单顺序运行启动/关闭钩子与事件处理器。
"""

from __future__ import annotations

import inspect
import logging

from app.platform.module.spec import ModuleSpec, import_string

logger = logging.getLogger(__name__)


async def run_startup_hooks(module_specs: list[ModuleSpec]) -> None:
    """按声明顺序运行所有模块的启动钩子。"""
    for module_spec in module_specs:
        await _run_hooks(module_spec.startup_hooks)


async def run_shutdown_hooks(module_specs: list[ModuleSpec]) -> None:
    """按逆序运行所有模块的关闭钩子。"""
    for module_spec in reversed(module_specs):
        await _run_hooks(module_spec.shutdown_hooks)


async def run_event_handlers(module_specs: list[ModuleSpec]) -> None:
    """运行所有模块的事件处理器注册钩子。"""
    for module_spec in module_specs:
        await _run_hooks(module_spec.event_handlers)


async def _run_hooks(hooks: tuple[str, ...]) -> None:
    """依次导入并调用钩子，协程结果会被等待。"""
    for hook_path in hooks:
        hook = import_string(hook_path)
        result = hook()
        if inspect.isawaitable(result):
            await result
