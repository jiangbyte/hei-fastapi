""" Author: Charlie """

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.schema.datetime import normalize_orm_datetimes
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.enums import AccountIdentityBindStatus
from app.modules.iam.schema import AccountIdentitySchema, SysAccountSchema
from app.modules.user.admin.repository import AdminUserProfileRepository
from app.modules.user.portal.repository import PortalUserProfileRepository
from app.platform.storage.url import resolve_file_url


class AccountQueryService:
    """IAM 与用户中心模块共用的账户读侧组装逻辑。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AccountRepository(db)

    async def build_account_schemas(self, accounts: list) -> list[SysAccountSchema]:
        account_ids = [account.id for account in accounts]
        identities = await self.repo.list_identities_by_account_ids(account_ids)
        admin_profiles = await AdminUserProfileRepository(self.db).list_by_account_ids(account_ids)
        portal_profiles = await PortalUserProfileRepository(self.db).list_by_account_ids(
            account_ids
        )
        identity_map: dict[str, list] = {}
        for identity in identities:
            identity_map.setdefault(identity.account_id, []).append(identity)
        admin_profile_map = {profile.account_id: profile for profile in admin_profiles}
        portal_profile_map = {profile.account_id: profile for profile in portal_profiles}

        items: list[SysAccountSchema] = []
        for account in accounts:
            account_identities = identity_map.get(account.id, [])
            primary_identity = next(
                (
                    item
                    for item in account_identities
                    if item.identity_type == "ACCOUNT" and item.is_primary
                ),
                None,
            ) or next(
                (item for item in account_identities if item.identity_type == "ACCOUNT"),
                None,
            )
            email_identity = next(
                (item for item in account_identities if item.identity_type == "EMAIL"),
                None,
            )
            phone_identity = next(
                (item for item in account_identities if item.identity_type == "PHONE"),
                None,
            )
            match account.account_type:
                case AccountType.ADMIN.value:
                    profile = admin_profile_map.get(account.id)
                case AccountType.PORTAL.value:
                    profile = portal_profile_map.get(account.id)
                case _:
                    profile = None
            normalize_orm_datetimes(account)
            if profile is not None:
                normalize_orm_datetimes(profile)
            for identity in account_identities:
                normalize_orm_datetimes(identity)
            items.append(
                SysAccountSchema(
                    id=account.id,
                    account=getattr(primary_identity, "identifier", ""),
                    account_type=account.account_type,
                    account_status=account.account_status,
                    name=getattr(profile, "name", None),
                    nickname=getattr(profile, "nickname", None),
                    avatar=resolve_file_url(getattr(profile, "avatar", None)),
                    signature=getattr(profile, "signature", None),
                    phone=getattr(profile, "phone", None),
                    email=getattr(profile, "email", None),
                    email_login_enabled=_identity_login_enabled(email_identity),
                    phone_login_enabled=_identity_login_enabled(phone_identity),
                    bio=getattr(profile, "bio", None),
                    level=getattr(profile, "level", None),
                    remark=getattr(profile, "remark", None),
                    email_identity=getattr(email_identity, "identifier", None),
                    phone_identity=getattr(phone_identity, "identifier", None),
                    email_identity_verified=bool(getattr(email_identity, "verified", False)),
                    phone_identity_verified=bool(getattr(phone_identity, "verified", False)),
                    email_identity_bind_status=getattr(email_identity, "bind_status", None),
                    phone_identity_bind_status=getattr(phone_identity, "bind_status", None),
                    identities=[
                        AccountIdentitySchema.model_validate(identity)
                        for identity in account_identities
                    ],
                    cancelled_at=account.cancelled_at,
                    cancelled_by=account.cancelled_by,
                    cancel_reason=account.cancel_reason,
                    last_login_ip=account.last_login_ip,
                    last_login_address=account.last_login_address,
                    last_login_time=account.last_login_time,
                    last_login_device=account.last_login_device,
                    latest_login_ip=account.latest_login_ip,
                    latest_login_address=account.latest_login_address,
                    latest_login_time=account.latest_login_time,
                    latest_login_device=account.latest_login_device,
                    created_at=account.created_at,
                    created_by=account.created_by,
                    updated_at=account.updated_at,
                    updated_by=account.updated_by,
                )
            )
        return items


def _identity_login_enabled(identity) -> bool:
    return bool(
        identity
        and identity.identifier
        and identity.verified
        and identity.bind_status == AccountIdentityBindStatus.BOUND.value
    )
