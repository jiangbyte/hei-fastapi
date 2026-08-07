#!/usr/bin/env python3
""" Author: Charlie

若 DR 检查清单 / 生产锚点 / 演练记录缺失则 CI 失败。
"""
from __future__ import annotations

import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    ROOT / "docs" / "dr-checklist.md",
    ROOT / "docs" / "production.md",
)

PRODUCTION_NEEDLES = (
    "灾备与备份",
    "PITR",
    "RPO",
    "RTO",
    "AUTH__SESSION_COOKIE_SECURE",
    "AUTH__SESSION_IDLE_TIMEOUT_SECONDS",
    "MFA",
    "SECRETS__BACKEND",
)

CHECKLIST_NEEDLES = (
    "PostgreSQL",
    "Redis",
    "alembic upgrade head",
    "AUTH__SESSION_COOKIE_SECURE",
    "dr-drills",
)

ENV_NEEDLES = (
    "AUTH__SESSION_COOKIE_SECURE",
    "AUTH__SESSION_IDLE_TIMEOUT_SECONDS",
    "DR",
    "SECRETS__BACKEND",
    "AUTH__MFA_REQUIRED",
)

DRILL_FIELDS = ("drill_date", "rpo_minutes", "rto_minutes", "result")


def _must_contain(path: Path, needles: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [n for n in needles if n not in text]


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[3:end].strip()
    data: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _check_drills() -> list[str]:
    errors: list[str] = []
    drills_dir = ROOT / "docs" / "dr-drills"
    if not drills_dir.is_dir():
        return ["missing directory: docs/dr-drills"]
    files = sorted(p for p in drills_dir.glob("*.md") if p.name.lower() != "readme.md")
    if not files:
        return ["docs/dr-drills requires at least one *-drill.md record"]

    newest: date | None = None
    for path in files:
        text = path.read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        for field in DRILL_FIELDS:
            if field not in meta and field not in text:
                errors.append(f"{path.relative_to(ROOT)} missing: {field}")
        raw_date = meta.get("drill_date")
        if not raw_date:
            match = re.search(r"drill_date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text)
            raw_date = match.group(1) if match else None
        if not raw_date:
            errors.append(f"{path.relative_to(ROOT)} missing drill_date")
            continue
        try:
            parsed = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            errors.append(f"{path.relative_to(ROOT)} invalid drill_date: {raw_date}")
            continue
        if newest is None or parsed > newest:
            newest = parsed

    if newest is not None and os.getenv("DR_DRILL_ALLOW_STALE", "").strip() not in {
        "1",
        "true",
        "TRUE",
        "yes",
    }:
        max_age = int(os.getenv("DR_DRILL_MAX_AGE_DAYS", "120"))
        age = (date.today() - newest).days
        if age > max_age:
            errors.append(
                f"newest drill_date {newest.isoformat()} is {age}d old "
                f"(max {max_age}; set DR_DRILL_ALLOW_STALE=1 to waive)"
            )
    return errors


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.is_file():
            errors.append(f"missing file: {path.relative_to(ROOT)}")

    prod = ROOT / "docs" / "production.md"
    if prod.is_file():
        for needle in _must_contain(prod, PRODUCTION_NEEDLES):
            errors.append(f"docs/production.md missing: {needle}")

    checklist = ROOT / "docs" / "dr-checklist.md"
    if checklist.is_file():
        for needle in _must_contain(checklist, CHECKLIST_NEEDLES):
            errors.append(f"docs/dr-checklist.md missing: {needle}")

    env_example = ROOT / ".env.example"
    if not env_example.is_file():
        errors.append("missing file: .env.example")
    else:
        for needle in _must_contain(env_example, ENV_NEEDLES):
            errors.append(f".env.example missing: {needle}")

    errors.extend(_check_drills())

    if errors:
        print("DR docs gate failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("DR docs gate OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
