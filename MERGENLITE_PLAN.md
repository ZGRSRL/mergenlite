# MergenLite Sadeleştirme Planı

## 📋 Genel Bakış

MergenLite, MergenAI Platformu'nun sadeleştirilmiş versiyonudur. 10 ajanlı, 10+ tabloluk karmaşık yapıdan, 4-5 çekirdek ajan ve 4 temel tabloluk minimalist bir yapıya indirgenmiştir.

## 🎯 Sadeleştirme Hedefleri

1. **Ajan Mimarisi**: 10 ajan → 4-5 çekirdek ajan
2. **Veritabanı**: 10+ tablo → 4 temel tablo
3. **Arayüz**: Dual (Streamlit + FastAPI) → Sadece Streamlit
4. **Kod Yapısı**: Çoklu dosya → Tekleştirilmiş yapı

## 🤖 Sadeleştirilmiş Ajan Mimarisi

### ✅ Korunan Çekirdek Ajanlar (4-5)

| Ajan | Görev | Neden Korunmalı? |
|------|-------|-------------------|
| **Document Processor Agent** | Ham belgeleri işlemek ve metayı yapılandırmak | Temel veri girişini sağlar |
| **Requirements Extractor Agent** | Sözleşme gereksinimlerini çıkarmak ve kategorize etmek | Sistemin birincil değer önerisi |
| **Compliance Analyst Agent** | FAR uyumluluğunu kontrol etmek ve risk analizi yapmak | Yüksek değere sahip kritik uyumluluk denetimi |
| **Proposal Writer Agent** | Analiz sonuçlarından teklif özetini ve bölümlerini oluşturmak | Projenin çıktı odaklı ana amacını gerçekleştirir |
| **Quality Assurance Agent** (Opsiyonel) | Nihai teklif taslağını kontrol etmek | Kalite kontrol için kısa bir adım (~1-2 sn) |

### ❌ Çıkarılan Ajanlar

| Ajan | Neden Çıkarıldı? |
|------|------------------|
| **Pricing Specialist Agent** | Karmaşık matematiksel modelleme ve maliyet hesaplaması gerektirir, manuel bütçeleme ile değiştirilebilir |
| **Smart Location Analyzer Agent** | Konum analizi, temel gereksinim çıkarım ajanı içinde bir fonksiyon olarak birleştirilebilir |
| **Smart Hotel Search Agent** | Dış veritabanı/API bağımlılığı ve lojistik odaklıdır, çekirdek analizden çıkarılmalıdır |
| **PDF Report Generator Agent** | Raporlama, teklif yazarı çıktısından basit bir PDF kütüphanesi ile gerçekleştirilebilir |
| **Email Sender Agent** | Dış SMTP bağımlılığı vardır, manuel indirme ve e-posta ile gönderim ile değiştirilmelidir |

## 🗄️ Sadeleştirilmiş Veritabanı Şeması

### 4 Temel Tablo

1. **opportunities** - SAM.gov Fırsatları
   - `opportunity_id` (PK)
   - `title`, `notice_type`, `naics_code`
   - `response_deadline`, `estimated_value`
   - `raw_data` (JSONB) - SAM.gov API'den gelen ham veri

2. **manual_documents** - Manuel Yüklenen Dokümanlar
   - `document_id` (PK, UUID)
   - `opportunity_id` (FK)
   - `file_name`, `file_mime_type`, `storage_path`
   - `document_metadata` (JSONB)

3. **ai_analysis_results** - Konsolide AI Analiz Sonuçları
   - `analysis_id` (PK, UUID)
   - `opportunity_id` (FK)
   - `analysis_status`, `analysis_version`
   - `consolidated_output` (JSONB) - Tüm ajan çıktıları burada birleştirilir
   - `start_time`, `end_time`, `analysis_duration_seconds`

4. **system_sessions** - Hafif Kullanıcı ve Sistem İzleme
   - `session_id` (PK, UUID)
   - `session_start`, `user_identifier`
   - `analysis_count`
   - `metric_data` (JSONB)

### Birleştirilen Veriler

Aşağıdaki veriler `ai_analysis_results.consolidated_output` JSONB alanında tutulur:
- Requirements (eski `requirements` tablosu)
- Evidence (eski `evidence` tablosu)
- Facility Features (eski `facility_features` tablosu)
- Pricing Items (eski `pricing_items` tablosu)
- Past Performance (eski `past_performance` tablosu)
- Compliance Matrix
- Proposal Draft

## 🖥️ Arayüz Sadeleştirmesi

### Önceki Durum (MergenAI)
- **Dual Interface**: Streamlit + FastAPI
- **Çoklu Dosya**: `app.py`, `opportunity_analysis.py`, `dashboard.py`, vb.
- **API Server**: `api_server.py` (ayrı servis)

