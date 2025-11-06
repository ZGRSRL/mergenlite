# MergenLite Kod Temizliği Planı

## 🎯 Amaç

MergenLite için gereksiz FastAPI, eski ajan ve test dosyalarını kaldırarak projeyi sadeleştirmek.

## 📋 Kaldırılacak Dosyalar

### 1. FastAPI Sunucusu ve Route'lar

**Tamamen Kaldırılacak:**
- `mergen/api/app/main.py` - FastAPI ana uygulaması
- `mergen/api/app/routes/*` - Tüm API route'ları:
  - `mergen/api/app/routes/health.py`
  - `mergen/api/app/routes/ingest.py`
  - `mergen/api/app/routes/compliance.py`
  - `mergen/api/app/routes/pricing.py`
  - `mergen/api/app/routes/proposal.py`
  - `mergen/api/app/routes/search.py`
  - `mergen/api/app/routes/sam_gov.py`
- `mergen/api/app/db.py` - FastAPI database bağlantısı (Streamlit'te kullanılmayacak)
- `mergen/api/app/deps.py` - FastAPI dependencies
- `mergen/api/app/config.py` - FastAPI config (Streamlit için gerekli değil)
- `mergen/api/app/schemas.py` - FastAPI schemas (Pydantic modelleri)
- `mergen/api/app/models.py` - Eski SQLAlchemy modelleri (mergenlite_models.py kullanılacak)

**Not:** `mergen/api/app/services/` klasöründeki servisler korunabilir (document processing, LLM, vb.) ama Streamlit'te doğrudan kullanılmayacak.

### 2. Eski API Server (Flask)

- `mergen/sam/document_management/api_server.py` - Flask API sunucusu

### 3. Çıkarılan Ajanlara Ait Dosyalar

**Kaldırılacak (5 ajan):**
- `mergen/api/app/services/pricing/` - Pricing Specialist Agent
- `mergen/api/app/services/compliance/` - Compliance (yeni ComplianceAnalystAgent kullanılacak)
- Eski ajan dosyaları (eğer varsa):
  - `*hotel*agent*.py` - Smart Hotel Search Agent
  - `*location*agent*.py` - Smart Location Analyzer Agent
  - `*email*agent*.py` - Email Sender Agent
  - `*report*agent*.py` - PDF Report Generator Agent

**Korunacak:**
- `mergen/api/app/services/llm/` - LLM servisleri (RAG, prompts, router)
- `mergen/api/app/services/parsing/` - Document parsing servisleri
- `mergen/api/app/services/proposal/` - Proposal composer (ProposalWriterAgent tarafından kullanılabilir)

### 4. Test ve Yedek Dosyalar

**Kaldırılacak:**
- `test_*.py` - Tüm test dosyaları (root'ta)
- `*_backup.py` - Yedek dosyalar
- `simple_*.py` - Basitleştirilmiş test dosyaları
- `check_*.py` - Kontrol scriptleri (opsiyonel)
- `update_*.py` - Güncelleme scriptleri (opsiyonel)

**Korunacak:**
- `mergen/create_mergenlite_db.py` - Veritabanı kurulum scripti
- `mergen/create_mergenlite_schema.sql` - SQL şeması

### 5. Eski Streamlit Dosyaları

**Kaldırılacak:**
- `mergen/sam/document_management/app.py` - Eski MergenAI Streamlit uygulaması
- `mergen/sam/document_management/opportunity_analysis.py` - Eski analiz sayfası

**Korunacak:**
- `app.py` - Mevcut MergenAI Lite uygulaması (referans için)
- `mergenlite_app.py` - Yeni birleşik MergenLite uygulaması

## 🔄 Yapılacak Değişiklikler

### 1. Ana Uygulama Dosyası

- `mergenlite_app.py` - Yeni birleşik uygulama (✅ Oluşturuldu)
- `app.py` - Eski uygulama (referans için tutulabilir veya kaldırılabilir)

### 2. Veritabanı Bağlantısı

- Eski: FastAPI `get_db()` dependency
- Yeni: Streamlit içinde doğrudan SQLAlchemy bağlantısı (`get_db_session()`)

### 3. İş Mantığı

- Eski: FastAPI route'ları → Streamlit'te API çağrıları
- Yeni: Tüm iş mantığı Streamlit içinde, doğrudan fonksiyon çağrıları

## 📝 Temizlik Scripti

Aşağıdaki script ile temizlik yapılabilir:

```bash
# FastAPI dosyalarını kaldır
rm -rf mergen/api/app/routes/
rm -f mergen/api/app/main.py
rm -f mergen/api/app/db.py
rm -f mergen/api/app/deps.py
rm -f mergen/api/app/config.py
rm -f mergen/api/app/schemas.py
rm -f mergen/api/app/models.py

# Eski API server
rm -f mergen/sam/document_management/api_server.py

# Test dosyaları
rm -f test_*.py
rm -f *_backup.py
rm -f simple_*.py
rm -f check_*.py
rm -f update_*.py

# Eski Streamlit dosyaları
rm -f mergen/sam/document_management/app.py
rm -f mergen/sam/document_management/opportunity_analysis.py
```

## ⚠️ Dikkat Edilmesi Gerekenler

1. **Servis Dosyaları**: `mergen/api/app/services/` klasöründeki servisler korunabilir çünkü bazıları Streamlit'te kullanılabilir (document processing, LLM, vb.)

2. **Veritabanı Migration**: Eski veriler için migration gerekebilir (gelecekte eklenecek)

3. **Bağımlılıklar**: `requirements.txt`'den FastAPI ve Flask bağımlılıkları kaldırılabilir (opsiyonel)

## ✅ Temizlik Sonrası Durum

- ✅ Tek birleşik Streamlit uygulaması (`mergenlite_app.py`)
- ✅ 4 temel veritabanı tablosu
- ✅ 4-5 çekirdek ajan
- ✅ FastAPI bağımlılığı yok
- ✅ Minimal kod yapısı

