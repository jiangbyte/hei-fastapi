from enum import Enum


class StatusEnum(str, Enum):
    YES = "YES"
    NO = "NO"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"

    @property
    def desc(self) -> str:
        descriptions = {
            StatusEnum.YES: "是",
            StatusEnum.NO: "否",
            StatusEnum.ENABLED: "启用",
            StatusEnum.DISABLED: "禁用",
        }
        return descriptions.get(self, "")

class UserStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"

    @property
    def desc(self) -> str:
        descriptions = {
            UserStatusEnum.ACTIVE: "正常",
            UserStatusEnum.INACTIVE: "停用",
            UserStatusEnum.LOCKED: "锁定",
        }
        return descriptions.get(self, "")
