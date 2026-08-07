""" Author: Charlie

将 codegen plan 的预览文件应用到工作区（低侵入）。

用法：
  python scripts/codegen/apply_plan.py --plan-id <id>
  python scripts/codegen/apply_plan.py --plan-id <id> --skip-menu-sql
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path


def bootstrap_project() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    return project_root


bootstrap_project()

from app.core.schema.base import IdQuery  # noqa: E402
from app.modules.sys.codegen.apply import apply_preview_files  # noqa: E402
from app.modules.sys.codegen.service import CodegenService  # noqa: E402
from app.platform.db.session import close_engine, get_session_factory  # noqa: E402


async def _run(plan_id: str, *, skip_menu_sql: bool, root: Path) -> None:
    try:
        factory = get_session_factory()
        async with factory() as session:
            preview = await CodegenService(session).preview(IdQuery(id=plan_id))
        result = apply_preview_files(preview.files, root, skip_menu_sql=skip_menu_sql)
        print(f"wrote {len(result.written)} files")
        for path in result.written:
            print(f"  W {path}")
        print(f"merged {len(result.merged)} files")
        for path in result.merged:
            print(f"  M {path}")
        print(f"skipped {len(result.skipped)} files")
        for path in result.skipped:
            print(f"  S {path}")
    finally:
        await close_engine()


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply codegen preview into the repo")
    parser.add_argument("--plan-id", required=True, help="sys_codegen_plan.id")
    parser.add_argument(
        "--skip-menu-sql",
        action="store_true",
        help="Do not write *_menu_permission.sql",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workspace root (default: repository root)",
    )
    args = parser.parse_args()
    root = (args.root or Path.cwd()).resolve()
    asyncio.run(_run(args.plan_id, skip_menu_sql=args.skip_menu_sql, root=root))


if __name__ == "__main__":
    main()
