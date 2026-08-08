""" Author: Charlie """

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
    db_session.add_all(
        [
            SysClientModule(
                id="m_admin",
                name="Admin Mod",
                code="admin-default",
                account_type=AccountType.ADMIN.value,
            ),
            SysClientModule(
                id="m_portal",
                name="Portal Mod",
                code="portal-default",
                account_type=AccountType.PORTAL.value,
            ),
            SysClientResource(
                id="cr_admin",
                code="home",
                name="Admin Home",
                resource_type=ResourceType.MENU.value,
                module_id="m_admin",
            ),
            SysClientResource(
                id="cr_portal",
                code="home",
                name="Portal Home",
                resource_type=ResourceType.MENU.value,
                module_id="m_portal",
            ),
        ]
    )
    await db_session.commit()

    from app.modules.iam.client.schema import ClientResourceTreeQuery

    tree = await ClientResourceService(db_session).list_tree(
        None,
        ClientResourceTreeQuery(account_type=AccountType.PORTAL),
    )
    assert [node.id for node in tree] == ["cr_portal"]
