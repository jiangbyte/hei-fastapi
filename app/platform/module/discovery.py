""" Author: Charlie

模块发现：扫描 app.modules 下的子包，加载各模块的 ModuleSpec 清单并做拓扑排序。

支持禁用/启用开关（环境变量或清单 enabled 字段）与进程级缓存。
"""

from __future__ import annotations

import importlib
import logging
import os
from functools import cache

from app.platform.module.spec import ModuleSpec

logger = logging.getLogger(__name__)


def _iter_module_manifest_names(package_name: str) -> list[str]:
    """遍历包下的子包，收集拥有 ``module`` 清单的子包名。"""
    import pkgutil

    package = importlib.import_module(package_name)
    package_paths = getattr(package, "__path__", None)
    if package_paths is None:
        logger.warning(
            "Package %s has no __path__ (namespace package?) — no modules will be discovered",
            package_name,
        )
        return []

    logger.info(
        "Scanning for module manifests in %s at paths: %s",
        package_name,
        list(package_paths),
    )

    names: list[str] = []
    subpkg_count = 0
    for module_info in pkgutil.walk_packages(package_paths, prefix=f"{package_name}."):
        if not module_info.ispkg:
            continue
        subpkg_count += 1
        manifest_name = f"{module_info.name}.module"
        if importlib.util.find_spec(manifest_name) is not None:
            names.append(manifest_name)

    logger.info(
        "Found %d subpackages in %s, %d have module manifests",
        subpkg_count,
        package_name,
        len(names),
    )
    return sorted(set(names))


def load_module_specs(
    package_name: str = "app.modules",
    *,
    include_disabled: bool = False,
) -> list[ModuleSpec]:
    """发现 ModuleSpec 清单。

    运行期调用方保持 ``include_disabled=False``，禁用模块不会注册路由/任务/钩子。
    Alembic 应传入 ``include_disabled=True``，以便模型元数据完整且无需切换模块开关。
    """
    package_names = _resolve_package_names(package_name)
    return list(_load_module_specs_cached(tuple(package_names), include_disabled))


def clear_module_specs_cache() -> None:
    """清除发现缓存（测试 / 热重载辅助）。"""
    _load_module_specs_cached.cache_clear()


@cache
def _load_module_specs_cached(
    package_names: tuple[str, ...],
    include_disabled: bool,
) -> tuple[ModuleSpec, ...]:
    specs: list[ModuleSpec] = []
    seen: set[str] = set()
    manifest_names: list[str] = []
    for package_name in package_names:
        manifest_names.extend(_iter_module_manifest_names(package_name))
    logger.info("Loading %d module specs from %s", len(manifest_names), package_names)
    for manifest_name in manifest_names:
        manifest = importlib.import_module(manifest_name)
        module_spec = getattr(manifest, "module", None)
        if not isinstance(module_spec, ModuleSpec):
            raise TypeError(f"{manifest_name}.module must be a ModuleSpec instance")
        if module_spec.name in seen:
            raise ValueError(f"Duplicate module name: {module_spec.name}")
        seen.add(module_spec.name)
        if not include_disabled and not _is_module_enabled(module_spec):
            logger.info("Module %s disabled", module_spec.name)
            continue
        specs.append(module_spec)

    specs = _topological_sort(specs)

    route_count = sum(len(spec.routes) for spec in specs)
    logger.info(
        "Loaded %d modules with %d route specs total (include_disabled=%s)",
        len(specs),
        route_count,
        include_disabled,
    )
    return tuple(specs)


def _resolve_package_names(package_name: str) -> list[str]:
    """合并显式包名与环境变量 HEI_MODULE_PACKAGES 中的包名。"""
    package_names = [item.strip() for item in package_name.split(",") if item.strip()]
    env_packages = [
        item.strip()
        for item in os.environ.get("HEI_MODULE_PACKAGES", "").split(",")
        if item.strip()
    ]
    for item in env_packages:
        if item not in package_names:
            package_names.append(item)
    return package_names


def _is_module_enabled(spec: ModuleSpec) -> bool:
    """判断模块是否启用：禁用/启用环境变量优先于清单 enabled。"""
    disabled = _env_name_set("HEI_DISABLED_MODULES")
    enabled = _env_name_set("HEI_ENABLED_MODULES")
    if spec.name in disabled:
        return False
    if spec.name in enabled:
        return True
    return spec.enabled


def _env_name_set(name: str) -> set[str]:
    """解析逗号分隔的环境变量为去空白的集合。"""
    return {item.strip() for item in os.environ.get(name, "").split(",") if item.strip()}


def _topological_sort(specs: list[ModuleSpec]) -> list[ModuleSpec]:
    """按 depends_on 拓扑排序，保证依赖模块在前。"""
    by_name = {s.name: s for s in specs}
    visited: set[str] = set()
    result: list[ModuleSpec] = []

    def visit(name: str, path: set[str]) -> None:
        if name in visited:
            return
        if name in path:
            raise ValueError(f"Circular module dependency: {' -> '.join(path)} -> {name}")
        spec = by_name.get(name)
        if spec is None:
            logger.warning("Module '%s' not found (declared as dependency)", name)
            visited.add(name)
            return
        path.add(name)
        for dep in spec.depends_on:
            visit(dep, path)
        path.remove(name)
        visited.add(name)
        result.append(spec)

    for spec in specs:
        if spec.name not in visited:
            visit(spec.name, set())

    # 未声明 depends_on 的模块保持原 order 排序
    resolved_names = {s.name for s in result}
    remaining = [s for s in specs if s.name not in resolved_names]
    remaining.sort(key=lambda s: (s.order, s.name))
    result.extend(remaining)

    return result
