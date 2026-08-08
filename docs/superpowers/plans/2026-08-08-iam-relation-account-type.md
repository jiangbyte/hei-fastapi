# IAM Relation Account Type Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every `sys_iam_relation` row carry a required `account_type`, so ADMIN/PORTAL membership and grants are stored and resolved separately.

**Architecture:** Add non-null `account_type` on `SysIamRelation`, rebuild uniqueness to include it, backfill from `sys_account` (else `ADMIN`). All relation factories and grant/replace paths write the type. Authorization aggregation filters relations to the account’s type. Non-account grant APIs accept explicit `account_type`; account-side grants derive it from the account.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, Vue 3 admin (`web/admin`), pytest.

**Spec:** `docs/superpowers/specs/2026-08-08-iam-relation-account-type-design.md`

## Global Constraints

- All relation types require `account_type` (`ADMIN` / `PORTAL`, matching `AccountType`)
- Unique key includes `account_type`
- Non-account historical rows backfill to `ADMIN`
- Account-side relations must equal `sys_account.account_type`
- Do not auto-migrate relations when an account’s type changes
- Do not restart `./entrypoint.sh` for the user; they run migrate themselves when ready
- Prefer existing IAM/Naive patterns; no parallel selector stacks

## File map

| File | Responsibility |
| --- | --- |
| `migrations/versions/d7e8f9a0b1c2_iam_relation_account_type.py` | Schema + backfill |
| `app/modules/iam/relation/model.py` | Column + unique constraint |
| `app/modules/iam/relation/repository.py` | Factories, delete filters, auth aggregation |
| `app/modules/iam/*/service.py` + `schema.py` | Grant/own APIs |
| `tests/iam_relation_helpers.py` | Test fixtures default `account_type` |
| `scripts/seed/seed_super_admin.py` (+ any SQL inserts) | Seed writes type |
| `web/admin/.../ModalGrant*.vue` + role resource grant | Pass/select `account_type` |

---

### Task 1: Migration + ORM model

**Files:**
- Create: `migrations/versions/d7e8f9a0b1c2_iam_relation_account_type.py`
- Modify: `app/modules/iam/relation/model.py`

**Interfaces:**
- Produces: `SysIamRelation.account_type: Mapped[str]` (non-null); unique `uq_sys_iam_relation_subject_relation_target` includes `account_type`

- [ ] **Step 1: Add Alembic revision** (`down_revision = "c6d7e8f9a0b1"`)

```python
"""sys_iam_relation 增加 account_type 并回填。"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "d7e8f9a0b1c2"
down_revision: str | Sequence[str] | None = "c6d7e8f9a0b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sys_iam_relation",
        sa.Column("account_type", sa.String(length=32), nullable=True, comment="账户类型"),
    )
    conn = op.get_bind()
    # Account as subject
    conn.execute(
        sa.text(
            """
            UPDATE sys_iam_relation r
            SET account_type = a.account_type
            FROM sys_account a
            WHERE r.subject_type = 'ACCOUNT' AND r.subject_id = a.id
              AND r.account_type IS NULL
            """
        )
    )
    # Account as target (e.g. role-own-user style if any)
    conn.execute(
        sa.text(
            """
            UPDATE sys_iam_relation r
            SET account_type = a.account_type
            FROM sys_account a
            WHERE r.target_type = 'ACCOUNT' AND r.target_id = a.id
              AND r.account_type IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            "UPDATE sys_iam_relation SET account_type = 'ADMIN' WHERE account_type IS NULL"
        )
    )
    remaining = conn.execute(
        sa.text("SELECT COUNT(*) FROM sys_iam_relation WHERE account_type IS NULL")
    ).scalar()
    if remaining:
        raise RuntimeError(f"sys_iam_relation.account_type still null: {remaining}")
    op.alter_column("sys_iam_relation", "account_type", nullable=False)
    op.drop_constraint(
        "uq_sys_iam_relation_subject_relation_target",
        "sys_iam_relation",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_sys_iam_relation_subject_relation_target",
        "sys_iam_relation",
        [
            "subject_type",
            "subject_id",
            "relation_type",
            "target_type",
            "target_id",
            "target_key",
            "account_type",
        ],
    )
    op.create_index(
        "ix_sys_iam_relation_account_type_relation",
        "sys_iam_relation",
        ["account_type", "relation_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_sys_iam_relation_account_type_relation", table_name="sys_iam_relation")
    op.drop_constraint(
        "uq_sys_iam_relation_subject_relation_target",
        "sys_iam_relation",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_sys_iam_relation_subject_relation_target",
        "sys_iam_relation",
        [
            "subject_type",
            "subject_id",
            "relation_type",
            "target_type",
            "target_id",
            "target_key",
        ],
    )
    op.drop_column("sys_iam_relation", "account_type")
```

