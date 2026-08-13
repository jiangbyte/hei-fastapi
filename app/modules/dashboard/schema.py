""" Author: Charlie

仪表盘概览响应模型：汇总、账户、IAM、运营、趋势与文件分布等分组。
"""

from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireInt


class DashboardTrendPoint(ApiSchema):
    """趋势图中的单个数据点。"""

    date: str
    type: str
    value: WireInt


class DashboardStatusItem(ApiSchema):
    """按名称统计的单项数据（如账户类型分布）。"""

    name: str
    value: WireInt


class DashboardSummary(ApiSchema):
    """概览汇总指标。"""

    account_total: WireInt
    online_sessions: WireInt
    file_total: WireInt
    storage_bytes: WireInt


class DashboardAccounts(ApiSchema):
    """账户维度统计。"""

    enabled: WireInt
    disabled: WireInt
    today_new: WireInt
    by_type: list[DashboardStatusItem]


class DashboardIam(ApiSchema):
    """IAM 资源数量统计。"""

    role_count: WireInt
    dept_count: WireInt
    group_count: WireInt
    menu_count: WireInt


class DashboardOpsToday(ApiSchema):
    """今日运营统计。"""

    audit_total: WireInt
    audit_failed: WireInt
    feedback_pending: WireInt


class DashboardTrends(ApiSchema):
    """账户与审计的 7 日趋势。"""

    account_trend: list[DashboardTrendPoint]
    audit_trend: list[DashboardTrendPoint]


class DashboardFiles(ApiSchema):
    """文件按内容类型分布。"""

    by_content_type: list[DashboardStatusItem]


class DashboardOverviewResponse(ApiSchema):
    """仪表盘概览响应根对象。"""

    summary: DashboardSummary
    accounts: DashboardAccounts
    iam: DashboardIam
    ops_today: DashboardOpsToday
    trends: DashboardTrends
    files: DashboardFiles
