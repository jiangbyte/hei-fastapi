from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from core.result import Result, PageData, success
from core.pojo import IdParam, IdsParam
from core.db import get_db
from core.auth.decorator import HeiCheckPermission, NoRepeat
from core.log import SysLog
from core.utils.excel_utils import handle_import
from ...params import ModuleVO, ResourceVO, ModulePageParam, ResourcePageParam
from ...params import ModuleExportParam, ResourceExportParam, ModuleImportParam, ResourceImportParam
from ...service import ModuleService, ResourceService

router = APIRouter()


# ---- Module APIs ----

@router.get(
    "/api/v1/sys/module/page",
    summary="获取模块分页",
    response_model=Result[PageData[ModuleVO]]
)
@HeiCheckPermission("sys:module:page")
async def module_page(
    request: Request,
    param: ModulePageParam = Depends(),
    db: Session = Depends(get_db)
):
    service = ModuleService(db)
    return success(service.page(param))


@router.post(
    "/api/v1/sys/module/create",
    summary="添加模块",
    response_model=Result
)
@SysLog("添加模块")
@HeiCheckPermission("sys:module:create")
@NoRepeat(interval=3000)
async def module_create(
    request: Request,
    vo: ModuleVO,
    db: Session = Depends(get_db)
):
    service = ModuleService(db)
    await service.create(vo, request)
    return success()


@router.post(
    "/api/v1/sys/module/modify",
    summary="编辑模块",
    response_model=Result
)
@SysLog("编辑模块")
@HeiCheckPermission("sys:module:modify")
async def module_modify(
    request: Request,
    vo: ModuleVO,
    db: Session = Depends(get_db)
):
    service = ModuleService(db)
    await service.modify(vo, request)
    return success()


@router.post(
    "/api/v1/sys/module/remove",
    summary="删除模块",
    response_model=Result
)
@SysLog("删除模块")
@HeiCheckPermission("sys:module:remove")
async def module_remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db)
):
    service = ModuleService(db)
    service.remove(param)
    return success()


@router.get(
    "/api/v1/sys/module/detail",
    summary="获取模块详情",
    response_model=Result[ModuleVO]
)
@HeiCheckPermission("sys:module:detail")
async def module_detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = ModuleService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.get(
    "/api/v1/sys/module/export",
    summary="导出模块数据")
@SysLog("导出模块数据")
@HeiCheckPermission("sys:module:export")
async def module_export(
    request: Request,
    param: ModuleExportParam = Depends(),
    db: Session = Depends(get_db)
):
    service = ModuleService(db)
    return service.export(param)


@router.get(
    "/api/v1/sys/module/template",
    summary="下载模块导入模板")
@HeiCheckPermission("sys:module:template")
async def module_download_template(
    request: Request,
    db: Session = Depends(get_db)
):
    service = ModuleService(db)
    return service.download_template()


@router.post(
    "/api/v1/sys/module/import",
    summary="导入模块数据",
    response_model=Result
)
@SysLog("导入模块数据")
@HeiCheckPermission("sys:module:import")
@NoRepeat(interval=5000)
async def module_import_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_import(file, ModuleService, ModuleVO, ModuleImportParam, db, request)


# ---- Resource APIs ----

@router.get(
    "/api/v1/sys/resource/tree",
    summary="获取资源树",
    response_model=Result[list]
)
@HeiCheckPermission("sys:resource:tree")
async def resource_tree(
    request: Request,
    db: Session = Depends(get_db)
):
    service = ResourceService(db)
    return success(service.tree())


@router.get(
    "/api/v1/sys/resource/page",
    summary="获取资源分页",
    response_model=Result[PageData[ResourceVO]]
)
@HeiCheckPermission("sys:resource:page")
async def resource_page(
    request: Request,
    param: ResourcePageParam = Depends(),
    db: Session = Depends(get_db)
):
    service = ResourceService(db)
    return success(service.page(param))


@router.post(
    "/api/v1/sys/resource/create",
    summary="添加资源",
    response_model=Result
)
@SysLog("添加资源")
@HeiCheckPermission("sys:resource:create")
@NoRepeat(interval=3000)
async def resource_create(
    request: Request,
    vo: ResourceVO,
    db: Session = Depends(get_db)
):
    service = ResourceService(db)
    await service.create(vo, request)
    return success()


@router.post(
    "/api/v1/sys/resource/modify",
    summary="编辑资源",
    response_model=Result
)
@SysLog("编辑资源")
@HeiCheckPermission("sys:resource:modify")
async def resource_modify(
    request: Request,
    vo: ResourceVO,
    db: Session = Depends(get_db)
):
    service = ResourceService(db)
    await service.modify(vo, request)
    return success()


@router.post(
    "/api/v1/sys/resource/remove",
    summary="删除资源",
    response_model=Result
)
@SysLog("删除资源")
@HeiCheckPermission("sys:resource:remove")
async def resource_remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db)
):
    service = ResourceService(db)
    service.remove(param)
    return success()


@router.get(
    "/api/v1/sys/resource/detail",
    summary="获取资源详情",
    response_model=Result[ResourceVO]
)
@HeiCheckPermission("sys:resource:detail")
async def resource_detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = ResourceService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.get(
    "/api/v1/sys/resource/export",
    summary="导出资源数据")
@SysLog("导出资源数据")
@HeiCheckPermission("sys:resource:export")
async def resource_export(
    request: Request,
    param: ResourceExportParam = Depends(),
    db: Session = Depends(get_db)
):
    service = ResourceService(db)
    return service.export(param)


@router.get(
    "/api/v1/sys/resource/template",
    summary="下载资源导入模板")
@HeiCheckPermission("sys:resource:template")
async def resource_download_template(
    request: Request,
    db: Session = Depends(get_db)
):
    service = ResourceService(db)
    return service.download_template()


@router.post(
    "/api/v1/sys/resource/import",
    summary="导入资源数据",
    response_model=Result
)
@SysLog("导入资源数据")
@HeiCheckPermission("sys:resource:import")
@NoRepeat(interval=5000)
async def resource_import_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_import(file, ResourceService, ResourceVO, ResourceImportParam, db, request)
