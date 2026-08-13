#!/bin/sh
set -e

echo "Stopping all services started by entrypoint.sh..."

if pkill -f "python -m app.worker.main" 2>/dev/null; then
  echo "  snailjob worker stopped"
else
  echo "  snailjob worker not found"
fi

if pkill -f "gunicorn.*app\.main:app" 2>/dev/null; then
  echo "  gunicorn        stopped"
else
  echo "  gunicorn        not found"
fi

echo "Done."
