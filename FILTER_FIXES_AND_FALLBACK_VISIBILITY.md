# 🔧 Filtre Düzeltmeleri ve Fallback Görünürlüğü

## ✅ Tamamlanan Düzeltmeler

### 1. **Web ile Aynı Sorgu Gönderimi**

#### NAICS Filtresi - Çift Gönderim
- **Öncesi**: Sadece `naicsCodes=721110` gönderiliyordu
- **Sonrası**: Hem `naicsCodes=721110` hem `keyword=721110` gönderiliyor
- **Sonuç**: Web'deki geniş eşleşme ile uyum sağlandı

**Kod**: `sam_integration.py` lines 314-322, `gsa_opportunities_client.py` lines 213-220

```python
# NAICS kodu - Web ile uyum için hem keyword hem naicsCodes gönder
if naics_codes:
    naics_str = ','.join(naics_codes)
    params['naicsCodes'] = naics_str
    # Web'deki gibi keyword olarak da ekle (geniş eşleşme için)
    if not keywords:  # Eğer kullanıcı keyword girmediyse
        keyword_parts.append(naics_str)
```

### 2. **Tarih Filtresi Yumuşatıldı**

#### Şartlı Tarih Filtresi
- **Öncesi**: Her zaman tarih filtresi gönderiliyordu (1-7 gün çok dar)
- **Sonrası**: Sadece `days_back >= 60` ise tarih filtresi gönderiliyor
- **Varsayılan**: 90 gün (slider'da)
- **Sonuç**: Web ile uyum (web'de genellikle tarih filtresi yok)

**Kod**: `sam_integration.py` lines 294-300, `gsa_opportunities_client.py` lines 203-206

```python
# Tarih filtresi - sadece days_back >= 60 ise
if days_back and days_back >= 60:
    params['postedFrom'] = (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y')
    params['postedTo'] = datetime.now().strftime('%m/%d/%Y')
# days_back < 60 ise tarih filtresi gönderme (web ile uyumlu)
```

### 3. **Retry Mekanizması**

#### Exponential Backoff
- **GSA Client**: 2 retry denemesi
- **Backoff**: 2s, 4s (429 için), 1s, 2s (diğer hatalar için)
- **Sonuç**: Geçici hatalarda otomatik retry

**Kod**: `gsa_opportunities_client.py` lines 188-281

```python
max_retries = 2
for attempt in range(max_retries):
    # API çağrısı
    if response.status_code == 429:
        if attempt < max_retries - 1:
            wait_time = (2 ** attempt) * 2  # 2s, 4s
            time.sleep(wait_time)
            continue
```

### 4. **Source Etiketleri**

#### Canlı/Fallback Ayrımı
- **GSA Live**: `source: 'gsa_live'`
- **SAM Live**: `source: 'sam_live'`
- **Fallback**: `source: 'fallback'`
- **Sonuç**: Her sonuçta kaynak bilgisi var

**Kod**: 
- `sam_integration.py` lines 364-366
- `gsa_opportunities_client.py` lines 105-107, 237-239, 279-280

### 5. **UI Görünürlüğü**

#### Source Badge
- **Kartlarda**: Her kartın başlığında küçük badge
  - `GSA (canlı)` - Yeşil badge
  - `SAM.gov (canlı)` - Yeşil badge
  - `Fallback (demo)` - Mor badge

#### Source Mesajı
- **Alert**: "✅ 5 fırsat bulundu · Kaynak: 3 GSA (canlı) · 2 SAM.gov (canlı)"
- **Fallback Uyarısı**: "⚠️ Rate limit (429) → Fallback devreye girdi"

**Kod**: `mergen/mergenlite_unified.py` lines 515-536, 563-580

### 6. **Filtre İpuçları**

#### Kullanıcı Bilgilendirmesi
- **NAICS İpucu**: "💡 NAICS girildiğinde web ile uyum için hem naicsCodes hem keyword=NAICS uygulanır."
- **Tarih İpucu**: "Son Kaç Gün (60+ önerilir)" - Tooltip ile açıklama

**Kod**: `mergen/mergenlite_unified.py` lines 465-473

## 📊 Öncesi vs Sonrası

### Öncesi
- ❌ Sadece `naicsCodes` gönderiliyordu
- ❌ Her zaman tarih filtresi (1-7 gün çok dar)
- ❌ Fallback görünmüyordu
- ❌ Retry yoktu
- ❌ Source bilgisi yoktu

### Sonrası
- ✅ Hem `naicsCodes` hem `keyword=NAICS` gönderiliyor
- ✅ Tarih filtresi sadece 60+ gün ise
- ✅ Fallback badge ve uyarı ile görünür
- ✅ 2 retry denemesi (exponential backoff)
- ✅ Her sonuçta source etiketi

## 🧪 Test Senaryoları

### Test 1: NAICS Keyword Birlikte
```
NAICS: 721110
Keyword: (boş)
Beklenen: Hem naicsCodes=721110 hem keyword=721110 gönderilmeli
Sonuç: Daha fazla sonuç gelmeli (web ile uyumlu)
```

### Test 2: Tarih Filtresi Şartlı
```
Days Back: 7
Beklenen: Tarih filtresi gönderilmemeli
Sonuç: Web ile uyumlu, daha fazla sonuç

Days Back: 90
Beklenen: Tarih filtresi gönderilmeli
Sonuç: Son 90 gün içindeki ilanlar
```

### Test 3: Source Badge
```
Canlı API: "GSA (canlı)" veya "SAM.gov (canlı)" badge'i görünmeli
Fallback: "Fallback (demo)" badge'i görünmeli
Uyarı: Fallback kullanıldığında uyarı mesajı görünmeli
```

### Test 4: Retry Mekanizması
```
429 Hatası: 2s bekleyip tekrar denemeli
Başarısız: Fallback'e düşmeli
Log: "GSA API Request (attempt 1/2)" görünmeli
```

## 📋 Kontrol Listesi

- ✅ NAICS hem keyword hem naicsCodes olarak gönderiliyor
- ✅ Tarih filtresi sadece 60+ gün ise gönderiliyor
- ✅ Retry mekanizması eklendi (2 deneme)
- ✅ Source etiketleri eklendi (gsa_live, sam_live, fallback)
- ✅ UI'da source badge gösteriliyor
- ✅ Fallback uyarısı gösteriliyor
- ✅ Filtre ipuçları eklendi
- ✅ Log'larda "GSA LIVE / SAM LIVE" belirtiliyor

## 🚀 Beklenen Sonuçlar

1. **Daha Fazla Sonuç**: NAICS keyword olarak da gönderildiği için daha geniş eşleşme
2. **Web ile Uyum**: Aynı sorgu parametreleri ile web ile aynı sonuçlar
3. **Fallback Görünürlüğü**: Kullanıcı fallback mi canlı mı görebiliyor
4. **Daha İyi Hata Yönetimi**: Retry ile geçici hatalar otomatik çözülüyor
5. **Kullanıcı Bilgilendirmesi**: İpuçları ile daha iyi UX

---

**Not**: Tüm değişiklikler test edilmeli. Özellikle:
- NAICS=721110 ile arama yapıldığında daha fazla sonuç gelmeli
- Fallback kullanıldığında badge ve uyarı görünmeli
- Tarih filtresi 60'dan küçükse gönderilmemeli

