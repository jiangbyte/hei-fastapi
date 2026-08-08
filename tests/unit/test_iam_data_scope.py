""" Author: Charlie """

from datetime import UTC, datetime

import pytest

from app.core.config.enums import AccountStatusEnum, AccountType, DataScope
from app.core.exceptions.business import AuthorizationError
from app.core.schema.base import IdQuery
from app.core.security.session import SessionPayload
from app.modules.iam.account.model import SysAccount, SysAccountIdentity
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.account.schema import AccountAdminPageQuery
from app.modules.iam.account.service import AccountService
from app.modules.iam.enums import AccountIdentityBindStatus, AccountIdentityType
from app.modules.user.admin.model import AdminUserProfile
from tests.iam_relation_helpers import account_dept


async def _admin_account(
    db_session, account_id: str, account_name: str, dept_id: str
) -> SysAccount:
    now = datetime.now(UTC)
    account = SysAccount(
        id=account_id,
        password_hash="hashed",
        account_type=AccountType.ADMIN.value,
        account_status=AccountStatusEnum.ENABLED.value,
        created_at=now,
        updated_at=now,
    )
    db_session.add(account)
    db_session.add(
        SysAccountIdentity(
            account_id=account_id,
            identity_type=AccountIdentityType.ACCOUNT.value,
            identifier=account_name,
            verified=True,
            is_primary=True,
            bind_status=AccountIdentityBindStatus.BOUND.value,
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        AdminUserProfile(account_id=account_id, name=account_name, created_at=now, updated_at=now)
    )
    db_session.add(account_dept(account_id, dept_id, created_at=now, updated_at=now))
    await db_session.flush()
    return account


def _session(
    data_scope: DataScope, custom_scope_dept_ids: list[str] | None = None
) -> SessionPayload:
    return SessionPayload(
        token="token",
        account_id="admin_a",
        account_type=AccountType.ADMIN.value,
        dept_ids=["dept_a", "dept_b"],
        permission_keys=["iam:account:page", "iam:account:detail"],
        permission_grants=[
            {
                "permission_key": "iam:account:page",
                "data_scope": data_scope.value,
                "custom_scope_dept_ids": custom_scope_dept_ids or [],
                "source_type": "ROLE",
                "source_id": "role_a",
            },
            {
                "permission_key": "iam:account:detail",
                "data_scope": data_scope.value,
                "custom_scope_dept_ids": custom_scope_dept_ids or [],
                "source_type": "ROLE",
                "source_id": "role_a",
            },
        ],
    )


async def test_account_page_respects_custom_dept_scope(db_session):
    await _admin_account(db_session, "admin_a", "admin_a", "dept_a")
    await _admin_account(db_session, "admin_b", "admin_b", "dept_b")
    await _admin_account(db_session, "admin_c", "admin_c", "dept_c")
    await db_session.commit()

    service = AccountService(db_session)
    data_scope_filter = await service._account_scope_filter(
        _session(DataScope.CUSTOM, ["dept_b"]),
        "iam:account:page",
    )
    accounts, total = await AccountRepository(db_session).page_admin(
        AccountAdminPageQuery(current=1, size=20),
        data_scope_filter,
    )

    assert total == 1
    assert [item.id for item in accounts] == ["admin_b"]


async def test_account_detail_rejects_out_of_scope_id(db_session):
    await _admin_account(db_session, "admin_a", "admin_a", "dept_a")
    await _admin_account(db_session, "admin_c", "admin_c", "dept_c")
    await db_session.commit()

    with pytest.raises(AuthorizationError):
        await AccountService(db_session).detail(
            IdQuery(id="admin_c"),
            _session(DataScope.CUSTOM, ["dept_b"]),
        )
