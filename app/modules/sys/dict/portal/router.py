from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response.schema import ApiResponse, success
from app.deps.db import get_db_session
from app.modules.sys.dict.schema import DictTreeQuery, SysDictTreeNode
from app.modules.sys.dict.service import DictService

router = APIRouter()


@router.get(
    "/sys/dicts/tree",
    response_model=ApiResponse[list[SysDictTreeNode]],
)
async def tree(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[DictTreeQuery, Depends()],
) -> ApiResponse[list[SysDictTreeNode]]:
    return success(await DictService(db).list_tree(query))
