""" Author: Charlie """

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountStatusEnum, StatusEnum
from app.core.security.session import session_store
from app.modules.dashboard.schema import (
    DashboardAccounts,
    DashboardFiles,
    DashboardIam,
    DashboardOpsToday,
    DashboardOverviewResponse,
    DashboardStatusItem,
    DashboardSummary,
    DashboardTrendPoint,
    DashboardTrends,
)
from app.modules.iam.account.model import SysAccount
from app.modules.iam.dept.model import SysDept
from app.modules.iam.enums import ResourceType
from app.modules.iam.group.model import SysGroup
from app.modules.iam.resource.model import SysResource
from app.modules.iam.role.model import SysRole
from app.modules.message.enums import FeedbackStatus
from app.modules.message.feedback.model import MsgFeedback
from app.modules.sys.audit.model import SysOperationAuditLog
from app.modules.sys.file.model import SysFile


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def overview(self) -> DashboardOverviewResponse:
        since = datetime.now(UTC) - timedelta(days=6)
        day_start = _day_start()

        account_total = await self._count(SysAccount.id)
        enabled = await self._count(
            SysAccount.id, SysAccount.account_status == AccountStatusEnum.ENABLED.value
        )
        disabled = await self._count(
            SysAccount.id, SysAccount.account_status == AccountStatusEnum.DISABLED.value
        )
        today_new = await self._count(SysAccount.id, SysAccount.created_at >= day_start)

        online_sessions = len(
            await session_store.list_sessions_by_tokens(await session_store.list_tokens())
        )
        file_total = await self._count(SysFile.id)
        storage_bytes = int(
            (await self.db.execute(select(func.coalesce(func.sum(SysFile.size), 0)))).scalar_one()
        )

        audit_total = await self._count(
            SysOperationAuditLog.id, SysOperationAuditLog.created_at >= day_start
        )
        audit_failed = await self._count(
            SysOperationAuditLog.id,
            SysOperationAuditLog.created_at >= day_start,
            SysOperationAuditLog.success.is_(False),
        )
        feedback_pending = await self._count(
            MsgFeedback.id, MsgFeedback.status == FeedbackStatus.PENDING.value
        )

        return DashboardOverviewResponse(
            summary=DashboardSummary(
                account_total=account_total,
                online_sessions=online_sessions,
                file_total=file_total,
                storage_bytes=storage_bytes,
            ),
            accounts=DashboardAccounts(
                enabled=enabled,
                disabled=disabled,
                today_new=today_new,
                by_type=await self._account_by_type(),
            ),
            iam=DashboardIam(
                role_count=await self._count(SysRole.id),
                dept_count=await self._count(SysDept.id),
                group_count=await self._count(SysGroup.id),
                menu_count=await self._count(
                    SysResource.id,
                    SysResource.resource_type == ResourceType.MENU.value,
                    SysResource.status == StatusEnum.ENABLED.value,
                ),
            ),
            ops_today=DashboardOpsToday(
                audit_total=audit_total,
                audit_failed=audit_failed,
                feedback_pending=feedback_pending,
            ),
            trends=DashboardTrends(
                account_trend=await self._daily_trend(SysAccount.created_at, since, "accounts"),
                audit_trend=await self._daily_trend(
                    SysOperationAuditLog.created_at, since, "audits"
                ),
            ),
            files=DashboardFiles(by_content_type=await self._file_type_share()),
        )

    async def _count(self, column, *filters) -> int:
        stmt = select(func.count(column))
        if filters:
            stmt = stmt.where(*filters)
        return int((await self.db.execute(stmt)).scalar_one())

    async def _account_by_type(self) -> list[DashboardStatusItem]:
        rows = (
            await self.db.execute(
                select(SysAccount.account_type, func.count(SysAccount.id))
                .group_by(SysAccount.account_type)
                .order_by(func.count(SysAccount.id).desc())
            )
        ).all()
        return [
            DashboardStatusItem(name=str(account_type or "unknown"), value=int(count))
            for account_type, count in rows
        ]

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
