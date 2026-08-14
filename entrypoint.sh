#!/bin/sh
set -eu

# 默认启动应用（单进程内嵌 SnailJob 执行器，外部 Server 见 scripts/docker/）。
ROLE="${1:-api}"

start_api() {
    exec gunicorn app.main:app -c gunicorn.conf.py
}

run_migrate() {
    exec python scripts/db/migrate.py
}

run_seed() {
    exec python scripts/db/import_data.py
}

case "$ROLE" in
    api|"")
        start_api
        ;;
    migrate)
        run_migrate
        ;;
    seed)
        run_seed
        ;;
    *)
        echo "Unknown entrypoint role: $ROLE" >&2
        echo "Expected: api, migrate, seed" >&2
        exit 64
        ;;
esac
