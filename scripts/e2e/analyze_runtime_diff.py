import json
import re
from pathlib import Path

p = Path(__file__).parent / "reports" / "boot_fastapi_runtime_diff.json"
r = json.loads(p.read_text(encoding="utf-8"))

status_paths = []
ts_only_paths = []
extra_paths = set()
missing_items = []
other_items = []

for m in r["mismatches"]:
    if m.get("status_mismatch") or m.get("code_mismatch"):
        status_paths.append(
            (m["path"], m["boot_status"], m["fast_status"], m["boot_code"], m["fast_code"])
        )
        continue
    diffs = m.get("data_diffs", [])
    only_ts = True
    for d in diffs:
        if "missing in fastapi" in d:
            only_ts = False
            missing_items.append((m["path"], d))
        elif "extra in fastapi" in d:
            only_ts = False
            extra_paths.add(m["path"])
        elif re.search(r"(created_at|updated_at|publish_at|expire_at|replied_at|paid_at|ordered_at)", d):
            continue
        else:
            only_ts = False
            other_items.append((m["path"], d[:120]))
    if diffs and only_ts:
        ts_only_paths.append(m["path"])

print("=== STATUS/CODE MISMATCH ===")
for x in status_paths:
    print(x)
print(f"\n=== TIMESTAMP PRECISION ONLY ({len(ts_only_paths)}) ===")
for x in ts_only_paths[:10]:
    print(x)
if len(ts_only_paths) > 10:
    print(f"... +{len(ts_only_paths)-10} more")
print(f"\n=== EXTRA FIELDS IN FASTAPI ({len(extra_paths)}) ===")
for x in sorted(extra_paths):
    print(x)
print(f"\n=== MISSING IN FASTAPI (sample {min(8,len(missing_items))}) ===")
for x in missing_items[:8]:
    print(x)
print(f"\n=== OTHER VALUE DIFFS ({len(other_items)}) ===")
for x in other_items[:12]:
    print(x)
