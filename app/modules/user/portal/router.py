""" Author: Charlie

门户用户中心路由：当前账户信息、资料、头像、密码、手机与邮箱维护，及公开主页。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.schema import ApiResponse, success
from app.core.security.session import SessionPayload
from app.core.security.transport import decrypt_passwords
from app.core.storage.url import resolve_file_url
from app.deps.auth import get_current_session, require_account_type
from app.deps.db import get_db_session
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.enums import AccountIdentityBindStatus
from app.modules.user.portal.schema import (
    PortalProfileResponse,
    PortalPublicProfileResponse,
    PortalPublicSpaceQuery,
    PortalUserCenterAvatarUpdateResponse,
    PortalUserCenterEmailUpdateRequest,
    PortalUserCenterPasswordUpdateRequest,
    PortalUserCenterPhoneUpdateRequest,
    PortalUserCenterProfileUpdateRequest,
)
from app.modules.user.portal.service import AVATAR_MAX_SIZE, PortalUserProfileService
from app.modules.user.schema import PortalMeResponse

router = APIRouter()


@router.get(
    "/v1/portal/me",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[PortalMeResponse],
)
async def get_me(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PortalMeResponse]:
    """查询当前门户用户的扩展资料信息。"""
    account_repo = AccountRepository(db)
    await account_repo.get_required(session.account_id)
    identities = await account_repo.list_identities_by_account_ids([session.account_id])
    primary_identity = next(
        (item for item in identities if item.identity_type == "ACCOUNT" and item.is_primary),
        None,
    ) or next((item for item in identities if item.identity_type == "ACCOUNT"), None)
    email_identity = next((item for item in identities if item.identity_type == "EMAIL"), None)
    phone_identity = next((item for item in identities if item.identity_type == "PHONE"), None)
    profile = await PortalUserProfileService(db).get_profile(session.account_id)
    avatar = resolve_file_url(profile.avatar if profile else None)
    return success(
        PortalMeResponse(
            account_id=session.account_id,
            account=getattr(primary_identity, "identifier", ""),
            account_type=AccountType(str(session.account_type)),
            name=profile.name if profile else None,
            nickname=profile.nickname if profile else None,
            avatar=avatar,
            role_ids=session.role_ids,
            dept_ids=session.dept_ids,
            group_ids=session.group_ids,
            permission_keys=session.permission_keys,
            profile=PortalProfileResponse(
                account_id=session.account_id,
                name=profile.name if profile else None,
                nickname=profile.nickname if profile else None,
                avatar=avatar,
                signature=profile.signature if profile else None,
                phone=profile.phone if profile else None,
                email=profile.email if profile else None,
                phone_login_enabled=_identity_login_enabled(phone_identity),
                email_login_enabled=_identity_login_enabled(email_identity),
                created_at=profile.created_at if profile else None,
                updated_at=profile.updated_at if profile else None,
            ),
        )
    )


@router.post(
    "/v1/portal/user-center/profile/update",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[None],
)
async def update_user_center_profile(
    payload: PortalUserCenterProfileUpdateRequest,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    """更新当前门户用户个人资料。"""
    await PortalUserProfileService(db).update_current_profile(payload, session)
    return success()


@router.post(
    "/v1/portal/user-center/avatar/upload",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[PortalUserCenterAvatarUpdateResponse],
)
async def upload_user_center_avatar(
    file: Annotated[UploadFile, File(...)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PortalUserCenterAvatarUpdateResponse]:
    """上传并更新当前门户用户头像。"""
    content = await file.read(AVATAR_MAX_SIZE + 1)
    return success(
        await PortalUserProfileService(db).update_current_avatar(
            content=content,
            content_type=file.content_type or "",
            session=session,
        )
    )


@router.post(
    "/v1/portal/user-center/password/send-code",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[None],
)
async def send_user_center_password_code(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    """向当前门户用户发送改密验证码。"""
    from app.modules.auth.password_change import send_change_password_code
    from app.modules.iam.account.repository import AccountRepository

    account = await AccountRepository(db).get_required(session.account_id)
    await send_change_password_code(
        db, account=account, account_type=AccountType.PORTAL
    )
    return success()


@router.post(
    "/v1/portal/user-center/password/update",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[None],
)
async def update_user_center_password(
    payload: PortalUserCenterPasswordUpdateRequest,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    """修改当前门户用户密码。"""
    old_password, new_password = await decrypt_passwords(
        payload.password_key_id,
        payload.old_password,
        payload.new_password,
    )
    await PortalUserProfileService(db).update_current_password(
        payload.model_copy(
            update={
                "old_password": old_password,
                "new_password": new_password or "",
            }
        ),
        session,
    )
    return success()


@router.post(
    "/v1/portal/user-center/phone/update",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[None],
)
async def update_user_center_phone(
    payload: PortalUserCenterPhoneUpdateRequest,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    """更新当前门户用户手机号绑定。"""
    password = (await decrypt_passwords(payload.password_key_id, payload.password))[0]
    await PortalUserProfileService(db).update_current_phone(
        payload.model_copy(update={"password": password or ""}),
        session,
    )
    return success()


@router.post(
    "/v1/portal/user-center/email/update",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[None],
)
async def update_user_center_email(
    payload: PortalUserCenterEmailUpdateRequest,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    """更新当前门户用户邮箱绑定。"""
    password = (await decrypt_passwords(payload.password_key_id, payload.password))[0]
    await PortalUserProfileService(db).update_current_email(
        payload.model_copy(update={"password": password or ""}),
        session,
    )
    return success()


@router.get(
    "/v1/portal/spaces/detail",
    response_model=ApiResponse[PortalPublicProfileResponse],
)
async def get_public_space(
    query: Annotated[PortalPublicSpaceQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PortalPublicProfileResponse]:
    """查询门户用户公开主页资料。"""
    return success(await PortalUserProfileService(db).get_public_profile(query))


def _identity_login_enabled(identity) -> bool:
    """判断绑定身份是否可用于登录（已绑定且已验证）。"""
    return bool(
        identity
        and identity.identifier
        and identity.verified
        and identity.bind_status == AccountIdentityBindStatus.BOUND.value
    )
