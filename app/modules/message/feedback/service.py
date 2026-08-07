""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte
"""
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.session import SessionPayload
from app.modules.message.feedback.repository import MsgFeedbackRepository
from app.modules.message.feedback.schema import (
    MsgFeedbackAdminPageQuery,
    MsgFeedbackCreateRequest,
    MsgFeedbackSchema,
    MsgFeedbackUpdateRequest,
    MyFeedbackPageQuery,
)
from app.modules.user.utils.profile import enrich_audit_names, get_profile, get_profiles_batch
from app.platform.db.transaction import transactional


class MsgFeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MsgFeedbackRepository(db)

    async def submit(self, payload: MsgFeedbackCreateRequest, session: SessionPayload) -> None:
        async with transactional(self.db):
            entity = await self.repo.create(payload)
            entity.submitter_account_type = str(session.account_type)
            entity.submitter_account_id = session.account_id

    async def update(self, payload: MsgFeedbackUpdateRequest, session: SessionPayload) -> None:
        async with transactional(self.db):
            entity = await self.repo.get_required(payload.id)
            entity.status = payload.status
            if payload.reply is not None:
                entity.reply = payload.reply
                entity.replied_by = session.account_id
                entity.replied_at = datetime.now(UTC)
            await self.db.flush()

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> MsgFeedbackSchema:
        entity = await self.repo.get_required(query.id)
        schema = to_schema(MsgFeedbackSchema, entity)
        return await self._enrich_profiles(schema)

    async def page_admin(self, query: MsgFeedbackAdminPageQuery) -> PageData[MsgFeedbackSchema]:
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(MsgFeedbackSchema, items)
        return build_page(query, total, await self._batch_enrich_profiles(schemas))

    async def page_my(
        self,
        query: MyFeedbackPageQuery,
        session: SessionPayload,
    ) -> PageData[MsgFeedbackSchema]:
        items, total = await self.repo.page_my(
            query,
            str(session.account_type),
            session.account_id,
        )
        schemas = to_schema_list(MsgFeedbackSchema, items)
        return build_page(query, total, schemas)

    async def _enrich_profiles(self, schema: MsgFeedbackSchema) -> MsgFeedbackSchema:
        await enrich_audit_names(self.db, [schema], account_type=AccountType.ADMIN)
        if schema.submitter_account_id:
            try:
                at = AccountType(schema.submitter_account_type)
                profile = await get_profile(self.db, at, schema.submitter_account_id)
                if profile:
                    schema.submitter_avatar = profile.avatar
                    schema.submitter_nickname = profile.nickname or profile.name
            except ValueError:
                pass
        return schema

    async def _batch_enrich_profiles(
        self, schemas: list[MsgFeedbackSchema]
    ) -> list[MsgFeedbackSchema]:
        await enrich_audit_names(self.db, schemas, account_type=AccountType.ADMIN)

        groups: dict[str, list[str]] = {}
        schema_map: list[tuple[MsgFeedbackSchema, str]] = []
        for schema in schemas:
            if schema.submitter_account_id and schema.submitter_account_type:
                groups.setdefault(schema.submitter_account_type, []).append(
                    schema.submitter_account_id
                )
                schema_map.append((schema, schema.submitter_account_type))
        for account_type_str, account_ids in groups.items():
            try:
                at = AccountType(account_type_str)
                batch = await get_profiles_batch(self.db, at, account_ids)
                for schema, _ in schema_map:
                    if (
                        schema.submitter_account_type == account_type_str
                        and schema.submitter_account_id in batch
                    ):
                        p = batch[schema.submitter_account_id]
                        schema.submitter_avatar = p.avatar
                        schema.submitter_nickname = p.nickname or p.name
            except ValueError:
                pass
        return schemas
