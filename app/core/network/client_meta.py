""" Author: Charlie

请求客户端元数据辅助（IP / UA / 设备标签）。
"""
from __future__ import annotations

from starlette.requests import Request

from app.core.network.client_ip import get_client_ip
from app.deps.context import client_ip_ctx, user_agent_ctx


def request_user_agent(request: Request) -> str | None:
    return user_agent_ctx.get() or request.headers.get("user-agent")


def request_client_ip(request: Request) -> str | None:
    return client_ip_ctx.get() or get_client_ip(request)


def device_label_from_user_agent(user_agent: str | None) -> str | None:
    if not user_agent:
        return None
    value = user_agent.lower()
    if "mobile" in value or "android" in value or "iphone" in value:
        return "Mobile"
    if "ipad" in value or "tablet" in value:
        return "Tablet"
    return "Desktop"


def request_client_meta(request: Request) -> tuple[str | None, str | None, str | None]:
    """返回 (client_ip, user_agent, device_label)。"""
    ua = request_user_agent(request)
    return request_client_ip(request), ua, device_label_from_user_agent(ua)
