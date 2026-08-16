""" Author: Charlie

展示图服务层：维护展示图、解析图片 URL/昵称，并提供交互计数入口。
"""

from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache.keys import banner_interaction_delta_key
from app.core.cache.redis import get_redis
from app.core.config.enums import AccountType
from app.core.db.transaction import transactional
from app.core.exceptions.business import BusinessError, NotFoundError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.storage.url import normalize_object_name
from app.modules.sys.banner.repository import BannerRepository
from app.modules.sys.banner.schema import (
    BannerAdminPageQuery,
    BannerCreateRequest,
    BannerPublicListQuery,
    BannerUpdateRequest,
    SysBannerSchema,
)
from app.modules.sys.file.service import FileService
from app.modules.profile.utils.profile import enrich_audit_names


class BannerService:
    """展示图服务，负责维护、展示查询和异步统计入口。"""

    def __init__(self, db: AsyncSession):
        """绑定会话并初始化仓储。"""
        self.db = db
        self.repo = BannerRepository(db)

    async def create(self, payload: BannerCreateRequest) -> None:
        """事务内创建展示图（image 对象名归一化，对齐 hei-boot）。"""
        normalized = payload.model_copy(
            update={"image": normalize_object_name(payload.image) or payload.image}
        )
        async with transactional(self.db):
            await self.repo.create(normalized)

    async def update(self, payload: BannerUpdateRequest) -> None:
        """事务内更新展示图（image 对象名归一化，对齐 hei-boot）。"""
        normalized = payload.model_copy(
            update={"image": normalize_object_name(payload.image) or payload.image}
        )
        async with transactional(self.db):
            await self.repo.update(normalized)

    async def delete(self, payload: IdsRequest) -> None:
        """事务内批量删除展示图。"""
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysBannerSchema:
        """查询展示图详情并解析图片 URL 与昵称。"""
        entity = await self.repo.get_required(query.id)
        schema = to_schema(SysBannerSchema, entity)
        await self._resolve_image_urls([schema])
        await enrich_audit_names(self.db, [schema], account_type=AccountType.ADMIN)
        return schema

    async def page_admin(self, query: BannerAdminPageQuery) -> PageData[SysBannerSchema]:
        """管理端分页查询并解析图片 URL 与昵称。"""
        entities, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysBannerSchema, entities)
        await self._resolve_image_urls(schemas)
        await enrich_audit_names(self.db, schemas, account_type=AccountType.ADMIN)
        return build_page(query, total, schemas)

    async def list_visible(
        self,
        query: BannerPublicListQuery,
        *,
        account_type: AccountType,
    ) -> list[SysBannerSchema]:
        """查询指定账户类型可见的展示图并解析图片 URL。"""
        items = await self.repo.list_public(
            now=datetime.now(UTC),
            query=query,
            account_type=account_type,
        )
        schemas = to_schema_list(SysBannerSchema, items)
        await self._resolve_image_urls(schemas)
        return schemas

    async def list_public(self, query: BannerPublicListQuery) -> list[SysBannerSchema]:
        """查询公开端（PORTAL）可见的展示图。"""
        return await self.list_visible(query, account_type=AccountType.PORTAL)

    async def list_admin(self, query: BannerPublicListQuery) -> list[SysBannerSchema]:
        """查询管理端（ADMIN）可见的展示图。"""
        return await self.list_visible(query, account_type=AccountType.ADMIN)

    async def record_interaction(
        self,
        payload: IdQuery,
        *,
        account_type: AccountType = AccountType.PORTAL,
    ) -> None:
        """校验可见性后向 Redis 累加一次交互计数。

        记录不存在 → 404；存在但当前不可见 → 400（对齐 hei-boot 错误语义）。
        """
        if await self.repo.get_by_id(payload.id) is None:
            raise NotFoundError("Display image not found")
        if not await self.repo.is_public_visible(
            payload.id,
            datetime.now(UTC),
            account_type=account_type,
        ):
            raise BusinessError("Banner is not publicly visible")
        redis = get_redis()
        if redis is None:
            return
        await redis.hincrby(banner_interaction_delta_key(), payload.id, 1)

    async def _resolve_image_urls(self, items: list[SysBannerSchema]) -> None:
        """image 保持 object_name；image_url 给前端展示（provider 感知解析）。"""
        urls = await FileService(self.db).resolve_access_urls([item.image for item in items])
        for item in items:
            raw = str(item.image).strip() if item.image else ""
            item.image_url = urls.get(raw) if raw else None


async def _read_positive_deltas(redis: Redis, key: str) -> dict[str, int]:
    """从 Redis 哈希读取正数交互增量，非法值忽略。"""
    raw_values = await redis.hgetall(key)
    if not raw_values:
        return {}

    deltas: dict[str, int] = {}
    for raw_id, raw_delta in raw_values.items():
        banner_id = raw_id.decode() if isinstance(raw_id, bytes) else str(raw_id)
        delta_text = raw_delta.decode() if isinstance(raw_delta, bytes) else str(raw_delta)
        try:
            delta = int(delta_text)
        except ValueError:
            continue
        if delta > 0:
            deltas[banner_id] = delta
    return deltas


async def flush_interaction_deltas(db: AsyncSession, redis: Redis) -> int:
    """将 Redis 中的展示图交互增量刷入数据库，返回处理条数。"""
    key = banner_interaction_delta_key()
    deltas = await _read_positive_deltas(redis, key)
    if not deltas:
        return 0
    async with transactional(db):
        await BannerRepository(db).increment_interactions(deltas)
    await redis.hdel(key, *deltas.keys())
    return len(deltas)
