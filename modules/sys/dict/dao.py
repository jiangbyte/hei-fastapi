from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, delete as sa_delete
from .models import SysDict
from .params import DictPageParam, DictListParam


class DictDao:
    def __init__(self, db: Session):
        self.db = db

    # ---- base CRUD ----

    def find_by_id(self, id: str) -> Optional[SysDict]:
        return self.db.execute(select(SysDict).where(SysDict.id == id)).scalar_one_or_none()

    def find_by_ids(self, ids: List[str]) -> List[SysDict]:
        return list(self.db.execute(
            select(SysDict).where(SysDict.id.in_(ids))
        ).scalars().all())

    def find_all(self) -> List[SysDict]:
        return list(self.db.execute(select(SysDict)).scalars().all())

    def insert(self, entity: SysDict, user_id: Optional[str] = None) -> SysDict:
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

    def update(self, entity: SysDict, user_id: Optional[str] = None) -> SysDict:
        entity.updated_at = datetime.now()
        if user_id is not None:
            entity.updated_by = user_id
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete_by_ids(self, ids: List[str]) -> int:
        if not ids:
            return 0
        stmt = sa_delete(SysDict).where(SysDict.id.in_(ids))
        affected = self.db.execute(stmt).rowcount
        self.db.commit()
        return affected

    # ---- custom ----

    def find_page_by_filters(self, param: DictPageParam) -> Dict[str, Any]:
        filters = []
        if param.parent_id is not None:
            if param.parent_id in ("", "0"):
                filters.append(or_(SysDict.parent_id.is_(None), SysDict.parent_id == "0"))
            else:
                filters.append((SysDict.parent_id == param.parent_id) | (SysDict.id == param.parent_id))
        if param.category:
            filters.append(SysDict.category == param.category)
        if param.keyword:
            filters.append(SysDict.label.like(f"%{param.keyword}%"))

        current = max(1, param.current)
        size = max(1, param.size)
        offset = (current - 1) * size

        count_stmt = select(func.count()).select_from(SysDict).where(*filters)
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = select(SysDict).where(*filters).order_by(SysDict.sort_code.asc()).offset(offset).limit(size)
        records = list(self.db.execute(stmt).scalars().all())

        return {"records": records, "total": total}

    def find_list_by_filters(self, param: DictListParam) -> List[SysDict]:
        filters = []
        if param.parent_id is not None:
            if param.parent_id in ("", "0"):
                filters.append(or_(SysDict.parent_id.is_(None), SysDict.parent_id == "0"))
            else:
                filters.append(SysDict.parent_id == param.parent_id)
        if param.category is not None:
            filters.append(SysDict.category == param.category)
        stmt = select(SysDict).where(*filters).order_by(SysDict.sort_code.asc())
        return list(self.db.execute(stmt).scalars().all())

    def find_all_ordered(self) -> List[SysDict]:
        return list(self.db.execute(
            select(SysDict).order_by(SysDict.sort_code.asc())
        ).scalars().all())

    def find_by_code(self, code: str) -> Optional[SysDict]:
        return self.db.execute(
            select(SysDict).where(SysDict.code == code)
        ).scalar_one_or_none()

    def find_by_parent_id(self, parent_id: str) -> List[SysDict]:
        return list(self.db.execute(
            select(SysDict).where(SysDict.parent_id == parent_id).order_by(SysDict.sort_code)
        ).scalars().all())

    def has_children_batch(self, parent_ids: List[str]) -> set:
        if not parent_ids:
            return set()
        rows = self.db.execute(
            select(SysDict.parent_id).where(SysDict.parent_id.in_(parent_ids)).distinct()
        ).scalars().all()
        return set(rows)

    def count_by_parent_and_label(self, parent_id: str, label: str, exclude_id: Optional[str] = None) -> int:
        filters = [SysDict.parent_id == parent_id, SysDict.label == label]
        if exclude_id:
            filters.append(SysDict.id != exclude_id)
        return self.db.execute(select(func.count()).select_from(SysDict).where(*filters)).scalar() or 0

    def count_by_parent_and_value(self, parent_id: str, value: str, exclude_id: Optional[str] = None) -> int:
        filters = [SysDict.parent_id == parent_id, SysDict.value == value]
        if exclude_id:
            filters.append(SysDict.id != exclude_id)
        return self.db.execute(select(func.count()).select_from(SysDict).where(*filters)).scalar() or 0
