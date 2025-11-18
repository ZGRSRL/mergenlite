# Backend → Opportunities + Attachments Implementation Report

**Tarih:** 2025-01-XX  
**Kapsam:** FAZ 1-3 Tamamlandı (DB Şeması, SAM Sync, Attachment Download)

---

## 📋 Özet

Bu implementasyon, SAM.gov entegrasyonunu merkezileştirerek React frontend ve FastAPI backend arasında unified bir veri modeli oluşturdu. Tüm SAM API çağrıları artık backend üzerinden yapılıyor ve attachment'lar otomatik olarak indirilip saklanıyor.

---

## ✅ Tamamlanan Görevler

### FAZ 1: DB Şeması & Python Modeller

#### 1.1 Unified Opportunity Model ✅

**Dosya:** `mergen/api/app/models.py`

**Değişiklikler:**
- `Opportunity` modeli unified schema'ya güncellendi
- Primary key: `id` (Integer, auto-increment)
- SAM identifiers: `opportunity_id`, `notice_id`, `solicitation_number`
- Tarih alanları: `posted_date`, `response_deadline` (DateTime with timezone)
- Classification: `naics_code`, `psc_code`, `classification_code`, `set_aside`, `contract_type`
- Organization: `agency`, `office`, `organization_type`, `point_of_contact`
- Data storage: `raw_data` (JSONB), `cached_data` (JSONB)
- Status: `status` (default: 'active')
- Relationships: `attachments` (one-to-many with OpportunityAttachment)

**Backward Compatibility:**
- `@property raw_json` → `raw_data` alias
- `@property analyzed` → `cached_data`'dan computed
- `@property source` → `raw_data`'dan extract
- `@property organization` → `raw_data`'dan extract

#### 1.2 OpportunityAttachment Model ✅

**Dosya:** `mergen/api/app/models.py`

**Yeni Model:**
```python
class OpportunityAttachment(Base):
    __tablename__ = "opportunity_attachments"
    
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="CASCADE"))
    name = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    attachment_type = Column(String(50), default='document')
    mime_type = Column(String(255))
    size_bytes = Column(Integer)
    local_path = Column(Text)  # Downloaded file path
    downloaded = Column(Boolean, default=False)
    storage_path = Column(Text)  # S3 path (future)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True))
    downloaded_at = Column(DateTime(timezone=True))
```

