# ✅ Debug Paneli ve Limit Güncellemeleri

## 🎯 Yapılan Değişiklikler

### 1. **Limit Artırımı**

#### sam_integration.py
- ✅ Limit maksimum değeri: 50 → **100**
- ✅ `optimized_limit = min(limit, 100)` olarak güncellendi

#### mergen/mergenlite_unified.py
- ✅ Varsayılan limit: 50 → **100**
- ✅ `st.number_input` varsayılan değeri 100 olarak güncellendi

### 2. **is_active Parametresi**

#### sam_integration.py
- ✅ `is_active: 'true'` parametresi zaten mevcut (line 293)
- ✅ `isActive: 'true'` alternatif parametresi de eklendi (line 296)
- ✅ Web araması ile uyumlu: Sadece aktif ilanlar listeleniyor

### 3. **Debug Paneli**

#### mergen/mergenlite_unified.py
- ✅ Sonuçların altına debug paneli eklendi
- ✅ Gösterilen bilgiler:
  - **effective_params**: Kullanılan API parametreleri
    - `naicsCodes`: NAICS kodu
    - `keyword`: Keyword (NAICS keyword olarak da ekleniyor)
    - `keywordRadio`: "ALL" (tüm alanlarda ara)
    - `limit`: Sonuç limiti (100)
    - `is_active`: "true"
    - `sort`: "-modifiedDate"
    - `postedFrom/postedTo`: Tarih filtresi (days_back >= 60 ise)
  - **result_stats**: Sonuç istatistikleri
    - `total_returned`: Toplam dönen sonuç sayısı
    - `by_source`: Kaynak dağılımı (gsa_live, sam_live)

## 🧪 Test Senaryoları

### Senaryo 1: Genel Arama (NAICS 721110)
1. Notice ID alanını **boş bırakın**
2. NAICS: `721110`
3. Keyword: **boş**
4. DaysBack: `90` (60+ önerilir)
5. Limit: `100`
6. "🔍 Fırsatları Ara" butonuna tıklayın

**Beklenen**:
- Daha fazla sonuç (limit 100'e çıkarıldı)
- Debug panelinde:
  ```json
  {
    "effective_params": {
      "naicsCodes": "721110",
      "keyword": "721110",  // NAICS keyword olarak da eklendi
      "keywordRadio": "ALL",
      "limit": 100,
      "is_active": "true",
      "sort": "-modifiedDate",
      "postedFrom": "01/15/2024",
      "postedTo": "04/15/2024"
    },
    "result_stats": {
      "total_returned": 85,
      "by_source": {
        "sam_live": 85
      }
    }
  }
  ```

### Senaryo 2: 60+ Gün Tarih Filtresi
1. DaysBack: `90`
2. Debug panelinde `postedFrom` ve `postedTo` alanlarının dolu olduğunu görün

### Senaryo 3: 60'dan Küçük Gün
1. DaysBack: `30`
2. Debug panelinde `postedFrom` ve `postedTo` alanlarının **olmadığını** görün

## 📊 Parametre Mantığı

### Keyword Oluşturma
- **Kullanıcı keyword girdiyse**: `keyword = kullanıcı_keyword`
- **Kullanıcı keyword girmediyse**: `keyword = naics_code` (NAICS keyword olarak ekleniyor)
- **Her ikisi de varsa**: `keyword = kullanıcı_keyword` (NAICS keyword olarak eklenmez)

### Tarih Filtresi
- **days_back >= 60**: `postedFrom` ve `postedTo` parametreleri gönderilir
- **days_back < 60**: Tarih filtresi gönderilmez (web ile uyumlu)

## 🔍 Debug Paneli Kullanımı

1. Arama yapın
2. Sonuçların altında "🔎 Debug: Parametreleri ve sayıları göster" expander'ını açın
3. JSON formatında:
   - **effective_params**: API'ye gönderilen parametreler
   - **result_stats**: Sonuç istatistikleri

## ⚠️ Önemli Notlar

### Notice ID vs Genel Arama
- **Notice ID doluysa**: Genel arama akışı çalışmaz, direkt ID araması yapılır
- **Genel aramayı test etmek için**: Notice ID alanını **boş bırakın**

### API Sayfalama
- Limit=100 ilk sayfayı getirir
- Toplam sonuç >100 ise, sonuçlar yine sınırlı kalır
- **Sayfalama desteği** eklenebilir (offset/page parametreleri)

## 🚀 Sonraki Adımlar (Opsiyonel)

### Sayfalama Desteği
Eğer sonuç sayısı hâlâ düşükse, sayfalama eklenebilir:
- `offset` veya `page` parametresi
- Ardışık sayfaları çekip birleştirme
- Toplam sonuç sayısını gösterme

**Örnek**:
```python
# İlk sayfa
params = {'limit': 100, 'offset': 0}
# İkinci sayfa
params = {'limit': 100, 'offset': 100}
# ...
```

---

**Sonuç**: Debug paneli eklendi, limit 100'e çıkarıldı, `is_active` parametresi aktif. Test edip sonuçları kontrol edin! 🎯

