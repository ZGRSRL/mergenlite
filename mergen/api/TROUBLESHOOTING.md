# Cloud Run Troubleshooting Guide

## Container Failed to Start / Port Not Listening

### Problem
```
Container failed to start and listen on the port defined provided by the PORT=8080
```

### Root Causes

1. **Windows Line Endings (CRLF)**
   - Windows'ta oluşturulan shell script'ler CRLF (`\r\n`) kullanır
   - Linux (Cloud Run) sadece LF (`\n`) bekler
   - **Solution**: Dockerfile'da `sed -i 's/\r$//'` ile dönüşüm yapılmalı

2. **Missing Executable Permission**
   - `docker-entrypoint.sh` dosyası çalıştırılabilir olmalı
   - **Solution**: Dockerfile'da `chmod +x` yapılmalı

3. **Wrong Entrypoint Path**
   - Entrypoint dosyası doğru yolda olmalı
   - **Solution**: `ENTRYPOINT ["/app/docker-entrypoint.sh"]` (absolute path)

4. **CMD/ENTRYPOINT Conflict**
   - ENTRYPOINT ve CMD birlikte kullanıldığında çakışma olabilir
   - **Solution**: Sadece ENTRYPOINT kullan, CMD'yi entrypoint içinde handle et

### Fixed Dockerfile

```dockerfile
# Copy files
COPY . /app/

# Fix Windows line endings (CRLF -> LF)
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh || true

# Make executable
RUN chmod +x /app/docker-entrypoint.sh

# Entrypoint handles everything
ENTRYPOINT ["/app/docker-entrypoint.sh"]
```

### Fixed docker-entrypoint.sh

```bash
#!/bin/sh
set -e

# Use PORT from environment (Cloud Run sets this)
APP_PORT=${PORT:-8080}

# Database check (only for Docker Compose)
DB_HOST=${POSTGRES_HOST:-${DB_HOST:-db}}
if [ "$DB_HOST" = "db" ] || [ "$DB_HOST" = "localhost" ]; then
  # Wait for Docker Compose database
  if command -v pg_isready >/dev/null 2>&1; then
    until pg_isready -h "$DB_HOST" -p "${POSTGRES_PORT:-5432}" >/dev/null 2>&1; do
      sleep 1
    done
  fi
fi

# Migrations
python -m alembic upgrade head || echo "Migration failed, continuing..."

# Start app
exec uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"
```

## Checking Logs

### View Recent Logs
```bash
gcloud run services logs read mergenlite-backend \
  --region europe-west1 \
  --limit 50
```

### Stream Logs (Real-time)
```bash
gcloud run services logs tail mergenlite-backend \
  --region europe-west1
```

### Filter by Error
```bash
gcloud run services logs read mergenlite-backend \
  --region europe-west1 \
  --limit 100 | grep -i error
```

## Common Errors

### 1. "Container failed to start"
- **Check**: Entrypoint script executable?
- **Check**: Line endings correct (LF, not CRLF)?
- **Check**: PORT environment variable set?

### 2. "Database connection failed"
- **Check**: `POSTGRES_HOST` set correctly?
- **Check**: Cloud SQL instance connection name format: `project:region:instance`
- **Check**: `--add-cloudsql-instances` flag used in deploy?

### 3. "Module not found"
- **Check**: All files copied in Dockerfile?
- **Check**: `.dockerignore` not excluding needed files?
- **Check**: `sam_integration.py` in correct location?

### 4. "Port already in use"
- **Check**: Only one process listening on PORT?
- **Check**: `exec` used in entrypoint (replaces shell process)?

## Testing Locally

### Build and Test Docker Image
```bash
cd mergen/api
docker build -t mergenlite-test .
docker run -p 8080:8080 -e PORT=8080 mergenlite-test
```

### Test Entrypoint Script
```bash
# Check line endings
file docker-entrypoint.sh
# Should show: "ASCII text" (not "ASCII text, with CRLF line terminators")

# Check executable
ls -la docker-entrypoint.sh
# Should show: -rwxr-xr-x (executable bit set)

# Test script syntax
sh -n docker-entrypoint.sh
# Should return no errors
```

## Deployment Checklist

- [ ] Dockerfile has `sed -i 's/\r$//'` for entrypoint
- [ ] Dockerfile has `chmod +x` for entrypoint
- [ ] `docker-entrypoint.sh` uses `exec` for uvicorn
- [ ] `docker-entrypoint.sh` uses `${PORT:-8080}` for port
- [ ] ENTRYPOINT uses absolute path: `/app/docker-entrypoint.sh`
- [ ] No CMD conflicting with ENTRYPOINT
- [ ] All environment variables set in deploy command
- [ ] Cloud SQL instance connection name correct format

