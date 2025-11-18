# 🚀 SAM.gov API Patch Özeti

## ✅ Yapılan Değişiklikler

### 1. Tarih Filtresi Zorunlu Hale Getirildi
- **Önceki**: Tarih filtresi sadece `days_back >= 60` ise gönderiliyordu
- **Yeni**: Tarih filtresi **her zaman** gönderiliyor (varsayılan: son 30 gün)
- **Format**: `MM/dd/YYYY` (SAM.gov API standardı)
- **Maksimum**: 1 yıl (365 gün)

```python
# Önceki
if days_back and days_back >= 60:
    params['postedFrom'] = ...

# Yeni
days_back = max(1, min(days_back or 30, 365))  # 1-365 gün arası
params['postedFrom'] = self._fmt_mmddyyyy(start_date)
params['postedTo'] = self._fmt_mmddyyyy(now_utc)
```

### 2. `ncode` Parametresi Eklendi
- **Public API uyumu**: `ncode=721110` parametresi eklendi
- **Geriye uyumluluk**: `naicsCodes` parametresi korundu
- **Web uyumu**: Her iki parametre de gönderiliyor

```python
params['ncode'] = naics_str      # Public API parametresi
params['naicsCodes'] = naics_str # Web iç arama uyumu (zararsız)
```

### 3. Sayfalama (Pagination) Desteği
- **Önceki**: Tek çağrıda maksimum 50-100 kayıt
- **Yeni**: Sayfalama ile **1000'e kadar** kayıt çekilebilir
- **Toplam limit**: 10,000 kayıt (sayfalama ile)
- **Sayfa boyutu**: 1000 kayıt/sayfa (SAM.gov API limiti)

```python
# Sayfalama döngüsü
while len(collected) < max_limit:
    params['limit'] = page_size  # 1000
    params['offset'] = offset
    
    # API çağrısı
    response = self.session.get(...)
    items = data.get("opportunitiesData", [])
    collected.extend(items)
    
    # Bitiş koşulları
    if len(collected) >= max_limit:
        break
    if len(items) < page_size:
        break  # Son sayfa
    
    offset += page_size
```

### 4. 429 Rate Limit Yönetimi
- **nextAccessTime** parse ediliyor
- Otomatik bekleme (en fazla 1 saat)
- Retry mekanizması ile devam ediyor

```python
def _sleep_until(self, next_access_time_str: str):
    """SAM 429 yanıtındaki nextAccessTime'a kadar bekler"""
    # Format: '2025-Nov-07 00:00:00+0000 UTC'
    dt = datetime.strptime(...).replace(tzinfo=timezone.utc)
    wait_s = max(0, int((dt - now).total_seconds()))
    time.sleep(min(wait_s, 3600))  # En fazla 1 saat
```

## 📋 API Parametreleri

### Genel Arama Parametreleri
```python
{
    'postedFrom': '01/15/2025',      # ZORUNLU (MM/dd/YYYY)
    'postedTo': '02/15/2025',        # ZORUNLU (MM/dd/YYYY)
    'ncode': '721110',               # Public API (yeni)
    'naicsCodes': '721110',          # Web uyumu (eski)
    'keyword': '721110 hotel',       # Keyword araması
    'keywordRadio': 'ALL',          # Tüm alanlarda ara
    'is_active': 'true',            # Aktif ilanlar
    'isActive': 'true',             # Alternatif format
    'limit': 1000,                  # Sayfa boyutu (max 1000)
    'offset': 0,                    # Sayfa offset
    'sort': '-modifiedDate',        # Sıralama
    'api_key': 'SAM-...'            # API anahtarı
}
```

## 🔧 .env Dosyası Formatı

**ÖNEMLİ**: `.env` dosyasında API anahtarı doğru formatta olmalı:

```bash
# mergen/.env
SAM_API_KEY=SAM-2cf274b1-5d51-4e4e-9622-4944b74f1e2c
```

**Yanlış formatlar**:
- `SAM-2cf274b1-5d51-4e4e-9622-4944b74f1e2c` (SAM_API_KEY= öneki yok)
- `SAM_API_KEY = SAM-...` (boşluk var)
- `SAM_API_KEY:SAM-...` (yanlış ayırıcı)

## 🧪 Test Komutları

