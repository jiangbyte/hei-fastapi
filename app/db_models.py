""" Author: Charlie

ORM 模型注册：显式导入全部模型模块，确保 Alembic 元数据完整。

新增模型时在此追加对应模块导入。
"""
# 平台级模型。
from app.core.db.models import sys_config as sys_config_model  # noqa: F401
from app.core.db.models import sys_weak_password as sys_weak_password_model  # noqa: F401

# 业务模块模型（按模块名排序）。
from app.modules.auth.oauth import model as oauth_binding_model  # noqa: F401
from app.modules.biz.cg_test_activity import model as cg_test_activity_model  # noqa: F401
from app.modules.biz.cg_test_catalog import model as cg_test_catalog_model  # noqa: F401
from app.modules.biz.cg_test_knowledge_category import (
    model as cg_test_knowledge_model,  # noqa: F401
)
from app.modules.biz.cg_test_order import model as cg_test_order_model  # noqa: F401
from app.modules.iam.account import model as iam_account_model  # noqa: F401
from app.modules.iam.account import password_history as iam_password_history_model  # noqa: F401
from app.modules.iam.client import model as iam_client_model  # noqa: F401
from app.modules.iam.dept import model as iam_dept_model  # noqa: F401
from app.modules.iam.group import model as iam_group_model  # noqa: F401
from app.modules.iam.position import model as iam_position_model  # noqa: F401
from app.modules.iam.relation import model as iam_relation_model  # noqa: F401
from app.modules.iam.resource import model as iam_resource_model  # noqa: F401
from app.modules.iam.role import model as iam_role_model  # noqa: F401
from app.modules.message.feedback import model as feedback_model  # noqa: F401
from app.modules.message.notice import model as notice_model  # noqa: F401
from app.modules.sys.audit import alert_model as audit_alert_model  # noqa: F401
from app.modules.sys.audit import model as audit_model  # noqa: F401
from app.modules.sys.audit import outbox as audit_outbox_model  # noqa: F401
from app.modules.sys.banner import model as banner_model  # noqa: F401
from app.modules.sys.codegen import model as codegen_model  # noqa: F401
from app.modules.sys.dict import model as dict_model  # noqa: F401
from app.modules.sys.file import model as file_model  # noqa: F401
from app.modules.user.admin import model as admin_user_model  # noqa: F401
from app.modules.user.portal import model as portal_user_model  # noqa: F401
