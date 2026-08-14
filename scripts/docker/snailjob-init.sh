#!/usr/bin/env bash
# One-shot init for the local SnailJob Server database (snail_job) using plain psql.
# No Flyway: schema (from upstream aizuda SQL) is applied only when missing, then the
# hei-fastapi seed (namespace/group/jobs) is applied idempotently.
#
# Prerequisites: role/DB snail_job exist (e.g. admin/123456).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PG_HOST="${SNAIL_JOB_PG_HOST:-host.docker.internal}"
PG_PORT="${SNAIL_JOB_PG_PORT:-5432}"
PG_USER="${SNAIL_JOB_DB_USER:-admin}"
PG_PASSWORD="${SNAIL_JOB_DB_PASSWORD:-123456}"
PG_DB="${SNAIL_JOB_DB_NAME:-snail_job}"

export PGPASSWORD="${PG_PASSWORD}"
PSQL=(psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DB}" -v ON_ERROR_STOP=1)

schema_present="$("${PSQL[@]}" -tAc "SELECT to_regclass('public.sj_namespace') IS NOT NULL")"
if [ "${schema_present}" = "t" ]; then
  echo "snail_job schema already present; applying seed only."
else
  echo "snail_job schema missing; applying upstream schema."
  "${PSQL[@]}" -f "${ROOT}/scripts/sql/postgres/snailjob/schema.sql"
fi

"${PSQL[@]}" -f "${ROOT}/scripts/sql/postgres/snailjob/seed.sql"
echo "hei-fastapi SnailJob seed applied."
