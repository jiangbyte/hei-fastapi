from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import ConflictError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.modules.sys.codegen.model import SysCodegenPlan
from app.modules.sys.codegen.repository import CodegenRepository
from app.modules.sys.codegen.schema import (
    CodegenFieldUpdateItem,
    CodegenFieldsQuery,
    CodegenFieldsUpdateBatchRequest,
    CodegenParentResourceOption,
    CodegenParentResourcesQuery,
    CodegenPlanCreateRequest,
    CodegenPlanPageQuery,
    CodegenPlanUpdateRequest,
    CodegenPreviewSchema,
    CodegenTableColumnsQuery,
    DatabaseColumnSchema,
    DatabaseTableSchema,
    SysCodegenFieldSchema,
    SysCodegenPlanSchema,
)
from app.modules.sys.codegen.templates import render_files
from app.platform.db.transaction import transactional


class CodegenService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CodegenRepository(db)

    async def create(self, payload: CodegenPlanCreateRequest) -> None:
        await self._validate_plan_tables(payload)
        async with transactional(self.db):
            plan = await self.repo.create(payload)
            await self._sync_reflected_fields(plan)

    async def update(self, payload: CodegenPlanUpdateRequest) -> None:
        await self._validate_plan_tables(payload)
        async with transactional(self.db):
            await self.repo.update(payload)
            plan = await self.repo.get_required(payload.id)
            await self._sync_reflected_fields(plan)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysCodegenPlanSchema:
        return to_schema(SysCodegenPlanSchema, await self.repo.get_required(query.id))

    async def page_admin(self, query: CodegenPlanPageQuery) -> PageData[SysCodegenPlanSchema]:
        items, total = await self.repo.page_admin(query)
        return build_page(query.pagination, total, to_schema_list(SysCodegenPlanSchema, items))

    async def tables(self) -> list[DatabaseTableSchema]:
        return [DatabaseTableSchema(**item) for item in await self.repo.list_database_tables()]

    async def table_columns(self, query: CodegenTableColumnsQuery) -> list[DatabaseColumnSchema]:
        return [
            DatabaseColumnSchema(**_column_schema_data(item))
            for item in await self.repo.list_database_columns(query.table_name)
        ]

    async def fields(self, query: CodegenFieldsQuery) -> list[SysCodegenFieldSchema]:
        return to_schema_list(SysCodegenFieldSchema, await self.repo.list_fields(query.plan_id, query.table_role))

    async def update_fields_batch(self, payload: CodegenFieldsUpdateBatchRequest) -> None:
        async with transactional(self.db):
            await self.repo.replace_fields(payload.plan_id, payload.fields)

    async def parent_resources(self, query: CodegenParentResourcesQuery) -> list[CodegenParentResourceOption]:
        return _build_resource_options(await self.repo.list_resource_options(query.module_id))

    async def preview(self, query: IdQuery) -> CodegenPreviewSchema:
        plan = await self.repo.get_required(query.id)
        main_fields = await self.repo.list_fields(plan.id, "MAIN")
        sub_fields = await self.repo.list_fields(plan.id, "SUB")
        if not main_fields:
            await self._sync_reflected_fields(plan)
            main_fields = await self.repo.list_fields(plan.id, "MAIN")
            sub_fields = await self.repo.list_fields(plan.id, "SUB")
        return CodegenPreviewSchema(files=render_files(plan, main_fields, sub_fields))

    async def download(self, query: IdQuery) -> tuple[bytes, str]:
        preview = await self.preview(query)
        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as zip_file:
            for file in preview.files:
                zip_file.writestr(file.path, file.content)
        return buffer.getvalue(), f"codegen-{query.id}.zip"

    async def _validate_plan_tables(self, payload: CodegenPlanCreateRequest | CodegenPlanUpdateRequest) -> None:
        main_columns = await self.repo.list_database_columns(payload.main_table)
        main_column_names = {column["column_name"] for column in main_columns}
        if payload.main_pk not in main_column_names:
            raise ConflictError("Main primary key field does not exist")
        if payload.gen_type in {"TREE", "LEFT_TREE_TABLE"}:
            if payload.tree_parent_field not in main_column_names:
                raise ConflictError("Tree parent field does not exist")
            if payload.tree_label_field not in main_column_names:
                raise ConflictError("Tree label field does not exist")
        if payload.gen_type in {"LEFT_TREE_TABLE", "MASTER_DETAIL"}:
            if not payload.sub_table or not payload.sub_pk or not payload.sub_foreign_key:
                raise ConflictError("Sub table configuration is incomplete")
            sub_columns = await self.repo.list_database_columns(payload.sub_table)
            sub_column_names = {column["column_name"] for column in sub_columns}
            if payload.sub_pk not in sub_column_names:
                raise ConflictError("Sub primary key field does not exist")
            if payload.sub_foreign_key not in sub_column_names:
                raise ConflictError("Sub foreign key field does not exist")

    async def _sync_reflected_fields(self, plan: SysCodegenPlan) -> None:
        main_columns = await self.repo.list_database_columns(plan.main_table)
        await self.repo.upsert_reflected_fields(
            plan.id,
            "MAIN",
            [_default_field(item, "MAIN") for item in main_columns],
        )
        if plan.gen_type in {"LEFT_TREE_TABLE", "MASTER_DETAIL"} and plan.sub_table:
            sub_columns = await self.repo.list_database_columns(plan.sub_table)
            await self.repo.upsert_reflected_fields(
                plan.id,
                "SUB",
                [_default_field(item, "SUB") for item in sub_columns],
            )


