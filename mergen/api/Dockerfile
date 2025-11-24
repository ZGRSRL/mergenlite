# Base Image
FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        postgresql-client \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for better Docker layer caching)
COPY pyproject.toml /app/pyproject.toml
COPY alembic.ini /app/alembic.ini

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install . && \
    pip install alembic pydantic-settings psycopg2-binary

# Copy everything else (respects .dockerignore)
COPY . /app/

# Expose port
EXPOSE 8080

# --- KRİTİK DEĞİŞİKLİK ---
# Değişken kullanma, direkt 8080 yaz. En güvenlisi budur.
# Alembic migration'ları uygulama başlamadan önce çalıştır (hata olsa bile devam et)
# app.main:app çünkü uygulama app/ klasörü içinde
CMD ["sh", "-c", "python -m alembic upgrade head || echo 'Migration failed, continuing...' && uvicorn app.main:app --host 0.0.0.0 --port 8080"]
