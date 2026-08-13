#!/usr/bin/env bash
# Apply hei-fastapi SnailJob seed only (idempotent SQL).
# Use when snail_job schema already exists (e.g. migrated by hei-boot).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEED="${ROOT}/script/sql/postgres/snailjob/V2__hei_fastapi_seed.sql"
PG_HOST="${SNAIL_JOB_PG_HOST:-127.0.0.1}"
PG_PORT="${SNAIL_JOB_PG_PORT:-5432}"
PG_USER="${SNAIL_JOB_DB_USER:-admin}"
PG_PASSWORD="${SNAIL_JOB_DB_PASSWORD:-123456}"
PG_DB="${SNAIL_JOB_DB_NAME:-snail_job}"

export PGPASSWORD="${PG_PASSWORD}"
psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DB}" -v ON_ERROR_STOP=1 -f "${SEED}"
echo "hei-fastapi SnailJob seed applied."
