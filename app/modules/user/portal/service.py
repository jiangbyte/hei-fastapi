""" Author: Charlie """

from datetime import UTC, datetime
from pathlib import PurePosixPath
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.exceptions.business import AuthenticationError, BusinessError, NotFoundError
from app.core.security.password import hash_password, verify_password
from app.core.security.session import SessionPayload
from app.modules.auth.session_service import AccountSessionService
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.enums import AccountIdentityType
from app.modules.sys.file.schema import FileUploadRequest
from app.modules.sys.file.service import FileService
from app.modules.user.portal.repository import PortalUserProfileRepository
from app.modules.user.portal.schema import (
    PortalProfileUpsertPayload,
    PortalPublicProfileResponse,
    PortalPublicSpaceQuery,
    PortalUserCenterAvatarUpdateResponse,
    PortalUserCenterEmailUpdateRequest,
    PortalUserCenterPasswordUpdateRequest,
    PortalUserCenterPhoneUpdateRequest,
    PortalUserCenterProfileUpdateRequest,
)
from app.platform.db.transaction import transactional
from app.platform.storage.url import is_external_url, normalize_object_name, resolve_file_url

AVATAR_MAX_SIZE = 2 * 1024 * 1024
AVATAR_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class PortalUserProfileService:
    """门户账户资料服务，负责资料初始化和显式查询。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PortalUserProfileRepository(db)
        self.account_repo = AccountRepository(db)

    async def create_default_profile(self, account_id: str):
        """为门户账户创建默认资料记录，避免把关联维护下放给数据库。"""
        return await self.repo.create_default(account_id)

    async def upsert_profile(self, payload: PortalProfileUpsertPayload):
        """创建或更新门户资料。"""
        return await self.repo.upsert(payload)

    async def get_profile(self, account_id: str):
        """按账户 ID 查询门户资料。"""
        return await self.repo.get_by_account_id(account_id)

    async def get_public_profile(
        self, query: PortalPublicSpaceQuery
    ) -> PortalPublicProfileResponse:
        """查询门户用户公开主页资料，不返回联系方式和授权信息。"""
        account_id = query.account_id
        account = await self.account_repo.get_required(account_id)
        if account.account_type != AccountType.PORTAL.value:
            raise NotFoundError("Portal profile not found")
        profile = await self.repo.get_by_account_id(account_id)
        return PortalPublicProfileResponse(
            account_id=account_id,
            name=profile.name if profile else None,
            nickname=profile.nickname if profile else None,
            avatar=resolve_file_url(profile.avatar if profile else None),
            signature=profile.signature if profile else None,
        )

    async def update_current_profile(
        self,
        payload: PortalUserCenterProfileUpdateRequest,
        session: SessionPayload,
    ) -> None:
        profile = await self.repo.get_by_account_id(session.account_id)
        async with transactional(self.db):
            await self.repo.upsert(
                PortalProfileUpsertPayload(
                    account_id=session.account_id,
                    name=payload.name,
                    nickname=payload.nickname,
                    avatar=profile.avatar if profile else None,
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
        account = await self.account_repo.get_required(session.account_id)
        self._ensure_password(account.password_hash, payload.password)
        profile = await self.repo.get_by_account_id(session.account_id)
        if payload.phone_login_enabled and not str(payload.phone or "").strip():
            raise BusinessError("Phone login requires a phone")
        async with transactional(self.db):
            await self.account_repo.upsert_account_identity(
                session.account_id,
                AccountIdentityType.PHONE,
                payload.phone,
                enabled=payload.phone_login_enabled,
            )
            await self.repo.upsert(
                PortalProfileUpsertPayload(
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
        account = await self.account_repo.get_required(session.account_id)
        self._ensure_password(account.password_hash, payload.password)
        profile = await self.repo.get_by_account_id(session.account_id)
        if payload.email_login_enabled and not str(payload.email or "").strip():
            raise BusinessError("Email login requires an email")
        async with transactional(self.db):
            await self.account_repo.upsert_account_identity(
                session.account_id,
                AccountIdentityType.EMAIL,
                payload.email,
                enabled=payload.email_login_enabled,
            )
            await self.repo.upsert(
                PortalProfileUpsertPayload(
                    account_id=session.account_id,
                    name=profile.name if profile else None,
                    nickname=profile.nickname if profile else None,
                    avatar=profile.avatar if profile else None,
                    signature=profile.signature if profile else None,
                    phone=profile.phone if profile else None,
                    email=payload.email,
                )
            )

    def _ensure_password(self, password_hash: str, password: str) -> None:
        if not verify_password(password, password_hash):
            raise AuthenticationError("Invalid account or password")

    def _normalize_avatar_content_type(self, content_type: str) -> str:
        return (content_type or "").split(";")[0].strip().lower()

    def _ensure_avatar_file(self, content: bytes, content_type: str) -> None:
        if not content:
            raise BusinessError("Avatar file is empty")
        if len(content) > AVATAR_MAX_SIZE:
            raise BusinessError("Avatar file must be 2MB or smaller")
        if content_type not in AVATAR_CONTENT_TYPES:
            raise BusinessError("Avatar file must be a JPEG, PNG, or WebP image")

    def _build_avatar_object_name(self, content_type: str) -> str:
        now = datetime.now(UTC)
        extension = AVATAR_CONTENT_TYPES[content_type]
        return f"{now:%Y}/{now:%m}/{now:%d}/{uuid4().hex}{extension}"

    async def _delete_previous_avatar(
        self,
        previous_avatar: str | None,
        current_avatar: str,
    ) -> None:
        previous_object_name = normalize_object_name(previous_avatar)
        current_object_name = normalize_object_name(current_avatar)
        if (
            not previous_object_name
            or previous_object_name == current_object_name
            or is_external_url(previous_object_name)
        ):
            return
        await FileService(self.db).delete_by_object_name(previous_object_name)