def _column_schema_data(column: dict) -> dict:
    return {
        "column_name": column["column_name"],
        "column_comment": column.get("column_comment"),
        "db_type": column["db_type"],
        "python_type": column["python_type"],
        "typescript_type": column["typescript_type"],
        "is_primary_key": column["is_primary_key"],
        "is_nullable": column["is_nullable"],
        "max_length": column.get("max_length"),
    }


def _default_field(column: dict, table_role: str) -> CodegenFieldUpdateItem:
    column_name = column["column_name"]
    is_pk = bool(column["is_primary_key"])
    is_audit = column_name in {"created_at", "created_by", "updated_at", "updated_by"}
    is_nullable = bool(column["is_nullable"])
    python_type = column["python_type"]
    widget = _default_widget(column_name, python_type)
    return CodegenFieldUpdateItem(
        table_role=table_role,  # type: ignore[arg-type]
        column_name=column_name,
        column_comment=column.get("column_comment"),
        db_type=column["db_type"],
        python_type=python_type,
        typescript_type=column["typescript_type"],
        form_widget=widget,
        dict_code="COMMON_STATUS" if column_name == "status" else None,
        query_operator=_default_query_operator(column_name, python_type),
        show_in_table=not is_audit,
        show_in_form=not is_pk and not is_audit,
        show_in_detail=True,
        show_in_query=column_name in {"name", "title", "code", "status", "category", "type"},
        is_primary_key=is_pk,
        is_required=not is_nullable and not is_pk and not is_audit,
        is_unique=False,
        is_nullable=is_nullable,
        max_length=column.get("max_length"),
        sort=int(column.get("sort") or 99),
    )


def _default_widget(column_name: str, python_type: str) -> str:
    if column_name == "status":
        return "dict"
    if python_type in {"int", "float"}:
        return "number"
    if python_type == "bool":
        return "switch"
    if any(keyword in column_name for keyword in ("content", "description", "remark")):
        return "textarea"
    return "input"


def _default_query_operator(column_name: str, python_type: str) -> str | None:
    if column_name == "status" or python_type in {"int", "bool"}:
        return "EQ"
    if column_name in {"name", "title", "code", "category", "type"}:
        return "LIKE"
    return None


def _build_resource_options(resources) -> list[CodegenParentResourceOption]:
    node_map = {
        item.id: CodegenParentResourceOption(
            id=item.id,
            parent_id=item.parent_id,
            code=item.code,
            name=item.name,
            resource_type=item.resource_type,
            module_id=item.module_id,
        )
        for item in resources
    }
    roots: list[CodegenParentResourceOption] = []
    for item in resources:
        node = node_map[item.id]
        if item.parent_id and item.parent_id in node_map:
            node_map[item.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots
