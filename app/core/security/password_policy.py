""" Author: Charlie

密码策略校验——强度验证与常见密码检查，对齐等保密码复杂度要求。

所有策略参数由 ``settings.password_policy`` 驱动。
"""
import re

from app.core.config.settings import settings
from app.core.exceptions.business import BusinessError

# fmt: off
_COMMON_PASSWORDS: frozenset[str] = frozenset({
    "123456", "password", "12345678", "qwerty", "123456789",
    "12345", "1234", "111111", "1234567", "sunshine",
    "qwerty123", "iloveyou", "princess", "admin", "welcome",
    "666666", "abc123", "football", "123123", "monkey",
    "654321", "!@#$%^&*", "charlie", "aa123456", "donald",
    "password1", "qwerty12345", "1234567890", "letmein", "password123",
    "admin123", "passw0rd", "hello123", "test123", "root",
    "administrator", "p@ssw0rd", "qwertyuiop", "asdfghjkl", "zxcvbnm",
    "pass123", "password!", "default", "change123", "changeme",
})
# fmt: on


def validate_password_strength(password: str) -> None:
    """按配置策略校验密码。

    违反首条规则时抛出带用户可读消息的 ``BusinessError``。
    """
    policy = settings.password_policy

    if len(password) < policy.min_length:
        raise BusinessError(f"密码长度至少 {policy.min_length} 个字符")
    if len(password) > policy.max_length:
        raise BusinessError(f"密码长度不能超过 {policy.max_length} 个字符")

    if policy.require_uppercase and not re.search(r"[A-Z]", password):
        raise BusinessError("密码必须包含至少一个大写字母")

    if policy.require_lowercase and not re.search(r"[a-z]", password):
        raise BusinessError("密码必须包含至少一个小写字母")

    if policy.require_digit and not re.search(r"[0-9]", password):
        raise BusinessError("密码必须包含至少一个数字")

    if policy.require_special and not re.search(r"[^A-Za-z0-9]", password):
        raise BusinessError("密码必须包含至少一个特殊字符")

    if policy.common_password_check and password.lower() in _COMMON_PASSWORDS:
        raise BusinessError("密码过于常见，请更换")


def estimate_strength_level(password: str) -> int:
    """返回粗略强度分数（0–4），供前端展示。"""
    score = 0
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r"[A-Z]", password) and re.search(r"[a-z]", password):
        score += 1
    if re.search(r"[0-9]", password) and re.search(r"[^A-Za-z0-9]", password):
        score += 1
    return min(score, 4)