### 1. Genel Arama Testi
```python
from sam_integration import SAMIntegration

sam = SAMIntegration()
results = sam.fetch_opportunities(
    naics_codes=['721110'],
    days_back=30,
    limit=1000,
    page_size=1000
)
print(f"✅ {len(results)} fırsat bulundu")
```

### 2. cURL Testi
```bash
curl -G "https://api.sam.gov/opportunities/v2/search" \
  --data-urlencode "api_key=$SAM_API_KEY" \
  --data-urlencode "postedFrom=01/15/2025" \
  --data-urlencode "postedTo=02/15/2025" \
  --data-urlencode "ncode=721110" \
  --data-urlencode "isActive=true" \
  --data-urlencode "limit=1000" \
  --data-urlencode "offset=0"
```

### 3. Debug Panel Kontrolü
Streamlit uygulamasında Debug Panel'de şunları görmelisiniz:
```json
{
  "effective_params": {
    "postedFrom": "01/15/2025",
    "postedTo": "02/15/2025",
    "ncode": "721110",
    "naicsCodes": "721110",
    "keyword": "721110",
    "keywordRadio": "ALL",
    "limit": 1000,
    "offset": 0,
    "is_active": "true"
  },
  "result_stats": {
    "total_returned": 150,
    "by_source": {
      "sam_live": 150
    }
  }
}
```

## 📊 Beklenen Sonuçlar

### Önceki Davranış
- Limit: 50-100 kayıt
- Tarih filtresi: Sadece `days_back >= 60` ise
- Sayfalama: Yok
- 429 hata: Hemen duruyordu

### Yeni Davranış
- Limit: 1000+ kayıt (sayfalama ile)
- Tarih filtresi: **Her zaman** (varsayılan: 30 gün)
- Sayfalama: Otomatik (offset döngüsü)
- 429 hata: `nextAccessTime`'a kadar bekleyip retry

## ⚠️ Önemli Notlar

1. **Tarih Filtresi Zorunlu**: Artık her aramada `postedFrom` ve `postedTo` gönderiliyor
2. **Sayfalama**: Büyük sonuç setleri için otomatik sayfalama yapılıyor
3. **Rate Limit**: 429 hatası alındığında `nextAccessTime`'a kadar bekleniyor
4. **ncode Parametresi**: Public API uyumu için eklendi, `naicsCodes` ile birlikte gönderiliyor
5. **Cache**: Sayfalama sonuçları cache'leniyor

## 🔍 Doğrulama Kontrol Listesi

- [ ] `postedFrom` ve `postedTo` her aramada gönderiliyor
- [ ] `ncode` parametresi eklendi
- [ ] Sayfalama çalışıyor (1000+ kayıt)
- [ ] 429 hatası durumunda `nextAccessTime` parse ediliyor
- [ ] Debug Panel'de doğru parametreler görünüyor
- [ ] Sonuç sayısı 50 barajını aşıyor
- [ ] `.env` dosyasında `SAM_API_KEY=...` formatı doğru

## 📝 Kullanım Örnekleri

### Örnek 1: 721110 + Aktif İlanlar + Son 30 Gün
```python
results = sam.fetch_opportunities(
    naics_codes=['721110'],
    days_back=30,
    limit=5000,
    page_size=1000
)
```

### Örnek 2: Combined Synopsis/Solicitation
```python
# ptype parametresi eklenebilir (gelecekte)
results = sam.fetch_opportunities(
    naics_codes=['721110'],
    days_back=30,
    limit=1000
)
```

### Örnek 3: WOSB Set-Aside
```python
# typeOfSetAside parametresi eklenebilir (gelecekte)
results = sam.fetch_opportunities(
    naics_codes=['721110'],
    days_back=30,
    limit=1000
)
```

## 🚀 Sonraki Adımlar

1. **Test**: Genel arama ile 1000+ kayıt çekmeyi test edin
2. **Doğrulama**: Debug Panel'de parametreleri kontrol edin
3. **Rate Limit**: 429 hatası durumunda bekleme süresini gözlemleyin
4. **Cache**: Cache temizliği yapıldıktan sonra test edin

---

**Patch Tarihi**: 2025-02-15  
**Dosya**: `sam_integration.py`  
**Fonksiyon**: `fetch_opportunities()`

