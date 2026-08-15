#!/bin/sh
set -eu

# 仅启动 API（单进程内嵌 SnailJob 执行器，对接外部 SnailJob Server）。
# 数据库表结构由人工维护：应用启动不执行迁移/种子；
# 需要时在维护机直接运行 python scripts/db/migrate.py / import_data.py。
ROLE="${1:-api}"

case "$ROLE" in
    api|"")
        exec gunicorn app.main:app -c gunicorn.conf.py
        ;;
    migrate|seed)
        echo "entrypoint role '$ROLE' removed: database schema/seed is maintained manually." >&2
        exit 64
        ;;
    *)
        echo "Unknown entrypoint role: $ROLE" >&2
        echo "Expected: api" >&2
        exit 64
        ;;
esac
