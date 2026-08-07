""" Author: Charlie """

import pytest

from app.core.config.enums import (
    AccountStatusEnum,
    AccountType,
    DataScope,
)
from app.core.exceptions.business import AuthenticationError
from app.core.security.password import hash_password
from app.modules.auth.schema import LoginPayload
from app.modules.auth.service import AuthService
from app.modules.iam.account.model import SysAccount, SysAccountIdentity
from app.modules.iam.enums import (
    AccountIdentityType,
    GrantSubjectType,
    ResourceType,
    RoleScopeType,
)
from app.modules.iam.group.model import SysGroup
from app.modules.iam.relation.repository import IamRelationRepository
from app.modules.iam.resource.model import SysResource
from app.modules.iam.role.constants import SUPER_ADMIN_ROLE_CODE
from app.modules.iam.role.model import SysRole
from tests.iam_relation_helpers import (
    account_group,
    account_role,
    group_role,
    resource_permission,
    subject_permission_grant,
    subject_resource_grant,
)


async def _seed_account(
    db_session,
    *,
    identifier: str,
    password: str,
    account_type: AccountType,
) -> SysAccount:
    account = SysAccount(
        password_hash=hash_password(password),
        account_type=account_type.value,
        account_status=AccountStatusEnum.ENABLED.value,
    )
    db_session.add(account)
    await db_session.flush()
    db_session.add(
        SysAccountIdentity(
            account_id=account.id,
            identity_type=AccountIdentityType.ACCOUNT.value,
            identifier=identifier,
            verified=True,
            is_primary=True,
        )
    )
    return account


async def test_admin_login_success(db_session):
    account = await _seed_account(
        db_session,
        identifier="admin",
        password="Admin@123456",
        account_type=AccountType.ADMIN,
    )

    role = SysRole(
        code=SUPER_ADMIN_ROLE_CODE,
        name="Super Admin",
        category="SYSTEM",
        scope_type=RoleScopeType.PLATFORM.value,
    )
    resource = SysResource(
        code="iam:user:list",
        name="Account List Resource",
        resource_type=ResourceType.BUTTON.value,
    )
    db_session.add_all([role, resource])
    await db_session.flush()
    db_session.add(resource_permission(resource.id, "iam:account:list"))
    db_session.add(subject_resource_grant(GrantSubjectType.ROLE, role.id, resource.id))
    db_session.add(account_role(account.id, role.id))
    await db_session.commit()

    outcome = await AuthService(db_session).login(
        LoginPayload(account="admin", password="Admin@123456", account_type=AccountType.ADMIN)
    )
    assert outcome.session is not None
    payload = outcome.session
    assert payload.account_id == account.id
    assert payload.account_type == AccountType.ADMIN.value
    assert "iam:account:list" in payload.permission_keys
    assert "*:*:*" in payload.permission_keys


async def test_portal_account_cannot_login_admin_account_type(db_session):
    await _seed_account(
        db_session,
        identifier="portal_account",
        password="Portal@123456",
        account_type=AccountType.PORTAL,
    )
    await db_session.commit()

    with pytest.raises(AuthenticationError):
        await AuthService(db_session).login(
            LoginPayload(
                account="portal_account",
                password="Portal@123456",
                account_type=AccountType.ADMIN,
            )
        )


async def test_legacy_subject_permission_grants_are_ignored(db_session):
    account = SysAccount(
        password_hash=hash_password("Admin@123456"),
        account_type=AccountType.ADMIN.value,
        account_status=AccountStatusEnum.ENABLED.value,
    )
    role = SysRole(
        code="priority_role",
        name="Priority Role",
        category="SYSTEM",
        scope_type=RoleScopeType.PLATFORM.value,
    )
    group = SysGroup(name="Priority Group")
    db_session.add_all([account, role, group])
    await db_session.flush()
    db_session.add_all(
        [
            account_role(account.id, role.id),
            account_group(account.id, group.id),
            group_role(group.id, role.id),
            subject_permission_grant(
                GrantSubjectType.ROLE,
                role.id,
                "sys:file:page",
                data_scope=DataScope.DEPT.value,
                custom_scope_dept_ids=[],
            ),
            subject_permission_grant(
                GrantSubjectType.GROUP,
                group.id,
                "sys:file:page",
                data_scope=DataScope.CUSTOM.value,
                custom_scope_dept_ids=["dept_2"],
            ),
            subject_permission_grant(
                GrantSubjectType.ACCOUNT,
                account.id,
                "sys:file:page",
                data_scope=DataScope.ALL.value,
                custom_scope_dept_ids=[],
            ),
        ]
    )
    await db_session.commit()

    authorization = await IamRelationRepository(db_session).get_account_authorization(account.id)
    assert authorization["permission_grants"] == []
    assert authorization["permission_keys"] == []
