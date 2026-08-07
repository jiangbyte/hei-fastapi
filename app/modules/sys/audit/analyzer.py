""" Author: Charlie

审计日志分析器 — 检测可疑模式并生成告警。

每条规则独立开关，由 settings.audit_alert 控制。
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AlertEvent:
    rule_name: str
    severity: str  # INFO / WARNING / CRITICAL
    summary: str
    details: dict | None = None


class AuditAnalyzer:
    """审计日志分析器，检查预设规则并生成告警事件。"""

    async def analyze(self, db_session) -> list[AlertEvent]:
        """执行所有已启用的分析规则，返回告警事件列表。"""
        events: list[AlertEvent] = []
        cfg = settings.audit_alert

        if cfg.rule_brute_force:
            events.extend(await self._check_brute_force(db_session, cfg.brute_force_threshold))
        if cfg.rule_unusual_hours:
            events.extend(await self._check_unusual_hours(db_session))
        if cfg.rule_sensitive_ops:
            events.extend(await self._check_sensitive_ops(db_session))
        if cfg.rule_bulk_delete:
            events.extend(await self._check_bulk_delete(db_session, cfg.bulk_delete_threshold))
        if cfg.rule_ip_anomaly:
            events.extend(await self._check_ip_anomaly(db_session, cfg.ip_anomaly_threshold))

        return events

    async def _check_brute_force(self, db, threshold: int) -> list[AlertEvent]:
        """同 IP 1 分钟内多次失败登录。"""
        from app.modules.sys.audit.model import SysOperationAuditLog

        since = datetime.now(UTC) - timedelta(seconds=60)
        stmt = (
            select(
                SysOperationAuditLog.ip,
                func.count(SysOperationAuditLog.id).label("cnt"),
            )
            .where(
                SysOperationAuditLog.created_at >= since,
                SysOperationAuditLog.success == False,  # noqa: E712
                SysOperationAuditLog.action == "login",
            )
            .group_by(SysOperationAuditLog.ip)
            .having(func.count(SysOperationAuditLog.id) >= threshold)
        )
        rows = (await db.execute(stmt)).all()
        return [
            AlertEvent(
                rule_name="brute_force",
                severity="CRITICAL",
                summary=f"IP {row.ip} 在 1 分钟内失败登录 {row.cnt} 次",
                details={"ip": row.ip, "count": row.cnt, "threshold": threshold},
            )
            for row in rows
        ]

    async def _check_unusual_hours(self, db) -> list[AlertEvent]:
        """凌晨 0-6 点的敏感操作（角色/权限变更）。"""
        from app.modules.sys.audit.model import SysOperationAuditLog

        now = datetime.now(UTC)
        if now.hour not in range(0, 6):
            return []
        since = now - timedelta(hours=1)
        sensitive_actions = ("role_create", "role_grant", "permission_change")
        stmt = (
            select(SysOperationAuditLog)
            .where(
                SysOperationAuditLog.created_at >= since,
                SysOperationAuditLog.action.in_(sensitive_actions),
            )
            .limit(20)
        )
        rows = (await db.execute(stmt)).scalars().all()
        if not rows:
            return []
        return [
            AlertEvent(
                rule_name="unusual_hours",
                severity="WARNING",
                summary=f"凌晨 {now.hour} 时检测到 {len(rows)} 次敏感操作",
                details={"count": len(rows), "actions": list({r.action for r in rows})},
            )
        ]

    async def _check_sensitive_ops(self, db) -> list[AlertEvent]:
        """检测角色授权/权限变更等敏感操作。"""
        from app.modules.sys.audit.model import SysOperationAuditLog

        since = datetime.now(UTC) - timedelta(seconds=300)
        sensitive_actions = ("role_grant", "permission_change", "permission_grant")
        stmt = (
            select(
                SysOperationAuditLog.account_id,
                SysOperationAuditLog.action,
                func.count(SysOperationAuditLog.id).label("cnt"),
            )
            .where(
                SysOperationAuditLog.created_at >= since,
                SysOperationAuditLog.action.in_(sensitive_actions),
            )
            .group_by(SysOperationAuditLog.account_id, SysOperationAuditLog.action)
        )
        rows = (await db.execute(stmt)).all()
        return [
            AlertEvent(
                rule_name="sensitive_ops",
                severity="WARNING",
                summary=f"账户 {row.account_id} 执行了 {row.action} ({row.cnt} 次)",
                details={"account_id": row.account_id, "action": row.action, "count": row.cnt},
            )
            for row in rows
        ]

    async def _check_bulk_delete(self, db, threshold: int) -> list[AlertEvent]:
        """同账户 5 分钟内大量删除操作。"""
        from app.modules.sys.audit.model import SysOperationAuditLog

        since = datetime.now(UTC) - timedelta(seconds=300)
        stmt = (
            select(
                SysOperationAuditLog.account_id,
                func.count(SysOperationAuditLog.id).label("cnt"),
            )
            .where(
                SysOperationAuditLog.created_at >= since,
                SysOperationAuditLog.action == "delete",
            )
            .group_by(SysOperationAuditLog.account_id)
            .having(func.count(SysOperationAuditLog.id) >= threshold)
        )
        rows = (await db.execute(stmt)).all()
        return [
            AlertEvent(
                rule_name="bulk_delete",
                severity="WARNING",
                summary=f"账户 {row.account_id} 在 5 分钟内删除了 {row.cnt} 条记录",
                details={"account_id": row.account_id, "count": row.cnt, "threshold": threshold},
            )
            for row in rows
        ]

    async def _check_ip_anomaly(self, db, threshold: int) -> list[AlertEvent]:
        """同账户短时间内从多个不同 IP 登录。"""
        from app.modules.sys.audit.model import SysOperationAuditLog

        since = datetime.now(UTC) - timedelta(seconds=900)
        stmt = (
            select(
                SysOperationAuditLog.account_id,
                func.count(func.distinct(SysOperationAuditLog.ip)).label("ip_cnt"),
            )
            .where(
                SysOperationAuditLog.created_at >= since,
                SysOperationAuditLog.action == "login",
                SysOperationAuditLog.success == True,  # noqa: E712
                SysOperationAuditLog.account_id.isnot(None),
            )
            .group_by(SysOperationAuditLog.account_id)
            .having(func.count(func.distinct(SysOperationAuditLog.ip)) >= threshold)
        )
        rows = (await db.execute(stmt)).all()
        return [
            AlertEvent(
                rule_name="ip_anomaly",
                severity="WARNING",
                summary=f"账户 {row.account_id} 在 15 分钟内从 {row.ip_cnt} 个不同 IP 登录",
                details={
                    "account_id": row.account_id,
                    "ip_count": row.ip_cnt,
                    "threshold": threshold,
                },
            )
            for row in rows
        ]


audit_analyzer = AuditAnalyzer()
