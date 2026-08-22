""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte

反馈服务层：提交、处理、查询反馈，并补充附件与提交者资料信息。
"""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.db.transaction import transactional
from app.core.exceptions.business import BusinessError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.session import SessionPayload
from app.core.storage.url import normalize_object_name
from app.modules.profile.utils.profile import enrich_audit_names, get_profile, get_profiles_batch
from app.modules.sys.feedback.repository import SysFeedbackRepository
from app.modules.sys.feedback.schema import (
    MyFeedbackPageQuery,
    SysFeedbackAdminPageQuery,
    SysFeedbackAttachmentSchema,
    SysFeedbackCreateRequest,
    SysFeedbackSchema,
    SysFeedbackUpdateRequest,
)
from app.modules.sys.file.repository import FileRepository
from app.modules.sys.file.service import FileService


class SysFeedbackService:
    """反馈业务服务，编排仓储与附件/资料 enrichment。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SysFeedbackRepository(db)
        self.file_repo = FileRepository(db)

    async def submit(self, payload: SysFeedbackCreateRequest, session: SessionPayload) -> None:
        """提交反馈：推导标题/分类默认值、规范化附件名后落库（对齐 hei-boot）。"""
        title = (payload.title or "").strip()
        if not title:
            title = payload.content.strip()[:64]
        category = (payload.category or "").strip() or "GENERAL"
        normalized_payload = payload.model_copy(
            update={"title": title, "category": category}
        )
        attach_object_names = await self._normalize_attach_object_names(
            normalized_payload.attach_object_names
        )
        async with transactional(self.db):
            await self.repo.create(
                normalized_payload,
                submitter_account_type=str(session.account_type),
                submitter_account_id=session.account_id,
                attach_object_names=attach_object_names,
            )

    async def update(self, payload: SysFeedbackUpdateRequest, session: SessionPayload) -> None:
        """处理反馈：仅在提供 status 时更新状态，回复时记录回复人与时间（对齐 hei-boot）。"""
        async with transactional(self.db):
            entity = await self.repo.get_required(payload.id)
            if payload.status is not None:
                entity.status = payload.status
            if payload.reply is not None:
                entity.reply = payload.reply
                entity.replied_by = session.account_id
                entity.replied_at = datetime.now(UTC)
            await self.db.flush()

    async def delete(self, payload: IdsRequest) -> None:
        """批量删除反馈。"""
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysFeedbackSchema:
        """管理端查询反馈详情，并补充附件与提交者资料。"""
        entity = await self.repo.get_required(query.id)
        schema = to_schema(SysFeedbackSchema, entity)
        return await self._enrich_profiles(schema)

    async def detail_my(self, query: IdQuery, session: SessionPayload) -> SysFeedbackSchema:
        """查询「我的反馈」详情，非本人反馈返回 403 无权查看（对齐 hei-boot）。"""
        entity = await self.repo.get_required(query.id)
        if (
            str(entity.submitter_account_type) != str(session.account_type)
            or str(entity.submitter_account_id) != str(session.account_id)
        ):
            raise BusinessError("无权查看")
        schema = to_schema(SysFeedbackSchema, entity)
        return await self._enrich_attachments(schema)

    async def page_admin(self, query: SysFeedbackAdminPageQuery) -> PageData[SysFeedbackSchema]:
        """管理端分页查询反馈，并批量补充提交者资料。"""
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysFeedbackSchema, items)
        return build_page(query, total, await self._batch_enrich_profiles(schemas))

    async def page_my(
        self,
        query: MyFeedbackPageQuery,
        session: SessionPayload,
    ) -> PageData[SysFeedbackSchema]:
        """分页查询「我的反馈」，并补充附件信息。"""
        items, total = await self.repo.page_my(
            query,
            str(session.account_type),
            session.account_id,
        )
        schemas = to_schema_list(SysFeedbackSchema, items)
        return build_page(query, total, await self._batch_enrich_profiles(schemas))

    async def _normalize_attach_object_names(self, values: list[str]) -> list[str]:
        """规范化附件名并校验其对应文件真实存在。"""
        normalized: list[str] = []
        for value in values:
            object_name = normalize_object_name(value)
            if not object_name:
                continue
            normalized.append(object_name)
        unique = list(dict.fromkeys(normalized))
        if not unique:
            return []
        entities = await self.file_repo.list_by_object_names(unique)
        found = {entity.object_name for entity in entities}
        missing = [name for name in unique if name not in found]
        if missing:
            raise BusinessError("附件文件不存在")
        return unique

    async def _enrich_attachments(self, schema: SysFeedbackSchema) -> SysFeedbackSchema:
        """为单条反馈补充附件明细。"""
        schemas = await self._enrich_attachments_many([schema])
        return schemas[0]

    async def _enrich_attachments_many(
        self, schemas: list[SysFeedbackSchema]
    ) -> list[SysFeedbackSchema]:
        """批量补充反馈附件明细（按 object_name 关联文件元数据）。"""
        all_names: list[str] = []
        for schema in schemas:
            names = [
                name
                for raw in (schema.attach_object_names or [])
                if (name := normalize_object_name(raw))
            ]
            schema.attach_object_names = list(dict.fromkeys(names))
            all_names.extend(schema.attach_object_names)

        entity_map = {
            entity.object_name: entity
            for entity in await self.file_repo.list_by_object_names(all_names)
        }
        url_map = await FileService(self.db).resolve_access_urls(all_names)
        for schema in schemas:
            attachments: list[SysFeedbackAttachmentSchema] = []
            for object_name in schema.attach_object_names:
                entity = entity_map.get(object_name)
                resolved = url_map.get(object_name)
                if entity is None:
                    attachments.append(
                        SysFeedbackAttachmentSchema(
                            object_name=object_name,
                            url=resolved,
                        )
                    )
                    continue
                attachments.append(
                    SysFeedbackAttachmentSchema(
                        object_name=entity.object_name,
                        id=entity.id,
                        original_name=entity.original_name,
                        content_type=entity.content_type,
                        size=entity.size,
                        url=resolved,
                    )
                )
            schema.attachments = attachments
        return schemas

    async def _enrich_profiles(self, schema: SysFeedbackSchema) -> SysFeedbackSchema:
        """为单条反馈补充审计人姓名与提交者头像昵称。"""
        await self._enrich_attachments(schema)
        await enrich_audit_names(self.db, [schema], account_type=AccountType.ADMIN)
        if schema.submitter_account_id:
            try:
                at = AccountType(schema.submitter_account_type)
                profile = await get_profile(self.db, at, schema.submitter_account_id)
                if profile:
                    schema.submitter_avatar = await FileService(self.db).resolve_access_url(
                        profile.avatar
                    )
                    schema.submitter_nickname = profile.nickname or profile.name
            except ValueError:
                pass
        return schema

    async def _batch_enrich_profiles(
        self, schemas: list[SysFeedbackSchema]
    ) -> list[SysFeedbackSchema]:
        """批量补充反馈的审计人姓名与提交者头像昵称。"""
        await self._enrich_attachments_many(schemas)
        await enrich_audit_names(self.db, schemas, account_type=AccountType.ADMIN)

        groups: dict[str, list[str]] = {}
        schema_map: list[tuple[SysFeedbackSchema, str]] = []
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
                avatars = [
                    batch[aid].avatar
                    for aid in account_ids
                    if aid in batch
                ]
                url_map = await FileService(self.db).resolve_access_urls(avatars)
                for schema, _ in schema_map:
                    if (
                        schema.submitter_account_type == account_type_str
                        and schema.submitter_account_id in batch
                    ):
                        p = batch[schema.submitter_account_id]
                        raw = str(p.avatar).strip() if p.avatar else ""
                        schema.submitter_avatar = url_map.get(raw) if raw else None
                        schema.submitter_nickname = p.nickname or p.name
            except ValueError:
                pass
        return schemas
