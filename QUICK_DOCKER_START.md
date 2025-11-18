# 🚀 Hızlı Docker Başlatma

## ✅ Hazır Dosyalar

1. ✅ `mergen/streamlit.Dockerfile` - Streamlit container için
2. ✅ `mergen/docker-compose.yml` - Streamlit servisi eklendi
3. ✅ `mergen/.env.example` - Environment değişkenleri örneği

## 📋 Adımlar

### 1. .env Dosyası Hazırla

```bash
cd mergen
cp .env.example .env
# .env dosyasını düzenleyin: SAM_API_KEY değerini girin
```

**Zorunlu değişkenler**:
```env
SAM_API_KEY=SAM-2cf274b1-5d51-4e4e-9622-4944b74f1e2c
API_PORT=8000
PROXY_API_URL=http://api:8000
POSTGRES_USER=zgr
POSTGRES_PASSWORD=zgrpw
POSTGRES_DB=zgrbid
POSTGRES_PORT=5432
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
```

### 2. Downloads Klasörü Oluştur

```bash
mkdir -p downloads
```

### 3. Alembic Config Fix (Opsiyonel)

Eğer `%04d` hatası alırsanız:

`mergen/api/alembic.ini` dosyasını açın, 37. satırı:
```ini
version_num_format = %%04d
```
olarak değiştirin (veya satırı yorum satırı yapın).

### 4. Docker Compose ile Başlat

```bash
cd mergen
docker compose up -d --build
```

## 🎯 Servisler

- **db** (PostgreSQL): Port 5432
- **redis**: Port 6379  
- **api** (FastAPI): Port 8000
  - Alembic migration otomatik çalışır
  - Proxy endpoints: `/api/proxy/opportunities/search`, `/noticedesc`
- **streamlit**: Port 8501
  - `app.py` çalışır
  - `PROXY_API_URL=http://api:8000` ile API'ye bağlanır

## 🔍 Doğrulama

### Container'ları Kontrol Et

```bash
docker compose ps
```

**Beklenen**: Tüm servisler `Up` durumunda

### API Test

```bash
curl http://localhost:8000/api/health
curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100"
```

### Streamlit UI

Tarayıcıda aç: http://localhost:8501

## 🛑 Durdurma

```bash
docker compose down
```

## 🔄 Yeniden Başlatma

```bash
docker compose restart
# veya
docker compose up -d --build
```

---

**Detaylar**: `DOCKER_SETUP.md` dosyasına bakın

