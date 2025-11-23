#!/bin/sh
set -e

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

if ! command -v pg_isready >/dev/null 2>&1; then
  echo "pg_isready not found. Ensure postgresql-client is installed in the image."
  exit 1
fi

echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; do
  sleep 1
done

echo "Running migrations..."
python -m alembic upgrade head || echo "Migration failed, continuing anyway..."

# Cloud Run compatibility: Use PORT environment variable if set
if [ -n "$PORT" ]; then
  echo "Starting application on port $PORT (Cloud Run mode)"
  exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
else
  echo "Starting application with default command"
  exec "$@"
fi
