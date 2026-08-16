""" Author: Charlie

API 路由装配：显式挂载全部业务模块路由（对齐 hei-boot "explicit deps, no bundle"）。

完整路径写在各路由装饰器上（``/v1/admin/...``），这里统一挂 ``/api`` 前缀并保留
OpenAPI tags（admin / portal / internal / public）。挂载顺序为历史注册顺序：
dashboard → auth → 其余按模块名字母序。
"""

from functools import cache

from fastapi import APIRouter

from app.core.paths import API_ROOT_PREFIX
from app.modules.auth.oauth.router import admin_router as oauth_admin_router
from app.modules.auth.oauth.router import portal_router as oauth_portal_router
from app.modules.auth.router import admin_router as auth_admin_router
from app.modules.auth.router import portal_router as auth_portal_router
from app.modules.auth.session_admin_router import router as auth_session_admin_router
from app.modules.biz.cg_test_activity.router import router as cg_test_activity_router
from app.modules.biz.cg_test_catalog.router import router as cg_test_catalog_router
from app.modules.biz.cg_test_knowledge_category.router import router as cg_test_knowledge_router
from app.modules.biz.cg_test_order.router import router as cg_test_order_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.iam.account.router import router as iam_account_router
from app.modules.iam.client.router import router as iam_client_router
from app.modules.iam.dept.router import router as iam_dept_router
from app.modules.iam.group.router import router as iam_group_router
from app.modules.iam.position.router import router as iam_position_router
from app.modules.iam.resource.portal.router import router as iam_resource_portal_router
from app.modules.iam.resource.router import router as iam_resource_router
from app.modules.iam.role.router import router as iam_role_router
from app.modules.internal.health.router import router as internal_health_router
from app.modules.message.feedback.router import admin_router as feedback_admin_router
from app.modules.message.feedback.router import portal_router as feedback_portal_router
from app.modules.message.notice.router import admin_router as notice_admin_router
from app.modules.message.notice.router import portal_router as notice_portal_router
from app.modules.sys.audit.router import router as sys_audit_router
from app.modules.sys.banner.portal.router import router as banner_portal_router
from app.modules.sys.banner.router import router as banner_router
from app.modules.sys.codegen.router import router as sys_codegen_router
from app.modules.sys.config.router import router as sys_config_router
from app.modules.sys.dict.portal.router import router as dict_portal_router
from app.modules.sys.dict.router import router as sys_dict_router
from app.modules.sys.file.portal.router import router as file_portal_router
from app.modules.sys.file.public_router import router as file_public_router
from app.modules.sys.file.router import router as sys_file_router
from app.modules.sys.job.router import router as sys_job_router
from app.modules.sys.weak_password.router import router as weak_password_router
from app.modules.user.admin.router import router as user_admin_router
from app.modules.user.portal.router import router as user_portal_router

# (tags, router) 挂载清单，顺序与历史注册顺序一致。
_ROUTERS: list[tuple[str, APIRouter]] = [
    ("admin", dashboard_router),
    ("admin", auth_admin_router),
    ("portal", auth_portal_router),
    ("admin", auth_session_admin_router),
    ("admin", oauth_admin_router),
    ("portal", oauth_portal_router),
    ("admin", cg_test_activity_router),
    ("admin", cg_test_catalog_router),
    ("admin", cg_test_knowledge_router),
    ("admin", cg_test_order_router),
    ("admin", iam_account_router),
    ("admin", iam_client_router),
    ("admin", iam_dept_router),
    ("admin", iam_group_router),
    ("admin", iam_position_router),
    ("admin", iam_resource_router),
    ("portal", iam_resource_portal_router),
    ("admin", iam_role_router),
    ("internal", internal_health_router),
    ("admin", feedback_admin_router),
    ("portal", feedback_portal_router),
    ("admin", notice_admin_router),
    ("portal", notice_portal_router),
    ("admin", sys_audit_router),
    ("admin", banner_router),
    ("portal", banner_portal_router),
    ("admin", sys_codegen_router),
    ("admin", sys_config_router),
    ("admin", sys_dict_router),
    ("portal", dict_portal_router),
    ("admin", sys_file_router),
    ("portal", file_portal_router),
    ("public", file_public_router),
    ("admin", sys_job_router),
    ("admin", weak_password_router),
    ("admin", user_admin_router),
    ("portal", user_portal_router),
]


@cache
def get_api_router() -> APIRouter:
    """构建并缓存 API 根路由。"""
    api_router = APIRouter()
    for tags, router in _ROUTERS:
        api_router.include_router(router, prefix=API_ROOT_PREFIX, tags=[tags])
    return api_router
