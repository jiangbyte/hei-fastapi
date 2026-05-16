from enum import Enum


class LoginTypeEnum(str, Enum):
    BUSINESS = "BUSINESS"
    CONSUMER = "CONSUMER"

    @property
    def desc(self) -> str:
        descriptions = {
            LoginTypeEnum.BUSINESS: "后台登录",
            LoginTypeEnum.CONSUMER: "客户端登录",
        }
        return descriptions.get(self, "")


class PermissionCategoryEnum(str, Enum):
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"

    @property
    def desc(self) -> str:
        descriptions = {
            PermissionCategoryEnum.BACKEND: "后端权限",
            PermissionCategoryEnum.FRONTEND: "前端权限",
        }
        return descriptions.get(self, "")


class PermissionScopeEnum(str, Enum):
    ALL = "ALL"
    ORG = "ORG"
    ORG_AND_BELOW = "ORG_AND_BELOW"
    SELF = "SELF"

    @property
    def desc(self) -> str:
        descriptions = {
            PermissionScopeEnum.ALL: "全部",
            PermissionScopeEnum.ORG: "本组织",
            PermissionScopeEnum.ORG_AND_BELOW: "本组织及以下",
            PermissionScopeEnum.SELF: "本人",
        }
        return descriptions.get(self, "")




class DataScopeEnum(str, Enum):
    ALL = "ALL"
    SELF = "SELF"
    ORG = "ORG"
    ORG_AND_BELOW = "ORG_AND_BELOW"
    CUSTOM_ORG = "CUSTOM_ORG"
    GROUP = "GROUP"
    GROUP_AND_BELOW = "GROUP_AND_BELOW"
    CUSTOM_GROUP = "CUSTOM_GROUP"

    @classmethod
    def most_restrictive(cls, *scopes: str) -> str:
        priority = {"SELF": 0, "CUSTOM_GROUP": 1, "CUSTOM_ORG": 2, "GROUP_AND_BELOW": 3, "GROUP": 4, "ORG_AND_BELOW": 5, "ORG": 6, "ALL": 7}
        return min(scopes, key=lambda s: priority.get(s, 99))


class CheckModeEnum(str, Enum):
    AND = "AND"
    OR = "OR"

    @property
    def desc(self) -> str:
        descriptions = {
            CheckModeEnum.AND: "且",
            CheckModeEnum.OR: "或",
        }
        return descriptions.get(self, "")


class PermissionPathEnum(str, Enum):
    """权限来源路径（值越小优先级越高）"""
    DIRECT = "P0"        # User → Direct Permission
    USER_ROLE = "P1"     # User → Role → Permission