- [ ] **Step 2: Update ORM model**

In `SysIamRelation.__table_args__` UniqueConstraint columns, append `"account_type"`. Add field after `subject_id` (or near other classifiers):

```python
account_type: Mapped[str] = mapped_column(
    String(32),
    nullable=False,
    comment="账户类型",
)
```

Add `Index("ix_sys_iam_relation_account_type_relation", "account_type", "relation_type")` to `__table_args__`.

- [ ] **Step 3: Commit**

```bash
git add migrations/versions/d7e8f9a0b1c2_iam_relation_account_type.py \
  app/modules/iam/relation/model.py
git commit -m "feat(iam): add account_type column on sys_iam_relation"
```

---

### Task 2: Relation factories + test helpers

**Files:**
- Modify: `app/modules/iam/relation/repository.py` (factories + `delete_subject_relations*`)
- Modify: `tests/iam_relation_helpers.py`
- Modify: `scripts/seed/seed_super_admin.py` (relation inserts)

**Interfaces:**
- Consumes: `AccountType` / `str` account_type on every factory
- Produces:
  - `account_role(account_id, role_id, account_type: str) -> SysIamRelation`
  - same pattern for `account_group`, `account_dept`, `group_role`, `subject_resource_grant`, `subject_permission_grant`, `resource_permission`
  - `delete_subject_relations(..., account_type: str | None = None)` filters when provided

- [ ] **Step 1: Update helpers so tests compile**

In `tests/iam_relation_helpers.py`, every helper requires `account_type` (or defaults via kwargs). Prefer **required** kw-only after ids:

```python
def account_role(account_id: str, role_id: str, *, account_type: str, **kwargs) -> SysIamRelation:
    return SysIamRelation(
        ...,
        account_type=account_type,
        **kwargs,
    )
```

Apply to all helpers in that file.

- [ ] **Step 2: Update repository factories** similarly (required `account_type: str` parameter, set on `SysIamRelation`).

- [ ] **Step 3: Scope deletes**

```python
async def delete_subject_relations(
    self,
    subject_type: str,
    subject_id: str,
    relation_type: IamRelationType,
    account_type: str | None = None,
) -> None:
    stmt = delete(SysIamRelation).where(
        SysIamRelation.subject_type == subject_type,
        SysIamRelation.subject_id == subject_id,
        SysIamRelation.relation_type == relation_type.value,
    )
    if account_type is not None:
        stmt = stmt.where(SysIamRelation.account_type == account_type)
    await self.db.execute(stmt)
```

Mirror on `delete_subject_relations_many` if used for typed replaces.

- [ ] **Step 4: Fix compile breakages**

Grep callers of factories / helpers:

```bash
rg -n "account_role\(|account_group\(|group_role\(|subject_resource_grant\(|resource_permission\(|subject_permission_grant\(" app tests scripts --glob '*.py'
```

Pass `account_type=AccountType.ADMIN.value` (or the fixture account’s type) everywhere. Update `seed_super_admin.py` relation creates with `account_type=AccountType.ADMIN.value`.

- [ ] **Step 5: Run focused tests (expect auth filter failures until Task 3 if any assert on cross-type — otherwise pass)**

```bash
pytest tests/unit/test_iam_relations.py tests/unit/test_iam_delete_guards.py -q --tb=line
```

- [ ] **Step 6: Commit**

```bash
git add app/modules/iam/relation/repository.py tests/iam_relation_helpers.py \
  scripts/seed/seed_super_admin.py tests/
git commit -m "feat(iam): require account_type on relation factories"
```

---

### Task 3: Authorization read path filters by account type

**Files:**
- Modify: `app/modules/iam/relation/repository.py` (`get_accounts_authorization`, `_get_account_role_and_group_ids`, `_list_resource_grants_by_account`, `_list_permission_grants_by_account`, `get_account_resource_grants`)
- Modify: `app/modules/iam/account/repository.py` (`get_account_role_ids`, `get_account_role_codes`, direct role/group/dept lists used at runtime)
- Test: `tests/unit/test_auth_service.py` (extend) or new `tests/unit/test_iam_relation_account_type.py`

**Interfaces:**
- Consumes: account id → load `SysAccount.account_type`
- Produces: authorization only from relations where `relation.account_type == account.account_type` (including `GROUP_ROLE` and `SUBJECT_RESOURCE_GRANT` / `RESOURCE_PERMISSION` used in the cascade)

- [ ] **Step 1: Write failing isolation test**

