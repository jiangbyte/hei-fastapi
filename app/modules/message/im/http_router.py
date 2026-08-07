""" Author: Charlie

IM 网关辅助 HTTP 接口（票据签发）。
"""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config.enums import AccountType
from app.core.exceptions.business import BusinessError
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import ApiSchema
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_account_type
from app.modules.message.im.auth import issue_im_ticket

admin_router = APIRouter()
portal_router = APIRouter()


class ImTicketResponse(ApiSchema):
    ticket: str
    expires_in: int


@admin_router.post(
    "/v1/admin/message/im/ticket",
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
    response_model=ApiResponse[ImTicketResponse],
)
@portal_router.post(
    "/v1/portal/message/im/ticket",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[ImTicketResponse],
)
async def create_im_ticket(
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[ImTicketResponse]:
    """签发用于 IM AUTH 帧的短时一次性票据。"""
    try:
        ticket, ttl = await issue_im_ticket(
            account_type=str(session.account_type),
            account_id=session.account_id,
        )
    except RuntimeError as exc:
        raise BusinessError(str(exc)) from exc
    return success(ImTicketResponse(ticket=ticket, expires_in=ttl))
