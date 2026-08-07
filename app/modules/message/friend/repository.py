"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:53
"""

from datetime import UTC, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.message.friend.model import (
    MsgFriend,
    MsgFriendRequest,
)


class MsgFriendRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, entity_id: str) -> MsgFriend | None:
        return await self.db.get(MsgFriend, entity_id)

    async def get_required(self, entity_id: str) -> MsgFriend:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("MsgFriend not found")
        return entity

    # ── 好友关系查询 ──────────────────────────────────────────────────

    async def find_friendship(
        self, account_type: str, account_id: str, friend_type: str, friend_id: str
    ) -> MsgFriend | None:
        """查找 ACTIVE 状态的双向好友记录（不区分方向）"""
        stmt = select(MsgFriend).where(
            and_(
                MsgFriend.status == "ACTIVE",
                or_(
                    and_(
                        MsgFriend.account_type == account_type,
                        MsgFriend.account_id == account_id,
                        MsgFriend.friend_account_type == friend_type,
                        MsgFriend.friend_account_id == friend_id,
                    ),
                    and_(
                        MsgFriend.account_type == friend_type,
                        MsgFriend.account_id == friend_id,
                        MsgFriend.friend_account_type == account_type,
                        MsgFriend.friend_account_id == account_id,
                    ),
                ),
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_my_friends(self, account_type: str, account_id: str) -> list[MsgFriend]:
        """列出当前用户的所有 ACTIVE 好友关系"""
        stmt = (
            select(MsgFriend)
            .where(
                and_(
                    MsgFriend.status == "ACTIVE",
                    MsgFriend.account_type == account_type,
                    MsgFriend.account_id == account_id,
                )
            )
            .order_by(MsgFriend.friend_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def soft_delete(self, entity_id: str) -> None:
        """软删除好友关系：状态设为 DELETED"""
        entity = await self.get_required(entity_id)
        entity.status = "DELETED"
        entity.updated_at = datetime.now(UTC)
        await self.db.flush()

    async def delete_bidirectional(
        self, account_type: str, account_id: str, friend_type: str, friend_id: str
    ) -> None:
        """双向软删除：标记两个方向的记录为 DELETED"""
        stmt = select(MsgFriend).where(
            or_(
                and_(
                    MsgFriend.account_type == account_type,
                    MsgFriend.account_id == account_id,
                    MsgFriend.friend_account_type == friend_type,
                    MsgFriend.friend_account_id == friend_id,
                ),
                and_(
                    MsgFriend.account_type == friend_type,
                    MsgFriend.account_id == friend_id,
                    MsgFriend.friend_account_type == account_type,
                    MsgFriend.friend_account_id == account_id,
                ),
            )
        )
        records = list((await self.db.execute(stmt)).scalars().all())
        now = datetime.now(UTC)
        for record in records:
            record.status = "DELETED"
            record.updated_at = now
        await self.db.flush()

    async def update_remark(self, entity_id: str, remark: str | None) -> None:
        """更新好友备注"""
        entity = await self.get_required(entity_id)
        entity.remark = remark
        entity.updated_at = datetime.now(UTC)
        await self.db.flush()

    # ── 好友申请查询 ──────────────────────────────────────────────

    async def create_friend_request(self, payload: dict) -> MsgFriendRequest:
        """创建好友申请记录"""
        entity = MsgFriendRequest(**payload)
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_friend_request_by_id(self, request_id: str) -> MsgFriendRequest | None:
        """按 ID 查询好友申请"""
        return await self.db.get(MsgFriendRequest, request_id)

    async def get_friend_request_required(self, request_id: str) -> MsgFriendRequest:
        entity = await self.get_friend_request_by_id(request_id)
        if entity is None:
            raise NotFoundError("Friend request not found")
        return entity

    async def find_pending_request(
        self, applicant_type: str, applicant_id: str, recipient_type: str, recipient_id: str
    ) -> MsgFriendRequest | None:
        """查找待处理的好友申请"""
        stmt = select(MsgFriendRequest).where(
            and_(
                MsgFriendRequest.applicant_type == applicant_type,
                MsgFriendRequest.applicant_id == applicant_id,
                MsgFriendRequest.recipient_type == recipient_type,
                MsgFriendRequest.recipient_id == recipient_id,
                MsgFriendRequest.status == "PENDING",
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def find_any_request(
        self, applicant_type: str, applicant_id: str, recipient_type: str, recipient_id: str
    ) -> MsgFriendRequest | None:
        """查找任意状态的好友申请记录（不限制 status）"""
        stmt = select(MsgFriendRequest).where(
            and_(
                MsgFriendRequest.applicant_type == applicant_type,
                MsgFriendRequest.applicant_id == applicant_id,
                MsgFriendRequest.recipient_type == recipient_type,
                MsgFriendRequest.recipient_id == recipient_id,
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def find_friend_requests_by_recipient(
        self, recipient_type: str, recipient_id: str, status: str = "PENDING"
    ) -> list[MsgFriendRequest]:
        """查询发给某人的好友申请（默认只查待处理的）"""
        stmt = (
            select(MsgFriendRequest)
            .where(
                and_(
                    MsgFriendRequest.recipient_type == recipient_type,
                    MsgFriendRequest.recipient_id == recipient_id,
                    MsgFriendRequest.status == status,
                )
            )
            .order_by(MsgFriendRequest.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def find_friend_requests_by_applicant(
        self, applicant_type: str, applicant_id: str
    ) -> list[MsgFriendRequest]:
        """查询某人发出的所有好友申请"""
        stmt = (
            select(MsgFriendRequest)
            .where(
                and_(
                    MsgFriendRequest.applicant_type == applicant_type,
                    MsgFriendRequest.applicant_id == applicant_id,
                )
            )
            .order_by(MsgFriendRequest.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def find_all_requests_for_user(
        self, account_type: str, account_id: str
    ) -> list[MsgFriendRequest]:
        """查询与用户相关的所有好友申请（发出的 + 收到的）"""
        stmt = (
            select(MsgFriendRequest)
            .where(
                or_(
                    and_(
                        MsgFriendRequest.applicant_type == account_type,
                        MsgFriendRequest.applicant_id == account_id,
                    ),
                    and_(
                        MsgFriendRequest.recipient_type == account_type,
                        MsgFriendRequest.recipient_id == account_id,
                    ),
                )
            )
            .order_by(MsgFriendRequest.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def count_pending_requests(self, recipient_type: str, recipient_id: str) -> int:
        """统计待处理的好友申请数量"""
        stmt = select(func.count(MsgFriendRequest.id)).where(
            and_(
                MsgFriendRequest.recipient_type == recipient_type,
                MsgFriendRequest.recipient_id == recipient_id,
                MsgFriendRequest.status == "PENDING",
            )
        )
        return (await self.db.execute(stmt)).scalar_one()
