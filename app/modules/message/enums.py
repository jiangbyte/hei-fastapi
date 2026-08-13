""" Author: Charlie

消息模块枚举定义：通知/公告类型、分类、状态、等级与目标范围等。
"""

from enum import StrEnum


class NoticeKind(StrEnum):
    """消息类型：通知或公告。"""

    NOTIFICATION = "NOTIFICATION"  # 通知
    ANNOUNCEMENT = "ANNOUNCEMENT"  # 公告


class NotificationCategory(StrEnum):
    """通知分类。"""

    ORDER = "ORDER"  # 订单
    APPROVAL = "APPROVAL"  # 审批
    SYSTEM = "SYSTEM"  # 系统
    SECURITY = "SECURITY"  # 安全
    BIZ = "BIZ"  # 业务


class NoticeStatus(StrEnum):
    """消息状态。"""

    DRAFT = "DRAFT"  # 草稿
    PUBLISHED = "PUBLISHED"  # 已发布
    REVOKED = "REVOKED"  # 已撤回


class NotificationSeverity(StrEnum):
    """通知等级。"""

    INFO = "INFO"  # 提示
    SUCCESS = "SUCCESS"  # 成功
    WARNING = "WARNING"  # 警告
    ERROR = "ERROR"  # 错误
    URGENT = "URGENT"  # 紧急


class TargetScope(StrEnum):
    """消息目标范围。"""

    ALL = "ALL"  # 全部
    ACCOUNT_TYPE = "ACCOUNT_TYPE"  # 按账户类型
    SPECIFIC = "SPECIFIC"  # 指定用户


class FeedbackStatus(StrEnum):
    """反馈处理状态。"""

    PENDING = "PENDING"  # 待处理
    REVIEWED = "REVIEWED"  # 已受理
    RESOLVED = "RESOLVED"  # 已解决
    CLOSED = "CLOSED"  # 已关闭
