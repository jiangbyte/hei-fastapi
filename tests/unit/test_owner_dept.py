""" Author: Charlie

owner_dept_id 接线冒烟测试。
"""
from pathlib import Path

from app.core.db.mixins import OwnerDeptMixin
from app.core.security.data_scope import default_owner_dept_id
from app.modules.biz.cg_test_activity.model import CgTestActivity
from app.modules.biz.cg_test_catalog.model import CgTestCatalog
from app.modules.biz.cg_test_knowledge_category.model import CgTestKnowledgeCategory
from app.modules.biz.cg_test_order.model import CgTestOrder

ROOT = Path(__file__).resolve().parents[2]


def test_default_owner_dept_id():
    assert default_owner_dept_id(None) is None

    class _S:
        dept_ids: list[str] = []

    empty = _S()
    assert default_owner_dept_id(empty) is None  # type: ignore[arg-type]

    empty.dept_ids = ["d2", "d1"]
    assert default_owner_dept_id(empty) == "d2"  # type: ignore[arg-type]


def test_biz_main_models_have_owner_dept_mixin():
    for model in (CgTestActivity, CgTestCatalog, CgTestOrder, CgTestKnowledgeCategory):
        assert issubclass(model, OwnerDeptMixin)
        assert hasattr(model, "owner_dept_id")


def test_migration_file_present():
    versions = ROOT / "migrations/versions"
    paths = sorted(versions.glob("*_initial_schema.py"))
    assert paths, "initial schema migration missing"
    text = paths[-1].read_text(encoding="utf-8")
    assert "owner_dept_id" in text
    assert "cg_test_activity" in text
