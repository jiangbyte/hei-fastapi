from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.db import get_db_session
from app.modules.sys.file.schema import ObjectNameQuery
from app.modules.sys.file.service import FileService

router = APIRouter()


@router.get("/files", response_class=Response)
async def get_file(
    query: Annotated[ObjectNameQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    return await FileService(db).response(query)
