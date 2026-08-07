""" Author: Charlie """

from collections.abc import Iterable
from typing import Annotated, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from app.core.schema.datetime import (
    ensure_utc_datetime,
    is_datetime_annotation,
    normalize_orm_datetimes,
)
from app.core.schema.wire import serialize_wire_value

SchemaT = TypeVar("SchemaT", bound="ApiSchema")
Id = Annotated[str, Field(min_length=1, max_length=64)]


class ApiSchema(BaseModel):
    """全局基础 DTO：内部保留真实类型，JSON 标量统一字符串化。"""

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    @field_serializer("*", when_used="json")
    def serialize_wire_fields(self, value):
        """JSON 出站：datetime / bool / int / float / Decimal / Enum → 字符串。"""
        return serialize_wire_value(value)

    @model_validator(mode="after")
    def normalize_datetimes(self):
        """在模型创建后规范化 datetime 字段，确保内部始终持有 UTC 时间对象。"""
        for field_name, field_info in self.__class__.model_fields.items():
            if not is_datetime_annotation(field_info.annotation):
                continue
            value = getattr(self, field_name, None)
            if value is not None:
                setattr(self, field_name, ensure_utc_datetime(value))
        return self


class IdQuery(ApiSchema):
    id: Id


class IdsRequest(ApiSchema):
    ids: list[Id] = Field(min_length=1)


class KeywordQuery(ApiSchema):
    keyword: str | None = None


def to_schema(schema_cls: type[SchemaT], item: object) -> SchemaT:
    """通过 Pydantic attributes 模式将 ORM/实体对象转换为 API schema。"""
    normalize_orm_datetimes(item)
    return schema_cls.model_validate(item)


def to_schema_list(schema_cls: type[SchemaT], items: Iterable[object]) -> list[SchemaT]:
    """将 ORM/实体对象列表转换为 API schema 列表。"""
    return [to_schema(schema_cls, item) for item in items]
