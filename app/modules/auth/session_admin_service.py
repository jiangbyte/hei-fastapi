""" Author: Charlie

会话管理服务：统计在线会话、分页聚合账户维度信息并支持强制下线。
"""

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData, build_page
from app.core.security.session import SessionPayload, session_store
from app.modules.auth.session_schema import (
    SessionAccountItem,
    SessionAnalysisResponse,
    SessionPageQuery,
    SessionTokenInfo,
    SessionTokensQuery,
)
from app.modules.iam.account.query_service import AccountQueryService
from app.modules.iam.account.repository import AccountRepository


class SessionAdminService:
    """会话管理服务：在线会话分析、分页与强制下线。"""

    def __init__(self, db: AsyncSession) -> None:
        """初始化账户仓储。"""
        self.db = db
        self.account_repo = AccountRepository(db)

    async def analysis(self) -> SessionAnalysisResponse:
        """统计在线账户、token 与近一小时新增等指标。"""
        grouped = await self._group_online_sessions()
        token_counts = [len(items) for items in grouped.values()]
        now = datetime.now(UTC)
        one_hour_ago = now - timedelta(hours=1)
        one_hour_new_count = 0
        for sessions in grouped.values():
            for session in sessions:
                login_at = _parse_datetime(session.login_at)
                if login_at and login_at >= one_hour_ago:
                    one_hour_new_count += 1
        account_types = Counter(account_type for account_type, _ in grouped)
        return SessionAnalysisResponse(
            online_account_count=len(grouped),
            online_token_count=sum(token_counts),
            admin_account_count=account_types.get(AccountType.ADMIN.value, 0),
            portal_account_count=account_types.get(AccountType.PORTAL.value, 0),
            one_hour_new_count=one_hour_new_count,
            max_token_count=max(token_counts, default=0),
        )

    async def page(self, query: SessionPageQuery) -> PageData[SessionAccountItem]:
        """按账户维度分页返回在线会话。"""
        grouped = await self._group_online_sessions()
        items = await self._build_items(grouped)
        items = self._filter_items(items, query)
        items.sort(key=self._sort_key, reverse=True)
        total = len(items)
        page_items = items[
            query.offset : query.offset + query.size
        ]
        return build_page(query, total, page_items)

    async def tokens(self, query: SessionTokensQuery) -> list[SessionTokenInfo]:
        """返回指定账户的在线 token 详情列表（account_type 缺省按 ADMIN）。"""
        account_type = query.account_type or AccountType.ADMIN
        tokens = await session_store.get_account_tokens(account_type.value, query.account_id)
        sessions = await session_store.list_sessions_by_tokens(tokens)
        return [_token_info(session) for session in sessions]

    async def exit_sessions(self, targets: list[SessionTokensQuery]) -> None:
        """批量删除指定账户的全部会话（account_type 缺省按 ADMIN）。"""
        for target in targets:
            account_type = target.account_type or AccountType.ADMIN
            await session_store.delete_account_sessions(
                account_type.value, target.account_id
            )

    async def exit_tokens(self, tokens: list[str]) -> None:
        """批量删除指定 token 的会话（去重后逐个删除）。"""
        for token in list(dict.fromkeys(tokens)):
            await session_store.delete(token)

    async def _group_online_sessions(self) -> dict[tuple[str, str], list[SessionPayload]]:
        """拉取全部会话并按（账户类型, 账户 ID）分组。"""
        tokens = await session_store.list_tokens()
        sessions = await session_store.list_sessions_by_tokens(tokens)
        grouped: dict[tuple[str, str], list[SessionPayload]] = {}
        for session in sessions:
            grouped.setdefault((str(session.account_type), session.account_id), []).append(session)
        return grouped

    async def _build_items(
        self,
        grouped: dict[tuple[str, str], list[SessionPayload]],
    ) -> list[SessionAccountItem]:
        """把分组会话聚合为账户维度的展示项。"""
        if not grouped:
            return []
        account_ids = [account_id for _, account_id in grouped]
        accounts = await self.account_repo.list_accounts_by_ids(account_ids)
        schema_map = {
            schema.id: schema
            for schema in await AccountQueryService(self.db).build_account_schemas(accounts)
        }
        items: list[SessionAccountItem] = []
        for (account_type, account_id), sessions in grouped.items():
            schema = schema_map.get(account_id)
            token_infos = [_token_info(session) for session in sessions]
            token_infos.sort(
                key=lambda item: (
                    item.last_active_at or item.login_at or datetime.min.replace(tzinfo=UTC)
                ),
                reverse=True,
            )
            login_times = [item.login_at for item in token_infos if item.login_at]
            active_times = [item.last_active_at for item in token_infos if item.last_active_at]
            newest = token_infos[0] if token_infos else None
            items.append(
                SessionAccountItem(
                    account_id=account_id,
                    account_type=account_type,
                    account=getattr(schema, "account", None) or "",
                    name=getattr(schema, "name", None),
                    nickname=getattr(schema, "nickname", None),
                    avatar=getattr(schema, "avatar", None),
                    latest_login_ip=getattr(schema, "latest_login_ip", None),
                    latest_login_time=getattr(schema, "latest_login_time", None),
                    client_ip=newest.client_ip if newest else None,
                    device_label=newest.device_label if newest else None,
                    token_count=len(token_infos),
                    first_login_at=min(login_times) if login_times else None,
                    latest_active_at=max(active_times) if active_times else None,
                    tokens=token_infos,
                )
            )
        return items

    def _filter_items(
        self,
        items: list[SessionAccountItem],
        query: SessionPageQuery,
    ) -> list[SessionAccountItem]:
        """按查询条件过滤账户维度会话项。"""
        result = items
        if query.account_type:
            result = [item for item in result if str(item.account_type) == query.account_type.value]
        if query.account_id:
            result = [item for item in result if query.account_id in item.account_id]
        if query.account:
            keyword = query.account.lower()
            result = [
                item
                for item in result
                if keyword in item.account.lower()
                or keyword in str(item.name or "").lower()
                or keyword in str(item.nickname or "").lower()
            ]
        if query.keyword:
            keyword = query.keyword.lower()
            result = [
                item
                for item in result
                if keyword in item.account.lower()
                or keyword in str(item.name or "").lower()
                or keyword in str(item.nickname or "").lower()
                or keyword in item.account_id.lower()
            ]
        if query.ip:
            result = [
                item
                for item in result
                if any(query.ip in str(token.client_ip or "") for token in item.tokens)
            ]
        return result

    def _sort_key(self, item: SessionAccountItem) -> tuple[datetime, str]:
        """会话项排序键：最近活跃时间 + 账户 ID。"""
        active_at = item.latest_active_at or item.first_login_at or datetime.min.replace(tzinfo=UTC)
        if active_at.tzinfo is None:
            active_at = active_at.replace(tzinfo=UTC)
        return active_at, item.account_id


def _token_info(session: SessionPayload) -> SessionTokenInfo:
    """把会话载荷转换为 token 信息模型。"""
    return SessionTokenInfo(
        token=session.token,
        account_id=session.account_id,
        account_type=session.account_type,
        remember_me=session.remember_me,
        device_label=session.device_label,
        client_ip=session.client_ip,
        user_agent=session.user_agent,
        login_at=_parse_datetime(session.login_at),
        last_active_at=_parse_datetime(session.last_active_at),
        expires_at=_parse_datetime(session.expires_at),
    )


def _parse_datetime(value: str | None) -> datetime | None:
    """解析 ISO 时间字符串，失败返回 None。"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