```python
# tests/unit/test_iam_relation_account_type.py
import pytest
from app.core.config.enums import AccountType
from app.modules.iam.relation.repository import IamRelationRepository
from tests.iam_relation_helpers import account_role

@pytest.mark.asyncio
async def test_authorization_ignores_other_account_type_roles(db_session, ...):
    # create ADMIN account A, role R
    # insert ACCOUNT_ROLE with account_type=PORTAL (mismatched) — should be ignored
    # insert ACCOUNT_ROLE with account_type=ADMIN — should appear
    auth = await IamRelationRepository(db_session).get_account_authorization(account.id)
    assert role_admin.id in auth["role_ids"]
    assert role_portal_only.id not in auth["role_ids"]
```

Use existing account/role fixtures from neighboring tests (`tests/unit/test_auth_service.py` patterns).

- [ ] **Step 2: Run test — expect FAIL** (mismatched row currently counted)

```bash
pytest tests/unit/test_iam_relation_account_type.py -v
```

- [ ] **Step 3: Implement filters**

Pattern for account-subject queries in `get_accounts_authorization`:

```python
account_types = {
    row.id: row.account_type
    for row in (
        await self.db.execute(
            select(SysAccount.id, SysAccount.account_type).where(
                SysAccount.id.in_(unique_account_ids)
            )
        )
    ).all()
}
# When selecting ACCOUNT_* rows, add:
# SysIamRelation.account_type == account_types[subject_id]
# For SQL batch, join SysAccount:
# .join(SysAccount, SysAccount.id == SysIamRelation.subject_id)
# .where(SysIamRelation.account_type == SysAccount.account_type)
```

For `GROUP_ROLE` expansion: only roles where `GROUP_ROLE.account_type` equals the account’s type.

For `_list_resource_grants_by_account` / permission cascade: only grants and `RESOURCE_PERMISSION` rows matching that account’s type. When attributing a group/role grant to accounts, skip if `grant.account_type != account.account_type`.

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/test_iam_relation_account_type.py tests/unit/test_auth_service.py -q --tb=short
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/modules/iam/relation/repository.py app/modules/iam/account/repository.py \
  tests/unit/test_iam_relation_account_type.py
git commit -m "feat(iam): filter authorization by relation account_type"
```

---

### Task 4: Account-side grant/own write paths derive type

**Files:**
- Modify: `app/modules/iam/account/repository.py` (`replace_account_roles`, `replace_account_groups`, `replace_account_depts`, assign_* helpers)
- Modify: `app/modules/iam/account/service.py` (ensure account loaded; pass type into repo)
- Optional schema: no new request field (derive server-side)

**Interfaces:**
- Produces: all new ACCOUNT_* rows set `account_type` from `SysAccount.account_type`
- Deletes for replace scoped with that `account_type`

- [ ] **Step 1: In replace methods**

```python
account = await self.get_required(payload.id)
account_type = account.account_type
await self.relations.delete_subject_relations(
    IamRelationSubjectType.ACCOUNT.value,
    payload.id,
    IamRelationType.ACCOUNT_ROLE,
    account_type=account_type,
)
for role_id in role_ids:
    self.db.add(self.relations.account_role(payload.id, role_id, account_type))
```

Same for groups/depts/resources on account.

- [ ] **Step 2: Run**

```bash
pytest tests/unit/test_iam_relations.py tests/api/test_auth_routes.py -q --tb=line
```

- [ ] **Step 3: Commit**

```bash
git add app/modules/iam/account/
git commit -m "feat(iam): write account_type on account grant relations"
```

---

### Task 5: Group/role grant APIs take explicit `account_type`

**Files:**
- Modify: `app/modules/iam/group/schema.py` — `GroupGrantRoleRequest`, `GroupGrantResourceRequest`, `GroupOwnRoleResponse` query path
- Modify: `app/modules/iam/role/schema.py` — `RoleGrantResourceRequest` (+ own-resource query)
- Modify: `app/modules/iam/account/schema.py` — only if account grant-resource needs type (prefer derive)
- Modify: group/role `service.py`, `repository.py`, `router.py` (own-* query params)
- Modify: `IamRelationRepository.replace_subject_resource_grant_infos` to accept `account_type` and pass through delete/create

**Interfaces:**
- Produces request fields:

```python
account_type: AccountType  # required on GroupGrantRoleRequest, GroupGrantResourceRequest, RoleGrantResourceRequest
```

- Own endpoints: `GET .../own-role?id=&account_type=ADMIN` (and own-resource likewise)
- `group_role(group_id, role_id, account_type)`
- `replace_subject_resource_grant_infos(..., account_type: str)`

- [ ] **Step 1: Schema + service wiring**

Import `AccountType` from `app.core.config.enums`. Add required field to grant requests. For own queries, extend `IdQuery` usage with a small query model:

```python
class GroupOwnRoleQuery(IdQuery):
    account_type: AccountType
