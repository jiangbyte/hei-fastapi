"""
Permission auto-discovery scanner.

At application startup, scans all registered routes for @HeiCheckPermission
decorator metadata, groups by module, and caches in Redis.
Only RELATIONSHIPS (grants) are persisted to MySQL — never the definitions.
"""
import logging
from typing import Set, Tuple

from core.constants import PERMISSION_CACHE_KEY

logger = logging.getLogger(__name__)


def collect_permissions_from_routes(app) -> Set[Tuple[str, str, str]]:
    """Collect all (permission_code, module, name) tuples from route endpoints.
    The name is extracted from the route's summary (FastAPI route summary text).
    """
    permissions = set()
    for route in app.routes:
        if not hasattr(route, "endpoint"):
            continue
        endpoint = route.endpoint
        permission = getattr(endpoint, "_hei_permission", None)
        if not permission:
            permission = getattr(endpoint, "_hei_client_permission", None)
        if not permission:
            continue

        name = getattr(route, "summary", None) or ""

        if isinstance(permission, str):
            perm_list = [permission]
        else:
            perm_list = permission

        for perm in perm_list:
            module = _get_module_from_code(perm)
            permissions.add((perm, module, name))

    logger.info(f"Discovered {len(permissions)} permission codes from route decorators")
    return permissions


def _get_module_from_code(code: str) -> str:
    parts = code.split(":")
    return ":".join(parts[:-1]) if len(parts) > 1 else code


def _build_module_tree(permissions: Set[Tuple[str, str, str]]) -> dict:
    """Build a module-grouped dict from scanned permissions."""
    tree: dict = {}
    for code, module, name in permissions:
        if module not in tree:
            tree[module] = {}
        tree[module][code] = {
            "code": code,
            "module": module,
            "name": name,
        }
    return tree


async def sync_to_redis(permissions: Set[Tuple[str, str, str]]):
    """Store scanned permissions grouped by module into Redis."""
    from core.db.redis import get_client

    redis_client = get_client()
    if not redis_client:
        logger.warning("Redis not available, skipping permission cache")
        return

    tree = _build_module_tree(permissions)
    import json
    await redis_client.set(PERMISSION_CACHE_KEY, json.dumps(tree, ensure_ascii=False))
    total = sum(len(v) for v in tree.values())
    logger.info(f"Cached {total} permissions in Redis across {len(tree)} modules")


async def get_modules_from_redis() -> list:
    """Get distinct permission module prefixes from Redis."""
    from core.db.redis import get_client
    import json

    redis_client = get_client()
    if not redis_client:
        return []
    data = await redis_client.get(PERMISSION_CACHE_KEY)
    if not data:
        return []
    tree = json.loads(data)
    return sorted(tree.keys())


async def get_permissions_by_module_from_redis(module: str) -> list:
    """Get all permissions under a specific module from Redis."""
    from core.db.redis import get_client
    import json

    redis_client = get_client()
    if not redis_client:
        return []
    data = await redis_client.get(PERMISSION_CACHE_KEY)
    if not data:
        return []
    tree = json.loads(data)
    module_perms = tree.get(module, {})
    return list(module_perms.values())


async def run_permission_scan(app):
    """Scan decorators, store grouped permissions in Redis."""
    permissions = collect_permissions_from_routes(app)
    if permissions:
        await sync_to_redis(permissions)
    return permissions
