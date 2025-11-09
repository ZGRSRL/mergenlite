# MergenLite - Docker Setup Guide

## 🐳 Docker ile Kurulum

### Gereksinimler
- Docker Desktop veya Docker Engine
- Docker Compose

### Hızlı Başlangıç

1. **Repository'yi klonlayın:**
```bash
git clone <repository-url>
cd Mergenlite
```

2. **Environment dosyasını oluşturun:**
```bash
cp .env.example .env
# veya manuel olarak .env dosyası oluşturun
```

`.env` dosyasına şunları ekleyin:
```env
OPENAI_API_KEY=your_openai_api_key_here
SAM_API_KEY=your_sam_api_key_here
DATABASE_URL=postgresql://postgres:postgres@db:5432/mergenlite
```

3. **Docker Compose ile başlatın:**
```bash
docker-compose up -d
```

4. **Uygulamaya erişin:**
- Tarayıcınızda: http://localhost:8501

### Docker Komutları

**Başlatma:**
```bash
docker-compose up -d
```

**Durdurma:**
```bash
docker-compose down
```

**Logları görüntüleme:**
```bash
docker-compose logs -f mergenlite
```

**Yeniden build:**
```bash
docker-compose build --no-cache
docker-compose up -d
```

**Container'a bağlanma:**
```bash
docker exec -it mergenlite bash
```

### Sadece Dockerfile ile (PostgreSQL olmadan)

Eğer harici bir PostgreSQL kullanıyorsanız:

```bash
# Build
docker build -t mergenlite .

# Run
docker run -d \
  -p 8501:8501 \
  -e OPENAI_API_KEY=your_key \
  -e SAM_API_KEY=your_key \
  -v $(pwd)/opportunities:/app/opportunities \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/samples:/app/samples \
  --name mergenlite \
  mergenlite
```

### Volume Mounts

Docker Compose aşağıdaki dizinleri volume olarak mount eder:
- `./opportunities` - Analiz edilen fırsatlar
- `./downloads` - İndirilen dökümanlar
- `./samples` - Örnek dosyalar
- `./hotel_database.json` - Otel veritabanı

Bu sayede container yeniden başlatılsa bile veriler korunur.

### Troubleshooting

**Port zaten kullanılıyor:**
```bash
# Port'u değiştirin docker-compose.yml'de
ports:
  - "8502:8501"  # 8502 portunu kullan
```

**Database bağlantı hatası:**
```bash
# Database container'ının çalıştığını kontrol edin
docker-compose ps

# Database loglarını kontrol edin
docker-compose logs db
```

**Build hatası:**
```bash
# Cache olmadan yeniden build
docker-compose build --no-cache
```

### Production Deployment

Production için:
1. Environment variables'ı güvenli bir şekilde yönetin (secrets management)
2. HTTPS için reverse proxy (nginx/traefik) kullanın
3. Database backup stratejisi oluşturun
4. Resource limits ekleyin (docker-compose.yml'de)

Örnek production docker-compose.yml:
```yaml
services:
  mergenlite:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

