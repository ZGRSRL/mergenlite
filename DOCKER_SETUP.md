# 🐳 Docker Setup - Toplu Çalıştırma

## ✅ Tamamlanan Değişiklikler

1. ✅ **Streamlit Dockerfile**: `mergen/streamlit.Dockerfile` oluşturuldu
2. ✅ **docker-compose.yml**: Streamlit servisi eklendi, API komutu güncellendi
3. ✅ **.env.example**: Örnek environment değişkenleri

## 📋 Kurulum

### 1. .env Dosyası Hazırla

`mergen/.env` dosyasını oluşturun (`.env.example`'dan kopyalayın):

```bash
cd mergen
cp .env.example .env
# .env dosyasını düzenleyin: SAM_API_KEY değerini girin
```

**Zorunlu değişkenler**:
- `SAM_API_KEY`: SAM.gov API anahtarı
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `REDIS_URL`: `redis://redis:6379/0`

### 2. Downloads Klasörü Oluştur

```bash
mkdir -p downloads
```

### 3. Docker Compose ile Başlat

```bash
cd mergen
docker compose up -d --build
```

## 🚀 Servisler

### Çalışan Servisler

1. **db** (PostgreSQL): Port 5432
2. **redis**: Port 6379
3. **api** (FastAPI): Port 8000
   - Alembic migration otomatik çalışır
   - Proxy endpoints: `/api/proxy/opportunities/search`, `/noticedesc`
4. **streamlit**: Port 8501
   - `app.py` veya `mergenlite_app.py` çalışır
   - `PROXY_API_URL=http://api:8000` ile API'ye bağlanır
5. **web** (Next.js, opsiyonel): Port 3000
6. **worker** (RQ worker, opsiyonel)

### URL'ler

- **API Docs**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501
- **Next.js Web** (opsiyonel): http://localhost:3000

## 🔧 Yapılandırma

### Streamlit Dockerfile

`mergen/streamlit.Dockerfile`:
- Python 3.11 slim base
- Sistem bağımlılıkları (gcc, g++)
- Requirements.txt'ten bağımlılıklar
- Çalışma dizini: `/app`
- Port: 8501

**Not**: `mergenlite_app.py` kullanmak için Dockerfile'daki `CMD` satırını değiştirin:
```dockerfile
CMD ["streamlit", "run", "mergenlite_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

### docker-compose.yml Değişiklikleri

1. **API servisi**:
   - Alembic migration otomatik çalışır (`alembic upgrade head || true`)
   - DB health check bekler
   - Redis başlangıcını bekler

2. **Streamlit servisi**:
   - Build context: `..` (repo kökü)
   - Dockerfile: `mergen/streamlit.Dockerfile`
   - Volumes: `downloads`, `samples`, `.cache`
   - Environment: `PROXY_API_URL=http://api:8000`

## 🧪 Doğrulama

### 1. Container'ları Kontrol Et

```bash
docker compose ps
```

**Beklenen**: Tüm servisler `Up` durumunda

### 2. API Health Check

```bash
curl http://localhost:8000/api/health
```

### 3. Proxy Endpoint Test

```bash
curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100"
```

### 4. Streamlit UI

Tarayıcıda aç: http://localhost:8501

**Beklenen**: Streamlit uygulaması açılır, API'ye bağlanır

## 🔍 Sorun Giderme

### Alembic %04d Hatası

Eğer `% must be followed by` hatası alırsanız:

1. `mergen/api/alembic.ini` dosyasını açın
2. `file_template` veya `log_format` satırlarında `%` karakterlerini `%%` yapın
3. Container'ı yeniden build edin:
   ```bash
   docker compose build api
   docker compose up -d api
   ```

### Port Çakışması

Eğer portlar kullanılıyorsa, `docker-compose.yml`'de port mapping'leri değiştirin:

```yaml
ports:
  - "8502:8501"  # Streamlit için farklı port
```

### Volume Mount Hataları

Windows'ta volume mount sorunları için:

```yaml
volumes:
  - ../downloads:/app/downloads:rw  # :rw ekleyin
```

### API Bağlantı Hatası

Streamlit'ten API'ye bağlanamıyorsa:

1. `PROXY_API_URL` environment değişkenini kontrol edin
2. API container'ının çalıştığını kontrol edin: `docker compose ps api`
3. Aynı Docker network'te olduklarını kontrol edin: `docker network ls`

## 📊 Toplu Çalışma Akışı

1. **Başlatma**: `docker compose up -d --build`
2. **API**: Alembic migration → FastAPI başlar
3. **Streamlit**: API'ye bağlanır (`PROXY_API_URL`)
4. **Kullanıcı**: Streamlit UI'da arama yapar
5. **Proxy**: Rate limiting + cache + circuit breaker
6. **DB**: Sonuçlar otomatik kaydedilir
7. **UI**: Metrikler gösterilir (Toplam Sonuç, DB'ye Kaydedilen, Son Senkron)

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
```

## 📝 Notlar

- **Windows**: `bash -c` komutu Linux container'larında çalışır
- **Volumes**: `downloads` ve `samples` klasörleri host'ta kalır
- **Cache**: `.cache` klasörü volume olarak mount edilir
- **Environment**: Tüm servisler `.env` dosyasını kullanır
- **Network**: Tüm servisler aynı Docker network'te (`mergen_default`)

---

**Oluşturulma Tarihi**: 2025-02-15  
**Dosyalar**: 
- `mergen/streamlit.Dockerfile`
- `mergen/docker-compose.yml` (güncellendi)
- `mergen/.env.example`

