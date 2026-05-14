from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from core.result import Result, PageData, success
from core.pojo import IdParam, IdsParam
from core.db import get_db
from core.auth.decorator import HeiCheckPermission, NoRepeat
from core.log import SysLog
from core.utils.excel_utils import handle_import
from ...params import RoleVO, RolePageParam, RoleExportParam, RoleImportParam, GrantPermissionParam, GrantResourceParam
from ...service import RoleService

router = APIRouter()


@router.get(
    "/api/v1/sys/role/page",
    summary="获取角色分页",
    response_model=Result[PageData[RoleVO]]
)
@HeiCheckPermission("sys:role:page")
async def page(
    request: Request,
    param: RolePageParam = Depends(),
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    return success(service.page(param))


@router.post(
    "/api/v1/sys/role/create",
    summary="添加角色",
    response_model=Result
)
@SysLog("添加角色")
@HeiCheckPermission("sys:role:create")
@NoRepeat(interval=3000)
async def create(
    request: Request,
    vo: RoleVO,
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    await service.create(vo, request)
    return success()


@router.post(
    "/api/v1/sys/role/modify",
    summary="编辑角色",
    response_model=Result
)
@SysLog("编辑角色")
@HeiCheckPermission("sys:role:modify")
async def modify(
    request: Request,
    vo: RoleVO,
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    await service.modify(vo, request)
    return success()


@router.post(
    "/api/v1/sys/role/remove",
    summary="删除角色",
    response_model=Result
)
@SysLog("删除角色")
@HeiCheckPermission("sys:role:remove")
async def remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    service.remove(param)
    return success()


@router.get(
    "/api/v1/sys/role/detail",
    summary="获取角色详情",
    response_model=Result[RoleVO]
)
@HeiCheckPermission("sys:role:detail")
async def detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.get(
    "/api/v1/sys/role/export",
    summary="导出角色数据")
@SysLog("导出角色数据")
@HeiCheckPermission("sys:role:export")
async def export(
    request: Request,
    param: RoleExportParam = Depends(),
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    return service.export(param)


@router.get(
    "/api/v1/sys/role/template",
    summary="下载角色导入模板")
@HeiCheckPermission("sys:role:template")
async def download_template(
    request: Request,
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    return service.download_template()


@router.post(
    "/api/v1/sys/role/import",
    summary="导入角色数据",
    response_model=Result
)
@SysLog("导入角色数据")
@HeiCheckPermission("sys:role:import")
@NoRepeat(interval=5000)
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_import(file, RoleService, RoleVO, RoleImportParam, db, request)


@router.post(
    "/api/v1/sys/role/grant-permission",
    summary="分配角色权限",
    response_model=Result
)
@SysLog("分配角色权限")
@HeiCheckPermission("sys:role:grant-permission")
@NoRepeat(interval=3000)
async def grant_permission(
    request: Request,
    param: GrantPermissionParam,
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    await service.grant_permissions(param, request)
    return success()


@router.post(
    "/api/v1/sys/role/grant-resource",
    summary="分配角色资源",
    response_model=Result
)
@SysLog("分配角色资源")
@HeiCheckPermission("sys:role:grant-resource")
@NoRepeat(interval=3000)
async def grant_resource(
    request: Request,
    param: GrantResourceParam,
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    await service.grant_resources(param, request)
    return success()


@router.get(
    "/api/v1/sys/role/own-permission",
    summary="获取角色已分配的权限编码列表"
)
@HeiCheckPermission("sys:role:own-permission")
async def own_permission(
    request: Request,
    role_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    return success(service.get_role_permission_codes(role_id))


@router.get(
    "/api/v1/sys/role/own-permission-detail",
    summary="获取角色已分配的权限详情（含scope和自定义范围）"
)
@HeiCheckPermission("sys:role:own-permission")
async def own_permission_detail(
    request: Request,
    role_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    return success(service.get_role_permission_details(role_id))


@router.get(
    "/api/v1/sys/role/own-resource",
    summary="获取角色已分配的资源ID列表"
)
@HeiCheckPermission("sys:role:own-resource")
async def own_resource(
    request: Request,
    role_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    return success(service.get_role_resource_ids(role_id))
