from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery, IdsRequest
from app.core.schema.base import ApiSchema
from app.deps.auth import require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.sys.config.schema import (
    CategoryQuery,
    ConfigAdminPageQuery,
    ConfigBatchSaveRequest,
    ConfigCreateRequest,
    ConfigUpdateRequest,
    SysConfigSchema,
)
from app.modules.sys.config.service import ConfigService
from pydantic import Field


class TestWebhookRequest(ApiSchema):
    webhook_url: str = Field(default="", max_length=1024)
    webhook_secret: str = Field(default="", max_length=256)

router = APIRouter()


@router.post(
    "/sys/config/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: ConfigCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ConfigService(db).create(payload)
    return success()


@router.post(
    "/sys/config/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: ConfigUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ConfigService(db).update(payload)
    return success()


@router.post(
    "/sys/config/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ConfigService(db).delete(payload)
    return success()


@router.get(
    "/sys/config/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:detail")),
    ],
    response_model=ApiResponse[SysConfigSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysConfigSchema]:
    return success(await ConfigService(db).detail(query))


@router.get(
    "/sys/config/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:page")),
    ],
    response_model=ApiResponse[PageData[SysConfigSchema]],
)
async def page(
    query: Annotated[ConfigAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SysConfigSchema]]:
    return success(await ConfigService(db).page_admin(query))


@router.get(
    "/sys/config/list",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:page")),
    ],
    response_model=ApiResponse[list[SysConfigSchema]],
)
async def list_config(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[CategoryQuery, Depends()],
) -> ApiResponse[list[SysConfigSchema]]:
    return success(await ConfigService(db).list_by_category(query))


@router.post(
    "/sys/config/batch-save",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:update")),
    ],
    response_model=ApiResponse[None],
)
async def batch_save(
    payload: ConfigBatchSaveRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ConfigService(db).batch_save(payload)
    return success()


@router.post(
    "/sys/config/audit-alert/test-webhook",
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
)
async def test_audit_alert_webhook(
    payload: TestWebhookRequest,
) -> ApiResponse[dict]:
    from app.modules.sys.audit.alert import send_test_webhook

    err = await send_test_webhook(payload.webhook_url, payload.webhook_secret)
    if err:
        from app.core.exceptions.business import BusinessError

        raise BusinessError(err)
    return success({"message": "测试消息已发送"})
