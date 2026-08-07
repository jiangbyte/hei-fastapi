""" Author: Charlie """

from enum import StrEnum


class ConfigCategory(StrEnum):
    """系统配置分类"""

    AUTH_TOKEN = "AUTH_TOKEN"
    AUTH_LOGIN = "AUTH_LOGIN"
    AUTH_REGISTER = "AUTH_REGISTER"
    AUTH_PASSWORD = "AUTH_PASSWORD"
    STORAGE = "STORAGE"
    UPLOAD = "UPLOAD"
    MAIL = "MAIL"
    OTHER = "OTHER"
