# Base Image
FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

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
# This ensures all necessary files (sam_integration.py, app/, migrations/, etc.) are included
COPY . /app/

# Expose port
EXPOSE 8080

# --- KRİTİK DEĞİŞİKLİK ---
# Entrypoint script'ini devre dışı bırakıyoruz.
# Doğrudan uvicorn komutunu çalıştırıyoruz.
# "sh -c" kullanarak $PORT değişkeninin algılanmasını sağlıyoruz.
# Alembic migration'ları uygulama başlarken çalıştırılıyor (opsiyonel, hata olsa bile devam eder).
CMD ["sh", "-c", "python -m alembic upgrade head || echo 'Migration failed, continuing...' && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
