# ✅ Test Kontrol Listesi

## 🧹 Cache Temizliği (Tamamlandı)

- ✅ `.cache` klasörü temizlendi
- ✅ `__pycache__` klasörleri temizlendi
- ✅ Python cache temizliği yapıldı

## 🚀 Uygulamayı Başlatma

### 1. API Başlatma
```bash
cd mergen/api
alembic upgrade head  # Migration gerekliyse
uvicorn app.main:app --reload
```

### 2. Streamlit Başlatma
```bash
cd mergen
streamlit run mergenlite_unified.py
```

## 🧪 Test Senaryoları

### ✅ Senaryo 1: Genel Arama (721110)

**Adımlar**:
1. Notice ID alanını **boş bırakın**
2. NAICS: `721110`
3. Keyword: **boş**
4. DaysBack: `90` (60+ önerilir)
5. Limit: `100`
6. "🔍 Fırsatları Ara" butonuna tıklayın

**Beklenen Sonuçlar**:
- ✅ Daha fazla sonuç (limit=100)
- ✅ Debug panelinde `effective_params` görünür:
  - `naicsCodes: "721110"`
  - `keyword: "721110"` (NAICS keyword olarak)
  - `keywordRadio: "ALL"`
  - `limit: 100`
  - `is_active: "true"`
  - `postedFrom/postedTo` (days_back >= 60 ise)
- ✅ `result_stats.by_source` dolu (sam_live veya gsa_live)

**Kontrol Listesi**:
- [ ] Sonuç sayısı > 50
- [ ] Debug panelinde parametreler görünür
- [ ] `is_active: "true"` gönderiliyor
- [ ] Tarih filtresi aktif (days_back >= 60)

### ✅ Senaryo 2: Notice ID Arama

**Test ID'leri**:
- `W50S7526QA010`
- `70LGLY25QGLB00090`
- `4af381a2c95d4e5e87b21a105a72af12` (32-hex opportunity ID)

**URL Formatı** (otomatik parse):
- Tam URL: `https://sam.gov/workspace/contract/opp/4af381a2c95d4e5e87b21a105a72af12/view`
- Sadece ID: `4af381a2c95d4e5e87b21a105a72af12`

**Beklenen Sonuçlar**:
- ✅ İlan bulunur
- ✅ Detaylar gösterilir
- ✅ Attachment'lar listelenir

**Kontrol Listesi**:
- [ ] Notice ID araması çalışıyor
- [ ] URL'den ID çıkarılıyor
- [ ] 32-hex ID'ler destekleniyor

### ✅ Senaryo 3: Debug Paneli

**Adımlar**:
1. Arama yapın
2. Sonuçların altında **"🔎 Debug: Parametreleri ve sayıları göster"** expander'ını açın

**Beklenen JSON**:
```json
{
  "effective_params": {
    "naicsCodes": "721110",
    "keyword": "721110",
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

**Kontrol Listesi**:
- [ ] Debug paneli görünür
- [ ] `effective_params` doğru
- [ ] `result_stats` dolu
- [ ] `by_source` bilgisi var

### ✅ Senaryo 4: Modern UI Bileşenleri

**Kontrol Listesi**:
- [ ] Modern tema aktif (dark theme)
- [ ] Opportunity kartları gelişmiş görünüm
- [ ] NAICS badge görünür
- [ ] Stepper ile aşama gösterimi
- [ ] Sekmeli görünüm seçeneği
- [ ] Hover efektleri çalışıyor

## 🔍 Sorun Giderme

### Sonuç Bulunamıyorsa

1. **API Key Kontrolü**:
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', os.getenv('SAM_API_KEY', 'YOK')[:20])"
   ```

2. **Cache Temizliği** (tekrar):
   ```bash
   python cache_cleanup_and_test.py
   ```

3. **Debug Paneli Çıktısı**:
   - Debug panelindeki `effective_params` değerlerini kontrol edin
   - `result_stats.by_source` boş mu?
   - `total_returned: 0` mu?

4. **API Limit Kontrolü**:
   - SAM.gov API quota limiti aşılmış olabilir
   - GSA Opportunities API otomatik devreye girer

### URL/ID Bulunamıyorsa

- İlan public/aktif olmayabilir
- SAM UI'de var ama public API'da görünmeyebilir
- `get_opportunity_details` fonksiyonu sırayla dener:
  1. `noticeId`
  2. `solicitationNumber`
  3. `opportunityId` (32-hex ise)
  4. `oppId` (32-hex ise)

## 📊 Beklenen İyileştirmeler

### Genel Arama (NAICS 721110)
- **Öncesi**: 2-5 sonuç (limit=50, cache'li)
- **Sonrası**: 50-100 sonuç (limit=100, cache temiz)

### Parametreler
- ✅ `is_active: "true"` eklendi
- ✅ `keyword: "721110"` (NAICS keyword olarak)
- ✅ `naicsCodes: "721110"`
- ✅ Tarih filtresi (days_back >= 60)

## 🎯 Başarı Kriterleri

- ✅ Cache temizlendi
- ✅ API key yüklendi
- ✅ Genel aramada daha fazla sonuç
- ✅ Debug panelinde parametreler görünür
- ✅ Notice ID araması çalışıyor
- ✅ Modern UI bileşenleri aktif
- ✅ Limit=100 ile daha fazla sonuç

---

**Sonraki Adım**: Uygulamayı başlatıp test edin! 🚀

