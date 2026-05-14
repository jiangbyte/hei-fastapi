from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from core.result import Result, PageData, success
from core.pojo import IdParam, IdsParam
from core.db import get_db
from core.auth.decorator import HeiCheckPermission, HeiCheckLogin, NoRepeat
from core.log import SysLog
from core.utils.excel_utils import handle_import
from ...params import UserVO, UserPageParam, UserExportParam, UserImportParam, GrantRoleParam, GrantUserPermissionParam, UpdateProfileParam, UpdateAvatarParam, UpdatePasswordParam
from ...service import UserService

router = APIRouter()


@router.get(
    "/api/v1/sys/user/page",
    summary="获取用户分页",
    response_model=Result[PageData[UserVO]]
)
@HeiCheckPermission("sys:user:page")
async def page(
    request: Request,
    param: UserPageParam = Depends(),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return success(service.page(param))


@router.post(
    "/api/v1/sys/user/create",
    summary="添加用户",
    response_model=Result
)
@SysLog("添加用户")
@HeiCheckPermission("sys:user:create")
@NoRepeat(interval=3000)
async def create(
    request: Request,
    vo: UserVO,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    await service.create(vo, request)
    return success()


@router.post(
    "/api/v1/sys/user/modify",
    summary="编辑用户",
    response_model=Result
)
@SysLog("编辑用户")
@HeiCheckPermission("sys:user:modify")
async def modify(
    request: Request,
    vo: UserVO,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    await service.modify(vo, request)
    return success()


@router.post(
    "/api/v1/sys/user/remove",
    summary="删除用户",
    response_model=Result
)
@SysLog("删除用户")
@HeiCheckPermission("sys:user:remove")
async def remove(
    request: Request,
    param: IdsParam,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    service.remove(param)
    return success()


@router.get(
    "/api/v1/sys/user/detail",
    summary="获取用户详情",
    response_model=Result[UserVO]
)
@HeiCheckPermission("sys:user:detail")
async def detail(
    request: Request,
    id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    data = service.detail(IdParam(id=id))
    return success(data if data else None)


@router.get(
    "/api/v1/sys/user/export",
    summary="导出用户数据")
@SysLog("导出用户数据")
@HeiCheckPermission("sys:user:export")
async def export(
    request: Request,
    param: UserExportParam = Depends(),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.export(param)


@router.get(
    "/api/v1/sys/user/template",
    summary="下载用户导入模板")
@HeiCheckPermission("sys:user:template")
async def download_template(
    request: Request,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.download_template()


@router.post(
    "/api/v1/sys/user/import",
    summary="导入用户数据",
    response_model=Result
)
@SysLog("导入用户数据")
@HeiCheckPermission("sys:user:import")
@NoRepeat(interval=5000)
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_import(file, UserService, UserVO, UserImportParam, db, request)


@router.post(
    "/api/v1/sys/user/grant-role",
    summary="分配用户角色",
    response_model=Result
)
@SysLog("分配用户角色")
@HeiCheckPermission("sys:user:grant-role")
@NoRepeat(interval=3000)
async def grant_role(
    request: Request,
    param: GrantRoleParam,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    await service.grant_roles(param, request)
    return success()


@router.post(
    "/api/v1/sys/user/grant-permission",
    summary="分配用户权限",
    response_model=Result
)
@SysLog("分配用户权限")
@HeiCheckPermission("sys:user:grant-permission")
@NoRepeat(interval=3000)
async def grant_permission(
    request: Request,
    param: GrantUserPermissionParam,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    await service.grant_permissions(param, request)
    return success()


@router.get(
    "/api/v1/sys/user/own-permission-detail",
    summary="获取用户已分配的权限详情"
)
@HeiCheckPermission("sys:user:own-permission-detail")
async def own_permission_detail(
    request: Request,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return success(service.get_user_permission_details(user_id))


@router.get(
    "/api/v1/sys/user/own-roles",
    summary="获取用户已分配的角色ID列表"
)
@HeiCheckPermission("sys:user:own-roles")
async def own_roles(
    request: Request,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return success(service.get_user_role_ids(user_id))


@router.get(
    "/api/v1/sys/user/current",
    summary="获取当前用户信息",
)
@HeiCheckLogin
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    service = UserService(db)
    data = await service.get_current_user(request)
    return success(data)


@router.get(
    "/api/v1/sys/user/menus",
    summary="获取当前用户菜单树",
)
@HeiCheckLogin
async def get_current_user_menus(request: Request, db: Session = Depends(get_db)):
    service = UserService(db)
    data = await service.get_current_user_menus(request)
    return success(data)


@router.get(
    "/api/v1/sys/user/permissions",
    summary="获取当前用户权限码列表",
)
@HeiCheckLogin
async def get_current_user_permissions(request: Request, db: Session = Depends(get_db)):
    service = UserService(db)
    data = await service.get_current_user_permissions(request)
    return success(data)


@router.post(
    "/api/v1/sys/user/update-profile",
    summary="更新当前用户个人信息",
    response_model=Result
)
@SysLog("更新个人信息")
@HeiCheckLogin
@NoRepeat(interval=3000)
async def update_profile(
    request: Request,
    param: UpdateProfileParam,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    await service.update_profile(param, request)
    return success()


@router.post(
    "/api/v1/sys/user/update-avatar",
    summary="更新当前用户头像（base64）",
    response_model=Result
)
@SysLog("更新头像")
@HeiCheckLogin
async def update_avatar(
    request: Request,
    param: UpdateAvatarParam,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    await service.update_avatar(param, request)
    return success()


@router.post(
    "/api/v1/sys/user/update-password",
    summary="修改当前用户密码",
    response_model=Result
)
@SysLog("修改密码")
@HeiCheckLogin
@NoRepeat(interval=3000)
async def update_password(
    request: Request,
    param: UpdatePasswordParam,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    await service.update_password(param, request)
    return success()