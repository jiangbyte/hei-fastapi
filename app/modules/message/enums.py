""" Author: Charlie """

from enum import StrEnum


class ConversationType(StrEnum):
    DIRECT = "DIRECT"
    GROUP = "GROUP"


class ConversationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class ConversationMemberRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class MessageType(StrEnum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    SYSTEM = "SYSTEM"


class MessageContentType(StrEnum):
    TEXT = "TEXT"
    RICH = "RICH"
    MARKDOWN = "MARKDOWN"


class MessageSenderType(StrEnum):
    USER = "USER"
    SYSTEM = "SYSTEM"


class GroupStatus(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    DISSOLVED = "DISSOLVED"


class GroupJoinMode(StrEnum):
    FREE = "FREE"
    APPROVAL = "APPROVAL"
    INVITE_ONLY = "INVITE_ONLY"


class GroupJoinRequestStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class FriendStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class FriendRequestStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class NotificationCategory(StrEnum):
    ORDER = "ORDER"
    APPROVAL = "APPROVAL"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    BIZ = "BIZ"


class NotificationStatus(StrEnum):
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


class AnnouncementStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    REVOKED = "REVOKED"


class DeviceType(StrEnum):
    WEB = "WEB"
    IOS = "IOS"
    ANDROID = "ANDROID"
    MINIPROGRAM = "MINIPROGRAM"
    DESKTOP = "DESKTOP"


class PushProvider(StrEnum):
    APNS = "APNS"
    FCM = "FCM"
    HUAWEI = "HUAWEI"
    XIAOMI = "XIAOMI"


class OfflineEventType(StrEnum):
    NEW_MESSAGE = "NEW_MESSAGE"
    NEW_NOTIFICATION = "NEW_NOTIFICATION"
    NEW_ANNOUNCEMENT = "NEW_ANNOUNCEMENT"
    FRIEND_REQUEST = "FRIEND_REQUEST"
    GROUP_JOIN_REQUEST = "GROUP_JOIN_REQUEST"


class OfflineMessageStatus(StrEnum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"


class AttachmentType(StrEnum):
    FILE = "FILE"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


class FeedbackStatus(StrEnum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
