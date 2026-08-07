""" Author: Charlie """

from enum import StrEnum


class RoleScopeType(StrEnum):
    """
    角色范围类型
    """

    PLATFORM = "PLATFORM"  # 平台级
    DEPT = "DEPT"  # 部门级


class ResourceType(StrEnum):
    """
    资源类型
    """

    CATALOG = "CATALOG"  # 目录
    MENU = "MENU"  # 菜单
    PAGE = "PAGE"  # 页面
    BUTTON = "BUTTON"  # 按钮
    ACTION = "ACTION"  # 操作
    API_GROUP = "API_GROUP"  # API组


class ResourceModuleClient(StrEnum):
    """
    资源模块所属端
    """

    ADMIN = "ADMIN"  # 管理后台
    PORTAL = "PORTAL"  # 门户端


class GrantSubjectType(StrEnum):
    """
    授权对象类型
    """

    ROLE = "ROLE"  # 角色
    ACCOUNT = "ACCOUNT"  # 账户
    GROUP = "GROUP"  # 组


class GrantMode(StrEnum):
    """
    授权模式
    """

    DIRECT = "DIRECT"  # 直接授权
    CASCADE = "CASCADE"  # 级联授权


class GrantEffect(StrEnum):
    """
    授权效果
    """

    ALLOW = "ALLOW"  # 允许
    DENY = "DENY"  # 拒绝


class IamRelationType(StrEnum):
    """
    IAM 通用关系类型
    """

    ACCOUNT_ROLE = "ACCOUNT_ROLE"
    ACCOUNT_DEPT = "ACCOUNT_DEPT"
    ACCOUNT_GROUP = "ACCOUNT_GROUP"
    GROUP_ROLE = "GROUP_ROLE"
    SUBJECT_RESOURCE_GRANT = "SUBJECT_RESOURCE_GRANT"
    SUBJECT_PERMISSION_GRANT = "SUBJECT_PERMISSION_GRANT"
    RESOURCE_PERMISSION = "RESOURCE_PERMISSION"


class IamRelationSubjectType(StrEnum):
    """
    IAM 通用关系主体类型
    """

    ACCOUNT = "ACCOUNT"
    GROUP = "GROUP"
    ROLE = "ROLE"
    RESOURCE = "RESOURCE"


class IamRelationTargetType(StrEnum):
    """
    IAM 通用关系目标类型
    """

    ACCOUNT = "ACCOUNT"
    GROUP = "GROUP"
    ROLE = "ROLE"
    DEPT = "DEPT"
    RESOURCE = "RESOURCE"
    PERMISSION = "PERMISSION"


class AccountIdentityType(StrEnum):
    """
    账户登录标识类型
    """

    ACCOUNT = "ACCOUNT"  # 登录账号
    EMAIL = "EMAIL"  # 邮箱登录标识
    PHONE = "PHONE"  # 手机号登录标识


class AccountIdentityBindStatus(StrEnum):
    """
    账户登录标识绑定状态
    """

    BOUND = "BOUND"  # 已绑定
    UNBOUND = "UNBOUND"  # 未绑定
