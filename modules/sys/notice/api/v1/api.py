from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from core.result import Result, PageData, success
from core.pojo import IdParam, IdsParam
from core.db import get_db
from core.auth.decorator import HeiCheckPermission, NoRepeat
from core.log import SysLog
from core.utils.excel_utils import handle_import
from ...params import NoticeVO, NoticePageParam, NoticeExportParam, NoticeImportParam
from ...service import NoticeService

router = APIRouter()


@router.get(
    "/api/v1/sys/notice/page",
    summary="获取通知分页",
    response_model=Result[PageData[NoticeVO]]
)
@HeiCheckPermission("sys:notice:page")
async def page(
    request: Request,
    param: NoticePageParam = Depends(),
    db: Session = Depends(get_db)
):
    service = NoticeService(db)
    return success(service.page(param))


@router.post(
    "/api/v1/sys/notice/create",
    summary="添加通知",
    response_model=Result
)
@SysLog("添加通知")
@HeiCheckPermission("sys:notice:create")
@NoRepeat(interval=3000)
async def create(
    request: Request,
    vo: NoticeVO,
    db: Session = Depends(get_db)
):
    service = NoticeService(db)
    await service.create(vo, request)
    return success()


@router.post(
    "/api/v1/sys/notice/modify",
    summary="编辑通知",
    response_model=Result
)
@SysLog("编辑通知")
@HeiCheckPermission("sys:notice:modify")
async def modify(
    request: Request,
    vo: NoticeVO,
    db: Session = Depends(get_db)
):
    service = NoticeService(db)
    await service.modify(vo, request)
    return success()


@router.post(
    "/api/v1/sys/notice/remove",
    summary="删除通知",
    response_model=Result
)
@SysLog("删除通知")
@HeiCheckPermission("sys:notice:remove")
async def remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db)
):
    service = NoticeService(db)
    service.remove(param)
    return success()


@router.get(
    "/api/v1/sys/notice/detail",
    summary="获取通知详情",
    response_model=Result[NoticeVO]
)
@HeiCheckPermission("sys:notice:detail")
async def detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = NoticeService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.get(
    "/api/v1/sys/notice/export",
    summary="导出通知数据")
@SysLog("导出通知数据")
@HeiCheckPermission("sys:notice:export")
async def export(
    request: Request,
    param: NoticeExportParam = Depends(),
    db: Session = Depends(get_db)
):
    service = NoticeService(db)
    return service.export(param)


@router.get(
    "/api/v1/sys/notice/template",
    summary="下载通知导入模板")
@HeiCheckPermission("sys:notice:template")
async def download_template(
    request: Request,
    db: Session = Depends(get_db)
):
    service = NoticeService(db)
    return service.download_template()


@router.post(
    "/api/v1/sys/notice/import",
    summary="导入通知数据",
    response_model=Result
)
@SysLog("导入通知数据")
@HeiCheckPermission("sys:notice:import")
@NoRepeat(interval=5000)
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_import(file, NoticeService, NoticeVO, NoticeImportParam, db, request)
