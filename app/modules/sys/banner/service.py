""" Author: Charlie

展示图服务层：维护展示图、解析图片 URL/昵称，并提供交互计数入口。
"""

from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.exceptions.business import NotFoundError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.modules.sys.banner.repository import BannerRepository
from app.modules.sys.banner.schema import (
    BannerAdminPageQuery,
    BannerCreateRequest,
    BannerPublicListQuery,
    BannerUpdateRequest,
    SysBannerSchema,
)
from app.modules.user.utils.profile import get_profiles_batch
from app.platform.cache.keys import banner_interaction_delta_key
from app.platform.cache.redis import get_redis
from app.platform.db.transaction import transactional
from app.platform.storage.url import resolve_file_url


class BannerService:
    """展示图服务，负责维护、展示查询和异步统计入口。"""

    def __init__(self, db: AsyncSession):
        """绑定会话并初始化仓储。"""
        self.db = db
        self.repo = BannerRepository(db)

    async def create(self, payload: BannerCreateRequest) -> None:
        """事务内创建展示图。"""
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: BannerUpdateRequest) -> None:
        """事务内更新展示图。"""
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        """事务内批量删除展示图。"""
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysBannerSchema:
        """查询展示图详情并解析图片 URL 与昵称。"""
        entity = await self.repo.get_required(query.id)
        schema = to_schema(SysBannerSchema, entity)
        _resolve_image_urls([schema])
        await _resolve_nicknames(self.db, [schema])
        return schema

    async def page_admin(self, query: BannerAdminPageQuery) -> PageData[SysBannerSchema]:
        """管理端分页查询并解析图片 URL 与昵称。"""
        entities, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysBannerSchema, entities)
        _resolve_image_urls(schemas)
        await _resolve_nicknames(self.db, schemas)
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
        _resolve_image_urls(schemas)
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
        """校验可见性后向 Redis 累加一次交互计数。"""
        if not await self.repo.is_public_visible(
            payload.id,
            datetime.now(UTC),
            account_type=account_type,
        ):
            raise NotFoundError("Display image not found")
        redis = get_redis()
        if redis is None:
            return
        await redis.hincrby(banner_interaction_delta_key(), payload.id, 1)


def _resolve_image_urls(items: list[SysBannerSchema]) -> None:
    """image 保持 object_name；image_url 给前端展示。"""
    for item in items:
        item.image_url = resolve_file_url(item.image) or item.image


async def _resolve_nicknames(db, items: list) -> list:
    """批量填充创建/更新人昵称到响应模型。"""
    creator_ids = list({i.created_by for i in items if i.created_by})
    updater_ids = list({i.updated_by for i in items if i.updated_by})
    all_ids = list(dict.fromkeys(creator_ids + updater_ids))
    if not all_ids:
        return items

    profiles = await get_profiles_batch(db, AccountType.ADMIN, all_ids)
    nickname_map = {aid: p.nickname for aid, p in profiles.items()}

    for item in items:
        if item.created_by and item.created_by in nickname_map:
            item.created_name = nickname_map[item.created_by]
        if item.updated_by and item.updated_by in nickname_map:
            item.updated_name = nickname_map[item.updated_by]
    return items


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
