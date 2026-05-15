from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Request
from .models import SysRole
from .params import RoleVO, RolePageParam, RoleExportParam, RoleImportParam, GrantPermissionParam, GrantResourceParam, \
    ButtonPermissionScope, PermissionItem
from .dao import RoleDao
from core.enums import DataScopeEnum
from core.pojo import IdParam, IdsParam
from core.result import page_data, PageDataField
from core.exception import BusinessException
from core.enums import ExportTypeEnum
from core.utils import export_excel, strip_system_fields, apply_update, make_template
from core.auth import HeiAuthTool
from core.db.base_service import BaseCrudService
import logging

logger = logging.getLogger(__name__)


class RoleService(BaseCrudService):
    model_class = SysRole
    vo_class = RoleVO
    dao_class = RoleDao
    page_param_class = RolePageParam
    export_name = "角色数据"

    def remove(self, param: IdsParam) -> None:
        from sqlalchemy import func, select, delete as sa_delete
        from .models import RelRolePermission, RelRoleResource
        from ..user.models import RelUserRole

        ids = param.ids
        db = self.dao.db

        if db.execute(
            select(func.count()).select_from(RelUserRole).where(RelUserRole.role_id.in_(ids))
        ).scalar() > 0:
            raise BusinessException("角色存在关联用户，无法删除")

        for model in [RelRolePermission, RelRoleResource, RelUserRole]:
            db.execute(sa_delete(model).where(model.role_id.in_(ids)))

        self.dao.delete_by_ids(ids)

    async def grant_permissions(self, param: GrantPermissionParam, request: Optional[Request] = None) -> None:
        created_by = await self._get_current_user_id(request)
        self.dao.grant_permissions(param.role_id, param.permissions, created_by)

    async def grant_resources(self, param: GrantResourceParam, request: Optional[Request] = None) -> None:
        created_by = await self._get_current_user_id(request)
        self.dao.grant_resources(param.role_id, param.resource_ids, created_by)

        # Auto-grant permissions linked via resource.extra -> permission_code
        import json

        resources = self.dao.find_resources_with_extra_by_ids(param.resource_ids)

        # Build code -> scope mapping from provided permissions
        scope_map: dict[str, ButtonPermissionScope] = {
            p.permission_code: p for p in param.permissions
        }

        permission_items = []
        for r in resources:
            try:
                extra = json.loads(r.extra)
                pcode = extra.get('permission_code')
                if not pcode:
                    continue
                scope = scope_map.get(pcode)
                permission_items.append(PermissionItem(
                    permission_code=pcode,
                    scope=scope.scope if scope else DataScopeEnum.ALL.value,
                    custom_scope_group_ids=scope.custom_scope_group_ids if scope else None,
                    custom_scope_org_ids=scope.custom_scope_org_ids if scope else None,
                ))
            except (json.JSONDecodeError, TypeError):
                continue

        if permission_items:
            # Deduplicate by permission_code to avoid unique-key violations
            seen = set()
            unique_items = []
            for item in permission_items:
                if item.permission_code not in seen:
                    seen.add(item.permission_code)
                    unique_items.append(item)
            self.dao.add_missing_permissions(param.role_id, unique_items)

    def get_role_permission_codes(self, role_id: str) -> List[str]:
        return self.dao.get_permission_codes_by_role_id(role_id)

    def get_role_permission_details(self, role_id: str) -> list[dict]:
        return self.dao.get_permission_details_by_role_id(role_id)

    def get_role_resource_ids(self, role_id: str) -> List[str]:
        return self.dao.get_resource_ids_by_role_id(role_id)
