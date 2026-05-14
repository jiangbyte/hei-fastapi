from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from core.result import Result, PageData, success
from core.pojo import IdParam, IdsParam
from core.db import get_db
from core.auth.decorator import HeiCheckPermission, NoRepeat
from core.log import SysLog
from core.utils.excel_utils import handle_import
from ...params import DictVO, DictPageParam, DictListParam, DictTreeParam, DictExportParam, DictImportParam
from ...service import DictService

router = APIRouter()


@router.get(
    "/api/v1/sys/dict/page",
    summary="获取字典分页",
    response_model=Result[PageData[DictVO]]
)
@HeiCheckPermission("sys:dict:page")
async def page(
    request: Request,
    param: DictPageParam = Depends(),
    db: Session = Depends(get_db)
):
    service = DictService(db)
    return success(service.page(param))


@router.get(
    "/api/v1/sys/dict/list",
    summary="获取字典列表",
    response_model=Result[list[DictVO]]
)
@HeiCheckPermission("sys:dict:list")
async def dict_list(
    request: Request,
    param: DictListParam = Depends(),
    db: Session = Depends(get_db)
):
    service = DictService(db)
    return success(service.list(param))


@router.get(
    "/api/v1/sys/dict/tree",
    summary="获取字典树",
    response_model=Result[list[dict]]
)
@HeiCheckPermission("sys:dict:tree")
async def tree(
    request: Request,
    param: DictTreeParam = Depends(),
    db: Session = Depends(get_db)
):
    service = DictService(db)
    return success(await service.tree(param))


@router.post(
    "/api/v1/sys/dict/create",
    summary="添加字典",
    response_model=Result
)
@SysLog("添加字典")
@HeiCheckPermission("sys:dict:create")
@NoRepeat(interval=3000)
async def create(
    request: Request,
    vo: DictVO,
    db: Session = Depends(get_db)
):
    service = DictService(db)
    await service.create(vo, request)
    return success()


@router.post(
    "/api/v1/sys/dict/modify",
    summary="编辑字典",
    response_model=Result
)
@SysLog("编辑字典")
@HeiCheckPermission("sys:dict:modify")
async def modify(
    request: Request,
    vo: DictVO,
    db: Session = Depends(get_db)
):
    service = DictService(db)
    await service.modify(vo, request)
    return success()


@router.post(
    "/api/v1/sys/dict/remove",
    summary="删除字典",
    response_model=Result
)
@SysLog("删除字典")
@HeiCheckPermission("sys:dict:remove")
async def remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db)
):
    service = DictService(db)
    await service.remove(param)
    return success()


@router.get(
    "/api/v1/sys/dict/detail",
    summary="获取字典详情",
    response_model=Result[DictVO]
)
@HeiCheckPermission("sys:dict:detail")
async def detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = DictService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.get(
    "/api/v1/sys/dict/get-label",
    summary="根据字典编码和值获取字典标签"
)
@HeiCheckPermission("sys:dict:get-label")
async def get_dict_label(
    request: Request,
    type_code: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_db)
):
    service = DictService(db)
    label = service.get_dict_label(type_code, value)
    return success({"type_code": type_code, "value": value, "label": label})


@router.get(
    "/api/v1/sys/dict/get-children",
    summary="根据字典编码获取子字典列表"
)
@HeiCheckPermission("sys:dict:get-children")
async def get_dict_children(
    request: Request,
    type_code: str = Query(...),
    db: Session = Depends(get_db)
):
    service = DictService(db)
    return success(service.get_dict_children(type_code))


@router.get(
    "/api/v1/sys/dict/export",
    summary="导出字典数据")
@SysLog("导出字典数据")
@HeiCheckPermission("sys:dict:export")
async def export(
    request: Request,
    param: DictExportParam = Depends(),
    db: Session = Depends(get_db)
):
    service = DictService(db)
    return service.export(param)


@router.get(
    "/api/v1/sys/dict/template",
    summary="下载字典导入模板")
@HeiCheckPermission("sys:dict:template")
async def download_template(
    request: Request,
    db: Session = Depends(get_db)
):
    service = DictService(db)
    return service.download_template()


@router.post(
    "/api/v1/sys/dict/import",
    summary="导入字典数据",
    response_model=Result
)
@SysLog("导入字典数据")
@HeiCheckPermission("sys:dict:import")
@NoRepeat(interval=5000)
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_import(file, DictService, DictVO, DictImportParam, db, request)
