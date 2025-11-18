# 🐳 Docker Quick Start - Tek Komutla Başlatma

## ✅ Hazır Dosyalar

- ✅ `mergen/streamlit.Dockerfile` - Streamlit container
- ✅ `mergen/docker-compose.yml` - Tüm servisler
- ✅ `mergen/.env.example` - Environment template

## 🚀 Hızlı Başlatma (3 Adım)

### 1. .env Dosyası Hazırla

```bash
cd mergen
cp .env.example .env
```

`.env` dosyasını düzenleyin, **SAM_API_KEY** değerini girin:

```env
SAM_API_KEY=SAM-2cf274b1-5d51-4e4e-9622-4944b74f1e2c
```

### 2. Downloads Klasörü Oluştur

```bash
# mergen klasöründen
mkdir -p ../downloads
```

### 3. Docker Compose ile Başlat

```bash
cd mergen
docker compose up -d --build
```

## 📊 Çalışan Servisler

| Servis | Port | URL | Açıklama |
|--------|------|-----|----------|
| **db** | 5432 | - | PostgreSQL (persist volume) |
| **redis** | 6379 | - | Rate limit + cache |
| **api** | 8000 | http://localhost:8000/docs | FastAPI (proxy endpoints) |
| **streamlit** | 8501 | http://localhost:8501 | Streamlit UI |
| **web** | 3000 | http://localhost:3000 | Next.js (opsiyonel) |

## 🔍 Doğrulama

### Container Durumu

```bash
docker compose ps
```

**Beklenen**: Tüm servisler `Up (healthy)` durumunda

### API Health Check

```bash
curl http://localhost:8000/api/health
```

### Proxy Endpoint Test

```bash
curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100"
```

**Beklenen Response**:
```json
{
  "total": 150,
  "results": [...],
  "saved": 150
}
```

### Streamlit UI

Tarayıcıda aç: **http://localhost:8501**

**Beklenen**: Streamlit uygulaması açılır, API'ye bağlanır

## 🔧 Yapılandırma

### Streamlit Dosyası Değiştirme

`mergenlite_app.py` kullanmak için `mergen/streamlit.Dockerfile` dosyasını düzenleyin:

```dockerfile
CMD ["streamlit", "run", "mergenlite_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

### Environment Değişkenleri

**Docker network içinde**:
- `PROXY_API_URL=http://api:8000` (servis adı: `api`)
- `NEXT_PUBLIC_API_URL=http://api:8000`

**Host'tan erişim**:
- `http://localhost:8000` (API)
- `http://localhost:8501` (Streamlit)

## 🛑 Durdurma

```bash
# Tüm servisleri durdur
docker compose down

# Volumes ile birlikte sil (DB verileri silinir!)
docker compose down -v
```

## 🔄 Yeniden Başlatma

```bash
# Sadece yeniden başlat
docker compose restart

# Yeniden build ile başlat
docker compose up -d --build

# Sadece streamlit'i yeniden başlat
docker compose restart streamlit
```

## 📝 Log Kontrolü

```bash
# Tüm servislerin logları
docker compose logs -f

# Sadece API logları
docker compose logs -f api

# Sadece Streamlit logları
docker compose logs -f streamlit
```

## ⚠️ Sorun Giderme

### Alembic %04d Hatası

Eğer migration sırasında hata alırsanız:

1. `mergen/api/alembic.ini` dosyasını açın
2. 37. satırı kontrol edin (zaten yorum satırı yapıldı)
3. API komutu `|| true` ile migration hatasını yok sayar

### Port Çakışması

Portlar kullanılıyorsa `docker-compose.yml`'de değiştirin:

```yaml
ports: ["8502:8501"]  # Streamlit için farklı port
```

### API Bağlantı Hatası

Streamlit'ten API'ye bağlanamıyorsa:

1. `PROXY_API_URL=http://api:8000` olduğundan emin olun
2. API container'ının çalıştığını kontrol edin: `docker compose ps api`
3. Logları kontrol edin: `docker compose logs api`

### Volume Mount Hataları

Windows'ta volume mount sorunları için:

```yaml
volumes:
  - ../downloads:/app/downloads:rw
```

## 🎯 Toplu Çalışma Akışı

1. **Başlatma**: `docker compose up -d --build`
2. **API**: Alembic migration → FastAPI başlar
3. **Streamlit**: API'ye bağlanır (`PROXY_API_URL`)
4. **Kullanıcı**: Streamlit UI'da arama yapar
5. **Proxy**: Rate limiting + cache + circuit breaker
6. **DB**: Sonuçlar otomatik kaydedilir
7. **UI**: Metrikler gösterilir (Toplam Sonuç, DB'ye Kaydedilen, Son Senkron)

## 📋 Environment Değişkenleri

### Zorunlu

```env
SAM_API_KEY=SAM-...
POSTGRES_USER=zgr
POSTGRES_PASSWORD=zgrpw
POSTGRES_DB=zgrbid
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
```

### Opsiyonel

```env
API_PORT=8000
PROXY_API_URL=http://api:8000
NEXT_PUBLIC_API_URL=http://api:8000
```

---

**Hazır!** Tek komutla tüm sistem ayağa kalkar. 🚀

