# 🧪 Proxy Endpoint Test Rehberi

## ✅ Sistem Başlatma

### 1. Redis
```powershell
docker-compose -f mergen/docker-compose.yml up -d redis
```

### 2. API
```powershell
cd mergen/api
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. UI (Yeni Terminal)
```powershell
cd mergen
streamlit run app.py
```

## 🔍 Proxy Sağlık Kontrolü

### API Docs
Aç: http://localhost:8000/docs

**Beklenen**: "proxy" tag'i altında 2 endpoint:
- `GET /api/proxy/opportunities/search`
- `GET /api/proxy/opportunities/noticedesc`

### Duman Testi

#### 1. Genel Arama
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

**Headers**:
- `X-Cache`: MISS (ilk istek) veya HIT (cache'den)
- `X-Source`: sam_live veya cache

#### 2. Notice Details
```bash
curl "http://localhost:8000/api/proxy/opportunities/noticedesc?id=70LGLY25QGLB00090"
```

**Beklenen Response**:
```json
{
  "success": true,
  "items": [...]
}
```

## 🎨 UI Doğrulama

### Genel Arama Testi
1. Streamlit uygulamasını aç: http://localhost:8501
2. **Fırsat Arama** sayfasına git
3. **Filtreler**:
   - Notice ID: **Boş bırak**
   - NAICS Kodu: **721110**
   - Son Günler: **30**
   - Sonuç Limiti: **100**

4. **"Fırsatları Getir"** butonuna tıkla

### Debug Panel Kontrolü
Debug panelini aç ve şunları kontrol et:

**effective_params**:
```json
{
  "ncode": "721110",
  "keyword": "721110",
  "keywordRadio": "ALL",
  "postedFrom": "01/15/2025",
  "postedTo": "02/15/2025",
  "is_active": "true",
  "limit": 1000,
  "offset": 0
}
```

**result_stats**:
```json
{
  "total_returned": 150,
  "by_source": {
    "sam_live": 150
  }
}
```

### Metrikler (app.py)
"Bulunan Fırsatlar" üstünde:
- **Toplam Sonuç**: 150+
- **DB'ye Kaydedilen**: 150
- **Son Senkron**: Şimdiki zaman

## 💾 DB Doğrulama

### PostgreSQL Bağlantısı
```bash
psql -U zgr -d zgrbid -h localhost
```

### Sorgular
```sql
-- Toplam kayıt sayısı
SELECT count(*) FROM opportunities;

-- Son 10 kayıt
SELECT notice_id, title, naics_code, posted_date, source 
FROM opportunities 
ORDER BY id DESC 
LIMIT 10;

-- NAICS 721110 kayıtları
SELECT count(*) 
FROM opportunities 
WHERE naics_code = '721110';

-- Son 30 gün içindeki kayıtlar
SELECT count(*) 
FROM opportunities 
WHERE posted_date >= NOW() - INTERVAL '30 days';
```

## ⚠️ Beklenen Davranış

### ✅ Başarılı Senaryo
1. **429 engeli kalktı**: Proxy araması sonuçları artırır (sayfalama + ncode + tarih)
2. **Proxy yanıtı**: `saved` alanıyla kaç kaydın DB'ye yazıldığını döner
3. **UI metrikler**: "DB'ye Kaydedilen" sayısını gösterir
4. **"Analizi Başlat"**: noticedesc'ten ekleri indirip analizi yürütür

### ❌ Sorun Tespiti

#### Sonuç sayısı düşükse (< 50)
- Debug panel'de `effective_params` kontrol et
- `ncode` ve `keyword` parametreleri gönderiliyor mu?
- `postedFrom` ve `postedTo` dolu mu?
- `is_active=true` var mı?

#### 429 hatası alıyorsanız
- Rate limiting çalışıyor (normal)
- Birkaç saniye bekleyip tekrar deneyin
- Redis çalışıyor mu? `docker ps | grep redis`

#### Circuit breaker OPEN
- 5 başarısız istek sonrası OPEN olur
- 60 saniye sonra HALF_OPEN'a geçer
- Başarılı isteklerle CLOSED'a döner

#### Cache HIT görmüyorsanız
- İlk istek: `X-Cache: MISS`
- İkinci istek: `X-Cache: HIT`
- Redis çalışıyor mu?

## 🔧 Debug Komutları

### Redis Kontrolü
```bash
docker exec -it mergen-redis-1 redis-cli
> KEYS *
> GET "search:naics=721110&days_back=30&limit=100&keyword="
```

### API Log Kontrolü
API terminalinde şunları görmelisiniz:
```
INFO: API Request (offset=0, limit=1000): {...}
INFO: 📊 Toplam kayıt: 150
INFO: ✅ 150 kayıt alındı (toplam: 150)
INFO: ✅ Toplam 150 fırsat bulundu
```

### Rate Limit Testi
```bash
# Hızlı ardışık istekler
for i in {1..5}; do 
  curl "http://localhost:8000/api/proxy/opportunities/search?naics=721110&limit=10"
  sleep 0.5
done
```

**Beklenen**: İlk 3 istek ✅, 4. istek 429

## 📊 Başarı Kriterleri

- [ ] Redis çalışıyor
- [ ] API başladı (http://localhost:8000/docs)
- [ ] Proxy endpoint'leri görünüyor
- [ ] Genel arama 100+ sonuç döndürüyor
- [ ] Debug panel'de doğru parametreler görünüyor
- [ ] DB'ye kayıtlar yazılıyor (`saved` > 0)
- [ ] Cache çalışıyor (ikinci istekte HIT)
- [ ] Rate limiting çalışıyor (429 testi)
- [ ] UI metrikleri doğru gösteriyor

---

**Test Tarihi**: 2025-02-15  
**Proxy Endpoints**: `/api/proxy/opportunities/search`, `/api/proxy/opportunities/noticedesc`

