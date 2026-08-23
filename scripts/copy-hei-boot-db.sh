#!/usr/bin/env bash
# Copy hei_boot (MySQL) to hei_fastapi. See hei-boot/scripts/copy-hei-boot-db-mysql.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec bash "${ROOT}/hei-boot/scripts/copy-hei-boot-db-mysql.sh" "${1:-hei_fastapi}"
