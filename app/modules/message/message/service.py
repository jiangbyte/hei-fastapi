""" Author: Charlie """

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.exceptions.business import BusinessError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import to_schema
from app.core.security.session import SessionPayload
from app.modules.message.conversation.service import MsgConversationService
from app.modules.message.message.model import MsgMessage
from app.modules.message.message.repository import MessageRepository
from app.modules.message.message.schema import (
    MessageAttachmentSchema,
    MessagePageQuery,
    MessageReadRequest,
    MessageSchema,
    MessageUnreadCountQuery,
    RevokeMessageRequest,
    SendMessageRequest,
    UnreadCountResponse,
)
from app.modules.user.utils.profile import get_profile, get_profiles_batch
from app.platform.db.transaction import transactional
from app.platform.storage.url import resolve_file_url


def _message_schema(item: MsgMessage, attachments: list) -> MessageSchema:
    schema = to_schema(MessageSchema, item)
    schema.attachments = [to_schema(MessageAttachmentSchema, att) for att in attachments]
    return schema


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MessageRepository(db)

    async def send(self, payload: SendMessageRequest, session: SessionPayload) -> MessageSchema:
        """发送消息；必要时自动创建会话（direct 含 participant_refs）。"""
        # 幂等重发：相同 client_msg_id 返回已有消息
        existing = await self.repo.find_by_client_msg_id(
            str(session.account_type),
            session.account_id,
            payload.client_msg_id,
        )
        if existing is not None:
            attachments = await self.repo.map_attachments([existing.id])
            schema = _message_schema(existing, attachments.get(existing.id, []))
            await self._enrich_message_schemas([schema])
            return schema

        push_ctx: dict | None = None
        async with transactional(self.db):
            conversation_id = payload.conversation_id
            if not conversation_id and payload.group_id:
                from app.modules.message.conversation.model import (
                    MsgConversation,
                    MsgConversationMember,
                )

                stmt = select(MsgConversation).where(
                    MsgConversation.group_id == payload.group_id,
                    MsgConversation.status == "ACTIVE",
                )
                conv = (await self.db.execute(stmt)).scalar_one_or_none()
                if conv is None:
                    # 为该群组自动创建会话
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

                    # 将所有活跃群成员加入会话
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
                    raise BusinessError(
                        "No conversation_id, group_id, or participant_refs provided"
                    )

            # ── 访问控制：会话须为 ACTIVE 且发送者须为成员 ──
            from app.modules.message.conversation.repository import MsgConversationRepository

            conv_repo = MsgConversationRepository(self.db)
            conv = await conv_repo.get_required(conversation_id)
            if conv.status != "ACTIVE":
                raise BusinessError("This conversation is no longer active")
            if (
                await conv_repo.get_member(
                    conversation_id, str(session.account_type), session.account_id
                )
                is None
            ):
                raise BusinessError("You are not a member of this conversation")

            # 未提供时从 profile 自动填充 sender_name（单次查询）
            sender_profile = await get_profile(
                self.db, str(session.account_type), session.account_id
            )
            sender_name = payload.sender_name
            if not sender_name and sender_profile:
                sender_name = getattr(sender_profile, "nickname", None) or getattr(
                    sender_profile, "name", None
                )
            payload.sender_name = sender_name

            msg = await self.repo.create_message(
                payload,
                conversation_id,
                sender_account_type=str(session.account_type),
                sender_account_id=session.account_id,
                sender_type="USER",
            )

            # 更新会话 last_message
            await conv_repo.update_last_message(conversation_id, msg.id, msg.created_at)
            # 为其他参与者递增未读数
            await conv_repo.increment_unread(
                conversation_id, str(session.account_type), session.account_id
            )

            attachments = await self.repo.map_attachments([msg.id])
            schema = _message_schema(msg, attachments.get(msg.id, []))

            if sender_profile:
                schema.sender_nickname = getattr(sender_profile, "nickname", None) or getattr(
                    sender_profile, "name", None
                )
                schema.sender_avatar = resolve_file_url(getattr(sender_profile, "avatar", None))

            members = await conv_repo.list_members(conversation_id)
            push_ctx = {
                "msg": msg,
                "schema": schema,
                "conversation_id": conversation_id,
                "sender_account_type": str(session.account_type),
                "sender_account_id": session.account_id,
                "targets": [
                    (m.account_type, m.account_id)
                    for m in members
                    if not (
                        m.account_type == str(session.account_type)
                        and m.account_id == session.account_id
                    )
                ],
            }

        # 仅在 DB 提交后扇出
        if push_ctx is not None:
            await _push_new_message_after_commit(push_ctx)
            return push_ctx["schema"]
        raise BusinessError("Failed to send message")

    async def reply(self, payload: SendMessageRequest, session: SessionPayload) -> MessageSchema:
        if not payload.parent_id:
            raise BusinessError("parent_id is required for reply")
        return await self.send(payload, session)

    async def revoke(self, payload: RevokeMessageRequest, session: SessionPayload) -> None:
        push_targets: list[tuple[str, str]] = []
        conversation_id = ""
        message_id = payload.message_id
        async with transactional(self.db):
            msg = await self.repo.get_required(payload.message_id)
            if msg.is_revoked:
                raise BusinessError("Message already revoked")
            if (
                msg.sender_account_type != str(session.account_type)
                or msg.sender_account_id != session.account_id
            ):
                raise BusinessError("Can only revoke your own messages")
            await self.repo.revoke_message(payload.message_id)
            conversation_id = msg.conversation_id
            from app.modules.message.conversation.repository import MsgConversationRepository

            members = await MsgConversationRepository(self.db).list_members(conversation_id)
            push_targets = [
                (m.account_type, m.account_id)
                for m in members
                if not (
                    m.account_type == str(session.account_type)
                    and m.account_id == session.account_id
                )
            ]

        from app.modules.message.im import PushEvent, im_router

        await im_router.push_many(
            push_targets,
            PushEvent.MESSAGE_REVOKED,
            {"message_id": message_id, "conversation_id": conversation_id},
            message_id=message_id,
            conversation_id=conversation_id,
        )

    async def page_messages(
        self, query: MessagePageQuery, session: SessionPayload | None = None
    ) -> PageData[MessageSchema]:
        """分页查询会话消息，最新优先。"""
        if session:
            from app.modules.message.conversation.repository import MsgConversationRepository

            member = await MsgConversationRepository(self.db).get_member(
                query.conversation_id, str(session.account_type), session.account_id
            )
            if member is None:
                raise BusinessError("Not a participant of this conversation")
        items, total = await self.repo.page_messages(
            query.conversation_id, query.offset, query.size
        )
        attachment_map = await self.repo.map_attachments([m.id for m in items])
        schemas = []
        for item in items:
            schemas.append(_message_schema(item, attachment_map.get(item.id, [])))
        # 填充发送者 profile
        await self._enrich_message_schemas(schemas)
        return build_page(query, total, schemas)

    async def _enrich_message_schemas(self, schemas: list[MessageSchema]) -> None:
        """批量填充消息发送者资料"""
        admin_ids: list[str] = []
        portal_ids: list[str] = []
        for s in schemas:
            if s.sender_account_type and s.sender_account_id:
                (admin_ids if s.sender_account_type == "ADMIN" else portal_ids).append(
                    s.sender_account_id
                )

        admin_profiles = (
            await get_profiles_batch(self.db, AccountType.ADMIN, admin_ids) if admin_ids else {}
        )
        portal_profiles = (
            await get_profiles_batch(self.db, AccountType.PORTAL, portal_ids) if portal_ids else {}
        )

        for s in schemas:
            if not s.sender_account_type or not s.sender_account_id:
                continue
            profiles = admin_profiles if s.sender_account_type == "ADMIN" else portal_profiles
            profile = profiles.get(s.sender_account_id)
            if profile:
                s.sender_nickname = getattr(profile, "nickname", None) or getattr(
                    profile, "name", None
                )
                s.sender_avatar = resolve_file_url(getattr(profile, "avatar", None))
                if not s.sender_name:
                    s.sender_name = s.sender_nickname

    async def mark_read(self, payload: MessageReadRequest, session: SessionPayload) -> None:
        """标记会话已读，取最新消息作为游标。"""
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

    async def unread_count(
        self, query: MessageUnreadCountQuery, session: SessionPayload
    ) -> UnreadCountResponse:
        from app.modules.message.conversation.repository import MsgConversationRepository

        member = await MsgConversationRepository(self.db).get_member(
            query.conversation_id, str(session.account_type), session.account_id
        )
        return UnreadCountResponse(unread_count=member.unread_count if member else 0)


async def _push_new_message_after_commit(ctx: dict) -> None:
    """DB 提交后推送 MESSAGE 事件。"""
    from app.modules.message.im import PushEvent, im_router

    schema: MessageSchema = ctx["schema"]
    payload = schema.model_dump(mode="json")
    await im_router.push_many(
        ctx["targets"],
        PushEvent.MESSAGE,
        payload,
        message_id=ctx["msg"].id,
        conversation_id=ctx["conversation_id"],
        skip=(ctx["sender_account_type"], ctx["sender_account_id"]),
    )
