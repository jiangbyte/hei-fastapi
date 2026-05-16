import bcrypt
from typing import Optional, List, Dict
from datetime import datetime
from core.utils import decrypt
from sqlalchemy.orm import Session
from fastapi import Request
from .models import SysUser
from .params import UserVO, UserPageParam, GrantRoleParam, GrantUserPermissionParam, UpdateProfileParam, UpdateAvatarParam, UpdatePasswordParam
from .dao import UserDao
from core.pojo import IdParam, IdsParam
from core.result import page_data, PageDataField
from core.exception import BusinessException
from core.utils import strip_system_fields, apply_update
from core.auth import HeiAuthTool, LoginUserInfo
from core.utils.resolve_utils import resolve_name_path, resolve_path_from_map
import logging

from ..resource import SysResource
from core.auth.permission.hei_permission_interface import SUPER_ADMIN_CODE

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session):
        self.dao = UserDao(db)

    async def _get_current_user_id(self, request: Optional[Request] = None) -> Optional[str]:
        try:
            return await HeiAuthTool.getLoginIdDefaultNull(request)
        except Exception as e:
            logger.warning(f"Failed to get current user: {e}")
            return None

    def find_by_id(self, user_id: str) -> Optional[SysUser]:
        return self.dao.find_by_id(user_id)

    def find_by_username(self, username: str) -> Optional[SysUser]:
        return self.dao.find_by_username(username)

    def find_by_email(self, email: str) -> Optional[SysUser]:
        return self.dao.find_by_email(email)

    def to_login_user_info(self, entity: Optional[SysUser]) -> Optional[LoginUserInfo]:
        if not entity:
            return None
        return LoginUserInfo(
            id=entity.id,
            username=entity.username,
            password=entity.password,
            nickname=entity.nickname,
            avatar=entity.avatar,
            motto=entity.motto,
            gender=entity.gender,
            birthday=entity.birthday,
            email=entity.email,
            github=entity.github,
            status=entity.status,
            last_login_at=entity.last_login_at,
            last_login_ip=entity.last_login_ip,
            login_count=entity.login_count,
        )

    def record_login(self, user_id: str, request: Request) -> None:
        entity = self.dao.find_by_id(user_id)
        if not entity:
            return
        entity.last_login_at = datetime.now()
        entity.last_login_ip = request.client.host if request.client else None
        entity.login_count = (entity.login_count or 0) + 1
        self.dao.update(entity)

    def page(self, param: UserPageParam) -> dict:
        result = self.dao.find_page_by_filters(param)
        records = result[PageDataField.RECORDS]
        user_ids = [r.id for r in records]
        role_map = self.dao.get_role_ids_map_by_user_ids(user_ids)
        group_map = self.dao.get_group_id_map_by_user_ids(user_ids)
        vo_list = []
        for r in records:
            vo = UserVO.model_validate(r).model_dump()
            vo["role_ids"] = role_map.get(r.id, [])
            vo["group_id"] = group_map.get(r.id)
            vo_list.append(vo)
        self._batch_enrich(vo_list)
        return page_data(
            records=vo_list,
            total=result[PageDataField.TOTAL],
            page=param.current,
            size=param.size
        )

    def _enrich_names(self, vo: dict) -> None:
        db = self.dao.db
        from modules.sys.org.models import SysOrg
        vo["org_names"] = resolve_name_path(vo.get("org_id"), db, SysOrg)
        from modules.sys.group.models import SysGroup
        vo["group_names"] = resolve_name_path(vo.get("group_id"), db, SysGroup)
        if vo.get("position_id"):
            from modules.sys.position.models import SysPosition
            pos = db.get(SysPosition, vo["position_id"])
            vo["position_name"] = pos.name if pos else None

    def _batch_enrich(self, vo_list: List[dict]) -> None:
        if not vo_list:
            return

        db = self.dao.db
        from sqlalchemy import select
        from modules.sys.org.models import SysOrg
        from modules.sys.group.models import SysGroup
        from modules.sys.position.models import SysPosition

        position_ids = {vo["position_id"] for vo in vo_list if vo.get("position_id")}

        pos_name_map = {}
        if position_ids:
            rows = db.execute(
                select(SysPosition.id, SysPosition.name).where(SysPosition.id.in_(position_ids))
            ).all()
            pos_name_map = {r.id: r.name for r in rows}

        org_rows = db.execute(select(SysOrg.id, SysOrg.name, SysOrg.parent_id)).all()
        org_node_map = {r.id: {"name": r.name, "parent_id": r.parent_id} for r in org_rows}
        group_rows = db.execute(select(SysGroup.id, SysGroup.name, SysGroup.parent_id)).all()
        group_node_map = {r.id: {"name": r.name, "parent_id": r.parent_id} for r in group_rows}

        for vo in vo_list:
            vo["org_names"] = resolve_path_from_map(vo.get("org_id"), org_node_map)
            vo["group_names"] = resolve_path_from_map(vo.get("group_id"), group_node_map)
            vo["position_name"] = pos_name_map.get(vo["position_id"]) if vo.get("position_id") else None

    def _enrich_vo(self, user_id: str, vo: dict):
        vo["role_ids"] = self.dao.get_role_ids_by_user_id(user_id)
        vo["group_id"] = self.dao.get_group_id_by_user_id(user_id)
        self._enrich_names(vo)

    async def create(self, vo: UserVO, request: Optional[Request] = None) -> None:
        if vo.username and self.find_by_username(vo.username):
            raise BusinessException("账号已存在")
        if vo.email and self.find_by_email(vo.email):
            raise BusinessException("邮箱已存在")

        entity = SysUser(**strip_system_fields(vo.model_dump(), extra_fields={'role_ids', 'group_id'}))
        user_id = await self._get_current_user_id(request)
        self.dao.insert(entity, user_id=user_id)

        if vo.role_ids:
            self.dao.grant_roles(entity.id, vo.role_ids, user_id)
        if vo.group_id:
            self.dao.set_group(entity.id, vo.group_id)

    async def modify(self, vo: UserVO, request: Optional[Request] = None) -> None:
        entity = self.dao.find_by_id(vo.id)
        if not entity:
            raise BusinessException("数据不存在")

        update_data = vo.model_dump(exclude_unset=True)
        apply_update(entity, update_data, extra_protected={'password', 'role_ids', 'group_id'})

        user_id = await self._get_current_user_id(request)
        self.dao.update(entity, user_id=user_id)

        if vo.role_ids is not None:
            self.dao.grant_roles(vo.id, vo.role_ids, user_id)
        if vo.group_id is not None:
            self.dao.set_group(vo.id, vo.group_id)

    def remove(self, param: IdsParam) -> None:
        from sqlalchemy import delete as sa_delete
        from .models import RelUserRole, RelUserPermission

        ids = param.ids
        db = self.dao.db

        for model in [RelUserRole, RelUserPermission]:
            db.execute(sa_delete(model).where(model.user_id.in_(ids)))

        self.dao.delete_by_ids(ids)

    def detail(self, param: IdParam) -> Optional[dict]:
        entity = self.dao.find_by_id(param.id)
        if not entity:
            return None
        vo = UserVO.model_validate(entity).model_dump()
        self._enrich_vo(param.id, vo)
        return vo

    # ---- Grant APIs ----

    async def grant_roles(self, param: GrantRoleParam, request: Optional[Request] = None) -> None:
        created_by = await self._get_current_user_id(request)
        self.dao.grant_roles(param.user_id, param.role_ids, created_by)

    async def grant_permissions(self, param: GrantUserPermissionParam, request: Optional[Request] = None) -> None:
        created_by = await self._get_current_user_id(request)
        self.dao.grant_permissions(param.user_id, param.permissions, created_by)

    def get_user_permission_details(self, user_id: str) -> list[dict]:
        return self.dao.get_permission_details_by_user_id(user_id)

    # ---- User role/group query ----
    def get_user_role_ids(self, user_id: str) -> List[str]:
        return self.dao.get_role_ids_by_user_id(user_id)

    def get_user_group_id(self, user_id: str) -> Optional[str]:
        return self.dao.get_group_id_by_user_id(user_id)

    # ---- Current user info for frontend ----

    async def get_current_user(self, request: Request) -> Optional[Dict]:
        user_id = await HeiAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            return None
        entity = self.find_by_id(user_id)
        if not entity:
            return None

        position_name = None
        if entity.position_id:
            from modules.sys.position.models import SysPosition
            pos = self.dao.db.get(SysPosition, entity.position_id)
            if pos:
                position_name = pos.name

        from modules.sys.org.models import SysOrg
        from modules.sys.group.models import SysGroup
        org_names = resolve_name_path(entity.org_id, self.dao.db, SysOrg)
        group_names = resolve_name_path(entity.group_id, self.dao.db, SysGroup)

        vo = UserVO.model_validate(entity).model_dump()
        vo["org_names"] = org_names
        vo["group_names"] = group_names
        vo["position_name"] = position_name
        return vo

    async def update_profile(self, param: UpdateProfileParam, request: Request) -> None:
        user_id = await HeiAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            raise BusinessException("用户未登录")
        entity = self.dao.find_by_id(user_id)
        if not entity:
            raise BusinessException("用户不存在")

        update_data = param.model_dump(exclude_unset=True)
        if 'username' in update_data and update_data['username'] != entity.username:
            if self.find_by_username(update_data['username']):
                raise BusinessException("账号已存在")
        apply_update(entity, update_data)
        self.dao.update(entity, user_id=user_id)

    async def update_avatar(self, param: UpdateAvatarParam, request: Request) -> None:
        user_id = await HeiAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            raise BusinessException("用户未登录")
        entity = self.dao.find_by_id(user_id)
        if not entity:
            raise BusinessException("用户不存在")

        entity.avatar = param.avatar
        self.dao.update(entity, user_id=user_id)

    async def update_password(self, param: UpdatePasswordParam, request: Request) -> None:
        user_id = await HeiAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            raise BusinessException("用户未登录")
        entity = self.dao.find_by_id(user_id)
        if not entity:
            raise BusinessException("用户不存在")
        if not entity.password:
            raise BusinessException("未设置密码，无法修改")

        current_password = decrypt(param.current_password)
        if not bcrypt.checkpw(current_password.encode('utf-8'), entity.password.encode('utf-8')):
            raise BusinessException("当前密码不正确")

        new_password = decrypt(param.new_password)
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        entity.password = hashed
        self.dao.update(entity, user_id=user_id)

    async def get_current_user_menus(self, request: Request) -> List[Dict]:
        user_id = await HeiAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            return []

        role_codes = self.dao.get_user_role_codes(user_id)
        if SUPER_ADMIN_CODE in role_codes:
            resources = self.dao.get_all_resources()
            return self._build_menu_tree(resources)

        role_ids = self._get_user_role_ids(user_id)
        if not role_ids:
            return []

        resource_ids = self.dao.get_role_resource_ids(role_ids)
        if not resource_ids:
            return []

        resources = self.dao.get_resources_by_ids(resource_ids)
        return self._build_menu_tree(resources)

    def _get_user_role_ids(self, user_id: str) -> List[str]:
        return self.dao.get_user_role_ids_all_sources(user_id)

    def _build_menu_tree(self, resources: List[SysResource]) -> List[Dict]:
        resource_map = {}
        for r in resources:
            resource_map[r.id] = {
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "type": r.type,
                "parent_id": r.parent_id,
                "route_path": r.route_path,
                "component_path": r.component_path,
                "redirect_path": r.redirect_path,
                "icon": r.icon,
                "is_visible": r.is_visible,
                "is_cache": r.is_cache,
                "is_affix": r.is_affix,
                "is_breadcrumb": r.is_breadcrumb,
                "sort_code": r.sort_code,
                "children": [],
            }

        tree = []
        for r in resources:
            node = resource_map[r.id]
            if r.parent_id and r.parent_id != "0" and r.parent_id in resource_map:
                resource_map[r.parent_id]["children"].append(node)
            else:
                tree.append(node)

        return tree

    async def get_current_user_permissions(self, request: Request) -> List[str]:
        user_id = await HeiAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            return []

        role_ids = self._get_user_role_ids(user_id)
        if not role_ids:
            return []

        codes = self.dao.get_role_permission_codes(role_ids)
        return sorted(codes)


class LoginUserApiProvider:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_current_login_user_info(self, request) -> Optional[LoginUserInfo]:
        user_id = await HeiAuthTool.getLoginIdAsString(request)
        if not user_id:
            return None
        return self.get_login_user_info_by_id(user_id)

    def get_login_user_info_by_id(self, user_id: str) -> Optional[LoginUserInfo]:
        db = self._session_factory()
        try:
            service = UserService(db)
            entity = service.find_by_id(user_id)
            return service.to_login_user_info(entity)
        finally:
            db.close()

    def get_login_user_info_by_username(self, username: str) -> Optional[LoginUserInfo]:
        db = self._session_factory()
        try:
            service = UserService(db)
            entity = service.find_by_username(username)
            return service.to_login_user_info(entity)
        finally:
            db.close()

    def get_login_user_info_by_email(self, email: str) -> Optional[LoginUserInfo]:
        db = self._session_factory()
        try:
            service = UserService(db)
            entity = service.find_by_email(email)
            return service.to_login_user_info(entity)
        finally:
            db.close()
