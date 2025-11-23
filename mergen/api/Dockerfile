FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev postgresql-client libgl1 libglib2.0-0 netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations
COPY app /app/app
COPY sam_integration.py /app/sam_integration.py

RUN pip install --upgrade pip && pip install . && pip install alembic pydantic-settings psycopg2-binary

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Cloud Run requires PORT environment variable
# Default to 8000 for local development
ENV PORT=8000

# Cloud Run requires PORT environment variable
# Default to 8000 for local development
ENV PORT=8000

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
# PORT will be handled by entrypoint.sh
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
