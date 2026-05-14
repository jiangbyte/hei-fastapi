from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from core.result import success
from core.pojo import IdParam, IdsParam
from core.db import get_db
from core.auth.decorator import HeiCheckPermission, NoRepeat
from core.log import SysLog
from ...params import ConfigVO, ConfigPageParam, ConfigListParam, ConfigBatchEditParam, ConfigCategoryEditParam
from ...service import ConfigService

router = APIRouter()


@router.get("/api/v1/sys/config/page", summary="获取配置分页")
@HeiCheckPermission("sys:config:page")
async def page(
    request: Request,
    param: ConfigPageParam = Depends(),
    db: Session = Depends(get_db),
):
    service = ConfigService(db)
    return success(service.page(param))


@router.get("/api/v1/sys/config/list-by-category", summary="根据分类获取配置列表")
@HeiCheckPermission("sys:config:list")
async def list_by_category(
    request: Request,
    param: ConfigListParam = Depends(),
    db: Session = Depends(get_db),
):
    service = ConfigService(db)
    return success(service.list_by_category(param))


@router.post("/api/v1/sys/config/create", summary="添加配置")
@SysLog("添加配置")
@HeiCheckPermission("sys:config:create")
@NoRepeat(interval=3000)
async def create(
    request: Request,
    vo: ConfigVO,
    db: Session = Depends(get_db),
):
    service = ConfigService(db)
    await service.create(vo, request)
    return success()


@router.post("/api/v1/sys/config/modify", summary="编辑配置")
@SysLog("编辑配置")
@HeiCheckPermission("sys:config:modify")
async def modify(
    request: Request,
    vo: ConfigVO,
    db: Session = Depends(get_db),
):
    service = ConfigService(db)
    await service.modify(vo, request)
    return success()


@router.post("/api/v1/sys/config/remove", summary="删除配置")
@SysLog("删除配置")
@HeiCheckPermission("sys:config:remove")
async def remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db),
):
    service = ConfigService(db)
    await service.remove(param)
    return success()


@router.get("/api/v1/sys/config/detail", summary="获取配置详情")
@HeiCheckPermission("sys:config:detail")
async def detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db),
):
    service = ConfigService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.post("/api/v1/sys/config/edit-batch", summary="批量编辑配置")
@SysLog("批量编辑配置")
@HeiCheckPermission("sys:config:edit")
@NoRepeat(interval=3000)
async def edit_batch(
    request: Request,
    param: ConfigBatchEditParam,
    db: Session = Depends(get_db),
):
    service = ConfigService(db)
    await service.edit_batch(param, request)
    return success()


@router.post("/api/v1/sys/config/edit-by-category", summary="按分类批量编辑配置")
@SysLog("按分类批量编辑配置")
@HeiCheckPermission("sys:config:edit")
@NoRepeat(interval=3000)
async def edit_by_category(
    request: Request,
    param: ConfigCategoryEditParam,
    db: Session = Depends(get_db),
):
    service = ConfigService(db)
    await service.edit_by_category(param, request)
    return success()
