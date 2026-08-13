#!/bin/sh
set -eu

ROLE="${1:-${HEI_PROCESS_ROLE:-${APP__PROCESS_ROLE:-all}}}"

snail_job_enabled() {
    case "${SNAIL_JOB__ENABLED:-true}" in
        1|true|TRUE|yes|YES|on|ON) return 0 ;;
        *) return 1 ;;
    esac
}

start_worker() {
    if ! snail_job_enabled; then
        echo "SnailJob disabled (SNAIL_JOB__ENABLED=false); worker will not start" >&2
        exit 0
    fi
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
