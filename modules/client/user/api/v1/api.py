from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from core.result import Result, PageData, success
from core.pojo import IdParam, IdsParam
from core.db import get_db
from core.auth.decorator import HeiClientCheckLogin, HeiCheckPermission
from core.log import SysLog
from core.auth.decorator import NoRepeat
from core.utils.excel_utils import handle_import
from ...params import (
    ClientUserVO, ClientUserPageParam, ClientUserExportParam, ClientUserImportParam,
    UpdateProfileParam, UpdateAvatarParam, UpdatePasswordParam,
)
from ...service import ClientUserService

router = APIRouter()


@router.get(
    "/api/v1/client-user/page",
    summary="获取C端用户分页",
    response_model=Result[PageData[ClientUserVO]]
)
@HeiCheckPermission("client:user:page")
async def page(
    request: Request,
    param: ClientUserPageParam = Depends(),
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    return success(service.page(param))


@router.post(
    "/api/v1/client-user/create",
    summary="添加C端用户",
    response_model=Result
)
@HeiCheckPermission("client:user:create")
async def create(
    request: Request,
    vo: ClientUserVO,
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    await service.create(vo, request)
    return success()


@router.post(
    "/api/v1/client-user/modify",
    summary="编辑C端用户",
    response_model=Result
)
@HeiCheckPermission("client:user:modify")
async def modify(
    request: Request,
    vo: ClientUserVO,
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    await service.modify(vo, request)
    return success()


@router.post(
    "/api/v1/client-user/remove",
    summary="删除C端用户",
    response_model=Result
)
@HeiCheckPermission("client:user:remove")
async def remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    service.remove(param)
    return success()


@router.get(
    "/api/v1/client-user/detail",
    summary="获取C端用户详情",
    response_model=Result[ClientUserVO]
)
@HeiCheckPermission("client:user:detail")
async def detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.get(
    "/api/v1/client-user/export",
    summary="导出C端用户数据")
@HeiCheckPermission("client:user:export")
async def export(
    request: Request,
    param: ClientUserExportParam = Depends(),
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    return service.export(param)


@router.get(
    "/api/v1/client-user/template",
    summary="下载C端用户导入模板")
@HeiCheckPermission("client:user:template")
async def download_template(
    request: Request,
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    return service.download_template()


@router.post(
    "/api/v1/client-user/import",
    summary="导入C端用户数据",
    response_model=Result
)
@HeiCheckPermission("client:user:import")
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_import(file, ClientUserService, ClientUserVO, ClientUserImportParam, db, request)


@router.get(
    "/api/v1/client-user/current",
    summary="获取当前C端用户信息",
)
@HeiClientCheckLogin
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    service = ClientUserService(db)
    data = await service.get_current_user(request)
    return success(data)


@router.post(
    "/api/v1/client-user/update-profile",
    summary="更新当前C端用户个人信息",
    response_model=Result
)
@SysLog("C端用户更新个人信息")
@HeiClientCheckLogin
@NoRepeat(interval=3000)
async def update_profile(
    request: Request,
    param: UpdateProfileParam,
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    await service.update_profile(param, request)
    return success()


@router.post(
    "/api/v1/client-user/update-avatar",
    summary="更新当前C端用户头像（base64）",
    response_model=Result
)
@SysLog("C端用户更新头像")
@HeiClientCheckLogin
async def update_avatar(
    request: Request,
    param: UpdateAvatarParam,
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    await service.update_avatar(param, request)
    return success()


@router.post(
    "/api/v1/client-user/update-password",
    summary="修改当前C端用户密码",
    response_model=Result
)
@SysLog("C端用户修改密码")
@HeiClientCheckLogin
@NoRepeat(interval=3000)
async def update_password(
    request: Request,
    param: UpdatePasswordParam,
    db: Session = Depends(get_db)
):
    service = ClientUserService(db)
    await service.update_password(param, request)
    return success()
