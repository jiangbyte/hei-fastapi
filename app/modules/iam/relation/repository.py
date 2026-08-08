""" Author: Charlie """

from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Literal, TypedDict

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.config.enums import AccountType, DataScope, StatusEnum
from app.core.exceptions.business import NotFoundError
from app.modules.iam.account.model import SysAccount
from app.modules.iam.enums import (
    GrantEffect,
    GrantMode,
    GrantSubjectType,
    IamRelationSubjectType,
    IamRelationTargetType,
    IamRelationType,
)
from app.modules.iam.group.model import SysGroup
from app.modules.iam.relation.model import SysIamRelation
from app.modules.iam.resource.model import SysResource
from app.modules.iam.role.model import SysRole


class AccountResourceGrantRecord(TypedDict):
    subject_type: GrantSubjectType | str
    subject_id: str
    resource_id: str
    grant_mode: GrantMode | str
    effect: GrantEffect | str


class PermissionGrantRecord(TypedDict):
    permission_key: str
    data_scope: DataScope | str
    custom_scope_dept_ids: list[str]
    effect: GrantEffect | str
    source_type: GrantSubjectType | Literal["RESOURCE"] | str
    source_id: str


class AccountAuthorizationRecord(TypedDict):
    role_ids: list[str]
    role_codes: list[str]
    group_ids: list[str]
    dept_ids: list[str]
    resource_ids: list[str]
    button_codes: list[str]
    permission_keys: list[str]
    permission_grants: list[PermissionGrantRecord]


_PERMISSION_PRIORITY_RESOURCE = 0


def account_dept_condition(relation_model=SysIamRelation, account_id_column=None):
    if account_id_column is None:
        account_id_column = relation_model.subject_id
    return and_(
        relation_model.subject_type == IamRelationSubjectType.ACCOUNT.value,
        relation_model.subject_id == account_id_column,
        relation_model.relation_type == IamRelationType.ACCOUNT_DEPT.value,
        relation_model.target_type == IamRelationTargetType.DEPT.value,
    )


def _as_account_type(value: AccountType | str) -> str:
    return value.value if isinstance(value, AccountType) else str(value)


