""" Author: Charlie

定期清理本地存储孤立对象（有对象无 DB 行）。
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from snailjob import ExecuteResult, ExecutorManager, JobArgs, SnailLog, job
from sqlalchemy import select

from app.core.config.enums import StorageProvider
from app.core.db.session import get_session_factory
from app.core.storage.local import LocalStorage
from app.core.storage.manager import get_storage
from app.core.tasks.async_runner import worker_async_runner
from app.modules.sys.file.model import SysFile

logger = logging.getLogger(__name__)


@job("sysFileCleanupLocalOrphans")
def cleanup_local_orphans(_args: JobArgs) -> ExecuteResult:
    """删除早于 min_age 且无对应 sys_file 行的本地文件。"""
    try:
        result = worker_async_runner.run(_cleanup(min_age_seconds=3600, limit=200))
        SnailLog.REMOTE.info(
            f"sysFileCleanupLocalOrphans scanned={result['scanned']} "
            f"deleted={result['deleted']} skipped={result['skipped']}"
        )
        return ExecuteResult.success(result)
    except Exception as exc:
        logger.exception("Local orphan cleanup failed")
        SnailLog.REMOTE.error(str(exc))
        return ExecuteResult.failure(str(exc))


async def _cleanup(*, min_age_seconds: int, limit: int) -> dict[str, int]:
    """扫描本地存储中无对应元数据行的过期文件并删除。"""
    storage = get_storage(provider=StorageProvider.LOCAL, allow_settings_fallback=True)
    if not isinstance(storage, LocalStorage):
        return {"scanned": 0, "deleted": 0, "skipped": 0}

    root: Path = storage.root
    if not root.exists():
        return {"scanned": 0, "deleted": 0, "skipped": 0}

    cutoff = time.time() - max(300, min_age_seconds)
    candidates: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            if path.stat().st_mtime > cutoff:
                continue
            rel = path.relative_to(root).as_posix()
            candidates.append(rel)
        except OSError:
            continue
        if len(candidates) >= limit * 5:
            break

    if not candidates:
        return {"scanned": 0, "deleted": 0, "skipped": 0}

    deleted = 0
    skipped = 0
    factory = get_session_factory()
    async with factory() as session:
        for chunk_start in range(0, len(candidates), limit):
            chunk = candidates[chunk_start : chunk_start + limit]
            existing = set(
                (
                    await session.execute(
                        select(SysFile.object_name).where(SysFile.object_name.in_(chunk))
                    )
                )
                .scalars()
                .all()
            )
            for object_name in chunk:
                if object_name in existing:
                    skipped += 1
                    continue
                try:
                    await asyncio.to_thread(storage.delete_object, object_name)
                    deleted += 1
                except Exception:
                    logger.debug("orphan delete failed: %s", object_name, exc_info=True)

    logger.info(
        "Local orphan cleanup scanned=%s deleted=%s skipped=%s", len(candidates), deleted, skipped
    )
    return {"scanned": len(candidates), "deleted": deleted, "skipped": skipped}


ExecutorManager.register(cleanup_local_orphans)
