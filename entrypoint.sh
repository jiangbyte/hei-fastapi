#!/bin/sh
set -eu

ROLE="${1:-${HEI_PROCESS_ROLE:-${APP__PROCESS_ROLE:-all}}}"

start_worker() {
    exec python -m app.worker.main
}

start_api() {
    exec gunicorn app.main:app -c gunicorn.conf.py
}

start_all() {
    exec python -m app.platform.runtime.process_group
}

run_migrate() {
    exec python scripts/db/migrate.py
}

run_seed() {
    exec python scripts/seed/seed_super_admin.py
}

case "$ROLE" in
    all)
        start_all
        ;;
    api)
        start_api
        ;;
    worker)
        start_worker
        ;;
    migrate)
        run_migrate
        ;;
    seed)
        run_seed
        ;;
    *)
        echo "Unknown entrypoint role: $ROLE" >&2
        echo "Expected: all, api, worker, migrate, seed" >&2
        exit 64
        ;;
esac