```

Filter `list_group_role_ids` / roles by `account_type`.

- [ ] **Step 2: Resource grant replace**

Thread `account_type` into delete + `subject_resource_grant(..., account_type=...)`.

- [ ] **Step 3: Unit/API smoke**

```bash
pytest tests/unit/test_iam_relations.py tests/unit/test_iam_delete_guards.py -q --tb=line
```

Add a small test: same group+role can exist for ADMIN and PORTAL as two rows; own-role?account_type=PORTAL only returns PORTAL row.

- [ ] **Step 4: Commit**

```bash
git add app/modules/iam/group/ app/modules/iam/role/ app/modules/iam/relation/repository.py tests/
git commit -m "feat(iam): scope group/role grants by account_type"
```

---

### Task 6: Admin UI — pass account type into grant drawers

**Files:**
- Modify: `web/admin/src/views/iam/components/ModalGrantRoleToGroup.vue`
- Modify: `web/admin/src/views/iam/components/ModalGrantRole.vue` / `ModalGrantGroup.vue` / `ModalGrantDept.vue` (account path: derive from `account.account_type` when calling own/grant if API starts requiring query type for own-*)
- Modify: `web/admin/src/views/iam/role/components/ModalGrantResource.vue` (+ group resource grant modal if present)
- Modify: callers that open group/role grant (role/group index pages)
- Reuse: `web/admin/src/constants/account.ts` (`ACCOUNT_TYPE_TABS` / enum values)

**Interfaces:**
- `openModal(entity, { accountType?: 'ADMIN' | 'PORTAL' })`
- Default `ADMIN` if omitted
- API calls include `account_type` on own/grant for group/role resource & group roles

- [ ] **Step 1: ModalGrantRoleToGroup**

Add `NSelect` or tab for account type (options from `ACCOUNT_TYPE_TABS`). On change: reload own roles + candidate page still `roleApi.page`. Submit `grantRoles({ id, role_ids, account_type })`.

- [ ] **Step 2: Role/Group resource grant modals**

Same: require `account_type` on own-resource / grant-resource API wrappers in `web/admin/src/api/iam/*.ts`.

- [ ] **Step 3: Account grant modals**

If backend own-* for accounts stays id-only (type derived), no UI selector. Ensure grant still works after migrate.

- [ ] **Step 4: Manual smoke** (user): migrate via `./entrypoint.sh migrate`, open group → assign roles for ADMIN and PORTAL separately.

- [ ] **Step 5: Commit**

```bash
git add web/admin/src/views/iam web/admin/src/api/iam
git commit -m "feat(admin): pass account_type in IAM grant drawers"
```

---

### Task 7: Seeds / bootstrap SQL + verification

**Files:**
- Modify: any `scripts/sql` / `scripts/seed` that `INSERT INTO sys_iam_relation` without `account_type`
- Grep: `rg -n "sys_iam_relation" scripts --glob '*.{sql,py}'`

- [ ] **Step 1: Add `account_type` column to inserts** (value `ADMIN` for platform seeds)

- [ ] **Step 2: Run unit suite slice**

```bash
pytest tests/unit/test_iam_relation_account_type.py tests/unit/test_iam_relations.py \
  tests/unit/test_auth_service.py tests/unit/test_iam_delete_guards.py -q
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add scripts/
git commit -m "chore(seed): set account_type on iam relation seeds"
```

---

## Spec coverage checklist

| Spec item | Task |
| --- | --- |
| Column + unique + index | Task 1 |
| Backfill account / default ADMIN | Task 1 |
| Factories write type | Task 2 |
| Delete scoped by type | Task 2 / 4 / 5 |
| Auth filter + group role same type | Task 3 |
| Account grants derive type | Task 4 |
| Group/role APIs explicit type | Task 5 |
| Admin UI | Task 6 |
| Seeds | Task 7 |
| No account-type-change migration | (explicit non-work) |

## Notes for implementers

- After Task 1, Charlie runs `./entrypoint.sh migrate` (do not start a second API process).
- PostgreSQL `UPDATE ... FROM` syntax is required (project uses Postgres in Docker).
- If unique constraint name differs in a given DB, inspect with `\d sys_iam_relation` before drop.
- `RESOURCE_PERMISSION` rows also carry `account_type`; cascade must filter them. Platform menu seeds stay `ADMIN` until portal resources exist.
