# 🧹 Cache Temizliği ve Test Rehberi

## ✅ Tamamlanan İşlemler

### 1. Cache Temizliği
- ✅ `.cache` klasörü temizlendi (SAMIntegration JSON cache)
- ✅ `__pycache__` klasörleri temizlendi
- ✅ Python cache temizliği yapıldı

### 2. Test Scripti
- ✅ `cache_cleanup_and_test.py` oluşturuldu
- ✅ Environment kontrolü eklendi
- ✅ Import testleri eklendi

## 🚀 Uygulamayı Başlatma

### API Başlatma
```bash
cd mergen/api
alembic upgrade head  # Migration gerekliyse
uvicorn app.main:app --reload
```

### Streamlit Başlatma
```bash
cd mergen
streamlit run mergenlite_unified.py
```

**Alternatif**:
```bash
streamlit run mergenlite_app.py
# veya
streamlit run app.py
```

## 🧪 Test Senaryoları

### Senaryo 1: Genel Arama (721110)
1. **Notice ID**: Boş bırakın
2. **NAICS**: `721110`
3. **Keyword**: Boş
4. **DaysBack**: `90` (60+ önerilir)
5. **Limit**: `100`
6. **"🔍 Fırsatları Ara"** → Sonuç sayısı artmalı

**Beklenen**:
- Limit=100 ile daha fazla sonuç
- Debug panelinde `effective_params` görünür
- `is_active=true` parametresi gönderiliyor
- Tarih filtresi aktif (days_back >= 60)

### Senaryo 2: Notice ID Arama
1. **Notice ID**: `W50S7526QA010` veya `70LGLY25QGLB00090`
2. **"🔍 Fırsatları Ara"** → İlan bulunmalı

**Alternatif URL Formatı**:
- Tam URL: `https://sam.gov/workspace/contract/opp/4af381a2c95d4e5e87b21a105a72af12/view`
- Sadece ID: `4af381a2c95d4e5e87b21a105a72af12`
- Notice ID: `70LGLY25QGLB00090`

### Senaryo 3: Debug Paneli
1. Arama yapın
2. Sonuçların altında **"🔎 Debug: Parametreleri ve sayıları göster"** expander'ını açın
3. JSON formatında görecekleriniz:
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

## 📊 Beklenen Sonuçlar

### Genel Arama (NAICS 721110)
- **Öncesi**: 2-5 sonuç (limit=50, cache'li)
- **Sonrası**: 50-100 sonuç (limit=100, cache temiz)

### Debug Paneli
- ✅ `effective_params` görünür
- ✅ `is_active: "true"` gönderiliyor
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

---

**Sonuç**: Cache temizliği tamamlandı! Uygulamayı başlatıp test edebilirsiniz. 🚀

