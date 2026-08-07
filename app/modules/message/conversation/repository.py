"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:54
"""

from datetime import UTC, datetime

from sqlalchemy import Select, and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.core.response.pagination import PageQuery
from app.modules.message.conversation.model import (
    MsgConversation,
    MsgConversationMember,
)
from app.modules.message.conversation.schema import (
    MsgConversationAdminPageQuery,
    MsgConversationCreateRequest,
    MsgConversationUpdateRequest,
)


class MsgConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── 生成的 CRUD ─────────────────────────────────────────────────────────

    async def create(self, payload: MsgConversationCreateRequest) -> MsgConversation:
        # 仅写入模型列，避免响应态字段（如 last_message）进入构造参数
        cols = MsgConversation.__table__.columns.keys()
        data = {k: v for k, v in payload.model_dump().items() if k in cols}
        entity = MsgConversation(**data)
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> MsgConversation | None:
        return await self.db.get(MsgConversation, entity_id)

    async def get_required(self, entity_id: str) -> MsgConversation:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("MsgConversation not found")
        return entity

    async def update(self, payload: MsgConversationUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        for key, value in payload.model_dump(exclude={"id"}).items():
            if key not in MsgConversation.__table__.columns:
                continue
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(entity_ids))
        stmt = select(MsgConversation.id).where(MsgConversation.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("MsgConversation not found")
        await self.db.execute(delete(MsgConversation).where(MsgConversation.id.in_(unique_ids)))

    async def page_admin(
        self, query: MsgConversationAdminPageQuery
    ) -> tuple[list[MsgConversation], int]:
        stmt: Select[tuple[MsgConversation]] = select(MsgConversation)
        count_stmt = select(func.count(MsgConversation.id))
        filters = []
        if query.title:
            filters.append(MsgConversation.title.ilike(f"%{query.title}%"))
        if query.status is not None:
            filters.append(MsgConversation.status == query.status)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(MsgConversation.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    # ── 会话查询 ────────────────────────────────────────────────────

    async def find_direct_conversation(
        self,
        account_type1: str,
        account_id1: str,
        account_type2: str,
        account_id2: str,
    ) -> MsgConversation | None:
        """查找两位用户之间已存在的 DIRECT 会话。"""
        # 子查询：包含双方参与者的会话
        member1 = select(MsgConversationMember.conversation_id).where(
            and_(
                MsgConversationMember.account_type == account_type1,
                MsgConversationMember.account_id == account_id1,
                MsgConversationMember.left_at.is_(None),
            )
        )
        member2 = select(MsgConversationMember.conversation_id).where(
            and_(
                MsgConversationMember.account_type == account_type2,
                MsgConversationMember.account_id == account_id2,
                MsgConversationMember.left_at.is_(None),
            )
        )
        stmt = (
            select(MsgConversation)
            .where(
                and_(
                    MsgConversation.conversation_type == "DIRECT",
                    MsgConversation.status == "ACTIVE",
                    MsgConversation.id.in_(member1),
                    MsgConversation.id.in_(member2),
                )
            )
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def list_my_conversations(
        self, account_type: str, account_id: str, page: PageQuery | None = None
    ) -> tuple[list[MsgConversation], int]:
        """列出用户的会话，按 last_message_at 降序，置顶优先。"""
        member_subq = select(MsgConversationMember.conversation_id).where(
            and_(
                MsgConversationMember.account_type == account_type,
                MsgConversationMember.account_id == account_id,
                MsgConversationMember.left_at.is_(None),
            )
        )
        # 统计总数
        count_stmt = (
            select(func.count())
            .select_from(MsgConversation)
            .where(MsgConversation.id.in_(member_subq))
        )
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(MsgConversation)
            .where(MsgConversation.id.in_(member_subq))
            .order_by(MsgConversation.last_message_at.desc().nullslast())
        )
        if page:
            stmt = stmt.offset(page.offset).limit(page.size)
        rows = list((await self.db.execute(stmt)).scalars().all())
        return rows, total

    # ── 成员管理 ───────────────────────────────────────────────────────

    async def add_member(
        self,
        conversation_id: str,
        account_type: str,
        account_id: str,
        role: str = "MEMBER",
    ) -> MsgConversationMember:
        member = MsgConversationMember(
            conversation_id=conversation_id,
            account_type=account_type,
            account_id=account_id,
            role=role,
            joined_at=datetime.now(UTC),
        )
        self.db.add(member)
        await self.db.flush()
        return member

    async def remove_member(self, conversation_id: str, account_type: str, account_id: str) -> None:
        """通过设置 left_at 软删除会话成员。"""
        await self.db.execute(
            update(MsgConversationMember)
            .where(
                MsgConversationMember.conversation_id == conversation_id,
                MsgConversationMember.account_type == account_type,
                MsgConversationMember.account_id == account_id,
                MsgConversationMember.left_at.is_(None),
            )
            .values(left_at=datetime.now(UTC))
        )

    async def get_member(
        self, conversation_id: str, account_type: str, account_id: str
    ) -> MsgConversationMember | None:
        stmt = select(MsgConversationMember).where(
            and_(
                MsgConversationMember.conversation_id == conversation_id,
                MsgConversationMember.account_type == account_type,
                MsgConversationMember.account_id == account_id,
                MsgConversationMember.left_at.is_(None),
            )
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def list_members(self, conversation_id: str) -> list[MsgConversationMember]:
        stmt = select(MsgConversationMember).where(
            and_(
                MsgConversationMember.conversation_id == conversation_id,
                MsgConversationMember.left_at.is_(None),
            )
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_members_for_conversations(
        self, conversation_ids: list[str]
    ) -> dict[str, list[MsgConversationMember]]:
        if not conversation_ids:
            return {}
        stmt = select(MsgConversationMember).where(
            and_(
                MsgConversationMember.conversation_id.in_(list(dict.fromkeys(conversation_ids))),
                MsgConversationMember.left_at.is_(None),
            )
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        result: dict[str, list[MsgConversationMember]] = {}
        for row in rows:
            result.setdefault(row.conversation_id, []).append(row)
        return result

    async def map_my_membership(
        self, conversation_ids: list[str], account_type: str, account_id: str
    ) -> dict[str, MsgConversationMember]:
        if not conversation_ids:
            return {}
        stmt = select(MsgConversationMember).where(
            and_(
                MsgConversationMember.conversation_id.in_(list(dict.fromkeys(conversation_ids))),
                MsgConversationMember.account_type == account_type,
                MsgConversationMember.account_id == account_id,
                MsgConversationMember.left_at.is_(None),
            )
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        return {row.conversation_id: row for row in rows}

    # ── 消息追踪 ────────────────────────────────────────────────────────

    async def update_last_message(
        self, conversation_id: str, message_id: str, message_at: datetime
    ) -> None:
        await self.db.execute(
            update(MsgConversation)
            .where(MsgConversation.id == conversation_id)
            .values(last_message_id=message_id, last_message_at=message_at)
        )
        await self.db.flush()

    async def increment_unread(
        self, conversation_id: str, exclude_account_type: str, exclude_account_id: str
    ) -> None:
        await self.db.execute(
            update(MsgConversationMember)
            .where(
                and_(
                    MsgConversationMember.conversation_id == conversation_id,
                    MsgConversationMember.left_at.is_(None),
                    ~and_(
                        MsgConversationMember.account_type == exclude_account_type,
                        MsgConversationMember.account_id == exclude_account_id,
                    ),
                )
            )
            .values(unread_count=MsgConversationMember.unread_count + 1)
        )
        await self.db.flush()

    async def reset_unread(self, conversation_id: str, account_type: str, account_id: str) -> None:
        await self.db.execute(
            update(MsgConversationMember)
            .where(
                and_(
                    MsgConversationMember.conversation_id == conversation_id,
                    MsgConversationMember.account_type == account_type,
                    MsgConversationMember.account_id == account_id,
                    MsgConversationMember.left_at.is_(None),
                )
            )
            .values(unread_count=0)
        )
        await self.db.flush()

    async def set_last_read(
        self, conversation_id: str, account_type: str, account_id: str, message_id: str
    ) -> None:
        await self.db.execute(
            update(MsgConversationMember)
            .where(
                and_(
                    MsgConversationMember.conversation_id == conversation_id,
                    MsgConversationMember.account_type == account_type,
                    MsgConversationMember.account_id == account_id,
                    MsgConversationMember.left_at.is_(None),
                )
            )
            .values(last_read_message_id=message_id, last_read_at=datetime.now(UTC))
        )
        await self.db.flush()

    # ── 偏好设置 ─────────────────────────────────────────────────────────────

    async def set_muted(
        self, conversation_id: str, account_type: str, account_id: str, muted: bool
    ) -> None:
        await self.db.execute(
            update(MsgConversationMember)
            .where(
                and_(
                    MsgConversationMember.conversation_id == conversation_id,
                    MsgConversationMember.account_type == account_type,
                    MsgConversationMember.account_id == account_id,
                    MsgConversationMember.left_at.is_(None),
                )
            )
            .values(is_muted=muted)
        )
        await self.db.flush()

    async def set_pinned(
        self, conversation_id: str, account_type: str, account_id: str, pinned: bool
    ) -> None:
        await self.db.execute(
            update(MsgConversationMember)
            .where(
                and_(
                    MsgConversationMember.conversation_id == conversation_id,
                    MsgConversationMember.account_type == account_type,
                    MsgConversationMember.account_id == account_id,
                    MsgConversationMember.left_at.is_(None),
                )
            )
            .values(is_pinned=pinned)
        )
        await self.db.flush()
