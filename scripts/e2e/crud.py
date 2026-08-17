"""CRUD cases for key admin resources (payloads aligned with hei-gin)."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from urllib.parse import quote

from .assert_util import (
    CaseBucket,
    CaseResult,
    as_string,
    assert_biz_ok,
    assert_keys,
    assert_page,
    find_id_by_field,
    parse_envelope,
    truncate,
)
from .client import do_raw


def run_crud_cases(base: str, admin_tok: str, bucket: CaseBucket) -> None:
    suffix = str(int(time.time()) % 1_000_000)

    def run(name: str, fn: Callable[[], None]) -> None:
        cr = CaseResult(name=name)
        try:
            fn()
            cr.ok = True
        except Exception as exc:  # noqa: BLE001 — collect all CRUD failures
            cr.error = str(exc)
        bucket.add(cr)

    # ---- dict ----
    def crud_dict() -> None:
        code = f"E2E_DICT_{suffix}"
        body = json.dumps(
            {
                "code": code,
                "label": "e2e-dict",
                "value": code,
                "category": "BIZ",
                "status": "ENABLED",
                "sort": 99,
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/dicts/create", admin_tok, body)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "GET",
            f"{base}/api/v1/admin/sys/dicts/page?current=1&size=100&code={quote(code)}",
            admin_tok,
        )
        assert_biz_ok(st, ar.code)
        _, data = parse_envelope(raw)
        recs = assert_page(data)
        row_id = find_id_by_field(recs, "code", code)
        if not row_id:
            codes = [as_string(r.get("code")) for r in recs[:10]]
            raise AssertionError(
                f"created dict not found in page total={data.get('total') if data else None} sample={codes}"
            )
        st, raw, ar = do_raw("GET", f"{base}/api/v1/admin/sys/dicts/detail?id={row_id}", admin_tok)
        assert_biz_ok(st, ar.code)
        _, dm = parse_envelope(raw)
        if as_string((dm or {}).get("code")) != code:
            raise AssertionError(f"detail code want {code}")
        ubody = json.dumps(
            {
                "id": row_id,
                "code": code,
                "label": "e2e-dict-upd",
                "value": code,
                "category": "BIZ",
                "status": "ENABLED",
                "sort": 98,
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/dicts/update", admin_tok, ubody)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw("GET", f"{base}/api/v1/admin/sys/dicts/detail?id={row_id}", admin_tok)
        _, dm = parse_envelope(raw)
        if as_string((dm or {}).get("label")) != "e2e-dict-upd":
            raise AssertionError(f"update not reflected label={ (dm or {}).get('label') }")
        dbody = json.dumps({"ids": [row_id]})
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/dicts/delete", admin_tok, dbody)
        assert_biz_ok(st, ar.code)

    # ---- weak password ----
    def crud_weak_password() -> None:
        pwd = f"e2e_weak_{suffix}"
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/weak-password/create",
            admin_tok,
            json.dumps({"password": pwd}),
        )
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "GET",
            f"{base}/api/v1/admin/sys/weak-password/page?current=1&size=50&keyword={quote(pwd)}",
            admin_tok,
        )
        assert_biz_ok(st, ar.code)
        _, data = parse_envelope(raw)
        recs = assert_page(data)
        row_id = find_id_by_field(recs, "password", pwd)
        if not row_id:
            raise AssertionError("weak password not found")
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/weak-password/update",
            admin_tok,
            json.dumps({"id": row_id, "password": pwd + "_u"}),
        )
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/weak-password/delete",
            admin_tok,
            json.dumps({"ids": [row_id]}),
        )
        assert_biz_ok(st, ar.code)

    # ---- banner ----
    def crud_banner() -> None:
        title = f"E2E Banner {suffix}"
        body = json.dumps(
            {
                "title": title,
                "image": "https://example.com/e2e.png",
                "link_type": "NONE",
                "category": "HOME",
                "type": "CAROUSEL",
                "position": "HOME_TOP",
                "target_account_types": ["PORTAL"],
                "sort": 0,
                "status": "DISABLED",
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/banners/create", admin_tok, body)
        try:
            assert_biz_ok(st, ar.code)
        except AssertionError as exc:
            raise AssertionError(f"create: {exc} {truncate(raw.decode('utf-8', 'replace'), 200)}") from exc
        st, raw, ar = do_raw(
            "GET",
            f"{base}/api/v1/admin/sys/banners/page?current=1&size=100&position=HOME_TOP&status=DISABLED",
            admin_tok,
        )
        assert_biz_ok(st, ar.code)
        _, data = parse_envelope(raw)
        recs = assert_page(data)
        row_id = find_id_by_field(recs, "title", title)
        if not row_id:
            # 回退：无 status 过滤再扫一页，避免种子 DISABLED 过多挤掉新行
            st, raw, ar = do_raw(
                "GET",
                f"{base}/api/v1/admin/sys/banners/page?current=1&size=100&position=HOME_TOP",
                admin_tok,
            )
            assert_biz_ok(st, ar.code)
            _, data = parse_envelope(raw)
            recs = assert_page(data)
            row_id = find_id_by_field(recs, "title", title)
        if not row_id:
            raise AssertionError(
                f"banner not found total={data.get('total') if data else None}"
            )
        match = next(r for r in recs if as_string(r.get("id")) == row_id)
        assert_keys(match, "target_account_types", "position")
        st, raw, ar = do_raw("GET", f"{base}/api/v1/admin/sys/banners/detail?id={row_id}", admin_tok)
        assert_biz_ok(st, ar.code)
        _, dm = parse_envelope(raw)
        if as_string((dm or {}).get("title")) != title:
            raise AssertionError("detail title mismatch")
        ubody = json.dumps(
            {
                "id": row_id,
                "title": title + " upd",
                "image": "https://example.com/e2e2.png",
                "link_type": "NONE",
                "category": "HOME",
                "type": "CAROUSEL",
                "position": "HOME_TOP",
                "target_account_types": ["PORTAL"],
                "sort": 98,
                "status": "DISABLED",
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/banners/update", admin_tok, ubody)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/banners/delete",
            admin_tok,
            json.dumps({"ids": [row_id]}),
        )
        assert_biz_ok(st, ar.code)

    # ---- notice ----
    def crud_notice() -> None:
        title = f"E2E Notice {suffix}"
        body = json.dumps(
            {
                "kind": "NOTIFICATION",
                "title": title,
                "content": "e2e content",
                "content_type": "TEXT",
                "category": "SYSTEM",
                "severity": "INFO",
                "target_scope": "ALL",
                "target_account_types": ["ADMIN"],
                "status": "DRAFT",
                "publish_locations": {"center": True},
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/notices/create", admin_tok, body)
        try:
            assert_biz_ok(st, ar.code)
        except AssertionError as exc:
            raise AssertionError(f"create: {exc} {truncate(raw.decode('utf-8', 'replace'), 200)}") from exc
        st, raw, ar = do_raw(
            "GET",
            f"{base}/api/v1/admin/sys/notices/page?current=1&size=50&title=E2E",
            admin_tok,
        )
        assert_biz_ok(st, ar.code)
        _, data = parse_envelope(raw)
        recs = assert_page(data)
        row_id = find_id_by_field(recs, "title", title)
        if not row_id:
            raise AssertionError("notice not found")
        st, raw, ar = do_raw("GET", f"{base}/api/v1/admin/sys/notices/detail?id={row_id}", admin_tok)
        assert_biz_ok(st, ar.code)
        _, dm = parse_envelope(raw)
        assert_keys(dm, "id", "title", "kind", "target_scope", "target_account_types")
        ubody = json.dumps(
            {
                "id": row_id,
                "kind": "NOTIFICATION",
                "title": title + " upd",
                "content": "e2e content2",
                "content_type": "TEXT",
                "category": "SYSTEM",
                "severity": "INFO",
                "target_scope": "ALL",
                "target_account_types": ["ADMIN"],
                "status": "DRAFT",
                "publish_locations": {"center": True},
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/notices/update", admin_tok, ubody)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/notices/delete",
            admin_tok,
            json.dumps({"ids": [row_id]}),
        )
        assert_biz_ok(st, ar.code)

    # ---- config ----
    def crud_config() -> None:
        key = f"e2e.config.{suffix}"
        body = json.dumps(
            {
                "config_key": key,
                "config_value": "v1",
                "category": "E2E",
                "value_type": "STRING",
                "label": "e2e",
                "sort_code": 99,
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/config/create", admin_tok, body)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "GET",
            f"{base}/api/v1/admin/sys/config/page?current=1&size=50&config_key={quote(key)}",
            admin_tok,
        )
        assert_biz_ok(st, ar.code)
        _, data = parse_envelope(raw)
        recs = assert_page(data)
        row_id = find_id_by_field(recs, "config_key", key)
        if not row_id:
            raise AssertionError("config not found")
        ubody = json.dumps(
            {
                "id": row_id,
                "config_key": key,
                "config_value": "v2",
                "category": "E2E",
                "value_type": "STRING",
                "label": "e2e",
                "sort_code": 98,
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/config/update", admin_tok, ubody)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/config/delete",
            admin_tok,
            json.dumps({"ids": [row_id]}),
        )
        assert_biz_ok(st, ar.code)

    # ---- role ----
    def crud_role() -> None:
        code = f"E2E_ROLE_{suffix}"
        body = json.dumps(
            {
                "code": code,
                "name": f"E2E Role {suffix}",
                "category": "CUSTOM",
                "scope_type": "PLATFORM",
                "sort": 99,
                "status": "ENABLED",
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/roles/create", admin_tok, body)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "GET",
            f"{base}/api/v1/admin/sys/roles/page?current=1&size=100&code={quote(code)}",
            admin_tok,
        )
        assert_biz_ok(st, ar.code)
        _, data = parse_envelope(raw)
        recs = assert_page(data)
        row_id = find_id_by_field(recs, "code", code)
        if not row_id:
            codes = [as_string(r.get("code")) for r in recs[:10]]
            raise AssertionError(
                f"role not found total={data.get('total') if data else None} sample={codes}"
            )
        ubody = json.dumps(
            {
                "id": row_id,
                "code": code,
                "name": f"E2E Role {suffix} upd",
                "category": "CUSTOM",
                "scope_type": "PLATFORM",
                "sort": 98,
                "status": "ENABLED",
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/roles/update", admin_tok, ubody)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/roles/delete",
            admin_tok,
            json.dumps({"ids": [row_id]}),
        )
        assert_biz_ok(st, ar.code)

    # ---- position ----
    def crud_position() -> None:
        name = f"E2E Pos {suffix}"
        body = json.dumps({"name": name, "category": "STAFF", "sort": 99, "status": "ENABLED"})
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/positions/create", admin_tok, body)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "GET",
            f"{base}/api/v1/admin/sys/positions/page?current=1&size=50&name={quote(name)}",
            admin_tok,
        )
        assert_biz_ok(st, ar.code)
        _, data = parse_envelope(raw)
        recs = assert_page(data)
        row_id = find_id_by_field(recs, "name", name)
        if not row_id:
            raise AssertionError("position not found")
        ubody = json.dumps(
            {
                "id": row_id,
                "name": name + " upd",
                "category": "STAFF",
                "sort": 98,
                "status": "ENABLED",
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/positions/update", admin_tok, ubody)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/positions/delete",
            admin_tok,
            json.dumps({"ids": [row_id]}),
        )
        assert_biz_ok(st, ar.code)

    # ---- group ----
    def crud_group() -> None:
        name = f"E2E Group {suffix}"
        body = json.dumps({"name": name, "status": "ENABLED"})
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/groups/create", admin_tok, body)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "GET",
            f"{base}/api/v1/admin/sys/groups/page?current=1&size=50&name={quote(name)}",
            admin_tok,
        )
        assert_biz_ok(st, ar.code)
        _, data = parse_envelope(raw)
        recs = assert_page(data)
        row_id = find_id_by_field(recs, "name", name)
        if not row_id:
            raise AssertionError("group not found")
        ubody = json.dumps({"id": row_id, "name": name + " upd", "status": "ENABLED"})
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/groups/update", admin_tok, ubody)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/groups/delete",
            admin_tok,
            json.dumps({"ids": [row_id]}),
        )
        assert_biz_ok(st, ar.code)

    # ---- dept ----
    def crud_dept() -> None:
        name = f"E2E Dept {suffix}"
        body = json.dumps({"name": name, "category": "DEPT", "sort": 0, "status": "ENABLED"})
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/depts/create", admin_tok, body)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "GET",
            f"{base}/api/v1/admin/sys/depts/page?current=1&size=100&name={quote(name)}",
            admin_tok,
        )
        assert_biz_ok(st, ar.code)
        _, data = parse_envelope(raw)
        recs = assert_page(data)
        row_id = find_id_by_field(recs, "name", name)
        if not row_id:
            raise AssertionError(
                f"dept not found total={data.get('total') if data else None} "
                f"sample={[as_string(r.get('name')) for r in recs[:5]]}"
            )
        ubody = json.dumps(
            {
                "id": row_id,
                "name": name + " upd",
                "category": "DEPT",
                "sort": 98,
                "status": "ENABLED",
            }
        )
        st, raw, ar = do_raw("POST", f"{base}/api/v1/admin/sys/depts/update", admin_tok, ubody)
        assert_biz_ok(st, ar.code)
        st, raw, ar = do_raw(
            "POST",
            f"{base}/api/v1/admin/sys/depts/delete",
            admin_tok,
            json.dumps({"ids": [row_id]}),
        )
        assert_biz_ok(st, ar.code)

    run("crud_dict", crud_dict)
    run("crud_weak_password", crud_weak_password)
    run("crud_banner", crud_banner)
    run("crud_notice", crud_notice)
    run("crud_config", crud_config)
    run("crud_role", crud_role)
    run("crud_position", crud_position)
    run("crud_group", crud_group)
    run("crud_dept", crud_dept)
