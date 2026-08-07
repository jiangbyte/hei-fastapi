""" Author: Charlie """

import pytest
from sqlalchemy import select

from app.core.config.enums import AccountStatusEnum, AccountType, DataScope, StatusEnum
from app.core.exceptions.business import ConflictError
from app.core.schema.base import IdsRequest
from app.modules.iam.account.model import SysAccount
from app.modules.iam.dept.model import SysDept
from app.modules.iam.dept.schema import DeptUpdateRequest
from app.modules.iam.dept.service import DeptService
from app.modules.iam.enums import GrantSubjectType, ResourceType, RoleScopeType
from app.modules.iam.group.model import SysGroup
from app.modules.iam.group.service import GroupService
from app.modules.iam.position.model import SysPosition
from app.modules.iam.position.service import PositionService
from app.modules.iam.resource.model import SysResource
from app.modules.iam.resource.schema import ResourceUpdateRequest
from app.modules.iam.resource.service import ResourceService
from app.modules.iam.role.model import SysRole
from app.modules.iam.role.service import RoleService
from tests.iam_relation_helpers import (
    account_dept,
    account_group,
    account_role,
    group_role,
    resource_permission,
    subject_permission_grant,
    subject_resource_grant,
)


async def _account(db_session) -> SysAccount:
    account = SysAccount(
        password_hash="hashed",
        account_type=AccountType.ADMIN.value,
        account_status=AccountStatusEnum.ENABLED.value,
    )
    db_session.add(account)
    await db_session.flush()
    return account


async def _role(db_session, code: str = "guard_role") -> SysRole:
    role = SysRole(
        code=code,
        name=code,
        category="SYS",
        scope_type=RoleScopeType.PLATFORM.value,
    )
    db_session.add(role)
    await db_session.flush()
    return role


async def _group(db_session, name: str = "Guard Group") -> SysGroup:
    group = SysGroup(name=name, status=StatusEnum.ENABLED.value)
    db_session.add(group)
    await db_session.flush()
    return group


async def _dept(db_session, code: str, parent_id: str | None = None) -> SysDept:
    dept = SysDept(
        name=code,
        category="SYS",
        parent_id=parent_id,
        status=StatusEnum.ENABLED.value,
    )
    db_session.add(dept)
    await db_session.flush()
    return dept


async def _resource(
    db_session,
    code: str,
    parent_id: str | None = None,
    resource_type: str = ResourceType.MENU.value,
) -> SysResource:
    resource = SysResource(
        code=code,
        name=code,
        resource_type=resource_type,
        parent_id=parent_id,
        status=StatusEnum.ENABLED.value,
    )
    db_session.add(resource)
    await db_session.flush()
    return resource


async def _assert_conflict_message(coro, *parts: str) -> None:
    with pytest.raises(ConflictError) as exc_info:
        await coro
    message = exc_info.value.message
    for part in parts:
        assert part in message


async def test_delete_role_rejects_account_and_group_relations(db_session):
    role = await _role(db_session)
    account = await _account(db_session)
    group = await _group(db_session)
    db_session.add_all(
        [
            account_role(account.id, role.id),
            group_role(group.id, role.id),
        ]
    )
    await db_session.commit()

    await _assert_conflict_message(
        RoleService(db_session).delete(IdsRequest(ids=[role.id])),
        "account_roles=1",
        "group_roles=1",
    )


async def test_delete_role_rejects_grants(db_session):
    role = await _role(db_session, "guard_role_grants")
    resource = await _resource(db_session, "guard_resource_grants")
    db_session.add_all(
        [
            subject_resource_grant(GrantSubjectType.ROLE, role.id, resource.id),
            subject_permission_grant(
                GrantSubjectType.ROLE,
                role.id,
                "iam:guard:delete",
                data_scope=DataScope.SELF.value,
            ),
        ]
    )
    await db_session.commit()

    await _assert_conflict_message(
        RoleService(db_session).delete(IdsRequest(ids=[role.id])),
        "resource_grants=1",
        "permission_grants=1",
    )


async def test_delete_group_rejects_account_role_and_grant_relations(db_session):
    group = await _group(db_session)
    account = await _account(db_session)
    role = await _role(db_session)
    resource = await _resource(db_session, "guard_group_resource")
    db_session.add_all(
        [
            account_group(account.id, group.id),
            group_role(group.id, role.id),
            subject_resource_grant(GrantSubjectType.GROUP, group.id, resource.id),
            subject_permission_grant(
                GrantSubjectType.GROUP,
                group.id,
                "iam:group:guard",
                data_scope=DataScope.SELF.value,
            ),
        ]
    )
    await db_session.commit()

    await _assert_conflict_message(
        GroupService(db_session).delete(IdsRequest(ids=[group.id])),
        "account_groups=1",
        "group_roles=1",
        "resource_grants=1",
        "permission_grants=1",
    )


