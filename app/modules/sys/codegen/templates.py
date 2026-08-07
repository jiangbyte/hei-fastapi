""" Author: Charlie """

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from re import sub
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.modules.sys.codegen.model import SysCodegenField, SysCodegenPlan
from app.modules.sys.codegen.schema import CodegenPreviewFile
from app.platform.id_generator.snowflake import generate_snowflake_id

AUDIT_COLUMNS = {"created_at", "created_by", "updated_at", "updated_by"}
TEMPLATE_DIR = Path(__file__).resolve().parent / "template_files"
MENU_PERMISSION_ACTIONS = (
    ("page", "分页", 10),
    ("create", "新增", 20),
    ("detail", "详情", 30),
    ("update", "编辑", 40),
    ("delete", "删除", 50),
    ("tables", "读取数据表", 60),
    ("preview", "预览", 70),
    ("download", "下载", 80),
)
TREE_MENU_PERMISSION_ACTION = ("list", "树列表", 90)


@dataclass(frozen=True)
class RenderContext:
    plan: SysCodegenPlan
    main_fields: list[SysCodegenField]
    sub_fields: list[SysCodegenField]
    generated_at: str

    @property
    def backend_parts(self) -> tuple[str, ...]:
        return tuple(
            python_identifier(part)
            for part in self.plan.main_module_path.strip("/.").split("/")
            if part.strip()
        )

    @property
    def module_import(self) -> str:
        return ".".join(["app.modules", *self.backend_parts])

    @property
    def module_name(self) -> str:
        return ".".join(self.backend_parts)

    @property
    def backend_dir(self) -> str:
        return "/".join(["app/modules", *self.backend_parts])

    @property
    def view_path(self) -> str:
        return str(PurePosixPath("web/admin/src/views") / self.plan.component_path.strip("/"))

    @property
    def view_component_dir(self) -> str:
        view_path = PurePosixPath(self.view_path)
        return str(view_path.parent / "components")

    @property
    def child_view_component_dir(self) -> str:
        return str(PurePosixPath(self.view_component_dir) / "children")

    @property
    def api_file(self) -> str:
        component_path = PurePosixPath(self.plan.component_path.strip("/"))
        parts = component_path.parts
        if len(parts) >= 2 and parts[-1] == "index.vue":
            return (
                str(PurePosixPath("web/admin/src/api") / PurePosixPath(*parts[:-1])).replace(
                    ".vue", ".ts"
                )
                + ".ts"
            )
        return str(
            PurePosixPath("web/admin/src/api") / f"{snake_case(self.plan.main_entity_name)}.ts"
        )

    @property
    def api_export(self) -> str:
        rel = PurePosixPath(self.api_file).relative_to("web/admin/src/api")
        return f"export * as {camel_case(self.plan.main_entity_name)}Api from './{rel.with_suffix('').as_posix()}'"


