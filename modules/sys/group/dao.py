from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, delete as sa_delete
from .models import SysGroup
from .params import GroupPageParam


class GroupDao:
    def __init__(self, db: Session):
        self.db = db

    # ---- base CRUD ----

    def find_by_id(self, id: str) -> Optional[SysGroup]:
        return self.db.execute(select(SysGroup).where(SysGroup.id == id)).scalar_one_or_none()

    def find_by_ids(self, ids: List[str]) -> List[SysGroup]:
        return list(self.db.execute(
            select(SysGroup).where(SysGroup.id.in_(ids))
        ).scalars().all())

    def find_all(self) -> List[SysGroup]:
        return list(self.db.execute(select(SysGroup)).scalars().all())

    def insert(self, entity: SysGroup, user_id: Optional[str] = None) -> SysGroup:
        from core.utils.snowflake_utils import generate_id
        now = datetime.now()
        if not entity.id:
            entity.id = generate_id()
        if entity.created_at is None:
            entity.created_at = now
        entity.updated_at = now
        if user_id is not None and entity.created_by is None:
            entity.created_by = user_id
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: SysGroup, user_id: Optional[str] = None) -> SysGroup:
        entity.updated_at = datetime.now()
        if user_id is not None:
            entity.updated_by = user_id
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete_by_ids(self, ids: List[str]) -> int:
        if not ids:
            return 0
        stmt = sa_delete(SysGroup).where(SysGroup.id.in_(ids))
        affected = self.db.execute(stmt).rowcount
        self.db.commit()
        return affected

    # ---- custom ----

    def find_page_by_filters(self, param: GroupPageParam) -> Dict[str, Any]:
        filters = []
        if param.parent_id is not None:
            if param.parent_id in ("", "0"):
                filters.append(SysGroup.parent_id.is_(None))
            else:
                filters.append(or_(SysGroup.parent_id == param.parent_id, SysGroup.id == param.parent_id))
        if param.org_id:
            filters.append(SysGroup.org_id == param.org_id)
        if param.keyword:
            filters.append(SysGroup.name.like(f"%{param.keyword}%"))

        current = max(1, param.current)
        size = max(1, param.size)
        offset = (current - 1) * size

        count_stmt = select(func.count()).select_from(SysGroup).where(*filters)
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = select(SysGroup).where(*filters).order_by(SysGroup.sort_code.asc()).offset(offset).limit(size)
        records = list(self.db.execute(stmt).scalars().all())

        return {"records": records, "total": total}

    def find_all_ordered(self) -> List[SysGroup]:
        return list(self.db.execute(
            select(SysGroup).order_by(SysGroup.sort_code.asc())
        ).scalars().all())
