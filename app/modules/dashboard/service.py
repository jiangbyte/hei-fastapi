""" Author: Charlie """

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.session import session_store
from app.modules.dashboard.schema import (
    DashboardMetric,
    DashboardOverviewResponse,
    DashboardStatusItem,
    DashboardTrendPoint,
)
from app.modules.iam.account.model import SysAccount
from app.modules.sys.file.model import SysFile


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def overview(self) -> DashboardOverviewResponse:
        since = datetime.now(UTC) - timedelta(days=6)
        account_total = await self._count(SysAccount.id)
        account_new = await self._count(SysAccount.id, SysAccount.created_at >= _day_start())
        online_sessions = len(
            await session_store.list_sessions_by_tokens(await session_store.list_tokens())
        )
        file_total = await self._count(SysFile.id)
        file_size = int(
            (await self.db.execute(select(func.coalesce(func.sum(SysFile.size), 0)))).scalar_one()
        )
        return DashboardOverviewResponse(
            metrics=[
                DashboardMetric(key="accounts", value=account_total, trend_value=account_new),
                DashboardMetric(key="online_sessions", value=online_sessions),
                DashboardMetric(key="files", value=file_total, trend_value=file_size),
            ],
            account_trend=await self._daily_trend(SysAccount.created_at, since, "accounts"),
            file_type_share=await self._file_type_share(),
        )

    async def _count(self, column, *filters) -> int:
        stmt = select(func.count(column))
        if filters:
            stmt = stmt.where(*filters)
        return int((await self.db.execute(stmt)).scalar_one())

    async def _daily_trend(self, column, since: datetime, label: str) -> list[DashboardTrendPoint]:
        rows = (await self.db.execute(select(column).where(column >= since))).scalars().all()
        counts: dict[str, int] = defaultdict(int)
        for value in rows:
            if not value:
                continue
            counts[value.date().isoformat()] += 1
        days = [(since + timedelta(days=index)).date().isoformat() for index in range(7)]
        return [
            DashboardTrendPoint(date=day[5:], type=label, value=counts.get(day, 0)) for day in days
        ]

    async def _file_type_share(self) -> list[DashboardStatusItem]:
        rows = (
            await self.db.execute(
                select(SysFile.content_type, func.count(SysFile.id))
                .group_by(SysFile.content_type)
                .order_by(func.count(SysFile.id).desc())
                .limit(8)
            )
        ).all()
        return [
            DashboardStatusItem(name=str(content_type or "unknown"), value=int(count))
            for content_type, count in rows
        ]


def _day_start() -> datetime:
    now = datetime.now(UTC)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)
