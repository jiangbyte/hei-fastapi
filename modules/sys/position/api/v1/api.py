from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from core.result import Result, PageData, success
from core.pojo import IdParam, IdsParam
from core.db import get_db
from core.auth.decorator import HeiCheckPermission, NoRepeat
from core.log import SysLog
from core.utils.excel_utils import handle_import
from ...params import PositionVO, PositionPageParam, PositionExportParam, PositionImportParam
from ...service import PositionService

router = APIRouter()


@router.get(
    "/api/v1/sys/position/page",
    summary="获取职位分页",
    response_model=Result[PageData[PositionVO]]
)
@SysLog("查看职位列表")
@HeiCheckPermission("sys:position:page")
async def page(
    request: Request,
    param: PositionPageParam = Depends(),
    db: Session = Depends(get_db)
):
    service = PositionService(db)
    return success(service.page(param))


@router.post(
    "/api/v1/sys/position/create",
    summary="添加职位",
    response_model=Result
)
@SysLog("添加职位")
@HeiCheckPermission("sys:position:create")
@NoRepeat(interval=3000)
async def create(
    request: Request,
    vo: PositionVO,
    db: Session = Depends(get_db)
):
    service = PositionService(db)
    await service.create(vo, request)
    return success()


@router.post(
    "/api/v1/sys/position/modify",
    summary="编辑职位",
    response_model=Result
)
@SysLog("编辑职位")
@HeiCheckPermission("sys:position:modify")
async def modify(
    request: Request,
    vo: PositionVO,
    db: Session = Depends(get_db)
):
    service = PositionService(db)
    await service.modify(vo, request)
    return success()


@router.post(
    "/api/v1/sys/position/remove",
    summary="删除职位",
    response_model=Result
)
@SysLog("删除职位")
@HeiCheckPermission("sys:position:remove")
async def remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db)
):
    service = PositionService(db)
    service.remove(param)
    return success()


@router.get(
    "/api/v1/sys/position/detail",
    summary="获取职位详情",
    response_model=Result[PositionVO]
)
@HeiCheckPermission("sys:position:detail")
async def detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = PositionService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.get(
    "/api/v1/sys/position/export",
    summary="导出职位数据")
@HeiCheckPermission("sys:position:export")
async def export(
    request: Request,
    param: PositionExportParam = Depends(),
    db: Session = Depends(get_db)
):
    service = PositionService(db)
    return service.export(param)


@router.get(
    "/api/v1/sys/position/template",
    summary="下载职位导入模板")
@HeiCheckPermission("sys:position:template")
async def download_template(
    request: Request,
    db: Session = Depends(get_db)
):
    service = PositionService(db)
    return service.download_template()


@router.post(
    "/api/v1/sys/position/import",
    summary="导入职位数据",
    response_model=Result
)
@HeiCheckPermission("sys:position:import")
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_import(file, PositionService, PositionVO, PositionImportParam, db, request)


