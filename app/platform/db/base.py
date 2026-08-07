""" Author: Charlie """

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class Base(DeclarativeBase):
    metadata = metadata


# 在 Session.flush 时注册 TimestampMixin created_by / updated_by 注入。
from app.platform.db import audit as _audit_hooks  # noqa: E402, F401
