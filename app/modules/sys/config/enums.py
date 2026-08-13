""" Author: Charlie

系统配置分类枚举：定义配置项所属的分类编码。
"""

from enum import StrEnum


class ConfigCategory(StrEnum):
    """系统配置分类。"""

    SYS = "SYS"
    AUTH_TOKEN = "AUTH_TOKEN"
    AUTH_LOGIN = "AUTH_LOGIN"
    AUTH_REGISTER = "AUTH_REGISTER"
    AUTH_PASSWORD = "AUTH_PASSWORD"
    STORAGE = "STORAGE"
    UPLOAD = "UPLOAD"
    MAIL = "MAIL"
    MAIL_TEMPLATE = "MAIL_TEMPLATE"
    SMS = "SMS"
    SMS_TEMPLATE = "SMS_TEMPLATE"
    PUSH = "PUSH"
    AUDIT_ALERT = "AUDIT_ALERT"
    OTHER = "OTHER"