**Özellikler:**
- Foreign key cascade delete (opportunity silinince attachments da silinir)
- Download tracking (`downloaded`, `downloaded_at`)
- MIME type ve file size tracking
- Metadata JSON field (SAM'dan gelen ek bilgiler)

#### 1.3 Pydantic Schemas ✅

**Dosya:** `mergen/api/app/schemas.py` (YENİ)

**Oluşturulan Schemas:**

1. **OpportunityBase**: Temel alanlar (notice_id, title, dates, agency, etc.)
2. **OpportunityCreate**: Create için (raw_data, cached_data dahil)
3. **OpportunityRead**: Read için (id, timestamps dahil, `from_attributes=True`)
4. **OpportunityAttachmentBase**: Attachment temel alanları
5. **OpportunityAttachmentCreate**: Attachment create
6. **OpportunityAttachmentRead**: Attachment read
7. **OpportunityWithAttachments**: Opportunity + attachments listesi
8. **SamSyncRequest**: Sync endpoint request body
9. **SyncResponse**: Sync endpoint response

**Özellikler:**
- Pydantic v2 uyumlu (`from_attributes=True` instead of `orm_mode=True`)
- Optional fields için proper typing
- DateTime serialization otomatik

---

### FAZ 2: SAM Sync Servisi (Merkezî Sync)

#### 2.1 SAM Service Katmanı ✅

**Dosya:** `mergen/api/app/services/sam_service.py` (YENİ)

**Fonksiyonlar:**
- `fetch_opportunities_from_sam(params: Dict) -> List[Dict]`
  - Mevcut `SAMIntegration` sınıfını wrapper olarak kullanır
  - `.env` dosyasını `mergen/.env`'den yükler
  - Rate limiting ve quota handling mevcut `SAMIntegration` içinde

**Özellikler:**
- Async/await desteği
- Error handling ve logging
- API key validation

#### 2.2 SAM Mapper Helper ✅

**Dosya:** `mergen/api/app/services/sam_mapper.py` (YENİ)

**Fonksiyonlar:**

1. **`map_sam_record_to_opportunity(record: Dict) -> Dict`**
   - SAM.gov raw kaydını Opportunity model formatına çevirir
   - Tarih parsing (ISO format, multiple fallbacks)
   - `cached_data` oluşturma (sık kullanılan alanlar)
   - `opportunity_id='N/A'` handling (notice_id'ye fallback)

2. **`extract_attachments_from_sam_record(record: Dict, opportunity_id: int) -> List[Dict]`**
   - `resourceLinks` array'inden attachment'ları çıkarır
   - `attachments` field'ından attachment'ları çıkarır
   - Her attachment için `OpportunityAttachmentCreate` formatında dict döner
   - Metadata tracking (source, index)

**Özellikler:**
- Robust date parsing (multiple formats)
- Safe string handling (None checks)
- Metadata preservation

#### 2.3 CRUD Fonksiyonları ✅

**Dosya:** `mergen/api/app/crud/opportunities.py` (YENİ)

**Fonksiyonlar:**

1. **`upsert_opportunity(db, data) -> Opportunity`**
   - `notice_id` üzerinden lookup
   - Fallback: `opportunity_id` üzerinden lookup
   - Varsa update, yoksa create
   - Transaction handling (commit/rollback)

2. **`get_opportunity(db, opportunity_id: int) -> Opportunity`**
   - Database ID ile lookup

3. **`get_opportunity_by_notice_id(db, notice_id: str) -> Opportunity`**
   - Notice ID ile lookup

4. **`list_opportunities(db, skip, limit, filters) -> List[Opportunity]`**
   - Pagination (skip/limit)
   - Filters: `naics_code`, `keyword`, `date_from`, `date_to`
   - Ordering: `posted_date DESC NULLS LAST`

5. **`create_attachment(db, attachment_data) -> OpportunityAttachment`**
   - Yeni attachment kaydı oluşturur

6. **`get_attachments_for_opportunity(db, opportunity_id: int) -> List[OpportunityAttachment]`**
   - Bir opportunity'nin tüm attachment'larını getirir

**Özellikler:**
- Comprehensive error handling
- Logging
- Transaction safety

#### 2.4 Sync Servisi ✅

**Dosya:** `mergen/api/app/services/opportunity_sync_service.py` (YENİ)

**Fonksiyon:**
- **`sync_from_sam(db, params) -> Dict`**
  - SAM'dan fırsatları çeker (`sam_service.fetch_opportunities_from_sam`)
  - Her kaydı map eder (`sam_mapper.map_sam_record_to_opportunity`)
  - Database'e upsert eder (`crud.upsert_opportunity`)
  - Attachment'ları extract eder (`sam_mapper.extract_attachments_from_sam_record`)
  - Attachment'ları database'e kaydeder (`crud.create_attachment`)
  - Duplicate kontrolü (source_url üzerinden)

**Return Value:**
```python
{
    "count_new": int,
    "count_updated": int,
    "total_processed": int,
    "count_attachments": int
}
```

**Özellikler:**
- Batch processing
- Error resilience (bir kayıt hata verse bile devam eder)
- Attachment deduplication
- Comprehensive logging

#### 2.5 /api/opportunities/sync Endpoint ✅

**Dosya:** `mergen/api/app/routes/opportunities.py`

**Endpoint:** `POST /api/opportunities/sync`

**Query Parameters:**
- `naics` (default: "721110")
- `days_back` (default: 30, min: 1, max: 365)
- `limit` (default: 1000, min: 1, max: 10000)
- `keyword` (optional)

**Response:**
```json
{
    "success": true,
    "count_new": 19,
    "count_updated": 12,
    "total_processed": 31,
    "count_attachments": 45
}
```

**Değişiklikler:**
- Eski GSA/SAM direct integration kodu kaldırıldı (commented out)
- Yeni centralized `sync_from_sam` servisi kullanılıyor
- Error handling iyileştirildi
- SAM_API_KEY validation mesajları eklendi

#### 2.6 /api/opportunities List & Detail Endpoints ✅

**Dosya:** `mergen/api/app/routes/opportunities.py`

**1. GET /api/opportunities** (List)
- **Response Model:** `List[OpportunityRead]`
- **Query Parameters:**
  - `notice_id` (optional, filter)
  - `naics_code` (optional, filter)
  - `keyword` (optional, search in title/description)
  - `page` (default: 1, min: 1)
  - `page_size` (default: 20, min: 1, max: 100)
- **Değişiklikler:**
  - Eski manual formatting kodu kaldırıldı
  - Pydantic `response_model` kullanılıyor (otomatik serialization)
  - CRUD `list_opportunities` fonksiyonu kullanılıyor
  - Pagination: `page`/`page_size` (eski `offset`/`limit` yerine)

**2. GET /api/opportunities/{opportunity_id}** (Detail)
- **Response Model:** `OpportunityWithAttachments`
- **Path Parameter:** `opportunity_id` (database ID, int)
- **Response:** Opportunity + attachments listesi (relationship'ten otomatik)

**3. GET /api/opportunities/{opportunity_id}/attachments**
- **Response Model:** `List[OpportunityAttachmentRead]`
- **Path Parameter:** `opportunity_id` (database ID, int)
- **Response:** Sadece attachments listesi

**Değişiklikler:**
- Tüm endpoint'ler Pydantic response models kullanıyor
- Manual JSON formatting kaldırıldı
- CRUD fonksiyonları kullanılıyor
- Error handling standardize edildi

---

### FAZ 3: Attachment Download Servisi

#### 3.1 Attachment Download Service ✅

**Dosya:** `mergen/api/app/services/attachment_service.py` (YENİ)

**Fonksiyon:**
- **`download_attachments_for_opportunity(db, opportunity_id: int) -> int`**

**Akış:**
1. Opportunity'yi database'den çeker
2. `data/opportunities/{notice_id}/attachments/` dizinini oluşturur
3. `downloaded=False` olan attachment'ları filtreler
4. Her attachment için:
   - `httpx.AsyncClient` ile indirir (120s timeout)
   - Safe filename oluşturur (path injection koruması)
   - MIME type'dan extension tahmin eder (gerekirse)
   - Dosyayı disk'e yazar
   - Database record'u günceller (`local_path`, `downloaded`, `size_bytes`, `downloaded_at`)
   - MIME type'ı response header'dan alır (gerekirse)

**Özellikler:**
- Async download (httpx)
- Duplicate check (zaten varsa skip)
- Error resilience (bir dosya hata verse bile devam eder)
- File size tracking
- MIME type detection
- Comprehensive logging

#### 3.2 POST /api/opportunities/{id}/download-attachments Endpoint ✅

**Dosya:** `mergen/api/app/routes/opportunities.py`

**Endpoint:** `POST /api/opportunities/{opportunity_id}/download-attachments`

**Path Parameter:** `opportunity_id` (database ID, int)

**Response:**
```json
{
    "success": true,
    "downloaded": 5,
    "message": "Downloaded 5 attachment(s)"
}
```

**Error Handling:**
- 404: Opportunity not found
- 500: Download error (detaylı mesaj)

---

## 📁 Yeni Dosya Yapısı

```
mergen/api/app/
├── schemas.py                          # YENİ - Pydantic schemas
├── models.py                           # GÜNCELLENDİ - Unified Opportunity + Attachment models
├── crud/
│   ├── __init__.py                     # YENİ
│   └── opportunities.py                # YENİ - CRUD operations
├── services/
│   ├── __init__.py                     # YENİ
│   ├── sam_service.py                  # YENİ - SAM API wrapper
│   ├── sam_mapper.py                   # YENİ - SAM → Opportunity mapper
│   ├── opportunity_sync_service.py     # YENİ - Sync business logic
│   └── attachment_service.py           # YENİ - Download service
└── routes/
    └── opportunities.py                # GÜNCELLENDİ - Yeni endpoints + sync service
```

---

## 🔄 Değişiklik Özeti

### Eski Yapı → Yeni Yapı

**ÖNCE:**
- SAM API çağrıları Streamlit ve FastAPI'de dağınık
- Manual JSON formatting
- Attachment'lar sadece `raw_data` içinde, ayrı tablo yok
- `opportunity_id='N/A'` unique constraint hataları
- Inconsistent error handling

**SONRA:**
- ✅ Tüm SAM çağrıları backend'de merkezileştirildi
- ✅ Pydantic schemas ile otomatik serialization
- ✅ `opportunity_attachments` tablosu eklendi
- ✅ `opportunity_id='N/A'` → `notice_id` fallback
- ✅ Standardized error handling ve logging
- ✅ Attachment download servisi
- ✅ Static file serving (`/files` mount)

---

## 🎯 API Endpoints Özeti

### Opportunities

| Method | Endpoint | Açıklama | Response Model |
|--------|----------|----------|----------------|
| GET | `/api/opportunities` | List opportunities (pagination + filters) | `List[OpportunityRead]` |
| GET | `/api/opportunities/{id}` | Get opportunity with attachments | `OpportunityWithAttachments` |
| GET | `/api/opportunities/{id}/attachments` | Get attachments only | `List[OpportunityAttachmentRead]` |
| POST | `/api/opportunities/sync` | Sync from SAM.gov | `SyncResponse` |
| POST | `/api/opportunities/{id}/download-attachments` | Download attachments | `{"success": bool, "downloaded": int}` |

---

## 🔧 Teknik Detaylar

### Database Schema

**opportunities tablosu:**
- Primary key: `id` (SERIAL)
- Unique index: `notice_id` (nullable, but indexed)
- Indexes: `opportunity_id`, `posted_date`, `naics_code`
- JSONB fields: `raw_data`, `cached_data`

**opportunity_attachments tablosu:**
- Primary key: `id` (SERIAL)
- Foreign key: `opportunity_id` → `opportunities.id` (CASCADE DELETE)
- Index: `opportunity_id`
- Fields: `name`, `source_url`, `local_path`, `mime_type`, `size_bytes`, `downloaded`, `metadata`

### File System Structure

```
data/
└── opportunities/
    └── {notice_id}/
        └── attachments/
            ├── file1.pdf
            ├── file2.docx
            └── ...
```

**Static Files:**
- FastAPI `StaticFiles` mount: `/files` → `data/` directory
- Access: `http://localhost:8000/files/opportunities/{notice_id}/attachments/file1.pdf`

### Error Handling

- **Database errors:** Rollback + detailed logging
- **API errors:** HTTPException with descriptive messages
- **File errors:** Continue with next file, log error
- **Validation errors:** Pydantic automatic validation

### Logging

- Structured logging with `logging.getLogger(__name__)`
- Info level: Normal operations
- Warning level: Recoverable errors
- Error level: Critical errors with `exc_info=True`

---

## 🚀 Sonraki Adımlar (TODO)

### Migration
- [ ] Alembic migration oluştur (opportunity_attachments tablosu)
- [ ] Mevcut `opportunities` tablosunu unified schema'ya migrate et
- [ ] `raw_json` → `raw_data` rename (gerekirse)

### Testing
- [ ] Unit tests: CRUD operations
- [ ] Unit tests: SAM mapper
- [ ] Integration tests: Sync endpoint
- [ ] Integration tests: Download endpoint
- [ ] E2E test: Full sync → download → pipeline flow

### Frontend Integration
- [ ] React `OpportunityCenter` → yeni endpoint'lere bağla
- [ ] Attachment listesi göster
- [ ] Download button → `/api/opportunities/{id}/download-attachments`
- [ ] Sync button → `/api/opportunities/sync`

### Pipeline Integration
- [ ] Pipeline'ın `local_path`'leri kullanması
- [ ] Attachment'ları pipeline'a input olarak geçirme

---

## 📝 Notlar

1. **Backward Compatibility:** Mevcut `Opportunity` modeli backward compatible (property'ler sayesinde). Eski kod çalışmaya devam eder.

2. **Migration Strategy:** Mevcut `opportunities` tablosu zaten `raw_data` kolonuna sahip. Sadece `opportunity_attachments` tablosunu eklemek yeterli.

3. **Performance:** 
   - Sync işlemi batch processing yapıyor (tek tek commit yerine)
   - Attachment download async (paralel indirme mümkün, şu an sequential)
   - Pagination ile list endpoint optimize

4. **Security:**
   - Filename sanitization (path injection koruması)
   - Static file serving sadece `data/` altında
   - API key validation

5. **Scalability:**
   - Attachment download'ları background task'a taşınabilir (Celery/RQ)
   - S3 storage path hazır (`storage_path` field)
   - Cached data ile sık kullanılan alanlar optimize edildi

---

## ✅ Tamamlanma Durumu

- [x] FAZ 1: DB Şeması & Modeller
- [x] FAZ 2: SAM Sync Servisi
- [x] FAZ 3: Attachment Download Servisi
- [ ] Migration (manuel SQL veya Alembic)
- [ ] Frontend integration
- [ ] Testing

**Toplam Tamamlanma:** ~85% (Core implementation tamamlandı, migration ve testing kaldı)

---

**Rapor Tarihi:** 2025-01-XX  
**Hazırlayan:** AI Assistant  
**Versiyon:** 1.0

