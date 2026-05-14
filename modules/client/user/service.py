from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Request
from .params import (
    ClientUserVO, ClientUserPageParam,
    UpdateProfileParam, UpdateAvatarParam, UpdatePasswordParam,
)
from .dao import ClientUserDao
from .models import ClientUser
from core.utils import decrypt
from core.result import page_data, PageDataField
from core.exception import BusinessException
from core.utils import strip_system_fields, apply_update, export_excel, make_template
from core.auth import HeiClientAuthTool, LoginUserInfo
from core.db.base_service import BaseCrudService
import bcrypt


class ClientUserService(BaseCrudService):
    model_class = ClientUser
    vo_class = ClientUserVO
    dao_class = ClientUserDao
    page_param_class = ClientUserPageParam
    export_name = "C端用户数据"

    @property
    def _auth_tool(self):
        return HeiClientAuthTool

    def page(self, param: ClientUserPageParam) -> dict:
        result = self.dao.find_page_by_filters(param)
        records = [self.vo_class.model_validate(r).model_dump() for r in result[PageDataField.RECORDS]]
        self._batch_enrich(records)
        return page_data(
            records=records,
            total=result[PageDataField.TOTAL],
            page=param.current,
            size=param.size,
        )

    def find_by_email(self, email: str) -> Optional[ClientUser]:
        return self.dao.find_by_email(email)

    async def create(self, vo: ClientUserVO, request: Optional[Request] = None) -> None:
        if vo.account and self.find_by_account(vo.account):
            raise BusinessException("账号已存在")
        if vo.email and self.find_by_email(vo.email):
            raise BusinessException("邮箱已存在")
        entity = ClientUser(**strip_system_fields(vo.model_dump()))
        self.dao.insert(entity, user_id=await self._get_current_user_id(request))

    async def modify(self, vo: ClientUserVO, request: Optional[Request] = None) -> None:
        entity = self.dao.find_by_id(vo.id)
        if not entity:
            raise BusinessException("数据不存在")
        update_data = vo.model_dump(exclude_unset=True)
        if 'account' in update_data and update_data['account'] != entity.account:
            if self.find_by_account(update_data['account']):
                raise BusinessException("账号已存在")
        apply_update(entity, update_data, extra_protected={'password'})
        self.dao.update(entity, user_id=await self._get_current_user_id(request))

    def download_template(self):
        return export_excel(
            make_template(ClientUser, extra_exclude={'password', 'last_login_at', 'last_login_ip', 'login_count'}),
            "C端用户导入模板", "C端用户数据"
        )

    def find_by_account(self, account: str) -> Optional[ClientUser]:
        return self.dao.find_by_account(account)

    def to_login_user_info(self, entity: Optional[ClientUser]) -> Optional[LoginUserInfo]:
        if not entity:
            return None
        return LoginUserInfo(
            id=entity.id,
            account=entity.account,
            password=entity.password,
            nickname=entity.nickname,
            avatar=entity.avatar,
            motto=entity.motto,
            gender=entity.gender,
            birthday=entity.birthday,
            email=entity.email,
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

    async def get_current_user(self, request: Request) -> Optional[Dict]:
        user_id = await HeiClientAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            return None
        entity = self.find_by_id(user_id)
        if not entity:
            return None
        return {
            "id": entity.id,
            "account": entity.account,
            "nickname": entity.nickname,
            "avatar": entity.avatar,
            "motto": entity.motto,
            "gender": entity.gender,
            "birthday": entity.birthday.isoformat() if entity.birthday else None,
            "email": entity.email,
            "github": entity.github,
            "status": entity.status,
            "last_login_at": entity.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if entity.last_login_at else None,
            "last_login_ip": entity.last_login_ip,
            "login_count": entity.login_count or 0,
        }

    async def update_profile(self, param: UpdateProfileParam, request: Request) -> None:
        user_id = await HeiClientAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            raise BusinessException("用户未登录")
        entity = self.dao.find_by_id(user_id)
        if not entity:
            raise BusinessException("用户不存在")
        update_data = param.model_dump(exclude_unset=True)
        apply_update(entity, update_data)
        self.dao.update(entity, user_id=user_id)

    async def update_avatar(self, param: UpdateAvatarParam, request: Request) -> None:
        user_id = await HeiClientAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            raise BusinessException("用户未登录")
        entity = self.dao.find_by_id(user_id)
        if not entity:
            raise BusinessException("用户不存在")
        entity.avatar = param.avatar
        self.dao.update(entity, user_id=user_id)

    async def update_password(self, param: UpdatePasswordParam, request: Request) -> None:
        user_id = await HeiClientAuthTool.getLoginIdDefaultNull(request)
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


class LoginUserApiProvider:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def get_login_user_info_by_id(self, user_id: str) -> Optional[LoginUserInfo]:
        db = self._session_factory()
        try:
            service = ClientUserService(db)
            entity = service.find_by_id(user_id)
            return service.to_login_user_info(entity)
        finally:
            db.close()

    def get_login_user_info_by_account(self, account: str) -> Optional[LoginUserInfo]:
        db = self._session_factory()
        try:
            service = ClientUserService(db)
            entity = service.find_by_account(account)
            return service.to_login_user_info(entity)
        finally:
            db.close()

    def get_login_user_info_by_email(self, email: str) -> Optional[LoginUserInfo]:
        db = self._session_factory()
        try:
            service = ClientUserService(db)
            entity = service.find_by_email(email)
            return service.to_login_user_info(entity)
        finally:
            db.close()

    async def get_current_login_user_info(self, request) -> Optional[LoginUserInfo]:
        user_id = await HeiClientAuthTool.getLoginIdAsString(request)
        if not user_id:
            return None
        return self.get_login_user_info_by_id(user_id)
