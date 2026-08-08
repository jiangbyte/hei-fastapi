""" Author: Charlie

告警分发器 — 通过邮件 / 消息推送 / 自定义 Webhook 发送告警，含冷却。
"""
import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config.settings import settings
from app.modules.sys.audit.alert_model import SysAlertLog
from app.modules.sys.audit.analyzer import AlertEvent
from app.platform.email.sender import send_mail
from app.platform.id_generator.snowflake import generate_snowflake_id

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """告警分发器，带冷却去重。"""

    async def dispatch(self, db_session, events: list[AlertEvent]) -> None:
        """过滤 + 去重 + 发送 + 记录。"""
        if not events:
            return

        # 1. 查询冷却期内已发送的规则
        cooldown_sec = settings.audit_alert.alert_cooldown_seconds
        since = datetime.now(UTC) - timedelta(seconds=cooldown_sec)
        stmt = (
            select(SysAlertLog.rule_name)
            .where(
                SysAlertLog.created_at >= since,
                SysAlertLog.rule_name.in_({e.rule_name for e in events}),
            )
            .distinct()
        )
        existing = set((await db_session.execute(stmt)).scalars().all())

        # 2. 过滤出未发送的新事件
        new_events = [e for e in events if e.rule_name not in existing]
        if not new_events:
            return

        # 3. 发送
        for event in new_events:
            await self._send_alert(event)

        # 4. 记录
        for event in new_events:
            db_session.add(
                SysAlertLog(
                    id=generate_snowflake_id(),
                    rule_name=event.rule_name,
                    severity=event.severity,
                    summary=event.summary,
                    details=event.details,
                    notified_via=self._notify_method(),
                )
            )

    def _notify_method(self) -> str:
        cfg = settings.audit_alert
        parts = []
        if cfg.notify_email and settings.mail.host and settings.mail.from_email:
            parts.append("email")
        if cfg.notify_push:
            parts.append("push")
        if cfg.notify_custom_webhook and cfg.webhook_url:
            parts.append("webhook")
        return ",".join(parts) if parts else "none"

    async def _send_alert(self, event: AlertEvent) -> None:
        """发送单条告警（邮件 / 推送 / 自定义 Webhook）。"""
        await self._send_email(event)
        await self._send_push(event)
        await self._send_webhook(event)

    async def _send_email(self, event: AlertEvent) -> None:
        """邮件发送（静默失败不阻塞流程）。"""
        if not settings.audit_alert.notify_email:
            return
        if not settings.mail.host or not settings.mail.from_email:
            return
        try:
            subject = f"[{event.severity}] 审计告警: {event.summary}"
            body = (
                f"规则: {event.rule_name}\n"
                f"级别: {event.severity}\n"
                f"摘要: {event.summary}\n"
                f"时间: {datetime.now(UTC).isoformat()}"
            )
            if event.details:
                body += f"\n详情: {json.dumps(event.details, ensure_ascii=False)}"
            await send_mail(settings.mail.from_email, subject, body)
        except Exception:
            logger.exception("Failed to send alert email for %s", event.rule_name)

    async def _send_push(self, event: AlertEvent) -> None:
        """复用消息推送配置（钉钉 / 飞书 / 企微）。"""
        if not settings.audit_alert.notify_push:
            return
        try:
            from app.platform.push.sender import send_push

            title = f"[{event.severity}] 审计告警"
            content = f"{event.summary}\n规则: {event.rule_name}"
            await send_push(title, content)
        except Exception:
            logger.exception("Failed to send alert push for %s", event.rule_name)

    async def _send_webhook(self, event: AlertEvent) -> None:
        """自定义 Webhook 发送（静默失败不阻塞流程）。"""
        if not settings.audit_alert.notify_custom_webhook:
            return
        url = settings.audit_alert.webhook_url
        secret = settings.audit_alert.webhook_secret
        if not url:
            return

        payload = {
            "msg_type": "text",
            "content": {"text": (f"[{event.severity}] {event.summary}\n规则: {event.rule_name}")},
        }

        if secret:
            timestamp = str(int(time.time()))
            string_to_sign = f"{timestamp}\n{secret}"
            hmac_code = hmac.new(
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
            sign = base64.b64encode(hmac_code).decode("utf-8")
            payload["timestamp"] = timestamp
            payload["sign"] = sign

        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json=payload)
        except Exception:
            logger.exception("Failed to send alert webhook for %s", event.rule_name)


async def send_test_webhook(webhook_url: str, webhook_secret: str = "") -> str:
    """发送测试 Webhook 消息。成功返回空字符串，失败返回错误信息。"""
    if not webhook_url:
        return "Webhook URL 为空"

    try:
        url = webhook_url
        payload = {
            "msg_type": "text",
            "content": {
                "text": "HEI-FastAPI 审计告警系统测试消息\n\n如果收到此消息，说明 Webhook 配置正确。"
            },
        }

        if webhook_secret:
            ts = str(int(time.time()))
            string_to_sign = f"{ts}\n{webhook_secret}"
            hmac_code = hmac.new(
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
            sign = base64.b64encode(hmac_code).decode("utf-8")
            payload["timestamp"] = ts
            payload["sign"] = sign

        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code >= 400:
                return f"HTTP {resp.status_code}: {resp.text[:200]}"
        return ""
    except Exception as exc:
        return f"发送失败: {exc}"


async def send_test_push() -> str:
    """通过默认消息推送引擎发送测试消息。成功返回空串。"""
    try:
        from app.platform.push.sender import send_push

        await send_push(
            "审计告警测试",
            "HEI-FastAPI 审计告警系统测试消息\n\n如果收到此消息，说明消息推送配置可复用于审计告警。",
        )
        return ""
    except Exception as exc:
        return f"推送失败: {exc}"


alert_dispatcher = AlertDispatcher()
