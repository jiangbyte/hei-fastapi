""" Author: Charlie """

from sqlalchemy import select

from app.core.config.enums import AccountType, DataScope
from app.core.security.data_scope import build_data_scope_filter, list_dept_and_child_ids
from app.core.security.session import SessionPayload
from app.modules.iam.dept.model import SysDept
from app.modules.iam.enums import IamRelationType
from app.modules.iam.relation.model import SysIamRelation
from tests.iam_relation_helpers import account_dept


async def test_data_scope_defaults_to_self(db_session):
    db_session.add_all(
        [
            account_dept("account_1", "dept_1"),
            account_dept("account_2", "dept_1"),
        ]
    )
    await db_session.commit()

    session = SessionPayload(
        token="token",
        account_id="account_1",
        account_type=AccountType.ADMIN.value,
        permission_keys=["sys:file:page"],
        permission_grants=[],
    )
    condition = await build_data_scope_filter(
        db_session,
        session,
        "sys:file:page",
        owner_column=SysIamRelation.subject_id,
        dept_column=SysIamRelation.target_id,
    )
    rows = (
        (
            await db_session.execute(
                select(SysIamRelation.subject_id).where(
                    SysIamRelation.relation_type == IamRelationType.ACCOUNT_DEPT.value,
                    condition,
                )
            )
        )
        .scalars()
        .all()
    )

    assert rows == ["account_1"]


async def test_data_scope_all_returns_all_rows(db_session):
    db_session.add_all(
        [
            account_dept("account_1", "dept_1"),
            account_dept("account_2", "dept_2"),
        ]
    )
    await db_session.commit()

    session = SessionPayload(
        token="token",
        account_id="account_1",
        account_type=AccountType.ADMIN.value,
        permission_keys=["sys:file:page"],
        permission_grants=[
            {
                "permission_key": "sys:file:page",
                "data_scope": DataScope.ALL.value,
                "custom_scope_dept_ids": [],
                "source_type": "ROLE",
                "source_id": "role_1",
            }
        ],
    )
    condition = await build_data_scope_filter(
        db_session,
        session,
        "sys:file:page",
        owner_column=SysIamRelation.subject_id,
        dept_column=SysIamRelation.target_id,
    )
    rows = (
        (
            await db_session.execute(
                select(SysIamRelation.subject_id).where(
                    SysIamRelation.relation_type == IamRelationType.ACCOUNT_DEPT.value,
                    condition,
                )
            )
        )
        .scalars()
        .all()
    )

    assert rows == ["account_1", "account_2"]


async def test_data_scope_custom_uses_custom_dept_ids(db_session):
    db_session.add_all(
        [
            account_dept("account_1", "dept_1"),
            account_dept("account_2", "dept_2"),
        ]
    )
    await db_session.commit()

    session = SessionPayload(
        token="token",
        account_id="account_1",
        account_type=AccountType.ADMIN.value,
        permission_keys=["sys:file:page"],
        permission_grants=[
            {
                "permission_key": "sys:file:page",
                "data_scope": DataScope.CUSTOM.value,
                "custom_scope_dept_ids": ["dept_2"],
                "source_type": "ACCOUNT",
                "source_id": "account_1",
            }
        ],
    )
    condition = await build_data_scope_filter(
        db_session,
        session,
        "sys:file:page",
        owner_column=SysIamRelation.subject_id,
        dept_column=SysIamRelation.target_id,
    )
    rows = (
        (
            await db_session.execute(
                select(SysIamRelation.subject_id).where(
                    SysIamRelation.relation_type == IamRelationType.ACCOUNT_DEPT.value,
                    condition,
                )
            )
        )
        .scalars()
        .all()
    )

    assert rows == ["account_2"]


async def test_data_scope_dept_and_child_loads_depts_in_batch(db_session):
    db_session.add_all(
        [
            SysDept(id="dept_1", name="Dept 1", category="SYS"),
            SysDept(id="dept_2", parent_id="dept_1", name="Dept 2", category="SYS"),
            SysDept(id="dept_3", parent_id="dept_2", name="Dept 3", category="SYS"),
            SysDept(id="dept_4", name="Dept 4", category="SYS"),
            account_dept("account_1", "dept_1"),
            account_dept("account_2", "dept_2"),
            account_dept("account_3", "dept_3"),
            account_dept("account_4", "dept_4"),
        ]
    )
    await db_session.commit()

    assert await list_dept_and_child_ids(db_session, ["dept_1"]) == ["dept_1", "dept_2", "dept_3"]

    session = SessionPayload(
        token="token",
        account_id="account_1",
        account_type=AccountType.ADMIN.value,
        dept_ids=["dept_1"],
        permission_keys=["sys:file:page"],
        permission_grants=[
            {
                "permission_key": "sys:file:page",
                "data_scope": DataScope.DEPT_AND_CHILD.value,
                "custom_scope_dept_ids": [],
                "source_type": "GROUP",
                "source_id": "group_1",
            }
        ],
    )
    condition = await build_data_scope_filter(
        db_session,
        session,
        "sys:file:page",
        owner_column=SysIamRelation.subject_id,
        dept_column=SysIamRelation.target_id,
    )
    rows = (
        (
            await db_session.execute(
                select(SysIamRelation.subject_id).where(
                    SysIamRelation.relation_type == IamRelationType.ACCOUNT_DEPT.value,
                    condition,
                )
            )
        )
        .scalars()
        .all()
    )

    assert rows == ["account_1", "account_2", "account_3"]
