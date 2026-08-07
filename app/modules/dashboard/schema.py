""" Author: Charlie """

from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireFloat, WireInt


class DashboardMetric(ApiSchema):
    key: str
    value: WireInt | float
    trend_value: WireFloat | None = None


class DashboardTrendPoint(ApiSchema):
    date: str
    type: str
    value: WireInt | float


class DashboardStatusItem(ApiSchema):
    name: str
    value: WireInt


class DashboardOverviewResponse(ApiSchema):
    metrics: list[DashboardMetric]
    account_trend: list[DashboardTrendPoint]
    file_type_share: list[DashboardStatusItem]
