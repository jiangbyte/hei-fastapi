"""将前端路由 JSON 资源数据转换为 sys_resource 表的 INSERT SQL。

使用方式：
  1. 从 web/admin/src/router/routes.static.ts 导出 JSON 数组：
     node -e "
       const fs = require('fs');
       const { staticRoutes } = require('./web/admin/src/router/routes.static.ts');
       fs.writeFileSync('/tmp/routes.json', JSON.stringify(staticRoutes, null, 2));
     "
     或手动将 staticRoutes 数组另存为 /tmp/routes.json。

  2. 运行：
     python scripts/seed/generate_resource_sql.py \
       --input /tmp/routes.json \
       --output /tmp/sys_resource_seed.sql

  3. 执行生成的 SQL（需要先手动插入 sys_resource_module 记录）：
     psql -U postgres -d hei_fastapi -f /tmp/sys_resource_seed.sql
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 与 sys_resource 表对应的字段列表（按表定义顺序）
RESOURCE_COLUMNS = [
    "id",
    "parent_id",
    "code",
    "name",
    "resource_type",
    "module_id",
    "path",
    "component",
    "redirect",
    "icon",
    "color",
    "href",
    "sort",
    "is_visible",
    "is_cache",
    "is_affix",
    "status",
    "description",
    "layout",
    "extra",
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
]

UPDATE_COLUMNS = [
    "parent_id", "code", "name", "resource_type", "module_id",
    "path", "component", "redirect", "icon", "color", "href",
    "sort", "is_visible", "is_cache", "is_affix", "status",
    "description", "layout", "extra",
    "updated_at", "updated_by",
]

# 前端独有、需丢弃的字段
FRONTEND_ONLY_FIELDS = {"module_id_name", "is_fullscreen"}


def coerce_bool(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def escape_sql_string(value: str | None) -> str:
    """将 Python 值转义为 SQL 字符串字面量，None 返回 NULL。"""
    if value is None:
        return "NULL"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def transform_row(row: dict) -> dict:
    """将前端路由记录映射为后端 sys_resource 列。"""

    def safe_str(key: str) -> str | None:
        v = row.get(key)
        if v is None or v == "":
            return None
        return str(v)

    def safe_bool(key: str) -> bool:
        return bool(row.get(key, False))

    # sort 强转 int（前端部分值为 string 如 '14'）
    raw_sort = row.get("sort", 99)
    sort_val = int(raw_sort) if raw_sort is not None else 99

    return {
        "id": safe_str("id"),
        "parent_id": safe_str("parent_id"),
        "code": safe_str("code"),
        "name": safe_str("name"),
        "resource_type": safe_str("resource_type"),
        "module_id": safe_str("module_id"),
        "path": safe_str("path"),
        "component": safe_str("component"),
        "redirect": safe_str("redirect"),
        "icon": safe_str("icon"),
        "color": safe_str("color"),
        "href": safe_str("href"),
        "sort": sort_val,
        "is_visible": safe_bool("is_visible"),
        "is_cache": safe_bool("is_cache"),
        "is_affix": safe_bool("is_affix"),
        "status": safe_str("status") or "ENABLED",
        "description": safe_str("description"),
        "layout": safe_str("layout"),
        "extra": {},
        "created_at": safe_str("created_at"),
        "created_by": safe_str("created_by"),
        "updated_at": safe_str("updated_at"),
        "updated_by": safe_str("updated_by"),
    }


def format_value(value) -> str:
    """将 Python 值格式化为 SQL 字面量。"""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return coerce_bool(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, dict):
        return escape_sql_string(json.dumps(value, ensure_ascii=False))
    return escape_sql_string(str(value))


def validate_data(rows: list[dict]) -> None:
    """检查数据是否有重复的 (module_id, code) 组合。"""
    seen: dict[tuple[str | None, str], str] = {}
    for r in rows:
        mid = r.get("module_id") or None
        code = r.get("code")
        if not code:
            print(f"警告：id={r.get('id')} 缺少 code，跳过检查", file=sys.stderr)
            continue
        key = (mid, code)
        if key in seen:
            print(
                f"错误：存在重复 (module_id, code) = ({mid!r}, {code!r})："
                f" id={seen[key]} 与 id={r.get('id')}",
                file=sys.stderr,
            )
            sys.exit(1)
        seen[key] = r.get("id") or ""


def generate_insert_sql(rows: list[dict]) -> str:
    """生成 INSERT INTO ... ON CONFLICT DO UPDATE 语句。"""
    if not rows:
        return "-- (empty data)"

    columns_str = ", ".join(RESOURCE_COLUMNS)
    values_lines: list[str] = []
    conflict_set = ", ".join(f"  {c} = EXCLUDED.{c}" for c in UPDATE_COLUMNS)

    for row in rows:
        transformed = transform_row(row)
        values = ", ".join(format_value(transformed[c]) for c in RESOURCE_COLUMNS)
        values_lines.append(f"  ({values})")

    values_block = ",\n".join(values_lines)

    sql = f"""INSERT INTO sys_resource ({columns_str})
VALUES
{values_block}
ON CONFLICT (id) DO UPDATE SET
{conflict_set};
"""
    return sql


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将前端路由 JSON 资源数据转换为 sys_resource 表的 INSERT SQL。",
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="输入 JSON 文件路径（包含资源对象数组）",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="输出 SQL 文件路径（默认输出到 stdout）",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"错误：输入文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("错误：JSON 内容必须是一个数组", file=sys.stderr)
        sys.exit(1)

    validate_data(data)
    sql = generate_insert_sql(data)

    output_path = args.output
    if output_path:
        Path(output_path).write_text(sql, encoding="utf-8")
        print(f"已生成 {len(data)} 条 INSERT 语句，写入: {output_path}")
    else:
        print(sql)


if __name__ == "__main__":
    main()
