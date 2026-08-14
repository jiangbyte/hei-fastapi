#!/bin/sh
set -e

echo "Stopping services started by entrypoint.sh..."

if pkill -f "gunicorn.*app\.main:app" 2>/dev/null; then
  echo "  gunicorn        stopped"
else
  echo "  gunicorn        not found"
fi

echo "Done."
