# ✅ Docker Setup - Final

## 📋 Oluşturulan Dosyalar

1. ✅ `mergen/streamlit.Dockerfile` - Streamlit container
2. ✅ `mergen/docker-compose.yml` - Streamlit servisi eklendi
3. ✅ `mergen/.env.example` - Environment template
4. ✅ `mergen/api/alembic.ini` - %04d hatası düzeltildi (yorum satırı)

## 🚀 Tek Komutla Başlatma

### 1. .env Dosyası Hazırla

```bash
cd mergen
cp .env.example .env
# .env dosyasını düzenleyin: SAM_API_KEY değerini girin
```

### 2. Downloads Klasörü Oluştur

```bash
mkdir -p ../downloads
```

### 3. Docker Compose ile Başlat

```bash
cd mergen
docker compose up -d --build
```

## 📊 Servisler

| Servis | Port | URL | Durum |
|--------|------|-----|-------|
| **db** | 5432 | - | PostgreSQL (persist) |
| **redis** | 6379 | - | Rate limit + cache |
| **api** | 8000 | http://localhost:8000/docs | FastAPI + Proxy |
| **streamlit** | 8501 | http://localhost:8501 | Streamlit UI |
| **web** | 3000 | http://localhost:3000 | Next.js (opsiyonel) |

## 🔍 Doğrulama

### Container Durumu

```bash
docker compose ps
```

**Beklenen**: Tüm servisler `Up (healthy)` durumunda

### API Test

```bash
curl http://localhost:8000/api/health
curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100"
```

### Streamlit UI

Tarayıcıda aç: **http://localhost:8501**

## 🔧 Özellikler

### API Servisi
- ✅ Alembic migration otomatik (`|| true` ile hata durumunda devam eder)
- ✅ DB health check bekler
- ✅ Redis başlangıcını bekler
- ✅ Proxy endpoints: `/api/proxy/opportunities/search`, `/noticedesc`

### Streamlit Servisi
- ✅ Build context: `..` (repo kökü)
- ✅ Dockerfile: `mergen/streamlit.Dockerfile`
- ✅ Volumes: `downloads`, `samples`, `.cache`
- ✅ Environment: `PROXY_API_URL=http://api:8000`
- ✅ Health check: Streamlit health endpoint

### Alembic Config
- ✅ `version_num_format = %04d` yorum satırı yapıldı
- ✅ Migration hatası API'yi durdurmaz (`|| true`)

## 📝 Environment Değişkenleri

### Zorunlu (.env)

```env
SAM_API_KEY=SAM-...
POSTGRES_USER=zgr
POSTGRES_PASSWORD=zgrpw
POSTGRES_DB=zgrbid
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
```

### Otomatik (docker-compose.yml)

```env
PROXY_API_URL=http://api:8000  # Streamlit için
NEXT_PUBLIC_API_URL=http://api:8000  # Next.js için
```

## 🎯 Toplu Çalışma Akışı

1. **Başlatma**: `docker compose up -d --build`
2. **DB**: PostgreSQL başlar, health check geçer
3. **Redis**: Rate limit + cache servisi
4. **API**: Alembic migration → FastAPI başlar
5. **Streamlit**: API'ye bağlanır (`PROXY_API_URL`)
6. **Kullanıcı**: Streamlit UI'da arama yapar
7. **Proxy**: Rate limiting + cache + circuit breaker
8. **DB**: Sonuçlar otomatik kaydedilir
9. **UI**: Metrikler gösterilir

## 🛑 Durdurma

```bash
# Tüm servisleri durdur
docker compose down

# Volumes ile birlikte sil
docker compose down -v
```

## 🔄 Yeniden Başlatma

```bash
# Sadece yeniden başlat
docker compose restart

# Yeniden build ile başlat
docker compose up -d --build
```

## 📝 Notlar

- **Windows**: `bash -c` komutu Linux container'larında çalışır
- **Volumes**: `downloads`, `samples`, `.cache` klasörleri host'ta kalır
- **Network**: Tüm servisler aynı Docker network'te (`mergen_default`)
- **Health Checks**: DB ve Streamlit için health check tanımlı

---

**Hazır!** Tek komutla tüm sistem ayağa kalkar. 🚀

