"""Compare job module OpenAPI schemas between live fastapi and hei-boot (if running)."""

from __future__ import annotations

import json
import sys
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

JOB_PATH_PREFIXES = (
    "/api/v1/admin/sys/jobs",
    "/api/v1/admin/sys/job-logs",
)

BOOT_EXPECTED_FIELDS = {
    "SysJob": {
        "id", "name", "handler", "trigger_type", "trigger_config", "params",
        "last_run_time", "next_run_time", "last_result", "enabled", "description",
        "sort", "created_at", "created_by", "updated_at", "updated_by",
    },
    "SysJobAddParam": {
        "name", "handler", "trigger_type", "trigger_config", "params",
        "description", "sort", "enabled",
    },
    "SysJobLog": {
        "id", "job_id", "params", "started_at", "duration_ms", "success",
        "result", "executor", "ip", "process_id", "app_dir", "created_at",
    },
}


def fetch_json(url: str, timeout: int = 30) -> dict[str, Any] | None:
    try:
        with urlopen(Request(url), timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"WARN: cannot fetch {url}: {exc}")
        return None


def collect_job_paths(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path, methods in (doc.get("paths") or {}).items():
        if not any(path.startswith(p) for p in JOB_PATH_PREFIXES):
            continue
        out[path] = methods
    return out


def schema_props(doc: dict[str, Any], ref: str) -> set[str]:
    if not ref.startswith("#/components/schemas/"):
        return set()
    name = ref.split("/")[-1]
    schema = ((doc.get("components") or {}).get("schemas") or {}).get(name) or {}
    props = schema.get("properties") or {}
    return set(props.keys())


def main() -> int:
    fast_base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    boot_base = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8080"

    fast_doc = fetch_json(f"{fast_base.rstrip('/')}/openapi.json")
    boot_doc = fetch_json(f"{boot_base.rstrip('/')}/v3/api-docs")

    if not fast_doc:
        print("ERROR: fastapi openapi unavailable")
        return 1

    fast_jobs = collect_job_paths(fast_doc)
    print(f"FastAPI job paths ({len(fast_jobs)}):")
    for path in sorted(fast_jobs):
        methods = [m.upper() for m in fast_jobs[path] if m in ("get", "post", "put", "delete")]
        print(f"  {', '.join(methods)} {path}")

  # Schema field check against boot entity/param names (snake_case)
    schemas = (fast_doc.get("components") or {}).get("schemas") or {}
    for boot_name, expected in BOOT_EXPECTED_FIELDS.items():
        # fastapi pydantic names may differ; find closest
        candidates = [k for k in schemas if boot_name.lower().replace("sys", "") in k.lower() or k == boot_name]
        if not candidates:
            # try SysJobSchema etc
            candidates = [k for k in schemas if "Job" in k and boot_name.replace("Sys", "") in k]
        found = None
        for c in candidates:
            props = set((schemas[c].get("properties") or {}).keys())
            if props:
                found = (c, props)
                break
        if not found:
            print(f"MISSING schema mapping for {boot_name}")
            continue
        name, props = found
        missing = expected - props
        extra = props - expected - {"created_name", "updated_name"}
        print(f"\nSchema {name} vs boot {boot_name}:")
        if missing:
            print(f"  missing fields: {sorted(missing)}")
        if extra:
            print(f"  extra fields: {sorted(extra)}")
        if not missing and not extra:
            print("  fields match boot entity")

    if boot_doc:
        boot_jobs = collect_job_paths(boot_doc)
        fast_set = set(fast_jobs.keys())
        boot_set = set(boot_jobs.keys())
        only_boot = sorted(boot_set - fast_set)
        only_fast = sorted(fast_set - boot_set)
        print(f"\nPath diff vs boot ({boot_base}):")
        if only_boot:
            print("  only boot:", only_boot)
        if only_fast:
            print("  only fastapi:", only_fast)
        if not only_boot and not only_fast:
            print("  job paths identical")
    else:
        print("\nBoot OpenAPI not available — field check used static boot entity/param lists.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
