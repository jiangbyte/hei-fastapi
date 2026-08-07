"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:54
"""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.core.schema.base import IdQuery
from app.core.security.session import SessionPayload
from app.modules.message.conversation.repository import (
    MsgConversationRepository,
)
from app.modules.message.conversation.schema import (
    MsgConversationSchema,
    MuteConversationRequest,
    PinConversationRequest,
)
from app.modules.user.utils.profile import get_profile
from app.platform.storage.url import resolve_file_url


class MsgConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MsgConversationRepository(db)

    async def _enrich_conversation_list(
        self, schemas: list[MsgConversationSchema], session: SessionPayload
    ) -> None:
        """为 DIRECT 会话填充对方的名称和头像"""
        for schema in schemas:
            if schema.conversation_type != "DIRECT" or not schema.members:
                continue
            other = next(
                (
                    m
                    for m in schema.members
                    if not (
                        m.account_type == str(session.account_type)
                        and m.account_id == session.account_id
                    )
                ),
                None,
            )
            if other:
                profile = await get_profile(self.db, other.account_type, other.account_id)
                if profile:
                    if not schema.title:
                        schema.title = getattr(profile, "nickname", None) or getattr(
                            profile, "name", None
                        )
                    if not schema.avatar:
                        schema.avatar = resolve_file_url(getattr(profile, "avatar", None))

    # ── 偏好设置 ─────────────────────────────────────────────────────────────

    async def mute(self, payload: MuteConversationRequest, session: SessionPayload) -> None:
        await self.repo.set_muted(
            payload.conversation_id,
            str(session.account_type),
            session.account_id,
            payload.is_muted,
        )

    async def pin(self, payload: PinConversationRequest, session: SessionPayload) -> None:
        await self.repo.set_pinned(
            payload.conversation_id,
            str(session.account_type),
            session.account_id,
            payload.is_pinned,
        )

    # ── 成员操作 ──────────────────────────────────────────────────────────

    async def leave(self, query: IdQuery, session: SessionPayload) -> None:
        member = await self.repo.get_member(query.id, str(session.account_type), session.account_id)
        if member is None:
            raise NotFoundError("Conversation member not found")
        member.left_at = datetime.now(UTC)
        await self.db.flush()

    async def mark_read(self, query: IdQuery, session: SessionPayload) -> None:
        await self.repo.reset_unread(query.id, str(session.account_type), session.account_id)
        await self.db.commit()