### Yeni Durum (MergenLite)
- **Tek Interface**: Sadece Streamlit
- **Tek Dosya**: Tüm sayfalar `app.py` içinde (Streamlit multi-page veya tabs)
- **İş Mantığı**: Streamlit içinde, veritabanı erişimi doğrudan

## 📁 Dosya Yapısı

### Oluşturulan Dosyalar

```
mergen/
├── create_mergenlite_schema.sql      # Veritabanı şeması (SQL)
├── create_mergenlite_db.py            # Veritabanı oluşturma scripti
├── mergenlite_agents.py               # Sadeleştirilmiş 4-5 ajan
└── mergenlite_models.py               # SQLAlchemy modelleri (4 tablo)

Mergenlite/ (root)
├── mergenlite_agents.py               # Ajanlar (root'ta da kopya)
└── mergenlite_models.py              # Modeller (root'ta da kopya)
```

### Temizlenecek Dosyalar

- `mergen/api/app/main.py` - FastAPI sunucusu (kaldırılacak)
- `mergen/api/app/routes/*` - API route'ları (kaldırılacak)
- `mergen/sam/document_management/api_server.py` - Eski API sunucusu (kaldırılacak)
- Test dosyaları: `test_*.py` (opsiyonel, temizlenebilir)
- Yedek dosyalar: `*_backup.py`, `simple_*.py` (temizlenebilir)

## 🔄 Migrasyon Planı

### Adım 1: Veritabanı Kurulumu ✅
```bash
cd mergen
python create_mergenlite_db.py
```

### Adım 2: Ajan Mimarisi Entegrasyonu
- `mergenlite_agents.py` dosyasını Streamlit uygulamasına entegre et
- Eski ajan dosyalarını referans olarak kullan, yeni sadeleştirilmiş versiyona geç

### Adım 3: Veritabanı Modelleri Entegrasyonu
- `mergenlite_models.py` modellerini kullan
- Eski modelleri (`mergen/api/app/models.py`) referans olarak tut, yeni yapıya geç

### Adım 4: Streamlit Uygulaması Güncelleme
- Tüm sayfaları tek `app.py` dosyasına birleştir
- FastAPI bağımlılıklarını kaldır
- Veritabanı erişimini doğrudan Streamlit içinde yap

### Adım 5: Kod Temizliği
- Kullanılmayan dosyaları kaldır
- Test dosyalarını temizle
- Yedek dosyaları kaldır

## 📊 Karşılaştırma

| Özellik | MergenAI | MergenLite | Azalma |
|---------|----------|------------|--------|
| Ajan Sayısı | 10 | 4-5 | ~50% ⬇️ |
| Veritabanı Tabloları | 10+ | 4 | ~60% ⬇️ |
| Arayüz | Dual (Streamlit + FastAPI) | Streamlit | %50 ⬇️ |
| Deployment Servisleri | 3 (Streamlit, FastAPI, DB) | 2 (Streamlit, DB) | %33 ⬇️ |
| Kod Karmaşıklığı | Yüksek | Düşük | ~40% ⬇️ |

## ✅ Tamamlanan İşler

- [x] MergenLite veritabanı şeması oluşturuldu (`create_mergenlite_schema.sql`)
- [x] Veritabanı oluşturma scripti hazırlandı (`create_mergenlite_db.py`)
- [x] Sadeleştirilmiş ajan mimarisi oluşturuldu (`mergenlite_agents.py`)
- [x] Veritabanı modelleri oluşturuldu (`mergenlite_models.py`)

## 🚧 Devam Eden İşler

- [ ] Veritabanı kurulumunu test et
- [ ] Ajan mimarisini Streamlit'e entegre et
- [ ] Streamlit uygulamasını tek dosyaya birleştir
- [ ] FastAPI bağımlılıklarını kaldır
- [ ] Kod temizliği yap

## 📝 Notlar

- **JSONB Kullanımı**: Tüm ajan çıktıları `ai_analysis_results.consolidated_output` JSONB alanında tutulur. Bu, esnek veri yapısı sağlar ve tablo sayısını azaltır.
- **Backward Compatibility**: Eski veriler için migration scripti gerekebilir (gelecekte eklenecek).
- **Performance**: JSONB index'leri ile sorgu performansı optimize edilebilir.

## 🔗 İlgili Dosyalar

- `mergen/create_mergenlite_schema.sql` - Veritabanı şeması
- `mergen/create_mergenlite_db.py` - Kurulum scripti
- `mergenlite_agents.py` - Sadeleştirilmiş ajanlar
- `mergenlite_models.py` - Veritabanı modelleri

