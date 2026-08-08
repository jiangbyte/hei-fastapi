""" Author: Charlie """

import pytest

from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.security.password import hash_password
from app.modules.iam.account.model import SysAccount
from app.modules.iam.enums import RoleScopeType
from app.modules.iam.relation.repository import IamRelationRepository
from app.modules.iam.role.model import SysRole
from tests.iam_relation_helpers import account_role


@pytest.mark.asyncio
async def test_authorization_ignores_mismatched_account_type_roles(db_session):
    account = SysAccount(
        password_hash=hash_password("Admin@123456"),
        account_type=AccountType.ADMIN.value,
        account_status=AccountStatusEnum.ENABLED.value,
    )
    role_admin = SysRole(
        code="role_admin_type",
        name="Admin Typed Role",
        category="SYSTEM",
        scope_type=RoleScopeType.PLATFORM.value,
    )
    role_portal = SysRole(
        code="role_portal_type",
        name="Portal Typed Role",
        category="SYSTEM",
        scope_type=RoleScopeType.PLATFORM.value,
    )
    db_session.add_all([account, role_admin, role_portal])
    await db_session.flush()
    db_session.add_all(
        [
            account_role(account.id, role_admin.id, account_type=AccountType.ADMIN.value),
            account_role(account.id, role_portal.id, account_type=AccountType.PORTAL.value),
        ]
    )
    await db_session.commit()

    auth = await IamRelationRepository(db_session).get_account_authorization(account.id)
    assert role_admin.id in auth["role_ids"]
    assert role_portal.id not in auth["role_ids"]