class IamRelationRepository:
    """通用 IAM 关系仓储，统一承载成员关系、资源权限挂载和授权规则。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def delete_subject_relations(
        self,
        subject_type: str,
        subject_id: str,
        relation_type: IamRelationType,
        account_type: str | None = None,
    ) -> None:
        stmt = delete(SysIamRelation).where(
            SysIamRelation.subject_type == subject_type,
            SysIamRelation.subject_id == subject_id,
            SysIamRelation.relation_type == relation_type.value,
        )
        if account_type is not None:
            stmt = stmt.where(SysIamRelation.account_type == account_type)
        await self.db.execute(stmt)

    async def delete_subject_relations_many(
        self,
        subject_type: str,
        subject_ids: Sequence[str],
        relation_types: Sequence[IamRelationType],
        account_type: str | None = None,
    ) -> None:
        if not subject_ids or not relation_types:
            return
        stmt = delete(SysIamRelation).where(
            SysIamRelation.subject_type == subject_type,
            SysIamRelation.subject_id.in_(list(subject_ids)),
            SysIamRelation.relation_type.in_([item.value for item in relation_types]),
        )
        if account_type is not None:
            stmt = stmt.where(SysIamRelation.account_type == account_type)
        await self.db.execute(stmt)

    async def delete_target_relations(
        self,
        relation_type: IamRelationType,
        target_type: str,
        target_ids: Sequence[str],
    ) -> None:
        if not target_ids:
            return
        await self.db.execute(
            delete(SysIamRelation).where(
                SysIamRelation.relation_type == relation_type.value,
                SysIamRelation.target_type == target_type,
                SysIamRelation.target_id.in_(list(target_ids)),
            )
        )

    def account_role(
        self,
        account_id: str,
        role_id: str,
        account_type: AccountType | str,
    ) -> SysIamRelation:
        return SysIamRelation(
            subject_type=IamRelationSubjectType.ACCOUNT.value,
            subject_id=account_id,
            account_type=_as_account_type(account_type),
            relation_type=IamRelationType.ACCOUNT_ROLE.value,
            target_type=IamRelationTargetType.ROLE.value,
            target_id=role_id,
        )

    def account_group(
        self,
        account_id: str,
        group_id: str,
        account_type: AccountType | str,
    ) -> SysIamRelation:
        return SysIamRelation(
            subject_type=IamRelationSubjectType.ACCOUNT.value,
            subject_id=account_id,
            account_type=_as_account_type(account_type),
            relation_type=IamRelationType.ACCOUNT_GROUP.value,
            target_type=IamRelationTargetType.GROUP.value,
            target_id=group_id,
        )

    def account_dept(
        self,
        account_id: str,
        dept_id: str,
        account_type: AccountType | str,
        is_primary: bool = False,
    ) -> SysIamRelation:
        return SysIamRelation(
            subject_type=IamRelationSubjectType.ACCOUNT.value,
            subject_id=account_id,
            account_type=_as_account_type(account_type),
            relation_type=IamRelationType.ACCOUNT_DEPT.value,
            target_type=IamRelationTargetType.DEPT.value,
            target_id=dept_id,
            is_primary=is_primary,
        )

    def group_role(
        self,
        group_id: str,
        role_id: str,
        account_type: AccountType | str,
    ) -> SysIamRelation:
        return SysIamRelation(
            subject_type=IamRelationSubjectType.GROUP.value,
            subject_id=group_id,
            account_type=_as_account_type(account_type),
            relation_type=IamRelationType.GROUP_ROLE.value,
            target_type=IamRelationTargetType.ROLE.value,
            target_id=role_id,
        )

    def subject_resource_grant(
        self,
        subject_type: GrantSubjectType,
        subject_id: str,
        resource_id: str,
        account_type: AccountType | str,
        grant_mode: GrantMode = GrantMode.CASCADE,
        effect: GrantEffect = GrantEffect.ALLOW,
    ) -> SysIamRelation:
        return SysIamRelation(
            subject_type=subject_type.value,
            subject_id=subject_id,
            account_type=_as_account_type(account_type),
            relation_type=IamRelationType.SUBJECT_RESOURCE_GRANT.value,
            target_type=IamRelationTargetType.RESOURCE.value,
            target_id=resource_id,
            grant_mode=grant_mode.value,
            effect=effect.value,
        )

    def subject_permission_grant(
        self,
        subject_type: GrantSubjectType,
        subject_id: str,
        permission_key: str,
        account_type: AccountType | str,
        data_scope: DataScope | str = DataScope.SELF,
        custom_scope_dept_ids: list[str] | None = None,
        effect: GrantEffect = GrantEffect.ALLOW,
    ) -> SysIamRelation:
        return SysIamRelation(
            subject_type=subject_type.value,
            subject_id=subject_id,
            account_type=_as_account_type(account_type),
            relation_type=IamRelationType.SUBJECT_PERMISSION_GRANT.value,
            target_type=IamRelationTargetType.PERMISSION.value,
            target_key=permission_key,
            data_scope=data_scope.value if isinstance(data_scope, DataScope) else data_scope,
            custom_scope_dept_ids=list(custom_scope_dept_ids or []),
            effect=effect.value,
        )

    def resource_permission(
        self,
        resource_id: str,
        permission_key: str,
        account_type: AccountType | str,
        data_scope: DataScope | str = DataScope.SELF,
        custom_scope_dept_ids: list[str] | None = None,
        sort: int = 99,
        status: StatusEnum | str = StatusEnum.ENABLED,
        description: str | None = None,
    ) -> SysIamRelation:
        return SysIamRelation(
            subject_type=IamRelationSubjectType.RESOURCE.value,
            subject_id=resource_id,
            account_type=_as_account_type(account_type),
            relation_type=IamRelationType.RESOURCE_PERMISSION.value,
            target_type=IamRelationTargetType.PERMISSION.value,
            target_key=permission_key,
            data_scope=data_scope.value if isinstance(data_scope, DataScope) else data_scope,
            custom_scope_dept_ids=list(custom_scope_dept_ids or []),
            sort=sort,
            status=status.value if isinstance(status, StatusEnum) else status,
            description=description,
        )

    async def get_account_resource_grants(
        self,
        account_id: str,
    ) -> list[AccountResourceGrantRecord]:
        account = await self.db.get(SysAccount, account_id)
        if account is None:
            return []
        account_type = account.account_type
        role_ids, group_ids = await self._get_account_role_and_group_ids(account_id)
        role_filter = SysIamRelation.subject_id.in_(role_ids) if role_ids else False
        group_filter = SysIamRelation.subject_id.in_(group_ids) if group_ids else False
        stmt = select(SysIamRelation).where(
            SysIamRelation.relation_type == IamRelationType.SUBJECT_RESOURCE_GRANT.value,
            SysIamRelation.target_type == IamRelationTargetType.RESOURCE.value,
            SysIamRelation.account_type == account_type,
            SysIamRelation.status == StatusEnum.ENABLED.value,
            or_(SysIamRelation.expired_at.is_(None), SysIamRelation.expired_at > datetime.now(UTC)),
            or_(
                (SysIamRelation.subject_type == GrantSubjectType.ACCOUNT.value)
                & (SysIamRelation.subject_id == account_id),
                (SysIamRelation.subject_type == GrantSubjectType.GROUP.value) & group_filter,
                (SysIamRelation.subject_type == GrantSubjectType.ROLE.value) & role_filter,
            ),
        )
        return [
            {
                "subject_type": grant.subject_type,
                "subject_id": grant.subject_id,
                "resource_id": grant.target_id,
                "grant_mode": grant.grant_mode,
                "effect": grant.effect,
            }
            for grant in (await self.db.execute(stmt)).scalars().all()
        ]

    async def get_account_resource_ids(self, account_id: str) -> list[str]:
        resource_grants = await self.get_account_resource_grants(account_id)
        return sorted(
            {
                grant["resource_id"]
                for grant in resource_grants
                if grant["effect"] != GrantEffect.DENY.value
            }
        )

    async def get_account_authorization(self, account_id: str) -> AccountAuthorizationRecord:
        return (await self.get_accounts_authorization([account_id]))[account_id]

    async def get_accounts_authorization(
        self,
        account_ids: list[str],
    ) -> dict[str, AccountAuthorizationRecord]:
        unique_account_ids = list(dict.fromkeys(account_ids))
        authorizations = {
            account_id: AccountAuthorizationRecord(
                role_ids=[],
                role_codes=[],
                group_ids=[],
                dept_ids=[],
                resource_ids=[],
                button_codes=[],
                permission_keys=[],
                permission_grants=[],
            )
            for account_id in unique_account_ids
        }
        if not unique_account_ids:
            return authorizations

        account_type_rows = (
            await self.db.execute(
                select(SysAccount.id, SysAccount.account_type).where(
                    SysAccount.id.in_(unique_account_ids)
                )
            )
        ).all()
        account_type_map = {
            str(account_id): str(account_type) for account_id, account_type in account_type_rows
        }

        group_rows = (
            await self.db.execute(
                select(SysIamRelation.subject_id, SysIamRelation.target_id)
                .join(SysAccount, SysAccount.id == SysIamRelation.subject_id)
                .where(
                    SysIamRelation.subject_type == IamRelationSubjectType.ACCOUNT.value,
                    SysIamRelation.subject_id.in_(unique_account_ids),
                    SysIamRelation.relation_type == IamRelationType.ACCOUNT_GROUP.value,
                    SysIamRelation.target_type == IamRelationTargetType.GROUP.value,
                    SysIamRelation.account_type == SysAccount.account_type,
                )
            )
        ).all()
        dept_rows = (
            await self.db.execute(
                select(SysIamRelation.subject_id, SysIamRelation.target_id)
                .join(SysAccount, SysAccount.id == SysIamRelation.subject_id)
                .where(
                    SysIamRelation.subject_type == IamRelationSubjectType.ACCOUNT.value,
                    SysIamRelation.subject_id.in_(unique_account_ids),
                    SysIamRelation.relation_type == IamRelationType.ACCOUNT_DEPT.value,
                    SysIamRelation.target_type == IamRelationTargetType.DEPT.value,
                    SysIamRelation.account_type == SysAccount.account_type,
                )
            )
        ).all()
        direct_role_rows = (
            await self.db.execute(
                select(SysIamRelation.subject_id, SysIamRelation.target_id)
                .join(SysAccount, SysAccount.id == SysIamRelation.subject_id)
                .where(
                    SysIamRelation.subject_type == IamRelationSubjectType.ACCOUNT.value,
                    SysIamRelation.subject_id.in_(unique_account_ids),
                    SysIamRelation.relation_type == IamRelationType.ACCOUNT_ROLE.value,
                    SysIamRelation.target_type == IamRelationTargetType.ROLE.value,
                    SysIamRelation.account_type == SysAccount.account_type,
                )
            )
        ).all()

        account_group_rel = aliased(SysIamRelation)
        group_role_rel = aliased(SysIamRelation)
        group_role_rows = (
            await self.db.execute(
                select(account_group_rel.subject_id, group_role_rel.target_id)
                .join(SysAccount, SysAccount.id == account_group_rel.subject_id)
                .join(
                    group_role_rel,
                    and_(
                        group_role_rel.subject_id == account_group_rel.target_id,
                        group_role_rel.account_type == account_group_rel.account_type,
                    ),
                )
                .where(
                    account_group_rel.subject_type == IamRelationSubjectType.ACCOUNT.value,
                    account_group_rel.subject_id.in_(unique_account_ids),
                    account_group_rel.relation_type == IamRelationType.ACCOUNT_GROUP.value,
                    account_group_rel.target_type == IamRelationTargetType.GROUP.value,
                    account_group_rel.account_type == SysAccount.account_type,
                    group_role_rel.subject_type == IamRelationSubjectType.GROUP.value,
                    group_role_rel.relation_type == IamRelationType.GROUP_ROLE.value,
                    group_role_rel.target_type == IamRelationTargetType.ROLE.value,
                )
            )
        ).all()

        account_ids_by_group: dict[str, set[str]] = defaultdict(set)
        account_ids_by_role: dict[str, set[str]] = defaultdict(set)
        role_ids_by_account: dict[str, set[str]] = defaultdict(set)

        for account_id, group_id in group_rows:
            account_id = str(account_id)
            group_id = str(group_id)
            authorizations[account_id]["group_ids"].append(group_id)
            account_ids_by_group[group_id].add(account_id)
        for account_id, dept_id in dept_rows:
            authorizations[str(account_id)]["dept_ids"].append(str(dept_id))
        for account_id, role_id in list(direct_role_rows) + list(group_role_rows):
            account_id = str(account_id)
            role_id = str(role_id)
            role_ids_by_account[account_id].add(role_id)
            account_ids_by_role[role_id].add(account_id)

        role_ids = sorted(
            {role_id for values in role_ids_by_account.values() for role_id in values}
        )
        role_code_map: dict[str, str] = {}
        if role_ids:
            role_rows = (
                await self.db.execute(
                    select(SysRole.id, SysRole.code).where(SysRole.id.in_(role_ids))
                )
            ).all()
            role_code_map = {str(role_id): str(code) for role_id, code in role_rows}
        for account_id, account_role_ids in role_ids_by_account.items():
            sorted_role_ids = sorted(account_role_ids)
            authorizations[account_id]["role_ids"] = sorted_role_ids
            authorizations[account_id]["role_codes"] = sorted(
                role_code_map[role_id] for role_id in sorted_role_ids if role_id in role_code_map
            )

        resource_grants_by_account = await self._list_resource_grants_by_account(
            unique_account_ids,
            account_ids_by_group,
            account_ids_by_role,
            account_type_map,
        )
        permission_grants_by_account = await self._list_permission_grants_by_account(
            resource_grants_by_account,
            account_type_map,
        )
        for account_id in unique_account_ids:
            resource_grants = resource_grants_by_account.get(account_id, [])
            permission_grants = permission_grants_by_account.get(account_id, [])
            authorizations[account_id]["group_ids"] = sorted(
                set(authorizations[account_id]["group_ids"])
            )
            authorizations[account_id]["dept_ids"] = sorted(
                set(authorizations[account_id]["dept_ids"])
            )
            authorizations[account_id]["resource_ids"] = sorted(
                {
                    grant["resource_id"]
                    for grant in resource_grants
                    if grant["effect"] != GrantEffect.DENY.value
                }
            )
            authorizations[account_id]["permission_grants"] = permission_grants
            authorizations[account_id]["permission_keys"] = sorted(
                {grant["permission_key"] for grant in permission_grants}
            )
            authorizations[account_id]["button_codes"] = authorizations[account_id][
                "permission_keys"
            ].copy()
        return authorizations

    async def list_subject_resource_grants(
        self,
        subject_type: GrantSubjectType,
        subject_id: str,
        account_type: AccountType | str | None = None,
    ) -> list[dict[str, object]]:
        await self._ensure_subject_exists(subject_type.value, subject_id)
        filters = [
            SysIamRelation.subject_type == subject_type.value,
            SysIamRelation.subject_id == subject_id,
            SysIamRelation.relation_type == IamRelationType.SUBJECT_RESOURCE_GRANT.value,
            SysIamRelation.target_type == IamRelationTargetType.RESOURCE.value,
        ]
        if account_type is not None:
            filters.append(SysIamRelation.account_type == _as_account_type(account_type))
        stmt = (
            select(SysIamRelation)
            .where(*filters)
            .order_by(SysIamRelation.id.asc())
        )
        grants = list((await self.db.execute(stmt)).scalars().all())
        resource_ids = [grant.target_id for grant in grants]
        if not resource_ids:
            return []
        resources = list(
            (await self.db.execute(select(SysResource).where(SysResource.id.in_(resource_ids))))
            .scalars()
            .all()
        )
        resource_map = {resource.id: resource for resource in resources}
        permission_stmt = select(SysIamRelation).where(
            SysIamRelation.subject_type == IamRelationSubjectType.RESOURCE.value,
            SysIamRelation.relation_type == IamRelationType.RESOURCE_PERMISSION.value,
            SysIamRelation.target_type == IamRelationTargetType.PERMISSION.value,
            SysIamRelation.subject_id.in_(resource_ids),
        )
        permission_map: dict[str, list[str]] = defaultdict(list)
        for permission in (await self.db.execute(permission_stmt)).scalars().all():
            permission_map[permission.subject_id].append(permission.target_key)

        grant_map: dict[str, set[str]] = defaultdict(set)
        for resource_id in resource_ids:
            resource = resource_map.get(resource_id)
            if not resource:
                continue
            if resource.resource_type in {"BUTTON", "ACTION"}:
                grant_map[resource.parent_id or resource.id].update(
                    permission_map.get(resource.id) or [resource.code]
                )
            else:
                grant_map[resource.id]
        return [
            {"resource_id": resource_id, "permission_keys": sorted(permission_keys)}
            for resource_id, permission_keys in sorted(grant_map.items())
        ]

    async def replace_subject_resource_grant_infos(
        self,
        subject_type: GrantSubjectType,
        subject_id: str,
        grant_info_list,
        account_type: AccountType | str,
    ) -> None:
        account_type = _as_account_type(account_type)
        await self._ensure_subject_exists(subject_type.value, subject_id)
        resource_ids = list(dict.fromkeys(item.resource_id for item in grant_info_list))
        original_resource_ids = set(resource_ids)
        permission_keys = list(
            dict.fromkeys(
                permission_key
                for item in grant_info_list
                for permission_key in item.permission_keys
            )
        )
        if resource_ids:
            existing_ids = set(
                (
                    await self.db.execute(
                        select(SysResource.id).where(SysResource.id.in_(resource_ids))
                    )
                )
                .scalars()
                .all()
            )
            if len(existing_ids) != len(resource_ids):
                raise NotFoundError("Resource not found")
        if permission_keys:
            permission_resource_rows = list(
                (
                    await self.db.execute(
                        select(SysIamRelation.target_key, SysIamRelation.subject_id).where(
                            SysIamRelation.subject_type == IamRelationSubjectType.RESOURCE.value,
                            SysIamRelation.relation_type
                            == IamRelationType.RESOURCE_PERMISSION.value,
                            SysIamRelation.target_type == IamRelationTargetType.PERMISSION.value,
                            SysIamRelation.account_type == account_type,
                            SysIamRelation.target_key.in_(permission_keys),
                        )
                    )
                ).all()
            )
            code_resource_rows = list(
                (
                    await self.db.execute(
                        select(SysResource.code, SysResource.id).where(
                            SysResource.code.in_(permission_keys),
                            SysResource.resource_type.in_(["BUTTON", "ACTION"]),
                        )
                    )
                ).all()
            )
            permission_resource_map: dict[str, set[str]] = defaultdict(set)
            for permission_key, resource_id in permission_resource_rows + code_resource_rows:
                permission_resource_map[str(permission_key)].add(str(resource_id))
            missing_permission_keys = [
                permission_key
                for permission_key in permission_keys
                if permission_key not in permission_resource_map
            ]
            if missing_permission_keys:
                raise NotFoundError("Permission resource not found")
            for permission_key in permission_keys:
                resource_ids.extend(permission_resource_map[permission_key])
        resource_ids = list(dict.fromkeys(resource_ids))
        await self.delete_subject_relations(
            subject_type.value,
            subject_id,
            IamRelationType.SUBJECT_RESOURCE_GRANT,
            account_type=account_type,
        )
        for resource_id in resource_ids:
            self.db.add(
                self.subject_resource_grant(
                    subject_type,
                    subject_id,
                    resource_id,
                    account_type,
                    GrantMode.DIRECT if resource_id in original_resource_ids else GrantMode.CASCADE,
                )
            )
        await self.db.flush()

    async def _get_account_role_and_group_ids(self, account_id: str) -> tuple[list[str], list[str]]:
        account = await self.db.get(SysAccount, account_id)
        if account is None:
            return [], []
        account_type = account.account_type
        group_rows = (
            (
                await self.db.execute(
                    select(SysIamRelation.target_id).where(
                        SysIamRelation.subject_type == IamRelationSubjectType.ACCOUNT.value,
                        SysIamRelation.subject_id == account_id,
                        SysIamRelation.relation_type == IamRelationType.ACCOUNT_GROUP.value,
                        SysIamRelation.target_type == IamRelationTargetType.GROUP.value,
                        SysIamRelation.account_type == account_type,
                    )
                )
            )
            .scalars()
            .all()
        )
        direct_role_rows = (
            (
                await self.db.execute(
                    select(SysIamRelation.target_id).where(
                        SysIamRelation.subject_type == IamRelationSubjectType.ACCOUNT.value,
                        SysIamRelation.subject_id == account_id,
                        SysIamRelation.relation_type == IamRelationType.ACCOUNT_ROLE.value,
                        SysIamRelation.target_type == IamRelationTargetType.ROLE.value,
                        SysIamRelation.account_type == account_type,
                    )
                )
            )
            .scalars()
            .all()
        )
        group_role_ids: list[str] = []
        group_ids = [str(value) for value in group_rows]
        if group_ids:
            group_role_ids = [
                str(value)
                for value in (
                    await self.db.execute(
                        select(SysIamRelation.target_id).where(
                            SysIamRelation.subject_type == IamRelationSubjectType.GROUP.value,
                            SysIamRelation.subject_id.in_(group_ids),
                            SysIamRelation.relation_type == IamRelationType.GROUP_ROLE.value,
                            SysIamRelation.target_type == IamRelationTargetType.ROLE.value,
                            SysIamRelation.account_type == account_type,
                        )
                    )
                )
                .scalars()
                .all()
            ]
        role_ids = sorted({str(value) for value in direct_role_rows}.union(group_role_ids))
        return role_ids, group_ids

    async def _list_resource_grants_by_account(
        self,
        account_ids: list[str],
        account_ids_by_group: dict[str, set[str]],
        account_ids_by_role: dict[str, set[str]],
        account_type_map: dict[str, str],
    ) -> dict[str, list[AccountResourceGrantRecord]]:
        subject_conditions = [
            (SysIamRelation.subject_type == GrantSubjectType.ACCOUNT.value)
            & (SysIamRelation.subject_id.in_(account_ids))
        ]
        if account_ids_by_group:
            subject_conditions.append(
                (SysIamRelation.subject_type == GrantSubjectType.GROUP.value)
                & (SysIamRelation.subject_id.in_(account_ids_by_group.keys()))
            )
        if account_ids_by_role:
            subject_conditions.append(
                (SysIamRelation.subject_type == GrantSubjectType.ROLE.value)
                & (SysIamRelation.subject_id.in_(account_ids_by_role.keys()))
            )
        stmt = select(SysIamRelation).where(
            SysIamRelation.relation_type == IamRelationType.SUBJECT_RESOURCE_GRANT.value,
            SysIamRelation.target_type == IamRelationTargetType.RESOURCE.value,
            SysIamRelation.status == StatusEnum.ENABLED.value,
            or_(SysIamRelation.expired_at.is_(None), SysIamRelation.expired_at > datetime.now(UTC)),
            or_(*subject_conditions),
        )
        grants_by_account: dict[str, list[AccountResourceGrantRecord]] = defaultdict(list)
        for grant in (await self.db.execute(stmt)).scalars().all():
            if grant.subject_type == GrantSubjectType.ACCOUNT.value:
                target_account_ids = {grant.subject_id}
            elif grant.subject_type == GrantSubjectType.GROUP.value:
                target_account_ids = account_ids_by_group.get(grant.subject_id, set())
            elif grant.subject_type == GrantSubjectType.ROLE.value:
                target_account_ids = account_ids_by_role.get(grant.subject_id, set())
            else:
                target_account_ids = set()
            record: AccountResourceGrantRecord = {
                "subject_type": grant.subject_type,
                "subject_id": grant.subject_id,
                "resource_id": grant.target_id,
                "grant_mode": grant.grant_mode,
                "effect": grant.effect,
            }
            for account_id in target_account_ids:
                if account_type_map.get(account_id) != grant.account_type:
                    continue
                grants_by_account[account_id].append(record)
        return grants_by_account

    async def _list_permission_grants_by_account(
        self,
        resource_grants_by_account: dict[str, list[AccountResourceGrantRecord]],
        account_type_map: dict[str, str],
    ) -> dict[str, list[PermissionGrantRecord]]:
        cascade_resource_ids = sorted(
            {
                grant["resource_id"]
                for grants in resource_grants_by_account.values()
                for grant in grants
                if grant["grant_mode"] == GrantMode.CASCADE.value
                and grant["effect"] != GrantEffect.DENY.value
            }
        )
        permission_rows_by_resource: dict[str, list[SysIamRelation]] = defaultdict(list)
        if cascade_resource_ids:
            permission_stmt = select(SysIamRelation).where(
                SysIamRelation.subject_type == IamRelationSubjectType.RESOURCE.value,
                SysIamRelation.relation_type == IamRelationType.RESOURCE_PERMISSION.value,
                SysIamRelation.target_type == IamRelationTargetType.PERMISSION.value,
                SysIamRelation.status == StatusEnum.ENABLED.value,
                SysIamRelation.subject_id.in_(cascade_resource_ids),
            )
            for row in (await self.db.execute(permission_stmt)).scalars().all():
                permission_rows_by_resource[row.subject_id].append(row)

        permission_map_by_account: dict[
            str,
            dict[str, tuple[int, PermissionGrantRecord]],
        ] = defaultdict(dict)
        for account_id, resource_grants in resource_grants_by_account.items():
            account_type = account_type_map.get(account_id)
            for grant in resource_grants:
                if (
                    grant["grant_mode"] != GrantMode.CASCADE.value
                    or grant["effect"] == GrantEffect.DENY.value
                ):
                    continue
                for row in permission_rows_by_resource.get(grant["resource_id"], []):
                    if account_type is not None and row.account_type != account_type:
                        continue
                    self._apply_permission_record(
                        permission_map_by_account[account_id],
                        _PERMISSION_PRIORITY_RESOURCE,
                        {
                            "permission_key": row.target_key,
                            "data_scope": row.data_scope,
                            "custom_scope_dept_ids": list(row.custom_scope_dept_ids),
                            "effect": GrantEffect.ALLOW.value,
                            "source_type": grant["subject_type"],
                            "source_id": grant["subject_id"],
                        },
                    )

        return {
            account_id: [
                record
                for _, record in sorted(
                    permission_map.values(),
                    key=lambda item: item[1]["permission_key"],
                )
                if record["effect"] != GrantEffect.DENY.value
            ]
            for account_id, permission_map in permission_map_by_account.items()
        }

    def _apply_permission_record(
        self,
        permission_map: dict[str, tuple[int, PermissionGrantRecord]],
        priority: int,
        record: PermissionGrantRecord,
    ) -> None:
        current = permission_map.get(record["permission_key"])
        if current is None or priority >= current[0]:
            permission_map[record["permission_key"]] = (priority, record)

    async def _ensure_subject_exists(self, subject_type: str, subject_id: str) -> None:
        entity: object | None
        if subject_type == GrantSubjectType.ROLE.value:
            entity = await self.db.get(SysRole, subject_id)
        elif subject_type == GrantSubjectType.ACCOUNT.value:
            entity = await self.db.get(SysAccount, subject_id)
        elif subject_type == GrantSubjectType.GROUP.value:
            entity = await self.db.get(SysGroup, subject_id)
        else:
            entity = None
        if not entity:
            raise NotFoundError("Subject not found")
