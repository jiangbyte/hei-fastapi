""" Author: Charlie """

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import ConflictError
from app.modules.iam.dept.model import SysDept
from app.modules.iam.enums import (
    GrantSubjectType,
    IamRelationSubjectType,
    IamRelationTargetType,
    IamRelationType,
)
from app.modules.iam.relation.model import SysIamRelation
from app.modules.iam.resource.model import SysResource
from app.modules.iam.role.model import SysRole


def unique_ids(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def raise_if_referenced(entity_name: str, counts: dict[str, int]) -> None:
    references = {key: value for key, value in counts.items() if value > 0}
    if not references:
        return
    details = ", ".join(f"{key}={value}" for key, value in sorted(references.items()))
    raise ConflictError(f"{entity_name} is referenced: {details}")


async def count_role_references(db: AsyncSession, role_ids: list[str]) -> dict[str, int]:
    ids = unique_ids(role_ids)
    if not ids:
        return {}
    return {
        "account_roles": await _count_relation_targets(
            db, IamRelationType.ACCOUNT_ROLE, IamRelationTargetType.ROLE.value, ids
        ),
        "group_roles": await _count_relation_targets(
            db, IamRelationType.GROUP_ROLE, IamRelationTargetType.ROLE.value, ids
        ),
        "resource_grants": await _count(
            db,
            select(func.count())
            .select_from(SysIamRelation)
            .where(
                SysIamRelation.subject_type == GrantSubjectType.ROLE.value,
                SysIamRelation.subject_id.in_(ids),
                SysIamRelation.relation_type == IamRelationType.SUBJECT_RESOURCE_GRANT.value,
            ),
        ),
        "permission_grants": await _count(
            db,
            select(func.count())
            .select_from(SysIamRelation)
            .where(
                SysIamRelation.subject_type == GrantSubjectType.ROLE.value,
                SysIamRelation.subject_id.in_(ids),
                SysIamRelation.relation_type == IamRelationType.SUBJECT_PERMISSION_GRANT.value,
            ),
        ),
    }


async def count_group_references(db: AsyncSession, group_ids: list[str]) -> dict[str, int]:
    ids = unique_ids(group_ids)
    if not ids:
        return {}
    return {
        "account_groups": await _count_relation_targets(
            db, IamRelationType.ACCOUNT_GROUP, IamRelationTargetType.GROUP.value, ids
        ),
        "group_roles": await _count(
            db,
            select(func.count())
            .select_from(SysIamRelation)
            .where(
                SysIamRelation.subject_type == IamRelationSubjectType.GROUP.value,
                SysIamRelation.subject_id.in_(ids),
                SysIamRelation.relation_type == IamRelationType.GROUP_ROLE.value,
            ),
        ),
        "resource_grants": await _count(
            db,
            select(func.count())
            .select_from(SysIamRelation)
            .where(
                SysIamRelation.subject_type == GrantSubjectType.GROUP.value,
                SysIamRelation.subject_id.in_(ids),
                SysIamRelation.relation_type == IamRelationType.SUBJECT_RESOURCE_GRANT.value,
            ),
        ),
        "permission_grants": await _count(
            db,
            select(func.count())
            .select_from(SysIamRelation)
            .where(
                SysIamRelation.subject_type == GrantSubjectType.GROUP.value,
                SysIamRelation.subject_id.in_(ids),
                SysIamRelation.relation_type == IamRelationType.SUBJECT_PERMISSION_GRANT.value,
            ),
        ),
    }


async def count_dept_references(db: AsyncSession, dept_ids: list[str]) -> dict[str, int]:
    ids = unique_ids(dept_ids)
    if not ids:
        return {}
    return {
        "child_depts": await _count(
            db, select(func.count()).select_from(SysDept).where(SysDept.parent_id.in_(ids))
        ),
        "account_depts": await _count_relation_targets(
            db, IamRelationType.ACCOUNT_DEPT, IamRelationTargetType.DEPT.value, ids
        ),
        "owner_roles": await _count(
            db, select(func.count()).select_from(SysRole).where(SysRole.owner_dept_id.in_(ids))
        ),
        "resource_permission_scopes": await _count_resource_permission_scope_refs(db, ids),
        "permission_grant_scopes": await _count_permission_grant_scope_refs(db, ids),
    }


async def count_resource_references(db: AsyncSession, resource_ids: list[str]) -> dict[str, int]:
    ids = unique_ids(resource_ids)
    if not ids:
        return {}
    return {
        "child_resources": await _count(
            db, select(func.count()).select_from(SysResource).where(SysResource.parent_id.in_(ids))
        ),
        "resource_permissions": await _count(
            db,
            select(func.count())
            .select_from(SysIamRelation)
            .where(
                SysIamRelation.subject_type == IamRelationSubjectType.RESOURCE.value,
                SysIamRelation.subject_id.in_(ids),
                SysIamRelation.relation_type == IamRelationType.RESOURCE_PERMISSION.value,
            ),
        ),
        "resource_grants": await _count_relation_targets(
            db, IamRelationType.SUBJECT_RESOURCE_GRANT, IamRelationTargetType.RESOURCE.value, ids
        ),
    }


async def ensure_parent_exists(
    db: AsyncSession, model, parent_id: str | None, entity_name: str
) -> None:
    if not parent_id:
        return
    if not await db.get(model, parent_id):
        raise ConflictError(f"{entity_name} parent does not exist")


async def ensure_not_self_or_descendant(
    db: AsyncSession,
    model,
    entity_id: str,
    parent_id: str | None,
    entity_name: str,
) -> None:
    if not parent_id:
        return
    if parent_id == entity_id:
        raise ConflictError(f"{entity_name} cannot move under itself")
    descendants = await list_descendant_ids(db, model, entity_id)
    if parent_id in descendants:
        raise ConflictError(f"{entity_name} cannot move under its descendant")


async def list_descendant_ids(db: AsyncSession, model, entity_id: str) -> set[str]:
    rows = (await db.execute(select(model.id, model.parent_id))).all()
    children_by_parent: dict[str, list[str]] = {}
    for current_id, parent_id in rows:
        if parent_id:
            children_by_parent.setdefault(str(parent_id), []).append(str(current_id))

    result: set[str] = set()
    stack = list(children_by_parent.get(entity_id, []))
    while stack:
        current_id = stack.pop()
        if current_id in result:
            continue
        result.add(current_id)
        stack.extend(children_by_parent.get(current_id, []))
    return result


async def _count(db: AsyncSession, stmt) -> int:
    return int((await db.execute(stmt)).scalar_one())


async def _count_relation_targets(
    db: AsyncSession,
    relation_type: IamRelationType,
    target_type: str,
    target_ids: list[str],
) -> int:
    return await _count(
        db,
        select(func.count())
        .select_from(SysIamRelation)
        .where(
            SysIamRelation.relation_type == relation_type.value,
            SysIamRelation.target_type == target_type,
            SysIamRelation.target_id.in_(target_ids),
        ),
    )


async def _count_resource_permission_scope_refs(db: AsyncSession, dept_ids: list[str]) -> int:
    rows = (
        (
            await db.execute(
                select(SysIamRelation.custom_scope_dept_ids).where(
                    SysIamRelation.relation_type == IamRelationType.RESOURCE_PERMISSION.value,
                    SysIamRelation.custom_scope_dept_ids.is_not(None),
                )
            )
        )
        .scalars()
        .all()
    )
    return _count_scope_refs(rows, dept_ids)


async def _count_permission_grant_scope_refs(db: AsyncSession, dept_ids: list[str]) -> int:
    rows = (
        (
            await db.execute(
                select(SysIamRelation.custom_scope_dept_ids).where(
                    SysIamRelation.relation_type == IamRelationType.SUBJECT_PERMISSION_GRANT.value,
                    SysIamRelation.custom_scope_dept_ids.is_not(None),
                )
            )
        )
        .scalars()
        .all()
    )
    return _count_scope_refs(rows, dept_ids)


def _count_scope_refs(rows, dept_ids: list[str]) -> int:
    target_ids = set(dept_ids)
    count = 0
    for row in rows:
        values = row or []
        if target_ids.intersection(str(value) for value in values):
            count += 1
    return count
