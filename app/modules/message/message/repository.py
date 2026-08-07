""" Author: Charlie """

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.message.message.model import MsgMessage, MsgMessageAttachment, MsgMessageRead
from app.modules.message.message.schema import SendMessageRequest


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self,
        payload: SendMessageRequest,
        conversation_id: str,
        sender_account_type: str | None,
        sender_account_id: str | None,
        sender_type: str = "USER",
    ) -> MsgMessage:
        from app.platform.id_generator.snowflake import generate_snowflake_id

        now = datetime.now(UTC)
        msg = MsgMessage(
            id=generate_snowflake_id(),
            conversation_id=conversation_id,
            client_msg_id=payload.client_msg_id,
            msg_type=payload.msg_type or "TEXT",
            parent_id=payload.parent_id,
            sender_type=sender_type,
            sender_account_type=sender_account_type,
            sender_account_id=sender_account_id,
            sender_name=payload.sender_name,
            content=payload.content,
            content_type=payload.content_type,
            reply_count=0,
            is_revoked=False,
            extra=payload.extra,
            created_at=now,
        )
        self.db.add(msg)
        await self.db.flush()

        # 保存附件
        for _i, att in enumerate(payload.attachments):
            self.db.add(
                MsgMessageAttachment(
                    id=generate_snowflake_id(),
                    message_id=msg.id,
                    file_id=att.file_id,
                    name=att.name,
                    url=att.url,
                    content_type=att.content_type,
                    size=att.size,
                    attachment_type=att.attachment_type or "FILE",
                    thumbnail_url=att.thumbnail_url,
                    sort=att.sort,
                    extra=att.extra,
                )
            )
        return msg

    async def get_by_id(self, message_id: str) -> MsgMessage | None:
        return await self.db.get(MsgMessage, message_id)

    async def find_by_client_msg_id(
        self,
        sender_account_type: str,
        sender_account_id: str,
        client_msg_id: str,
    ) -> MsgMessage | None:
        stmt = select(MsgMessage).where(
            MsgMessage.sender_account_type == sender_account_type,
            MsgMessage.sender_account_id == sender_account_id,
            MsgMessage.client_msg_id == client_msg_id,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_required(self, message_id: str) -> MsgMessage:
        entity = await self.get_by_id(message_id)
        if entity is None:
            raise NotFoundError("MsgMessage not found")
        return entity

    async def revoke_message(self, message_id: str) -> None:
        now = datetime.now(UTC)
        await self.db.execute(
            update(MsgMessage)
            .where(MsgMessage.id == message_id)
            .values(is_revoked=True, revoked_at=now)
        )
        await self.db.flush()

    async def page_messages(
        self, conversation_id: str, offset: int, size: int
    ) -> tuple[list[MsgMessage], int]:
        stmt = (
            select(MsgMessage)
            .where(MsgMessage.conversation_id == conversation_id)
            .order_by(MsgMessage.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (
            await self.db.execute(
                select(func.count(MsgMessage.id)).where(
                    MsgMessage.conversation_id == conversation_id
                )
            )
        ).scalar_one()
        return items, total

    async def map_attachments(
        self, message_ids: list[str]
    ) -> dict[str, list[MsgMessageAttachment]]:
        if not message_ids:
            return {}
        stmt = (
            select(MsgMessageAttachment)
            .where(MsgMessageAttachment.message_id.in_(list(dict.fromkeys(message_ids))))
            .order_by(MsgMessageAttachment.message_id, MsgMessageAttachment.sort)
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        result: dict[str, list[MsgMessageAttachment]] = {}
        for row in rows:
            result.setdefault(row.message_id, []).append(row)
        return result

    async def get_message_before(self, conversation_id: str, message_id: str) -> MsgMessage | None:
        """获取会话中指定 message_id 之前紧邻的消息。"""
        before = await self.db.execute(
            select(MsgMessage)
            .where(MsgMessage.conversation_id == conversation_id, MsgMessage.id < message_id)
            .order_by(MsgMessage.id.desc())
            .limit(1)
        )
        return before.scalar_one_or_none()

    async def count_unread(self, conversation_id: str, account_type: str, account_id: str) -> int:
        """统计用户 last_read_message_id 之后的消息数。"""
        cursor = await self.db.execute(
            select(MsgMessageRead)
            .where(
                MsgMessageRead.conversation_id == conversation_id,
                MsgMessageRead.account_type == account_type,
                MsgMessageRead.account_id == account_id,
            )
            .order_by(MsgMessageRead.last_read_at.desc())
            .limit(1)
        )
        read = cursor.scalar_one_or_none()
        if read is None:
            stmt = select(func.count(MsgMessage.id)).where(
                MsgMessage.conversation_id == conversation_id
            )
        else:
            last_msg = await self.get_by_id(read.last_read_message_id)
            if last_msg is None:
                return 0
            stmt = select(func.count(MsgMessage.id)).where(
                MsgMessage.conversation_id == conversation_id,
                MsgMessage.created_at > last_msg.created_at,
            )
        return (await self.db.execute(stmt)).scalar_one()

    async def mark_read(
        self,
        conversation_id: str,
        account_type: str,
        account_id: str,
        last_read_message_id: str,
        terminal_id: str | None = None,
    ) -> None:
        now = datetime.now(UTC)
        stmt = select(MsgMessageRead).where(
            MsgMessageRead.conversation_id == conversation_id,
            MsgMessageRead.account_type == account_type,
            MsgMessageRead.account_id == account_id,
            MsgMessageRead.terminal_id == terminal_id
            if terminal_id
            else MsgMessageRead.terminal_id.is_(None),
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.last_read_message_id = last_read_message_id
            existing.last_read_at = now
        else:
            from app.platform.id_generator.snowflake import generate_snowflake_id

            self.db.add(
                MsgMessageRead(
                    id=generate_snowflake_id(),
                    conversation_id=conversation_id,
                    account_type=account_type,
                    account_id=account_id,
                    last_read_message_id=last_read_message_id,
                    last_read_at=now,
                    terminal_id=terminal_id,
                )
            )
        await self.db.flush()