def render_files(
    plan: SysCodegenPlan,
    main_fields: list[SysCodegenField],
    sub_fields: list[SysCodegenField],
) -> list[CodegenPreviewFile]:
    ctx = RenderContext(
        plan=plan,
        main_fields=main_fields,
        sub_fields=sub_fields,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    file_specs = [
        (f"{ctx.backend_dir}/__init__.py", "python", "init.py.j2"),
        (f"{ctx.backend_dir}/model.py", "python", "model.py.j2"),
        (f"{ctx.backend_dir}/schema.py", "python", "schema.py.j2"),
        (f"{ctx.backend_dir}/repository.py", "python", "repository.py.j2"),
        (f"{ctx.backend_dir}/service.py", "python", "service.py.j2"),
        (f"{ctx.backend_dir}/router.py", "python", "router.py.j2"),
        (f"{ctx.backend_dir}/module.py", "python", "module.py.j2"),
        (ctx.api_file, "typescript", "api.ts.j2"),
        ("web/admin/src/api/index.ts.append", "typescript", "api_index_export.ts.j2"),
        (ctx.view_path, "vue", "index.vue.j2"),
        (f"{ctx.view_component_dir}/ModalForm.vue", "vue", "modal_form.vue.j2"),
        (f"{ctx.view_component_dir}/ModalDetail.vue", "vue", "modal_detail.vue.j2"),
        (
            f"scripts/{snake_case(plan.main_entity_name)}_menu_permission.sql",
            "sql",
            "menu_permission.sql.j2",
        ),
    ]
    if (
        plan.gen_type in {"LEFT_TREE_TABLE", "MASTER_DETAIL"}
        and plan.sub_entity_name
        and plan.sub_table
        and plan.sub_pk
    ):
        file_specs.extend(
            [
                (
                    f"{ctx.child_view_component_dir}/ChildModalForm.vue",
                    "vue",
                    "child_modal_form.vue.j2",
                ),
                (
                    f"{ctx.child_view_component_dir}/ChildModalDetail.vue",
                    "vue",
                    "child_modal_detail.vue.j2",
                ),
            ]
        )
    return [
        CodegenPreviewFile(path=path, language=language, content=render_template(template, ctx))
        for path, language, template in file_specs
    ]


def render_template(template_name: str, ctx: RenderContext) -> str:
    env = _environment()
    template = env.get_template(template_name)
    has_tree = ctx.plan.gen_type in {"TREE", "LEFT_TREE_TABLE"}
    has_sub = ctx.plan.gen_type in {"LEFT_TREE_TABLE", "MASTER_DETAIL"}
    main_table_exclude = (
        {ctx.plan.tree_parent_field}
        if ctx.plan.gen_type == "TREE" and ctx.plan.tree_parent_field
        else set()
    )
    main = entity_context(
        ctx.plan.main_entity_name,
        ctx.plan.main_table,
        ctx.plan.main_pk,
        ctx.main_fields,
        table_exclude=main_table_exclude,
    )
    sub = (
        entity_context(
            ctx.plan.sub_entity_name, ctx.plan.sub_table, ctx.plan.sub_pk, ctx.sub_fields
        )
        if ctx.plan.sub_entity_name and ctx.plan.sub_table and ctx.plan.sub_pk
        else None
    )
    target = sub if template_name.startswith("child_") and sub else main
    has_tree_parent_form = bool(
        has_tree
        and not template_name.startswith("child_")
        and ctx.plan.tree_parent_field
        and any(
            field["name"] == ctx.plan.tree_parent_field for field in main.get("form_fields", [])
        )
    )
    return (
        template.render(
            ctx=ctx,
            plan=ctx.plan,
            main=main,
            sub=sub,
            target=target,
            is_child_template=template_name.startswith("child_"),
            has_tree=has_tree,
            has_tree_parent_form=has_tree_parent_form,
            has_sub=has_sub,
            needs_list_permission=has_tree,
            menu_permission=menu_permission_context(has_tree)
            if template_name == "menu_permission.sql.j2"
            else None,
        ).rstrip()
        + "\n"
    )


def _environment() -> Environment:
    # 代码生成输出 Python/TS/Vue 源码而非 HTML — autoescape 会破坏模板。
    env = Environment(  # nosec B701
        loader=FileSystemLoader(TEMPLATE_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,
    )
    env.filters.update(
        camel=camel_case,
        snake=snake_case,
        sql=sql_str,
        vue_default=vue_default,
        ts_api_name=lambda value: f"{camel_case(value)}Api",
    )
    return env


def entity_context(
    entity_name: str | None,
    table_name: str | None,
    pk_name: str | None,
    fields: list[SysCodegenField],
    table_exclude: set[str] | None = None,
) -> dict[str, Any]:
    if not entity_name or not table_name or not pk_name:
        return {}
    table_exclude = table_exclude or set()
    model_fields = [
        field_context(field) for field in fields if field.column_name not in AUDIT_COLUMNS
    ]
    form_fields = [field_context(field) for field in fields if is_form_field(field)]
    query_fields = [
        field_context(field) for field in fields if field.show_in_query and not field.is_primary_key
    ]
    table_fields = [
        field_context(field)
        for field in fields
        if field.show_in_table
        and field.column_name not in AUDIT_COLUMNS
        and field.column_name not in table_exclude
    ]
    detail_fields = [
        field_context(field)
        for field in fields
        if field.show_in_detail and field.column_name not in AUDIT_COLUMNS
    ]
    return {
        "entity_name": entity_name,
        "var_name": camel_case(entity_name),
        "table_name": table_name,
        "pk_name": pk_name,
        "fields": fields,
        "model_fields": model_fields,
        "form_fields": form_fields,
        "query_fields": query_fields,
        "table_fields": table_fields,
        "detail_fields": detail_fields,
        "has_form_datetime": any(field["is_datetime"] for field in form_fields),
        "has_form_json": any(field["is_json"] for field in form_fields),
        "has_form_bool": any(field["is_bool"] for field in form_fields),
        "has_form_int": any(field["python_type"] == "int" for field in form_fields),
        "has_form_float": any(field["python_type"] == "float" for field in form_fields),
        "has_detail_json": any(field["is_json"] for field in detail_fields),
        "has_table_dict": any(field["dict_code"] for field in table_fields),
        "has_table_bool": any(field["is_bool"] for field in table_fields),
        "has_table_tag": any(field["dict_code"] or field["is_bool"] for field in table_fields),
        "has_detail_dict": any(field["dict_code"] for field in detail_fields),
        "needs_form_normalize": any(
            field["is_datetime"] or field["is_json"] for field in form_fields
        ),
        "needs_submit_normalize": any(
            field["is_datetime"] or field["is_json"] for field in form_fields
        ),
        "uses_wire_bool": any(
            "WireBool" in field["schema_type"] or "WireBool" in field["query_schema_type"]
            for field in (*form_fields, *detail_fields, *query_fields)
        ),
        "uses_wire_int": any(
            "WireInt" in field["schema_type"] or "WireInt" in field["query_schema_type"]
            for field in (*form_fields, *detail_fields, *query_fields)
        ),
        "uses_wire_float": any(
            "WireFloat" in field["schema_type"] or "WireFloat" in field["query_schema_type"]
            for field in (*form_fields, *detail_fields, *query_fields)
        ),
    }


def menu_permission_context(needs_list_permission: bool) -> dict[str, Any]:
    actions = list(MENU_PERMISSION_ACTIONS)
    if needs_list_permission:
        actions.append(TREE_MENU_PERMISSION_ACTION)
    return {
        "menu_id": generate_snowflake_id(),
        "actions": [
            {
                "key": key,
                "label": label,
                "sort": sort,
                "resource_id": generate_snowflake_id(),
                "relation_id": generate_snowflake_id(),
            }
            for key, label, sort in actions
        ],
    }


def field_context(field: SysCodegenField) -> dict[str, Any]:
    python_type = normalized_py_type(field)
    is_datetime = field.form_widget == "datetime" or python_type == "datetime"
    is_json = is_json_field(field, python_type)
    return {
        "name": field.column_name,
        "label": field.column_comment or field.column_name,
        "comment": field.column_comment,
        "db_type": field.db_type,
        "python_type": python_type,
        "schema_type": schema_py_type(field),
        "query_schema_type": query_schema_py_type(field),
        "ts_type": field.typescript_type,
        "sa_type": sa_type(field),
        "form_widget": field.form_widget,
        "dict_code": field.dict_code,
        "query_operator": field.query_operator or "LIKE",
        "show_in_table": field.show_in_table,
        "show_in_form": field.show_in_form,
        "show_in_detail": field.show_in_detail,
        "show_in_query": field.show_in_query,
        "is_primary_key": field.is_primary_key,
        "is_required": field.is_required,
        "is_nullable": field.is_nullable,
        "max_length": field.max_length,
        "default": schema_default(field),
        "vue_default": vue_default(field),
        "is_datetime": is_datetime,
        "is_json": is_json,
        "is_bool": python_type == "bool",
    }


def is_form_field(field: SysCodegenField) -> bool:
    return (
        field.show_in_form and not field.is_primary_key and field.column_name not in AUDIT_COLUMNS
    )


def normalized_py_type(field: SysCodegenField) -> str:
    if field.python_type == "datetime":
        return "datetime"
    if field.python_type == "dict":
        return "dict[str, Any]"
    return field.python_type


def is_json_field(field: SysCodegenField, python_type: str | None = None) -> bool:
    raw_python_type = python_type or normalized_py_type(field)
    return raw_python_type in {"dict", "dict[str, Any]"} or "json" in field.db_type.lower()


def _wire_schema_type(raw: str) -> str:
    mapping = {"int": "WireInt", "bool": "WireBool", "float": "WireFloat"}
    return mapping.get(raw, raw)


def schema_py_type(field: SysCodegenField) -> str:
    raw = _wire_schema_type(normalized_py_type(field))
    if field.is_nullable and not field.is_primary_key:
        return f"{raw} | None"
    return raw


def query_schema_py_type(field: SysCodegenField) -> str:
    raw = _wire_schema_type(normalized_py_type(field))
    if raw.endswith(" | None"):
        return raw
    return f"{raw} | None"


def schema_default(field: SysCodegenField) -> str:
    if field.is_primary_key or field.is_required:
        return ""
    if field.python_type in {"dict", "dict[str, Any]"}:
        return " = Field(default_factory=dict)"
    if field.is_nullable:
        return " = None"
    if field.python_type in {"int", "float"}:
        return " = 0"
    if field.python_type == "bool":
        return " = False"
    return ""


def sa_type(field: SysCodegenField) -> str:
    raw = field.db_type.lower()
    if "json" in raw:
        return "JSON"
    if "bool" in raw:
        return "Boolean"
    if "date" in raw or "time" in raw:
        return "DateTime(timezone=True)"
    if any(item in raw for item in ("int", "serial")):
        return "Integer"
    if any(item in raw for item in ("numeric", "decimal")):
        return "Numeric"
    if any(item in raw for item in ("float", "double", "real")):
        return "Float"
    if "text" in raw:
        return "Text"
    if field.max_length:
        return f"String({field.max_length})"
    return "String(255)"


def vue_default(field: SysCodegenField | dict[str, Any]) -> str:
    python_type = field["python_type"] if isinstance(field, dict) else field.python_type
    form_widget = field["form_widget"] if isinstance(field, dict) else field.form_widget
    if isinstance(field, dict) and "is_json" in field:
        is_json = field["is_json"]
    elif isinstance(field, SysCodegenField):
        is_json = is_json_field(field)
    else:
        is_json = python_type in {"dict", "dict[str, Any]"}
    if form_widget == "datetime" or python_type == "datetime":
        return "null"
    if python_type in {"int", "float"}:
        return "0"
    if python_type == "bool":
        return "false"
    if is_json:
        return "'{}'"
    return "''"


def snake_case(value: str) -> str:
    value = sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    value = sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.replace("-", "_").replace(" ", "_").lower().strip("_")


def python_identifier(value: str) -> str:
    value = sub(r"[^0-9a-zA-Z_]", "_", snake_case(value))
    value = sub(r"_+", "_", value).strip("_")
    if not value:
        return "module"
    if value[0].isdigit():
        return f"_{value}"
    return value


def camel_case(value: str) -> str:
    snake = snake_case(value)
    head, *tail = snake.split("_")
    return head + "".join(item.capitalize() for item in tail)


def sql_str(value: str | None) -> str:
    if value is None or value == "":
        return "NULL"
    return "'" + value.replace("'", "''") + "'"
