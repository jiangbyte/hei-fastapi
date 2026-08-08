""" Author: Charlie """

from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireInt


class DashboardTrendPoint(ApiSchema):
    date: str
    type: str
    value: WireInt


class DashboardStatusItem(ApiSchema):
    name: str
    value: WireInt


class DashboardSummary(ApiSchema):
    account_total: WireInt
    online_sessions: WireInt
    file_total: WireInt
    storage_bytes: WireInt


class DashboardAccounts(ApiSchema):
    enabled: WireInt
    disabled: WireInt
    today_new: WireInt
    by_type: list[DashboardStatusItem]


class DashboardIam(ApiSchema):
    role_count: WireInt
    dept_count: WireInt
    group_count: WireInt
    menu_count: WireInt


class DashboardOpsToday(ApiSchema):
    audit_total: WireInt
    audit_failed: WireInt
    feedback_pending: WireInt


class DashboardTrends(ApiSchema):
    account_trend: list[DashboardTrendPoint]
    audit_trend: list[DashboardTrendPoint]


class DashboardFiles(ApiSchema):
    by_content_type: list[DashboardStatusItem]


class DashboardOverviewResponse(ApiSchema):
    summary: DashboardSummary
    accounts: DashboardAccounts
    iam: DashboardIam
    ops_today: DashboardOpsToday
    trends: DashboardTrends
    files: DashboardFiles
