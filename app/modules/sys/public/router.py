""" Author: Charlie

公开站点信息接口（无需登录）。
"""

from fastapi import APIRouter

from app.core.response.schema import ApiResponse, success
from app.modules.auth.schema import SiteFooterResponse
from app.modules.sys.public.site_footer import resolve_site_footer

router = APIRouter()


@router.get(
    "/v1/public/site-footer",
    response_model=ApiResponse[SiteFooterResponse],
)
async def site_footer() -> ApiResponse[SiteFooterResponse]:
    """站点页脚：版权与备案信息。"""
    return success(resolve_site_footer())