async def test_delete_dept_rejects_child_account_owner_and_custom_scope_refs(db_session):
    dept = await _dept(db_session, "guard_dept")
    account = await _account(db_session)
    role = await _role(db_session, "guard_dept_role")
    role.owner_dept_id = dept.id
    child = await _dept(db_session, "guard_child_dept", parent_id=dept.id)
    child_parent_id = child.parent_id
    dept_id = dept.id
    db_session.add_all(
        [
            account_dept(account.id, dept.id),
            resource_permission(
                (await _resource(db_session, "guard_dept_resource")).id,
                "iam:dept:resource-scope",
                data_scope=DataScope.CUSTOM.value,
                custom_scope_dept_ids=[dept.id],
            ),
            subject_permission_grant(
                GrantSubjectType.ACCOUNT,
                account.id,
                "iam:dept:custom-scope",
                data_scope=DataScope.CUSTOM.value,
                custom_scope_dept_ids=[dept.id],
            ),
        ]
    )
    await db_session.commit()

    await _assert_conflict_message(
        DeptService(db_session).delete(IdsRequest(ids=[dept_id])),
        "child_depts=1",
        "account_depts=1",
        "owner_roles=1",
        "permission_grant_scopes=1",
        "resource_permission_scopes=1",
    )
    assert child_parent_id == dept_id


async def test_delete_resource_rejects_child_permission_and_grant_refs(db_session):
    resource = await _resource(db_session, "guard_resource")
    child = await _resource(db_session, "guard_child_resource", parent_id=resource.id)
    child_parent_id = child.parent_id
    resource_id = resource.id
    account = await _account(db_session)
    db_session.add_all(
        [
            resource_permission(
                resource_id,
                "iam:resource:guard",
                data_scope=DataScope.SELF.value,
            ),
            subject_resource_grant(GrantSubjectType.ACCOUNT, account.id, resource_id),
        ]
    )
    await db_session.commit()

    await _assert_conflict_message(
        ResourceService(db_session).delete(IdsRequest(ids=[resource_id])),
        "child_resources=1",
        "resource_permissions=1",
        "resource_grants=1",
    )
    assert child_parent_id == resource_id


async def test_dept_update_rejects_self_and_descendant_parent(db_session):
    root = await _dept(db_session, "guard_root_dept")
    child = await _dept(db_session, "guard_leaf_dept", parent_id=root.id)
    self_payload = DeptUpdateRequest(
        id=root.id,
        name=root.name,
        category=root.category,
        parent_id=root.id,
    )
    descendant_payload = DeptUpdateRequest(
        id=root.id,
        name=root.name,
        category=root.category,
        parent_id=child.id,
    )
    await db_session.commit()

    await _assert_conflict_message(
        DeptService(db_session).update(self_payload),
        "cannot move under itself",
    )
    await _assert_conflict_message(
        DeptService(db_session).update(descendant_payload),
        "cannot move under its descendant",
    )


async def test_resource_update_rejects_self_and_descendant_parent(db_session):
    root = await _resource(db_session, "guard_root_resource")
    child = await _resource(db_session, "guard_leaf_resource", parent_id=root.id)
    self_payload = ResourceUpdateRequest(
        id=root.id,
        code=root.code,
        name=root.name,
        resource_type=ResourceType(root.resource_type),
        parent_id=root.id,
    )
    descendant_payload = ResourceUpdateRequest(
        id=root.id,
        code=root.code,
        name=root.name,
        resource_type=ResourceType(root.resource_type),
        parent_id=child.id,
    )
    await db_session.commit()

    await _assert_conflict_message(
        ResourceService(db_session).update(self_payload),
        "cannot move under itself",
    )
    await _assert_conflict_message(
        ResourceService(db_session).update(descendant_payload),
        "cannot move under its descendant",
    )


async def test_unreferenced_iam_entities_can_be_deleted(db_session):
    role = await _role(db_session, "guard_delete_role")
    group = await _group(db_session, "Guard Delete Group")
    dept = await _dept(db_session, "guard_delete_dept")
    resource = await _resource(db_session, "guard_delete_resource")
    position = SysPosition(
        name="Guard Position",
        category="SYS",
        status=StatusEnum.ENABLED.value,
    )
    db_session.add(position)
    await db_session.commit()

    await RoleService(db_session).delete(IdsRequest(ids=[role.id]))
    await GroupService(db_session).delete(IdsRequest(ids=[group.id]))
    await DeptService(db_session).delete(IdsRequest(ids=[dept.id]))
    await ResourceService(db_session).delete(IdsRequest(ids=[resource.id]))
    await PositionService(db_session).delete(IdsRequest(ids=[position.id]))
    await db_session.commit()

    assert (
        await db_session.execute(select(SysRole).where(SysRole.id == role.id))
    ).scalar_one_or_none() is None
    assert (
        await db_session.execute(select(SysGroup).where(SysGroup.id == group.id))
    ).scalar_one_or_none() is None
    assert (
        await db_session.execute(select(SysDept).where(SysDept.id == dept.id))
    ).scalar_one_or_none() is None
    assert (
        await db_session.execute(select(SysResource).where(SysResource.id == resource.id))
    ).scalar_one_or_none() is None
    assert (
        await db_session.execute(select(SysPosition).where(SysPosition.id == position.id))
    ).scalar_one_or_none() is None
