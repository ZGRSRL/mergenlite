FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        postgresql-client \
        libgl1 \
        libglib2.0-0 \
        netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for better Docker layer caching)
COPY pyproject.toml /app/pyproject.toml

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install . && \
    pip install alembic pydantic-settings psycopg2-binary

# Copy everything else (respects .dockerignore)
# This ensures all necessary files (sam_integration.py, app/, migrations/, etc.) are included
COPY . /app/

# Fix Windows line endings (CRLF -> LF) for entrypoint script
# This is critical for Cloud Run (Linux-based)
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh || true

# Make entrypoint executable (required for Cloud Run)
RUN chmod +x /app/docker-entrypoint.sh

# Cloud Run requires PORT environment variable
# Default to 8080 (Cloud Run standard) for production, 8000 for local
ENV PORT=8080

EXPOSE 8080

# Entrypoint script handles PORT env var and starts uvicorn
ENTRYPOINT ["/app/docker-entrypoint.sh"]
