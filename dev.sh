#!/bin/sh
set -e

echo "Starting development infrastructure..."

for container in dev-postgres dev-minio dev-redis; do
  if docker start "$container" >/dev/null 2>&1; then
    echo "  $container  started"
  else
    echo "  $container  not found or failed to start"
  fi
done

echo "Done."
