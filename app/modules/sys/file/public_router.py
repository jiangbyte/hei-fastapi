""" Author: Charlie

文件公共读取接口：无需登录，按对象路径返回文件内容。
"""

from typing import Annotated
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Path
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.db import get_db_session
from app.modules.sys.file.schema import ObjectNameQuery
from app.modules.sys.file.service import FileService

router = APIRouter()


@router.get("/v1/files/{object_name:path}", response_class=Response)
async def get_file(
    object_name: Annotated[str, Path(min_length=1, max_length=512)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    """按对象路径读取文件内容（路径经 URL 解码与规范化）。"""
    # 路径段可能被浏览器编码；统一还原后再规范化。
    normalized = unquote(object_name).replace("\\", "/").lstrip("/")
    return await FileService(db).response(ObjectNameQuery(object_name=normalized))
