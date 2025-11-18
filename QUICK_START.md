# 🚀 Hızlı Başlatma Rehberi

## ✅ Tamamlanan Adımlar

1. ✅ **Redis başlatıldı**: `mergen-redis-1` çalışıyor
2. ✅ **Cache temizlendi**: `.cache` ve `__pycache__` silindi
3. ✅ **Proxy endpoints hazır**: `/api/proxy/opportunities/search` ve `/noticedesc`

## 📋 Manuel Başlatma Komutları

### 1. API Başlat (Yeni Terminal)
```powershell
cd d:\Mergenlite\mergen\api
uvicorn app.main:app --reload
```

**Beklenen**: 
- API çalışıyor: http://localhost:8000
- Docs: http://localhost:8000/docs
- Proxy endpoints görünüyor

### 2. UI Başlat (Yeni Terminal)
```powershell
cd d:\Mergenlite\mergen
streamlit run app.py
```

**Beklenen**: 
- UI çalışıyor: http://localhost:8501
- "Fırsat Arama" sayfası açılıyor

## 🧪 Hızlı Test

### Proxy Search Test
```powershell
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

**Headers Kontrolü**:
- `X-Cache`: MISS (ilk istek) veya HIT (cache'den)
- `X-Source`: sam_live veya cache

### Proxy Notice Details Test
```powershell
curl "http://localhost:8000/api/proxy/opportunities/noticedesc?id=70LGLY25QGLB00090"
```

## 🎯 UI Doğrulama Adımları

1. **Streamlit uygulamasını aç**: http://localhost:8501
2. **"Fırsat Arama"** sayfasına git
3. **Filtreler**:
   - Notice ID: **Boş**
   - NAICS: **721110**
   - Son Günler: **30**
   - Limit: **100**
4. **"Fırsatları Getir"** butonuna tıkla
5. **Debug panelini aç** ve kontrol et:
   - `ncode=721110` ✅
   - `keyword=721110` ✅
   - `postedFrom` ve `postedTo` dolu ✅
   - `is_active=true` ✅
6. **Sonuç sayısı**: 100+ olmalı ✅

## 📊 Beklenen Sonuçlar

### ✅ Başarılı Senaryo
- **Toplam Sonuç**: 100-1000+ (sayfalama ile)
- **DB'ye Kaydedilen**: `saved` > 0
- **Cache**: İkinci istekte `X-Cache: HIT`
- **Rate Limiting**: İlk 3 istek ✅, 4. istek 429

### ⚠️ Sorun Tespiti

#### Sonuç sayısı düşükse (< 50)
- Debug panel'de `effective_params` kontrol et
- `ncode` ve `keyword` gönderiliyor mu?
- `postedFrom/postedTo` dolu mu?

#### 429 hatası
- Normal (rate limiting çalışıyor)
- Birkaç saniye bekleyip tekrar deneyin

#### Circuit breaker OPEN
- 5 başarısız istek sonrası OPEN
- 60 saniye sonra HALF_OPEN
- Başarılı isteklerle CLOSED

## 🔧 Debug Komutları

### Redis Kontrolü
```powershell
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
```

## 📝 Notlar

- **Alembic hatası**: Config dosyasında `%` karakteri sorunu var, şimdilik atlanabilir
- **Redis**: Zaten çalışıyor (`mergen-redis-1`)
- **Proxy endpoints**: `/api/proxy/opportunities/search` ve `/noticedesc` hazır
- **Cache**: Redis yoksa in-memory fallback çalışır

---

**Hazır!** API ve UI'yi başlatıp test edebilirsiniz. 🚀

