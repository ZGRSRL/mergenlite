#!/bin/sh
set -e

# Cloud Run compatibility: Use PORT environment variable if set
APP_PORT=${PORT:-8000}

# Database connection check - only wait for Docker Compose 'db' host
# Cloud SQL connections don't need waiting (they're already ready)
DB_HOST=${POSTGRES_HOST:-${DB_HOST:-db}}
DB_PORT=${POSTGRES_PORT:-${DB_PORT:-5432}}

# Only wait for database if using Docker Compose (host = 'db')
# Cloud SQL uses Unix socket path (/cloudsql/...) which doesn't need pg_isready
if [ "$DB_HOST" = "db" ] || [ "$DB_HOST" = "localhost" ]; then
  if command -v pg_isready >/dev/null 2>&1; then
    echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; do
      sleep 1
    done
    echo "Database is ready!"
  else
    echo "Warning: pg_isready not found. Skipping database readiness check."
  fi
else
  echo "Using Cloud SQL or external database at ${DB_HOST}. Skipping readiness check."
fi

# Run migrations (only if database is accessible)
echo "Running migrations..."
python -m alembic upgrade head || echo "Migration failed, continuing anyway..."

# Start application
echo "Starting application on port ${APP_PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"
