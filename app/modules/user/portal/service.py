""" Author: Charlie

门户账户资料服务层：资料初始化、公开主页查询与用户中心维护。
"""

from datetime import UTC, datetime
from pathlib import PurePosixPath
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.db.transaction import transactional
from app.core.exceptions.business import AuthenticationError, BusinessError, NotFoundError
from app.core.schema.common_schema import IdNameResponse
from app.core.security.password import hash_password, verify_password
from app.core.security.session import SessionPayload
from app.core.storage.url import is_external_url, normalize_object_name, resolve_file_url
from app.modules.auth.session_service import AccountSessionService
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.enums import AccountIdentityType
from app.modules.sys.file.schema import FileUploadRequest
from app.modules.sys.file.service import FileService
from app.modules.user.portal.repository import ProfileUserPortalRepository
from app.modules.user.portal.schema import (
    PortalPublicProfileResponse,
    PortalPublicSpaceQuery,
    PortalUserCenterAvatarUpdateResponse,
    PortalUserCenterEmailUpdateRequest,
    PortalUserCenterPasswordUpdateRequest,
    PortalUserCenterPhoneUpdateRequest,
    PortalUserCenterProfileUpdateRequest,
    ProfileUserPortalUpsertPayload,
)

AVATAR_MAX_SIZE = 2 * 1024 * 1024  # 头像文件大小上限（2MB）
AVATAR_CONTENT_TYPES = {  # 允许的头像内容类型及其扩展名
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class ProfileUserPortalService:
    """门户账户资料服务，负责资料初始化和显式查询。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProfileUserPortalRepository(db)
        self.account_repo = AccountRepository(db)

    async def create_default_profile(self, account_id: str):
        """为门户账户创建默认资料记录，避免把关联维护下放给数据库。"""
        return await self.repo.create_default(account_id)

    async def upsert_profile(self, payload: ProfileUserPortalUpsertPayload):
        """创建或更新门户资料。"""
        return await self.repo.upsert(payload)

    async def get_profile(self, account_id: str):
        """按账户 ID 查询门户资料。"""
        return await self.repo.get_by_account_id(account_id)

    async def get_id_name_groups(
        self,
        role_ids: list[str],
        dept_ids: list[str],
        group_ids: list[str],
    ) -> tuple[list[IdNameResponse], list[IdNameResponse], list[IdNameResponse]]:
        """按 ID 列表批量查询角色/部门/群组的名称（对齐 hei-boot me 回显）。"""
        from app.modules.iam.dept.repository import DeptRepository
        from app.modules.iam.group.repository import GroupRepository
        from app.modules.iam.role.repository import RoleRepository

        roles = await RoleRepository(self.db).list_by_ids(role_ids)
        depts = await DeptRepository(self.db).list_by_ids(dept_ids)
        groups = await GroupRepository(self.db).list_by_ids(group_ids)
        role_map = {item.id: item.name for item in roles}
        dept_map = {item.id: item.name for item in depts}
        group_map = {item.id: item.name for item in groups}
        return (
            [
                IdNameResponse(id=item_id, name=role_map.get(item_id))
                for item_id in role_ids
            ],
            [
                IdNameResponse(id=item_id, name=dept_map.get(item_id))
                for item_id in dept_ids
            ],
            [
                IdNameResponse(id=item_id, name=group_map.get(item_id))
                for item_id in group_ids
            ],
        )

    async def get_public_profile(
        self, query: PortalPublicSpaceQuery
    ) -> PortalPublicProfileResponse:
        """查询门户用户公开主页资料，不返回联系方式和授权信息。

        无资料行时返回 404（对齐 hei-boot：selectById 无行抛 Profile not found）。
        """
        account_id = query.account_id
        await self.account_repo.get_required(account_id)
        profile = await self.repo.get_by_account_id(account_id)
        if profile is None:
            raise NotFoundError("Profile not found")
        return PortalPublicProfileResponse(
            account_id=account_id,
            name=profile.name,
            nickname=profile.nickname,
            avatar=resolve_file_url(profile.avatar) if profile.avatar else None,
            signature=profile.signature,
        )

    async def update_current_profile(
        self,
        payload: PortalUserCenterProfileUpdateRequest,
        session: SessionPayload,
    ) -> None:
        """更新当前门户用户个人资料（头像按载荷规范化写入，其余字段保留，对齐 hei-boot）。"""
        profile = await self.repo.get_by_account_id(session.account_id)
        avatar = (
            normalize_object_name(payload.avatar)
            if payload.avatar
            else (profile.avatar if profile else None)
        )
        async with transactional(self.db):
            await self.repo.upsert(
                ProfileUserPortalUpsertPayload(
                    account_id=session.account_id,
                    name=payload.name,
                    nickname=payload.nickname,
                    avatar=avatar,
                    signature=payload.signature,
                    phone=profile.phone if profile else None,
                    email=profile.email if profile else None,
                )
            )

    async def update_current_avatar(
        self,
        content: bytes,
        content_type: str,
        session: SessionPayload,
    ) -> PortalUserCenterAvatarUpdateResponse:
        """上传新头像并更新资料，随后清理旧头像文件。"""
        content_type = self._normalize_avatar_content_type(content_type)
        self._ensure_avatar_file(content, content_type)
        profile = await self.repo.get_by_account_id(session.account_id)
        previous_avatar = profile.avatar if profile else None
        avatar_object_name = self._build_avatar_object_name(content_type)
        uploaded = await FileService(self.db).upload(
            FileUploadRequest(
                filename=PurePosixPath(avatar_object_name).name,
                content=content,
                content_type=content_type,
                object_name=avatar_object_name,
            )
        )
        async with transactional(self.db):
            await self.repo.update_avatar(session.account_id, uploaded.object_name)
        await self._delete_previous_avatar(previous_avatar, uploaded.object_name)
        return PortalUserCenterAvatarUpdateResponse(
            avatar=resolve_file_url(uploaded.object_name) or uploaded.url,
            file_id=uploaded.id,
            object_name=uploaded.object_name,
            url=resolve_file_url(uploaded.object_name) or uploaded.url,
        )

    async def update_current_password(
        self,
        payload: PortalUserCenterPasswordUpdateRequest,
        session: SessionPayload,
    ) -> None:
        """校验旧密码/验证码后修改密码，并刷新账户会话。"""
        from app.core.config.enums import AccountType
        from app.modules.auth.password_change import verify_change_password
        from app.modules.iam.account.password_helper import validate_and_record_password

        account = await self.account_repo.get_required(session.account_id)
        await verify_change_password(
            self.db,
            account=account,
            account_type=AccountType.PORTAL,
            old_password=payload.old_password,
            otp_code=payload.otp_code,
        )
        async with transactional(self.db):
            await validate_and_record_password(
                self.db,
                session.account_id,
                payload.new_password,
                changed_by=session.account_id,
                change_reason="self_change",
                account=account,
            )
            await self.account_repo.update_password_hash(
                session.account_id,
                hash_password(payload.new_password),
            )
        await AccountSessionService(self.db).refresh_account_sessions(session.account_id)

    async def update_current_phone(
        self,
        payload: PortalUserCenterPhoneUpdateRequest,
        session: SessionPayload,
    ) -> None:
        """校验密码（绑定/换绑时另需 OTP）后更新当前门户用户手机号绑定。"""
        account = await self.account_repo.get_required(session.account_id)
        self._ensure_password(account.password_hash, payload.password)
        phone_value = str(payload.phone or "").strip()
        if phone_value:
            await self._consume_bind_code(
                AccountType.PORTAL, "PHONE", session.account_id, phone_value, payload.otp_code
            )
        profile = await self.repo.get_by_account_id(session.account_id)
        if payload.phone_login_enabled and not phone_value:
            raise BusinessError("Phone login requires a phone")
        async with transactional(self.db):
            await self.account_repo.upsert_account_identity(
                session.account_id,
                AccountIdentityType.PHONE,
                payload.phone,
                enabled=payload.phone_login_enabled,
            )
            await self.repo.upsert(
                ProfileUserPortalUpsertPayload(
                    account_id=session.account_id,
                    name=profile.name if profile else None,
                    nickname=profile.nickname if profile else None,
                    avatar=profile.avatar if profile else None,
                    signature=profile.signature if profile else None,
                    phone=payload.phone,
                    email=profile.email if profile else None,
                )
            )

    async def update_current_email(
        self,
        payload: PortalUserCenterEmailUpdateRequest,
        session: SessionPayload,
    ) -> None:
        """校验密码（绑定/换绑时另需 OTP）后更新当前门户用户邮箱绑定。"""
        account = await self.account_repo.get_required(session.account_id)
        self._ensure_password(account.password_hash, payload.password)
        email_value = str(payload.email or "").strip()
        if email_value:
            await self._consume_bind_code(
                AccountType.PORTAL, "EMAIL", session.account_id, email_value, payload.otp_code
            )
        profile = await self.repo.get_by_account_id(session.account_id)
        if payload.email_login_enabled and not email_value:
            raise BusinessError("Email login requires an email")
        async with transactional(self.db):
            await self.account_repo.upsert_account_identity(
                session.account_id,
                AccountIdentityType.EMAIL,
                payload.email,
                enabled=payload.email_login_enabled,
            )
            await self.repo.upsert(
                ProfileUserPortalUpsertPayload(
                    account_id=session.account_id,
                    name=profile.name if profile else None,
                    nickname=profile.nickname if profile else None,
                    avatar=profile.avatar if profile else None,
                    signature=profile.signature if profile else None,
                    phone=profile.phone if profile else None,
                    email=payload.email,
                )
            )

    async def _consume_bind_code(
        self,
        account_type: AccountType,
        channel: str,
        account_id: str,
        target: str,
        otp_code: str | None,
    ) -> None:
        """校验绑定验证码（一次性消费）。"""
        from app.modules.auth.service import AuthService

        await AuthService(self.db).consume_bind_code(
            account_type=account_type,
            channel=channel,
            account_id=account_id,
            target=target,
            code=otp_code,
        )

    def _ensure_password(self, password_hash: str, password: str) -> None:
        """校验明文密码与哈希是否匹配，失败抛出 AuthenticationError。"""
        if not verify_password(password, password_hash):
            raise AuthenticationError("Invalid account or password")

    def _normalize_avatar_content_type(self, content_type: str) -> str:
        """去除 content-type 中的参数（如 ; charset），并转为小写。"""
        return (content_type or "").split(";")[0].strip().lower()

    def _ensure_avatar_file(self, content: bytes, content_type: str) -> None:
        """校验头像文件非空、大小与类型合法。"""
        if not content:
            raise BusinessError("Avatar file is empty")
        if len(content) > AVATAR_MAX_SIZE:
            raise BusinessError("Avatar file must be 2MB or smaller")
        if content_type not in AVATAR_CONTENT_TYPES:
            raise BusinessError("Avatar file must be a JPEG, PNG, or WebP image")

    def _build_avatar_object_name(self, content_type: str) -> str:
        """按日期目录 + 随机名生成头像 object_name。"""
        now = datetime.now(UTC)
        extension = AVATAR_CONTENT_TYPES[content_type]
        return f"{now:%Y}/{now:%m}/{now:%d}/{uuid4().hex}{extension}"

    async def _delete_previous_avatar(
        self,
        previous_avatar: str | None,
        current_avatar: str,
    ) -> None:
        """删除被替换的旧头像文件（跳过空值、同对象与外部 URL）。"""
        previous_object_name = normalize_object_name(previous_avatar)
        current_object_name = normalize_object_name(current_avatar)
        if (
            not previous_object_name
            or previous_object_name == current_object_name
            or is_external_url(previous_object_name)
        ):
            return
        await FileService(self.db).delete_by_object_name(previous_object_name)
