""" Author: Charlie

数据范围解析接口：展开部门及其全部子部门 ID 的抽象协议。
"""

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession


@runtime_checkable
class DataScopeResolverProtocol(Protocol):
    """数据范围解析协议，由部门相关模块提供实现。"""

    async def list_dept_and_child_ids(
        self, db: AsyncSession, dept_ids: Iterable[str]
    ) -> list[str]: ...
