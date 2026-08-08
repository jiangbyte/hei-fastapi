""" Author: Charlie """

from enum import StrEnum


class NoticeKind(StrEnum):
    NOTIFICATION = "NOTIFICATION"
    ANNOUNCEMENT = "ANNOUNCEMENT"


class NotificationCategory(StrEnum):
    ORDER = "ORDER"
    APPROVAL = "APPROVAL"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    BIZ = "BIZ"


class NoticeStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    REVOKED = "REVOKED"


class NotificationSeverity(StrEnum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    URGENT = "URGENT"


class TargetScope(StrEnum):
    ALL = "ALL"
    ACCOUNT_TYPE = "ACCOUNT_TYPE"
    SPECIFIC = "SPECIFIC"


class FeedbackStatus(StrEnum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
