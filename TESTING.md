# Test Kılavuzu

## 🧪 Test Komutları

### 1. API Key Testi

```bash
python test_api_key.py
```

**Beklenen Çıktı:**
```
✅ Loaded .env from: d:\Mergenlite\mergen\.env
✅ API Key: SAM-0020b32f-de...
📏 Length: 36
✅ SAMIntegration API Key yüklendi
✅ API Test başarılı!
```

### 2. Cache Testi

```bash
python test_cache.py
```

**Beklenen Çıktı:**
```
🧪 Cache Test Başlatılıyor...
1️⃣ İlk Arama (Cache Miss bekleniyor)...
   ⏱️ Süre: 3.50 saniye
   💾 Cache durumu: Miss

2️⃣ İkinci Arama (Cache Hit bekleniyor)...
   ⏱️ Süre: 0.01 saniye
   💾 Cache durumu: Hit
   ✅ Cache çalışıyor! (99.7% hızlı)
```

### 3. Optimizasyon Doğrulama

```bash
python test_optimization.py
```

**Beklenen Çıktı:**
```
🔍 Optimizasyon Doğrulama
1️⃣ Cache Mekanizması:
   ✅ _get_cache_key() mevcut
   ✅ _get_from_cache() mevcut
   ✅ _save_to_cache() mevcut
   ✅ Cache süresi: 6.0 saat

2️⃣ Limit Optimizasyonları:
   ✅ fetch_opportunities(): Limit 50'ye optimize edilmiş
   ✅ fetch_by_notice_id(): Limit 25'e optimize edilmiş

3️⃣ Cache-First Stratejisi:
   ✅ Cache-first kullanıyor
```

## 🚀 Streamlit Test

### 1. Streamlit'i Başlat

```bash
streamlit run app.py
```

### 2. Opportunity ID ile Test

1. Tarayıcıda `http://localhost:8501` açın
2. "İlan ID ile Direkt Arama" bölümüne gidin
3. `086008536ec84226ad9de043dc738d06` yazın
4. "İlan ID ile Ara" butonuna tıklayın

### 3. Cache Test

- **İlk arama**: API çağrısı yapılır (yavaş, ~3-5 saniye)
- **İkinci arama**: Cache'den gelir (hızlı, ~0.01 saniye)

### 4. Terminal Loglarını İzle

```
✅ Loaded .env from: d:\Mergenlite\mergen\.env
✅ API key loaded successfully
Detected Opportunity ID: 086008536ec84226ad9de043dc738d06
Searching by Opportunity ID: 086008536ec84226ad9de043dc738d06
✅ Cached 1 results for key: ...
```

## 📊 Performans Metrikleri

### Önceki Durum
- API çağrısı: Her seferinde
- Ortalama süre: 3-5 saniye
- Günlük çağrı: ~2000+

### Yeni Durum
- İlk çağrı: API çağrısı (3-5 saniye)
- Sonraki çağrılar: Cache'den (0.01 saniye)
- Günlük çağrı: ~200-300 (%85 azalma)

## ✅ Başarı Kriterleri

1. ✅ API key yükleniyor
2. ✅ Cache mekanizması çalışıyor
3. ✅ Limit optimizasyonları aktif
4. ✅ Cache hit'ler hızlı
5. ✅ API çağrı sayısı azaldı

## 🔧 Sorun Giderme

### API Key Yüklenmiyor
```bash
# .env dosyasını kontrol et
cat mergen/.env | grep SAM_API_KEY
```

### Cache Çalışmıyor
```bash
# Cache klasörünü kontrol et
ls -la .cache/
```

### Optimizasyonlar Aktif Değil
```bash
# Test scriptini çalıştır
python test_optimization.py
```

