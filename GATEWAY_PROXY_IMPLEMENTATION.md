# 🚀 Gateway/Proxy Implementation Summary

## ✅ Tamamlanan Özellikler

### 1. Redis Client & Rate Limiting
- **Dosya**: `mergen/api/app/services/redis_client.py`
- **Token Bucket**: 1 req/sec, burst 3
- **Lua Script**: Atomic token bucket operations
- **Graceful Degradation**: Redis yoksa rate limiting devre dışı

### 2. Circuit Breaker
- **Dosya**: `mergen/api/app/services/circuit_breaker.py`
- **States**: CLOSED → OPEN → HALF_OPEN
- **Thresholds**: 5 failures → OPEN, 2 successes → CLOSED
- **Timeout**: 60 seconds

### 3. Proxy Endpoints
- **Dosya**: `mergen/api/app/routes/proxy.py`
- **GET /api/proxy/opportunities/search**: DB/cache-first, sayfalama, rate limiting
- **GET /api/proxy/opportunities/noticedesc**: URL/ID autodetect, cache-first

### 4. Response Headers
- `X-Cache`: HIT/MISS/DB
- `X-Source`: sam_live/gsa_live/db/cache
- `X-Rate-Limit-Remaining`: Kalan token sayısı
- `X-Circuit-Breaker`: OPEN/CLOSED/HALF_OPEN

### 5. Saatlik Sync Job
- **Dosya**: `mergen/api/app/scripts/sync_opportunities.py`
- **NAICS 721110**: Otomatik senkronizasyon
- **Cron/RQ**: Saatlik çalıştırma

## 📋 API Endpoints

### GET /api/proxy/opportunities/search
```bash
curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100"
```

**Parametreler**:
- `keywords` (optional): Arama kelimeleri
- `naics` (default: 721110): NAICS kodu
- `days_back` (default: 30, min: 1, max: 365): Geriye dönük gün sayısı
- `limit` (default: 100, min: 1, max: 1000): Döndürülecek maksimum sonuç
- `page_size` (default: 1000, min: 1, max: 1000): Sayfalama boyutu

**Response**:
```json
{
  "opportunities": [...],
  "total": 150,
  "source": "sam_live",
  "cached_at": "2025-02-15T10:30:00"
}
```

**Headers**:
- `X-Cache`: HIT/MISS/DB
- `X-Source`: sam_live/db/cache
- `X-Rate-Limit-Remaining`: 2
- `X-Circuit-Breaker`: CLOSED

### GET /api/proxy/opportunities/noticedesc
```bash
curl "http://localhost:8000/api/proxy/opportunities/noticedesc?notice_id=W50S7526QA010"
# veya
curl "http://localhost:8000/api/proxy/opportunities/noticedesc?url=https://sam.gov/opp/4af381a2.../view"
```

**Parametreler**:
- `notice_id` (optional): Notice ID
- `opportunity_id` (optional): Opportunity ID
- `url` (optional): SAM.gov URL (auto-detect ID)

**Response**:
```json
{
  "success": true,
  "data": {
    "noticeId": "W50S7526QA010",
    "title": "...",
    "attachments": [...]
  }
}
```

## 🔧 Redis Configuration

### docker-compose.yml
Redis zaten mevcut:
```yaml
redis:
  image: redis:7
  ports: ["6379:6379"]
```

### Config
```python
# mergen/api/app/config.py
redis_url: str = "redis://redis:6379/0"
```

### Local Development
```bash
# Redis'i başlat
docker-compose up redis -d

# veya local Redis
redis_url = "redis://localhost:6379/0"
```

## 📊 Rate Limiting

### Token Bucket
- **Rate**: 1 token/second
- **Capacity**: 3 tokens (burst)
- **Key**: `rate_limit:sam_api`

### Örnek Senaryo
1. İlk 3 istek: ✅ (burst)
2. 4. istek: ⏳ 1 saniye bekle
3. 5. istek: ⏳ 1 saniye bekle
4. ...

### 429 Response
```json
{
  "detail": "Rate limit exceeded. Wait 1.2s"
}
```

## 🔄 Circuit Breaker

### States
- **CLOSED**: Normal operation
- **OPEN**: API down, reject requests
- **HALF_OPEN**: Testing recovery

### Thresholds
- **Failure Threshold**: 5 failures → OPEN
- **Success Threshold**: 2 successes → CLOSED
- **Timeout**: 60 seconds

### Örnek Senaryo
1. 5 başarısız istek → OPEN
2. 60 saniye bekle
3. HALF_OPEN → test isteği
4. 2 başarılı istek → CLOSED

## 💾 Cache Strategy

