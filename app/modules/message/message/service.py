from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import BusinessError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import to_schema, to_schema_list
from app.core.security.session import SessionPayload
from app.platform.db.transaction import transactional
from app.platform.storage.url import resolve_file_url
from app.modules.message.message.model import MsgMessage
from app.modules.message.message.repository import MessageRepository
from app.modules.message.message.schema import (
    MessagePageQuery,
    MessageReadRequest,
    MessageSchema,
    MessageAttachmentSchema,
    MessageUnreadCountQuery,
    RevokeMessageRequest,
    SendMessageRequest,
    UnreadCountResponse,
)
from app.modules.message.conversation.service import MsgConversationService
from app.modules.message.offline.model import MsgOfflineQueue
from app.core.config.enums import AccountType
from app.modules.user.utils.profile import get_profiles_batch, get_profile


def _message_schema(item: MsgMessage, attachments: list) -> MessageSchema:
    schema = to_schema(MessageSchema, item)
    schema.attachments = [to_schema(MessageAttachmentSchema, att) for att in attachments]
    return schema


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MessageRepository(db)

    async def send(self, payload: SendMessageRequest, session: SessionPayload) -> MessageSchema:
        """Send a message. Auto-creates conversation if needed (direct with participant_refs)."""
        async with transactional(self.db):
            conversation_id = payload.conversation_id
            if not conversation_id and payload.group_id:
                from app.modules.message.conversation.model import MsgConversation, MsgConversationMember
                stmt = select(MsgConversation).where(
                    MsgConversation.group_id == payload.group_id,
                    MsgConversation.status == "ACTIVE",
                )
                conv = (await self.db.execute(stmt)).scalar_one_or_none()
                if conv is None:
                    # Auto-create conversation for this group
                    from app.modules.message.group.model import MsgGroup, MsgGroupMember
                    group_stmt = select(MsgGroup).where(MsgGroup.id == payload.group_id)
                    group = (await self.db.execute(group_stmt)).scalar_one_or_none()
                    if group is None:
                        raise BusinessError("Group not found")

                    conv = MsgConversation(
                        conversation_type="GROUP",
                        title=group.name,
                        group_id=group.id,
                        owner_account_type=group.owner_account_type,
                        owner_account_id=group.owner_account_id,
                        status="ACTIVE",
                    )
                    self.db.add(conv)
                    await self.db.flush()

                    # Add all active group members to the conversation
                    member_stmt = select(MsgGroupMember).where(
                        MsgGroupMember.group_id == payload.group_id,
                        MsgGroupMember.left_at.is_(None),
                    )
                    group_members = list((await self.db.execute(member_stmt)).scalars().all())
                    for gm in group_members:
                        conv_member = MsgConversationMember(
                            conversation_id=conv.id,
                            account_type=gm.account_type,
                            account_id=gm.account_id,
                            role=gm.role,
                        )
                        self.db.add(conv_member)
                    await self.db.flush()

                conversation_id = conv.id

            if not conversation_id:
                from app.modules.message.conversation.schema import CreateDirectConversationRequest

                conv_service = MsgConversationService(self.db)
                if payload.participant_refs:
                    ref = payload.participant_refs[0]
                    conv = await conv_service.create_direct(
                        CreateDirectConversationRequest(
                            account_type=ref.get("account_type", "PORTAL"),
                            account_id=ref.get("account_id"),
                        ),
                        session,
                    )
                    conversation_id = conv.id
                else:
                    raise BusinessError("No conversation_id, group_id, or participant_refs provided")

            # ── Access control: conversation must be ACTIVE and sender must be a member ──
            from app.modules.message.conversation.repository import MsgConversationRepository
            conv_repo = MsgConversationRepository(self.db)
            conv = await conv_repo.get_required(conversation_id)
            if conv.status != "ACTIVE":
                raise BusinessError("This conversation is no longer active")
            if await conv_repo.get_member(
                conversation_id, str(session.account_type), session.account_id
            ) is None:
                raise BusinessError("You are not a member of this conversation")

            # Auto-fill sender_name from profile if not provided
            sender_name = payload.sender_name
            if not sender_name:
                profile = await get_profile(self.db, str(session.account_type), session.account_id)
                if profile:
                    sender_name = getattr(profile, "nickname", None) or getattr(profile, "name", None)
            payload.sender_name = sender_name

            msg = await self.repo.create_message(
                payload, conversation_id,
                sender_account_type=str(session.account_type),
                sender_account_id=session.account_id,
                sender_type="USER",
            )

            # Update conversation last_message
            from app.modules.message.conversation.repository import MsgConversationRepository
            conv_repo = MsgConversationRepository(self.db)
            await conv_repo.update_last_message(conversation_id, msg.id, msg.created_at)
            # Increment unread for other participants
            await conv_repo.increment_unread(conversation_id, str(session.account_type), session.account_id)

            attachments = await self.repo.map_attachments([msg.id])
            schema = _message_schema(msg, attachments.get(msg.id, []))

            # Enrich sender profile
            sender_profile = await get_profile(self.db, str(session.account_type), session.account_id)
            if sender_profile:
                schema.sender_nickname = getattr(sender_profile, "nickname", None) or getattr(sender_profile, "name", None)
                schema.sender_avatar = resolve_file_url(getattr(sender_profile, "avatar", None))

            await _push_new_message(self.db, msg, schema, conversation_id,
                                    str(session.account_type), session.account_id)
            return schema

    async def reply(self, payload: SendMessageRequest, session: SessionPayload) -> MessageSchema:
        if not payload.parent_id:
            raise BusinessError("parent_id is required for reply")
        return await self.send(payload, session)

    async def revoke(self, payload: RevokeMessageRequest, session: SessionPayload) -> None:
        async with transactional(self.db):
            msg = await self.repo.get_required(payload.message_id)
            if msg.is_revoked:
                raise BusinessError("Message already revoked")
            if msg.sender_account_type != str(session.account_type) or msg.sender_account_id != session.account_id:
                raise BusinessError("Can only revoke your own messages")
            await self.repo.revoke_message(payload.message_id)

    async def page_messages(self, query: MessagePageQuery, session: SessionPayload | None = None) -> PageData[MessageSchema]:
        """Paginate messages in a conversation, newest first."""
        if session:
            from app.modules.message.conversation.repository import MsgConversationRepository
            member = await MsgConversationRepository(self.db).get_member(
                query.conversation_id, str(session.account_type), session.account_id
            )
            if member is None:
                raise BusinessError("Not a participant of this conversation")
        items, total = await self.repo.page_messages(query.conversation_id, query.pagination.offset, query.pagination.size)
        attachment_map = await self.repo.map_attachments([m.id for m in items])
        schemas = []
        for item in items:
            schemas.append(_message_schema(item, attachment_map.get(item.id, [])))
        # Enrich sender profiles
        await self._enrich_message_schemas(schemas)
        return build_page(query.pagination, total, schemas)

    async def _enrich_message_schemas(self, schemas: list[MessageSchema]) -> None:
        """批量填充消息发送者资料"""
        admin_ids: list[str] = []
        portal_ids: list[str] = []
        for s in schemas:
            if s.sender_account_type and s.sender_account_id:
                (admin_ids if s.sender_account_type == "ADMIN" else portal_ids).append(s.sender_account_id)

        admin_profiles = await get_profiles_batch(self.db, AccountType.ADMIN, admin_ids) if admin_ids else {}
        portal_profiles = await get_profiles_batch(self.db, AccountType.PORTAL, portal_ids) if portal_ids else {}

        for s in schemas:
            if not s.sender_account_type or not s.sender_account_id:
                continue
            profiles = admin_profiles if s.sender_account_type == "ADMIN" else portal_profiles
            profile = profiles.get(s.sender_account_id)
            if profile:
                s.sender_nickname = getattr(profile, "nickname", None) or getattr(profile, "name", None)
                s.sender_avatar = resolve_file_url(getattr(profile, "avatar", None))
                if not s.sender_name:
                    s.sender_name = s.sender_nickname

    async def mark_read(self, payload: MessageReadRequest, session: SessionPayload) -> None:
        """Mark conversation as read. Finds the latest message and uses it as cursor."""
        async with transactional(self.db):
            items, _ = await self.repo.page_messages(payload.conversation_id, 0, 1)
            if not items:
                return
            latest = items[0]
            await self.repo.mark_read(
                payload.conversation_id,
                str(session.account_type),
                session.account_id,
                latest.id,
                terminal_id=payload.terminal_id,
            )
            from app.modules.message.conversation.repository import MsgConversationRepository
            await MsgConversationRepository(self.db).reset_unread(
                payload.conversation_id, str(session.account_type), session.account_id
            )

    async def unread_count(self, query: MessageUnreadCountQuery, session: SessionPayload) -> UnreadCountResponse:
        count = await self.repo.count_unread(query.conversation_id, str(session.account_type), session.account_id)
        return UnreadCountResponse(unread_count=count)


