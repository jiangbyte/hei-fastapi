from enum import Enum


class PermissionPathEnum(str, Enum):
    """权限来源路径（值越小优先级越高）"""
    DIRECT = "P0"        # User → Direct Permission
    USER_ROLE = "P1"     # User → Role → Permission