### TTL (Time To Live)
- **1-6 saat**: `days_back` parametresine göre dinamik
- **Formula**: `min(21600, max(3600, days_back * 120))`

### Cache Key
```python
cache_key = f"opp_search:{md5_hash(params)}"
```

### Cache Flow
1. Cache kontrolü (Redis)
2. Cache MISS → DB kontrolü
3. DB MISS → SAM API
4. Sonuç cache'le

## 🔄 Request Coalescing

### Mantık
Aynı parametreli eşzamanlı istekler:
1. İlk istek: SAM API'ye git
2. Diğer istekler: İlk isteğin tamamlanmasını bekle
3. Sonuç: Tüm istekler aynı sonucu alır

### Implementation
```python
if key in self.in_flight:
    # Wait for in-flight request
    await asyncio.sleep(0.1)
    cached = self.get(key)
    if cached:
        return cached
```

## 📅 Saatlik Sync Job

### Manuel Çalıştırma
```bash
cd mergen/api
python -m app.scripts.sync_opportunities
```

### Cron (Linux/Mac)
```bash
# Saatlik çalıştır
0 * * * * cd /path/to/mergen/api && python -m app.scripts.sync_opportunities
```

### RQ Scheduler (Python)
```python
from rq_scheduler import Scheduler
from app.scripts.sync_opportunities import sync_naics_721110

scheduler = Scheduler(connection=redis_conn)
scheduler.cron(
    cron_string='0 * * * *',  # Her saat başı
    func=sync_naics_721110,
    args=[30, 1000]  # days_back, limit
)
```

### Windows Task Scheduler
1. Task Scheduler'ı aç
2. "Create Basic Task"
3. Trigger: Hourly
4. Action: `python -m app.scripts.sync_opportunities`

## 🧪 Test Planı

### 1. Genel Arama
```bash
curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100"
```

**Beklenen**:
- `X-Cache`: MISS (ilk istek)
- `X-Source`: sam_live
- `X-Rate-Limit-Remaining`: 2
- `opportunities`: 100+ kayıt

### 2. Cache Hit
```bash
# Aynı isteği tekrar gönder
curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100"
```

**Beklenen**:
- `X-Cache`: HIT
- `X-Source`: cache
- Response: Cached data

### 3. Rate Limit
```bash
# Hızlı ardışık istekler
for i in {1..5}; do curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110"; done
```

**Beklenen**:
- İlk 3 istek: ✅
- 4. istek: 429 (Rate limit exceeded)

### 4. Circuit Breaker
```bash
# API key'i geçersiz yap (5 başarısız istek)
# Sonra normal istek
curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110"
```

**Beklenen**:
- İlk 5 istek: 500/429
- 6. istek: 503 (Circuit breaker OPEN)
- 60 saniye sonra: HALF_OPEN → test

### 5. DB Fallback
```bash
# Circuit breaker OPEN iken
curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110"
```

**Beklenen**:
- `X-Cache`: DB
- `X-Source`: db
- `X-Circuit-Breaker`: OPEN
- Response: DB'den gelen veriler

## 🔍 Debug Headers

Tüm proxy endpoint'leri şu header'ları döndürür:
- `X-Cache`: HIT/MISS/DB
- `X-Source`: sam_live/gsa_live/db/cache
- `X-Rate-Limit-Remaining`: Kalan token sayısı
- `X-Circuit-Breaker`: OPEN/CLOSED/HALF_OPEN
- `X-Fallback`: true (DB fallback kullanıldıysa)

## 📝 Notlar

1. **Redis Zorunlu Değil**: Redis yoksa rate limiting devre dışı, cache çalışmaz
2. **DB Fallback**: Circuit breaker OPEN iken DB'den veri döner
3. **Request Coalescing**: Aynı parametreli eşzamanlı istekler birleştirilir
4. **Background Save**: API sonuçları arka planda DB'ye kaydedilir
5. **TTL Dinamik**: Cache TTL, `days_back` parametresine göre ayarlanır

## 🚀 Sonraki Adımlar

1. **UI Entegrasyonu**: Streamlit uygulamasını proxy endpoint'lere yönlendir
2. **Monitoring**: Rate limit ve circuit breaker metrikleri
3. **Alerting**: Circuit breaker OPEN olduğunda bildirim
4. **Load Testing**: Rate limiting ve coalescing testleri

---

**Oluşturulma Tarihi**: 2025-02-15  
**Dosyalar**: 
- `mergen/api/app/services/redis_client.py`
- `mergen/api/app/services/circuit_breaker.py`
- `mergen/api/app/routes/proxy.py`
- `mergen/api/app/scripts/sync_opportunities.py`

