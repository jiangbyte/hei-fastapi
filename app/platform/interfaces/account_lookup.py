""" Author: Charlie

账户查询接口：供安全/审计等基础设施按账户 ID 查询活跃账户的抽象协议。
"""

from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession


@runtime_checkable
class AccountLookupProtocol(Protocol):
    """按账户 ID 查询活跃账户的协议，由具体模块提供实现。"""

    async def get_active_account_by_id(
        self, db: AsyncSession, account_id: str
    ) -> object | None: ...
