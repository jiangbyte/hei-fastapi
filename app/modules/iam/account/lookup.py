""" Author: Charlie

实现 AccountLookupProtocol — 包装 AccountRepository。
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.account.repository import AccountRepository


class AccountLookup:
    async def get_active_account_by_id(self, db: AsyncSession, account_id: str) -> object | None:
        return await AccountRepository(db).get_account_by_id(account_id)


account_lookup = AccountLookup()
