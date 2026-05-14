from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from core.result import Result, PageData, success
from core.pojo import IdParam, IdsParam
from core.db import get_db
from core.auth.decorator import HeiCheckPermission, NoRepeat
from core.log import SysLog
from core.utils.excel_utils import handle_import
from ...params import GroupVO, GroupPageParam, GroupTreeParam, GroupExportParam, GroupImportParam
from ...service import GroupService

router = APIRouter()


@router.get(
    "/api/v1/sys/group/page",
    summary="获取用户组分页",
    response_model=Result[PageData[GroupVO]]
)
@HeiCheckPermission("sys:group:page")
async def page(
    request: Request,
    param: GroupPageParam = Depends(),
    db: Session = Depends(get_db)
):
    service = GroupService(db)
    return success(service.page(param))


@router.get(
    "/api/v1/sys/group/union-tree",
    summary="获取组织与用户组联合树",
    response_model=Result[list[dict]]
)
@HeiCheckPermission("sys:group:tree")
async def union_tree(
    request: Request,
    db: Session = Depends(get_db)
):
    service = GroupService(db)
    return success(service.union_tree())


@router.get(
    "/api/v1/sys/group/tree",
    summary="获取用户组树",
    response_model=Result[list[dict]]
)
@HeiCheckPermission("sys:group:tree")
async def tree(
    request: Request,
    param: GroupTreeParam = Depends(),
    db: Session = Depends(get_db)
):
    service = GroupService(db)
    return success(service.tree(param))


@router.post(
    "/api/v1/sys/group/create",
    summary="添加用户组",
    response_model=Result
)
@SysLog("添加用户组")
@HeiCheckPermission("sys:group:create")
@NoRepeat(interval=3000)
async def create(
    request: Request,
    vo: GroupVO,
    db: Session = Depends(get_db)
):
    service = GroupService(db)
    await service.create(vo, request)
    return success()


@router.post(
    "/api/v1/sys/group/modify",
    summary="编辑用户组",
    response_model=Result
)
@SysLog("编辑用户组")
@HeiCheckPermission("sys:group:modify")
async def modify(
    request: Request,
    vo: GroupVO,
    db: Session = Depends(get_db)
):
    service = GroupService(db)
    await service.modify(vo, request)
    return success()


@router.post(
    "/api/v1/sys/group/remove",
    summary="删除用户组",
    response_model=Result
)
@SysLog("删除用户组")
@HeiCheckPermission("sys:group:remove")
async def remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db)
):
    service = GroupService(db)
    service.remove(param)
    return success()


@router.get(
    "/api/v1/sys/group/detail",
    summary="获取用户组详情",
    response_model=Result[GroupVO]
)
@HeiCheckPermission("sys:group:detail")
async def detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = GroupService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.get(
    "/api/v1/sys/group/export",
    summary="导出用户组数据")
@SysLog("导出用户组数据")
@HeiCheckPermission("sys:group:export")
async def export(
    request: Request,
    param: GroupExportParam = Depends(),
    db: Session = Depends(get_db)
):
    service = GroupService(db)
    return service.export(param)


@router.get(
    "/api/v1/sys/group/template",
    summary="下载用户组导入模板")
@HeiCheckPermission("sys:group:template")
async def download_template(
    request: Request,
    db: Session = Depends(get_db)
):
    service = GroupService(db)
    return service.download_template()


@router.post(
    "/api/v1/sys/group/import",
    summary="导入用户组数据",
    response_model=Result
)
@SysLog("导入用户组数据")
@HeiCheckPermission("sys:group:import")
@NoRepeat(interval=5000)
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_import(file, GroupService, GroupVO, GroupImportParam, db, request)


# 用户组-角色关联已废弃（使用 ral_role_permission.scope 的 GROUP / CUSTOM_GROUP）
