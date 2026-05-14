from typing import Optional, Dict, Any
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from .models import ClientUser
from .params import ClientUserPageParam
from core.db.base_dao import BaseDAO
from core.db.query_wrapper import QueryWrapper


class ClientUserDao(BaseDAO):
    def __init__(self, db: Session):
        super().__init__(db, ClientUser)

    def find_page_by_filters(self, param: ClientUserPageParam) -> Dict[str, Any]:
        wrapper = QueryWrapper(ClientUser)
        if param.keyword:
            keyword = f"%{param.keyword}%"
            wrapper.where(or_(ClientUser.account.ilike(keyword), ClientUser.nickname.ilike(keyword)))
        if param.status:
            wrapper.eq(ClientUser.status, param.status)
        wrapper.order_by_desc(ClientUser.created_at)
        return self.select_page(wrapper, param)

    def find_by_account(self, account: str) -> Optional[ClientUser]:
        return (
            self.db.execute(
                select(ClientUser).where(
                    ClientUser.account == account,
                )
            )
            .scalar_one_or_none()
        )

    def find_by_email(self, email: str) -> Optional[ClientUser]:
        return (
            self.db.execute(
                select(ClientUser).where(ClientUser.email == email)
            )
            .scalar_one_or_none()
        )
