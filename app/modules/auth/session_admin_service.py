""" Author: Charlie """

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

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
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.account_repo = AccountRepository(db)

    async def analysis(self) -> SessionAnalysisResponse:
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
            admin_account_count=account_types.get("ADMIN", 0),
            portal_account_count=account_types.get("PORTAL", 0),
            one_hour_new_count=one_hour_new_count,
            max_token_count=max(token_counts, default=0),
        )

    async def page(self, query: SessionPageQuery) -> PageData[SessionAccountItem]:
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
        tokens = await session_store.get_account_tokens(query.account_type.value, query.account_id)
        sessions = await session_store.list_sessions_by_tokens(tokens)
        return [_token_info(session) for session in sessions]

    async def exit_sessions(self, targets: list[SessionTokensQuery]) -> None:
        for target in targets:
            await session_store.delete_account_sessions(
                target.account_type.value, target.account_id
            )

    async def exit_tokens(self, tokens: list[str]) -> None:
        for token in list(dict.fromkeys(tokens)):
            await session_store.delete(token)

    async def _group_online_sessions(self) -> dict[tuple[str, str], list[SessionPayload]]:
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
        if query.ip:
            result = [
                item
                for item in result
                if any(query.ip in str(token.client_ip or "") for token in item.tokens)
            ]
        return result

    def _sort_key(self, item: SessionAccountItem) -> tuple[datetime, str]:
        active_at = item.latest_active_at or item.first_login_at or datetime.min.replace(tzinfo=UTC)
        if active_at.tzinfo is None:
            active_at = active_at.replace(tzinfo=UTC)
        return active_at, item.account_id


def _token_info(session: SessionPayload) -> SessionTokenInfo:
    return SessionTokenInfo(
        token=session.token,
        device_label=session.device_label,
        client_ip=session.client_ip,
        user_agent=session.user_agent,
        login_at=_parse_datetime(session.login_at),
        last_active_at=_parse_datetime(session.last_active_at),
        expires_at=_parse_datetime(session.expires_at),
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
