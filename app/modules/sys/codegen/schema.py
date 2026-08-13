""" Author: Charlie

代码生成相关 Schema：方案创建/更新、字段配置、数据库内省与预览文件。
"""

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireBool, WireInt

CodegenType = Literal["TABLE", "TREE", "LEFT_TREE_TABLE", "MASTER_DETAIL"]  # 生成类型
CodegenTableRole = Literal["MAIN", "SUB"]  # 表角色：主表/子表


class CodegenPlanCreateRequest(ApiSchema):
    """代码生成方案创建请求。"""

    name: str = Field(min_length=1, max_length=128)
    gen_type: CodegenType = "TABLE"
    author: str = Field(min_length=1, max_length=64)
    description: str | None = None
    main_table: str = Field(min_length=1, max_length=128)
    main_pk: str = Field(default="id", min_length=1, max_length=128)
    main_entity_name: str = Field(min_length=1, max_length=128)
    main_module_path: str = Field(min_length=1, max_length=255)
    main_business_name: str = Field(min_length=1, max_length=128)
    api_prefix: str = Field(min_length=1, max_length=255)
    permission_prefix: str = Field(min_length=1, max_length=128)
    resource_module_id: str | None = Field(default=None, max_length=64)
    parent_resource_id: str | None = Field(default=None, max_length=64)
    menu_name: str = Field(min_length=1, max_length=64)
    menu_path: str = Field(min_length=1, max_length=255)
    component_path: str = Field(min_length=1, max_length=255)
    icon: str | None = Field(default=None, max_length=255)
    sort: WireInt = 99
    tree_parent_field: str | None = Field(default=None, max_length=128)
    tree_label_field: str | None = Field(default=None, max_length=128)
    sub_table: str | None = Field(default=None, max_length=128)
    sub_pk: str | None = Field(default=None, max_length=128)
    sub_foreign_key: str | None = Field(default=None, max_length=128)
    sub_entity_name: str | None = Field(default=None, max_length=128)
    sub_business_name: str | None = Field(default=None, max_length=128)

    @field_validator("author")
    @classmethod
    def validate_author(cls, value: str) -> str:
        """去除作者名首尾空白并校验非空。"""
        value = value.strip()
        if not value:
            raise ValueError("author is required")
        return value

    @model_validator(mode="after")
    def validate_codegen_type(self):
        """校验树形/关系型方案所需的树字段与子表配置齐全。"""
        if self.gen_type in {"TREE", "LEFT_TREE_TABLE"}:
            if not self.tree_parent_field:
                raise ValueError("tree_parent_field is required for tree codegen")
            if not self.tree_label_field:
                raise ValueError("tree_label_field is required for tree codegen")
        if self.gen_type in {"LEFT_TREE_TABLE", "MASTER_DETAIL"}:
            if not self.sub_table:
                raise ValueError("sub_table is required for relation codegen")
            if not self.sub_pk:
                raise ValueError("sub_pk is required for relation codegen")
            if not self.sub_foreign_key:
                raise ValueError("sub_foreign_key is required for relation codegen")
            if not self.sub_entity_name:
                raise ValueError("sub_entity_name is required for relation codegen")
            if not self.sub_business_name:
                raise ValueError("sub_business_name is required for relation codegen")
        return self


class CodegenPlanUpdateRequest(CodegenPlanCreateRequest):
    """代码生成方案更新请求，在创建字段基础上增加主键。"""

    id: str = Field(min_length=1, max_length=64)


class CodegenPlanPageQuery(PageQuery):
    """代码生成方案分页查询参数。"""

    name: str | None = Field(default=None, max_length=128)
    main_table: str | None = Field(default=None, max_length=128)
    gen_type: CodegenType | None = None


class SysCodegenPlanSchema(ApiSchema):
    """代码生成方案响应模型。"""

    id: str
    name: str
    gen_type: CodegenType
    author: str | None = None
    description: str | None = None
    main_table: str
    main_pk: str
    main_entity_name: str
    main_module_path: str
    main_business_name: str
    api_prefix: str
    permission_prefix: str
    resource_module_id: str | None = None
    parent_resource_id: str | None = None
    menu_name: str
    menu_path: str
    component_path: str
    icon: str | None = None
    sort: WireInt
    tree_parent_field: str | None = None
    tree_label_field: str | None = None
    sub_table: str | None = None
    sub_pk: str | None = None
    sub_foreign_key: str | None = None
    sub_entity_name: str | None = None
    sub_business_name: str | None = None
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None


class CodegenFieldUpdateItem(ApiSchema):
    """代码生成字段配置项。"""

    id: str | None = Field(default=None, max_length=64)
    table_role: CodegenTableRole = "MAIN"
    column_name: str = Field(min_length=1, max_length=128)
    column_comment: str | None = Field(default=None, max_length=255)
    db_type: str = Field(min_length=1, max_length=128)
    python_type: str = Field(default="str", min_length=1, max_length=64)
    typescript_type: str = Field(default="string", min_length=1, max_length=64)
    form_widget: str = Field(default="input", min_length=1, max_length=32)
    dict_code: str | None = Field(default=None, max_length=128)
    query_operator: str | None = Field(default=None, max_length=32)
    show_in_table: WireBool = True
    show_in_form: WireBool = True
    show_in_detail: WireBool = True
    show_in_query: WireBool = False
    is_primary_key: WireBool = False
    is_required: WireBool = False
    is_unique: WireBool = False
    is_nullable: WireBool = True
    max_length: WireInt | None = None
    sort: WireInt = 99


class CodegenFieldsUpdateBatchRequest(ApiSchema):
    """代码生成字段批量更新请求。"""

    plan_id: str = Field(min_length=1, max_length=64)
    fields: list[CodegenFieldUpdateItem]


class SysCodegenFieldSchema(CodegenFieldUpdateItem):
    """代码生成字段响应模型。"""

    id: str
    plan_id: str
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None


class DatabaseTableSchema(ApiSchema):
    """数据库表响应模型。"""

    table_name: str
    table_comment: str | None = None


class DatabaseColumnSchema(ApiSchema):
    """数据库列响应模型。"""

    column_name: str
    column_comment: str | None = None
    db_type: str
    python_type: str
    typescript_type: str
    is_primary_key: WireBool
    is_nullable: WireBool
    max_length: WireInt | None = None


class CodegenPreviewFile(ApiSchema):
    """代码生成预览文件。"""

    path: str
    language: str
    content: str


class CodegenPreviewSchema(ApiSchema):
    """代码生成预览响应，包含文件列表。"""

    files: list[CodegenPreviewFile]


class CodegenTableColumnsQuery(ApiSchema):
    """查询表列的请求参数。"""

    table_name: str = Field(min_length=1, max_length=128)


class CodegenFieldsQuery(ApiSchema):
    """查询字段的请求参数。"""

    plan_id: str = Field(min_length=1, max_length=64)
    table_role: str | None = Field(default=None, max_length=16)


class CodegenParentResourcesQuery(ApiSchema):
    """查询父资源的请求参数。"""

    module_id: str | None = Field(default=None, max_length=64)


class CodegenParentResourceOption(ApiSchema):
    """父资源选项（树形结构）。"""

    id: str
    parent_id: str | None = None
    code: str
    name: str
    resource_type: str
    module_id: str | None = None
    children: list["CodegenParentResourceOption"] = Field(default_factory=list)
