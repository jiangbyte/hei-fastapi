""" Author: Charlie """

from app.core.config.enums import AccountType
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.account.schema import AccountCreateRequest
from app.modules.iam.account.service import AccountService
from app.modules.user.admin.service import ProfileUserAdminService


async def test_create_admin_account_creates_profile(db_session):
    await AccountService(db_session).create(
        AccountCreateRequest(
            account="admin2",
            password="Admin@123456",
            account_type=AccountType.ADMIN,
            name="Admin 2",
            nickname="Admin 2",
            avatar=None,
            signature=None,
            phone=None,
            email=None,
        )
    )
    await db_session.commit()
    account = await AccountRepository(db_session).get_account_by_account("admin2")
    assert account is not None
    assert account.id is not None
    profile = await ProfileUserAdminService(db_session).get_profile(account.id)
    assert profile is not None