async def _push_new_message(
    db: AsyncSession,
    message: MsgMessage,
    schema: MessageSchema,
    conversation_id: str,
    sender_account_type: str,
    sender_account_id: str,
) -> None:
    """Push new message to all conversation participants via WebSocket.
    Online users get it in real-time; offline users get a queue entry.
    Uses lazy imports to avoid circular dependencies.
    """
    from app.modules.message.conversation.repository import MsgConversationRepository
    from app.modules.message.websocket.handler import on_new_message, manager as ws_manager

    members = await MsgConversationRepository(db).list_members(conversation_id)

    payload = {
        "type": "new_message",
        "data": schema.model_dump(mode="json"),
    }

    now = datetime.now(timezone.utc)
    for member in members:
        if member.account_type == sender_account_type and member.account_id == sender_account_id:
            continue

        # Push via WS（本机 + Redis 跨 worker）
        try:
            await on_new_message(member.account_type, member.account_id, payload)
        except Exception:
            import logging

            logging.getLogger(__name__).warning(
                "WS push failed for %s/%s",
                member.account_type,
                member.account_id,
                exc_info=True,
            )

        # 全局不在线时写入离线队列（前端按 message.id 去重）
        globally_online = await ws_manager.is_globally_online(
            member.account_type, member.account_id
        )
        if not globally_online:
            offline = MsgOfflineQueue(
                message_id=message.id,
                conversation_id=conversation_id,
                target_account_type=member.account_type,
                target_account_id=member.account_id,
                event_type="NEW_MESSAGE",
                event_payload=payload,
                status="PENDING",
                created_at=now,
            )
            db.add(offline)

    if db.new:  # flush if we added any offline entries
        await db.flush()
