""" Author: Charlie """

import uuid

from app.core.config.enums import AccountType, StatusEnum
from app.modules.iam.client.model import SysClientModule, SysClientResource
from app.modules.iam.client.schema import ClientModuleSelectorQuery
from app.modules.iam.client.service import ClientModuleService, ClientResourceService
from app.modules.iam.enums import GrantSubjectType, ResourceType
from app.modules.iam.relation.repository import IamRelationRepository
from app.modules.iam.role.model import SysRole


async def test_client_module_selector_filters_by_account_type(db_session):
    db_session.add_all(
        [
            SysClientModule(
                id="m_admin",
                name="A",
                code="a",
                account_type=AccountType.ADMIN.value,
            ),
            SysClientModule(
                id="m_portal",
                name="P",
                code="p",
                account_type=AccountType.PORTAL.value,
            ),
        ]
    )
    await db_session.commit()

    options = await ClientModuleService(db_session).selector(
        ClientModuleSelectorQuery(account_type=AccountType.PORTAL)
    )
    assert [item.id for item in options] == ["m_portal"]


async def test_client_resource_grant_isolated_from_resource_ids(db_session):
    db_session.add_all(
        [
            SysClientModule(
                id="m1",
                name="Default",
                code="default",
                account_type=AccountType.ADMIN.value,
            ),
            SysClientResource(
                id="cr1",
                code="home",
                name="Home",
                resource_type=ResourceType.MENU.value,
                module_id="m1",
            ),
            SysRole(id="role1", code="demo", name="Demo", status=StatusEnum.ENABLED.value),
        ]
    )
    await db_session.commit()

    class GrantItem:
        def __init__(self, resource_id: str, permission_keys: list[str] | None = None):
            self.resource_id = resource_id
            self.permission_keys = permission_keys or []

    relations = IamRelationRepository(db_session)
    await relations.replace_subject_client_resource_grant_infos(
        GrantSubjectType.ROLE,
        "role1",
        [GrantItem("cr1")],
        account_type=AccountType.ADMIN,
    )
    await db_session.commit()

    grants = await relations.list_subject_client_resource_grants(
        GrantSubjectType.ROLE,
        "role1",
        account_type=AccountType.ADMIN,
    )
    assert [item["resource_id"] for item in grants] == ["cr1"]

    modules = await ClientResourceService(db_session).list_grant_modules(AccountType.ADMIN)
    assert len(modules) == 1
    assert modules[0].menu[0].id == "cr1"

    portal_modules = await ClientResourceService(db_session).list_grant_modules(
        AccountType.PORTAL
    )
    assert portal_modules == []


async def test_client_resource_tree_filters_by_account_type(db_session):
    suffix = uuid.uuid4().hex[:8]
    admin_module_id = f"m_admin_{suffix}"
    portal_module_id = f"m_portal_{suffix}"
    db_session.add_all(
        [
            SysClientModule(
                id=admin_module_id,
                name="Admin Mod",
                code=f"admin-default-{suffix}",
                account_type=AccountType.ADMIN.value,
            ),
            SysClientModule(
                id=portal_module_id,
                name="Portal Mod",
                code=f"portal-default-{suffix}",
                account_type=AccountType.PORTAL.value,
            ),
            SysClientResource(
                id=f"cr_admin_{suffix}",
                code="home",
                name="Admin Home",
                resource_type=ResourceType.MENU.value,
                module_id=admin_module_id,
            ),
            SysClientResource(
                id=f"cr_portal_{suffix}",
                code="home",
                name="Portal Home",
                resource_type=ResourceType.MENU.value,
                module_id=portal_module_id,
            ),
        ]
    )
    await db_session.commit()

    from app.modules.iam.client.schema import ClientResourceTreeQuery

    tree = await ClientResourceService(db_session).list_tree(
        None,
        ClientResourceTreeQuery(account_type=AccountType.PORTAL),
    )
    assert [node.id for node in tree] == [f"cr_portal_{suffix}"]
