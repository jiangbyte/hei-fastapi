from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, delete as sa_delete, update as sa_update
from .models import SysUser, RelUserRole, RelUserPermission
from .params import UserPageParam
from core.db.base_dao import BaseDAO
from core.db.query_wrapper import QueryWrapper
from core.enums import ResourceCategoryEnum, ResourceTypeEnum, StatusEnum, DataScopeEnum
from core.utils import generate_id
from modules.sys.role.params import PermissionItem


class UserDao(BaseDAO):
    def __init__(self, db: Session):
        super().__init__(db, SysUser)

    def find_page_by_filters(self, param: UserPageParam) -> Dict[str, Any]:
        wrapper = QueryWrapper(SysUser)
        if param.keyword:
            keyword = f"%{param.keyword}%"
            wrapper.where(or_(SysUser.account.ilike(keyword), SysUser.nickname.ilike(keyword)))
        if param.status:
            wrapper.eq(SysUser.status, param.status)
        wrapper.order_by_desc(SysUser.created_at)
        return self.select_page(wrapper, param)

    def find_by_account(self, account: str) -> Optional[SysUser]:
        return (
            self.db.execute(
                select(SysUser).where(SysUser.account == account)
            )
            .scalar_one_or_none()
        )

    def find_by_email(self, email: str) -> Optional[SysUser]:
        return (
            self.db.execute(
                select(SysUser).where(SysUser.email == email)
            )
            .scalar_one_or_none()
        )

    # ---- RAL: User Roles ----

    def get_role_ids_by_user_id(self, user_id: str) -> List[str]:
        rows = self.db.execute(
            select(RelUserRole.role_id).where(RelUserRole.user_id == user_id)
        ).scalars().all()
        return list(rows)

    def get_role_ids_map_by_user_ids(self, user_ids: List[str]) -> Dict[str, List[str]]:
        if not user_ids:
            return {}
        rows = self.db.execute(
            select(RelUserRole.user_id, RelUserRole.role_id).where(
                RelUserRole.user_id.in_(user_ids),
            )
        ).all()
        result: Dict[str, List[str]] = {uid: [] for uid in user_ids}
        for uid, rid in rows:
            result.setdefault(uid, []).append(rid)
        return result

    def grant_roles(self, user_id: str, role_ids: List[str], created_by: Optional[str] = None,
                    scope: Optional[str] = None, custom_scope_group_ids: Optional[str] = None):
        self.db.execute(sa_delete(RelUserRole).where(RelUserRole.user_id == user_id))

        for rid in role_ids:
            rel = RelUserRole(
                id=generate_id(), user_id=user_id, role_id=rid,
                scope=scope, custom_scope_group_ids=custom_scope_group_ids,
            )
            self.db.add(rel)
        self.db.commit()

    # ---- RAL: User Groups ----

    def get_group_id_by_user_id(self, user_id: str) -> Optional[str]:
        return self.db.execute(
            select(SysUser.group_id).where(SysUser.id == user_id)
        ).scalar()

    def get_group_id_map_by_user_ids(self, user_ids: List[str]) -> Dict[str, str]:
        if not user_ids:
            return {}
        rows = self.db.execute(
            select(SysUser.id, SysUser.group_id).where(
                SysUser.id.in_(user_ids),
            )
        ).all()
        return {uid: gid for uid, gid in rows if gid}

    def set_group(self, user_id: str, group_id: Optional[str]) -> None:
        self.db.execute(
            sa_update(SysUser).where(SysUser.id == user_id).values(group_id=group_id)
        )
        self.db.commit()

    # ---- RAL: User Permissions (direct) ----

    def get_permission_details_by_user_id(self, user_id: str) -> list[dict]:
        rows = self.db.execute(
            select(
                RelUserPermission.permission_code,
                RelUserPermission.scope,
                RelUserPermission.custom_scope_group_ids,
                RelUserPermission.custom_scope_org_ids,
            ).where(
                RelUserPermission.user_id == user_id,
            )
        ).all()
        return [
            {
                "permission_code": r[0],
                "scope": r[1] or DataScopeEnum.ALL.value,
                "custom_scope_group_ids": r[2],
                "custom_scope_org_ids": r[3],
            }
            for r in rows
        ]

    def grant_permissions(self, user_id: str, permissions: Optional[List[PermissionItem]] = None, created_by: Optional[str] = None):
        self.db.execute(sa_delete(RelUserPermission).where(RelUserPermission.user_id == user_id))

        if permissions:
            for p in permissions:
                rel = RelUserPermission(
                    id=generate_id(), user_id=user_id, permission_code=p.permission_code,
                    scope=p.scope, custom_scope_group_ids=p.custom_scope_group_ids,
                    custom_scope_org_ids=p.custom_scope_org_ids,
                )
                self.db.add(rel)
        self.db.commit()

    # ---- Cross-table auth queries ----

    def get_user_role_ids_all_sources(self, user_id: str) -> List[str]:
        """Get role IDs from direct assignment + org membership."""
        role_ids: set[str] = set()

        # Direct role assignments (RelUserRole)
        direct_rows = self.db.execute(
            select(RelUserRole.role_id).where(RelUserRole.user_id == user_id)
        ).scalars().all()
        role_ids.update(direct_rows)

        # Via org (RelOrgRole)
        from ..org.models import RelOrgRole as _RelOrgRole
        org_id = self.db.execute(
            select(SysUser.org_id).where(
                SysUser.id == user_id,
            )
        ).scalar()
        if org_id:
            org_rows = self.db.execute(
                select(_RelOrgRole.role_id).where(
                    _RelOrgRole.org_id == org_id,
                )
            ).scalars().all()
            role_ids.update(org_rows)

        return list(role_ids)

    def get_role_resource_ids(self, role_ids: List[str]) -> List[str]:
        from ..role.models import RelRoleResource as _RelRoleResource
        rows = self.db.execute(
            select(_RelRoleResource.resource_id).where(
                _RelRoleResource.role_id.in_(role_ids),
            )
        ).scalars().all()
        return list(set(rows))

    def get_resources_by_ids(self, resource_ids: List[str]):
        """Get backend menu resources by IDs, ordered by sort_code."""
        from ..resource.models import SysResource as _SysResource
        stmt = (
            select(_SysResource)
            .where(
                _SysResource.id.in_(resource_ids),
                _SysResource.category == ResourceCategoryEnum.BACKEND_MENU,
                _SysResource.type.in_([ResourceTypeEnum.DIRECTORY, ResourceTypeEnum.MENU]),
                _SysResource.status == StatusEnum.ENABLED,
            )
            .order_by(_SysResource.sort_code.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_user_role_codes(self, user_id: str) -> List[str]:
        """Get role codes for a user."""
        from ..role.models import SysRole as _SysRole
        rows = self.db.execute(
            select(_SysRole.code).join(
                RelUserRole, _SysRole.id == RelUserRole.role_id
            ).where(RelUserRole.user_id == user_id)
        ).scalars().all()
        return list(rows)

    def get_all_resources(self):
        """Get ALL backend menu resources, ordered by sort_code."""
        from ..resource.models import SysResource as _SysResource
        stmt = (
            select(_SysResource)
            .where(
                _SysResource.category == ResourceCategoryEnum.BACKEND_MENU,
                _SysResource.type.in_([ResourceTypeEnum.DIRECTORY, ResourceTypeEnum.MENU]),
                _SysResource.status == StatusEnum.ENABLED,
            )
            .order_by(_SysResource.sort_code.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_role_permission_codes(self, role_ids: List[str]) -> List[str]:
        from ..role.models import RelRolePermission as _RelRolePermission
        rows = self.db.execute(
            select(_RelRolePermission.permission_code).where(
                _RelRolePermission.role_id.in_(role_ids),
            )
        ).scalars().all()
        return list(set(rows))
