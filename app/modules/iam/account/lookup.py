""" Author: Charlie

实现 AccountLookupProtocol — 包装 AccountRepository。
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.account.repository import AccountRepository


class AccountLookup:
    """账户查找服务，实现 AccountLookupProtocol 并包装 AccountRepository。"""

    async def get_active_account_by_id(self, db: AsyncSession, account_id: str) -> object | None:
        """按 ID 查询账户实体，供认证等核心流程复用。"""
        return await AccountRepository(db).get_account_by_id(account_id)


account_lookup = AccountLookup()
