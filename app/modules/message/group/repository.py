"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:52
"""

from datetime import UTC, datetime

from sqlalchemy import Select, delete, func, not_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.message.enums import (
    ConversationMemberRole,
    GroupJoinRequestStatus,
    GroupStatus,
)
from app.modules.message.group.model import (
    MsgGroup,
    MsgGroupJoinRequest,
    MsgGroupMember,
)
from app.modules.message.group.schema import (
    MsgGroupAdminPageQuery,
    MsgGroupCreateRequest,
    MsgGroupUpdateRequest,
)


class MsgGroupRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== MsgGroup CRUD ====================

    async def create(self, payload: MsgGroupCreateRequest) -> MsgGroup:
        entity = MsgGroup(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> MsgGroup | None:
        return await self.db.get(MsgGroup, entity_id)

    async def get_required(self, entity_id: str) -> MsgGroup:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("MsgGroup not found")
        return entity

    async def update(self, payload: MsgGroupUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        for key, value in payload.model_dump(exclude={"id"}).items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(entity_ids))
        stmt = select(MsgGroup.id).where(MsgGroup.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("MsgGroup not found")
        await self.db.execute(delete(MsgGroup).where(MsgGroup.id.in_(unique_ids)))

    async def page_admin(self, query: MsgGroupAdminPageQuery) -> tuple[list[MsgGroup], int]:
        stmt: Select[tuple[MsgGroup]] = select(MsgGroup)
        count_stmt = select(func.count(MsgGroup.id))
        filters = []
        if query.name:
            filters.append(MsgGroup.name.ilike(f"%{query.name}%"))
        if query.status is not None:
            filters.append(MsgGroup.status == query.status)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(MsgGroup.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    # ==================== 群组搜索 ====================

    async def search_groups(
        self, keyword: str, exclude_group_ids: list[str], limit: int = 50
    ) -> list[MsgGroup]:
        """按名称关键词搜索群组，排除已解散群组及指定群组 ID。"""
        stmt = (
            select(MsgGroup)
            .where(
                MsgGroup.name.ilike(f"%{keyword}%"),
                MsgGroup.status != GroupStatus.DISSOLVED.value,
            )
            .order_by(MsgGroup.member_count.desc())
            .limit(limit)
        )
        if exclude_group_ids:
            stmt = stmt.where(not_(MsgGroup.id.in_(exclude_group_ids)))
        return list((await self.db.execute(stmt)).scalars().all())

    # ==================== 群组成员 ====================

    async def list_my_groups(self, account_type: str, account_id: str) -> list[MsgGroup]:
        """列出当前用户所属群组（仅活跃群组，成员未退出）。"""
        stmt = (
            select(MsgGroup)
            .join(MsgGroupMember, MsgGroupMember.group_id == MsgGroup.id)
            .where(
                MsgGroupMember.account_type == account_type,
                MsgGroupMember.account_id == account_id,
                MsgGroupMember.left_at.is_(None),
                MsgGroup.status != GroupStatus.DISSOLVED.value,
            )
            .order_by(MsgGroup.id.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def add_member(
        self,
        group_id: str,
        account_type: str,
        account_id: str,
        role: str = ConversationMemberRole.MEMBER.value,
    ) -> MsgGroupMember:
        """向群组添加单个成员，返回成员实体。"""
        now = datetime.now(UTC)
        member = MsgGroupMember(
            group_id=group_id,
            account_type=account_type,
            account_id=account_id,
            role=role,
            joined_at=now,
        )
        self.db.add(member)
        await self.db.flush()
        return member

    async def add_members_batch(
        self,
        group_id: str,
        members: list[tuple[str, str]],
    ) -> list[MsgGroupMember]:
        """批量向群组添加成员。"""
        now = datetime.now(UTC)
        entities = [
            MsgGroupMember(
                group_id=group_id,
                account_type=acct_type,
                account_id=acct_id,
                role=ConversationMemberRole.MEMBER.value,
                joined_at=now,
            )
            for acct_type, acct_id in members
        ]
        self.db.add_all(entities)
        await self.db.flush()
        return entities

    async def get_member(
        self, group_id: str, account_type: str, account_id: str
    ) -> MsgGroupMember | None:
        """获取活跃成员（未退出）。"""
        stmt = select(MsgGroupMember).where(
            MsgGroupMember.group_id == group_id,
            MsgGroupMember.account_type == account_type,
            MsgGroupMember.account_id == account_id,
            MsgGroupMember.left_at.is_(None),
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_members(self, group_id: str) -> list[MsgGroupMember]:
        """列出活跃成员，按角色降序（OWNER > ADMIN > MEMBER）。"""
        stmt = (
            select(MsgGroupMember)
            .where(
                MsgGroupMember.group_id == group_id,
                MsgGroupMember.left_at.is_(None),
            )
            .order_by(MsgGroupMember.role.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def count_members(self, group_ids: list[str]) -> dict[str, int]:
        """批量统计指定群组的活跃成员数。"""
        if not group_ids:
            return {}
        stmt = (
            select(MsgGroupMember.group_id, func.count(MsgGroupMember.id))
            .where(
                MsgGroupMember.group_id.in_(group_ids),
                MsgGroupMember.left_at.is_(None),
            )
            .group_by(MsgGroupMember.group_id)
        )
        rows = list((await self.db.execute(stmt)).all())
        return {row[0]: row[1] for row in rows}

    async def remove_member(self, group_id: str, account_type: str, account_id: str) -> None:
        """通过设置 left_at 软删除成员。"""
        now = datetime.now(UTC)
        stmt = (
            update(MsgGroupMember)
            .where(
                MsgGroupMember.group_id == group_id,
                MsgGroupMember.account_type == account_type,
                MsgGroupMember.account_id == account_id,
                MsgGroupMember.left_at.is_(None),
            )
            .values(left_at=now)
        )
        await self.db.execute(stmt)

    async def update_member_role(
        self, group_id: str, account_type: str, account_id: str, role: str
    ) -> None:
        """更新成员角色。"""
        member = await self.get_member(group_id, account_type, account_id)
        if member is None:
            raise NotFoundError("Member not found in group")
        member.role = role
        await self.db.flush()

    async def increment_member_count(self, group_id: str, delta: int = 1) -> None:
        """递增群组的 member_count。"""
        stmt = select(MsgGroup).where(MsgGroup.id == group_id)
        group = (await self.db.execute(stmt)).scalar_one_or_none()
        if group is None:
            raise NotFoundError("MsgGroup not found")
        group.member_count += delta
        await self.db.flush()

    async def decrement_member_count(self, group_id: str) -> None:
        """递减群组的 member_count（减 1）。"""
        await self.increment_member_count(group_id, delta=-1)

    async def is_owner_or_admin(self, group_id: str, account_type: str, account_id: str) -> bool:
        """检查用户是否为群主或管理员成员。"""
        group = await self.get_required(group_id)
        if group.owner_account_type == account_type and group.owner_account_id == account_id:
            return True
        member = await self.get_member(group_id, account_type, account_id)
        if member is None:
            return False
        return member.role in (
            ConversationMemberRole.OWNER.value,
            ConversationMemberRole.ADMIN.value,
        )

    async def is_owner(self, group_id: str, account_type: str, account_id: str) -> bool:
        """检查用户是否为群主。"""
        group = await self.get_required(group_id)
        return group.owner_account_type == account_type and group.owner_account_id == account_id

    # ==================== 入群申请 ====================

    async def get_pending_join_request(
        self, group_id: str, applicant_type: str, applicant_id: str
    ) -> MsgGroupJoinRequest | None:
        """获取待处理的入群申请（尚未处理）。"""
        stmt = select(MsgGroupJoinRequest).where(
            MsgGroupJoinRequest.group_id == group_id,
            MsgGroupJoinRequest.applicant_type == applicant_type,
            MsgGroupJoinRequest.applicant_id == applicant_id,
            MsgGroupJoinRequest.status == GroupJoinRequestStatus.PENDING.value,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_any_join_request(
        self, group_id: str, applicant_type: str, applicant_id: str
    ) -> MsgGroupJoinRequest | None:
        """获取申请人在指定群组的最新入群申请（不限状态）。"""
        stmt = (
            select(MsgGroupJoinRequest)
            .where(
                MsgGroupJoinRequest.group_id == group_id,
                MsgGroupJoinRequest.applicant_type == applicant_type,
                MsgGroupJoinRequest.applicant_id == applicant_id,
            )
            .order_by(MsgGroupJoinRequest.created_at.desc())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_join_request_by_id(self, request_id: str) -> MsgGroupJoinRequest | None:
        return await self.db.get(MsgGroupJoinRequest, request_id)

    async def create_join_request(
        self,
        group_id: str,
        applicant_type: str,
        applicant_id: str,
        message: str | None = None,
    ) -> MsgGroupJoinRequest:
        """创建新的入群申请。"""
        entity = MsgGroupJoinRequest(
            group_id=group_id,
            applicant_type=applicant_type,
            applicant_id=applicant_id,
            message=message,
            status=GroupJoinRequestStatus.PENDING.value,
        )
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def list_pending_requests(self, group_ids: list[str]) -> list[MsgGroupJoinRequest]:
        """列出指定群组的所有待处理入群申请。"""
        if not group_ids:
            return []
        stmt = (
            select(MsgGroupJoinRequest)
            .where(
                MsgGroupJoinRequest.group_id.in_(group_ids),
                MsgGroupJoinRequest.status == GroupJoinRequestStatus.PENDING.value,
            )
            .order_by(MsgGroupJoinRequest.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_my_join_requests(
        self, applicant_type: str, applicant_id: str
    ) -> list[MsgGroupJoinRequest]:
        """列出指定申请人的所有入群申请。"""
        stmt = (
            select(MsgGroupJoinRequest)
            .where(
                MsgGroupJoinRequest.applicant_type == applicant_type,
                MsgGroupJoinRequest.applicant_id == applicant_id,
            )
            .order_by(MsgGroupJoinRequest.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def count_pending_requests(self, group_ids: list[str]) -> dict[str, int]:
        """批量统计指定群组的待处理入群申请数。"""
        if not group_ids:
            return {}
        stmt = (
            select(MsgGroupJoinRequest.group_id, func.count(MsgGroupJoinRequest.id))
            .where(
                MsgGroupJoinRequest.group_id.in_(group_ids),
                MsgGroupJoinRequest.status == GroupJoinRequestStatus.PENDING.value,
            )
            .group_by(MsgGroupJoinRequest.group_id)
        )
        rows = list((await self.db.execute(stmt)).all())
        return {row[0]: row[1] for row in rows}

    # ==================== 群组更新辅助 ====================

    async def update_group_fields(self, group_id: str, **kwargs) -> MsgGroup:
        """用给定 kwargs 更新群组字段，返回更新后的实体。"""
        group = await self.get_required(group_id)
        for key, value in kwargs.items():
            if value is not None:
                setattr(group, key, value)
        await self.db.flush()
        return group
