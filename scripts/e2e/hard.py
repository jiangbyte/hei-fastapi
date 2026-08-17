"""Dialect / smoke hard checks (same spirit as hei-gin hardChecks)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HardCheck:
    name: str
    method: str
    path: str
    body: str = ""


def hard_checks() -> list[HardCheck]:
    return [
        HardCheck("health_live", "GET", "/api/v1/internal/health/live"),
        HardCheck("health_ready", "GET", "/api/v1/internal/health/ready"),
        HardCheck("dashboard_overview", "GET", "/api/v1/admin/dashboard/overview"),
        HardCheck("roles_page_ilike", "GET", "/api/v1/admin/sys/roles/page?current=1&size=5&name=admin"),
        HardCheck("banners_page_json", "GET", "/api/v1/admin/sys/banners/page?current=1&size=5&position=HOME_TOP"),
        HardCheck("banners_list", "GET", "/api/v1/admin/sys/banners/list?position=HOME_TOP"),
        HardCheck("notices_page", "GET", "/api/v1/admin/sys/notices/page?current=1&size=5&title=a"),
        HardCheck("notices_my_page", "GET", "/api/v1/admin/sys/notices/my-page?current=1&size=5"),
        HardCheck("accounts_page_ilike", "GET", "/api/v1/admin/sys/accounts/page?current=1&size=5&account=super"),
        HardCheck("codegen_tables", "GET", "/api/v1/admin/sys/codegen/tables"),
        HardCheck("portal_banners_list", "GET", "/api/v1/portal/sys/banners/list?position=HOME_TOP"),
        HardCheck("portal_dicts_tree", "GET", "/api/v1/portal/sys/dicts/tree"),
        HardCheck("portal_notices_list", "GET", "/api/v1/portal/sys/notices/list"),
        HardCheck("admin_me", "GET", "/api/v1/admin/me"),
    ]
