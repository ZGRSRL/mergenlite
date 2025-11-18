# Mimari Plan - React Odaklı Geliştirme

## 🎯 Genel Strateji

**React: Primary Product UI**  
**Streamlit: Admin/PoC/Internal Debug (Opsiyonel)**

Tüm fonksiyonel akış React + FastAPI üzerinden çalışacak.

---

## 📊 Veri Modeli Tekleştirme

### Mevcut Durum
- `mergenlite_models.py`: `opportunity_id` primary key, minimal şema
- `mergen/api/app/models.py`: `id` primary key, genişletilmiş şema

### Unified Schema (models_unified.py)

```python
Opportunity:
  - id (int PK)
  - opportunity_id (string, indexed, not unique - fallback için)
  - notice_id (string, indexed)
  - title, description
  - posted_date, response_deadline
  - naics_code, psc_code
  - agency, office
  - raw_data (JSON)
  - cached_data (JSON)
  
OpportunityAttachment:
  - id (int PK)
  - opportunity_id (FK)
  - name, source_url
  - local_path, storage_path
  - downloaded, mime_type
  
AIAnalysisResult:
  - id (int PK)
  - opportunity_id (FK)
  - analysis_type, status
  - result_json, pdf_path
  - created_at, completed_at
  
AnalysisLog:
  - id (int PK)
  - analysis_result_id (FK)
  - step, level, message
  - timestamp
```

### Migration Stratejisi

1. **Mevcut veriyi koru**: `opportunity_id` değerlerini kullan
2. **Yeni kolonlar ekle**: `agency`, `office`, `psc_code` gibi
3. **Attachment tablosu oluştur**: Mevcut `raw_data` içindeki `resourceLinks`'i parse et
4. **Analysis tablosunu genişlet**: `status`, `pdf_path` gibi alanlar ekle

---

## 🔄 SAM Entegrasyonu Merkezileştirme

### Backend Endpoint: `/api/opportunities/sync`

**Akış:**
1. SAM/GSA API'den veri çek
2. `opportunities` tablosuna yaz
3. `resourceLinks` ve `attachments` bilgisini `opportunity_attachments` tablosuna kaydet
4. Response: `{success, count_new, count_updated, total_processed}`

### Streamlit Değişiklikleri

**Önce:**
```python
sam = SAMIntegration()
opportunities = sam.fetch_opportunities(...)
```

**Sonra:**
```python
response = requests.post("http://localhost:8000/api/opportunities/sync", params={...})
```

### Attachment Download Servisi

**Dosya:** `mergen/api/app/services/attachment_service.py`

```python
async def download_and_store_attachments(opportunity_id: str) -> List[Dict]:
    """
    1. opportunity_attachments tablosundan source_url'leri çek
    2. Her attachment'ı indir
    3. /data/opportunities/{notice_id}/attachments/ altına kaydet
    4. local_path kolonunu güncelle
    5. downloaded=True yap
    """
```

**Endpoint:** `POST /api/opportunities/{id}/download-attachments`

---

## 🤖 Pipeline & AutoGen Entegrasyonu

### D:/RFQ Bağımlılığını Temizle

**Seçenek 1: Repo İçine Taşı**
- `D:/RFQ/backend/services/` → `mergen/api/services/pipeline/`
- `D:/RFQ/backend/agents/` → `mergen/api/services/agents/`
- `D:/RFQ/agents/` → `mergen/api/services/agents/`

**Seçenek 2: Import Path Düzelt**
- `sys.path`'e D:/RFQ eklemek yerine
- Pipeline modüllerini `mergen/api/services/` altına kopyala
- Import'ları güncelle

### `/api/pipeline/run` Endpoint

**Request Body:**
```json
{
  "opportunity_id": "abc123...",
  "selected_documents": ["attachment_id_1", "attachment_id_2"],
  "pipeline_version": "v3",
  "use_template_engine": true,
  "pricing_inputs": {...},
  "strategy_notes": "..."
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "analysis_result_id",
  "status": "pending",
  "message": "Pipeline started"
}
```

**Akış:**
1. Request al
2. `AIAnalysisResult` kaydı oluştur (status='pending')
3. Background task başlat
4. AutoGen pipeline çalıştır
5. Sonuçları `ai_analysis_results` tablosuna yaz
6. Log'ları `analysis_logs` tablosuna yaz

### Background Task

**İlk Aşama:** FastAPI `BackgroundTasks`
```python
from fastapi import BackgroundTasks

@router.post("/run")
async def run_pipeline(..., background_tasks: BackgroundTasks):
    # Create analysis_result record
    analysis_result = create_analysis_result(...)
    
    # Start background task
    background_tasks.add_task(run_pipeline_task, analysis_result.id, ...)
    
    return {"job_id": analysis_result.id, "status": "pending"}
```

**Sonra:** Celery/RQ/Arq queue (TODO)

### Log Streaming

**Endpoint:** `GET /api/analysis/{analysis_result_id}/logs`

**Response:**
```json
{
  "logs": [
    {"step": "document_processing", "level": "INFO", "message": "...", "timestamp": "..."},
    ...
  ],
  "total": 42
}
```

**React:** Polling ile log'ları çek (her 2 saniyede bir)

---

## 🎨 React API Entegrasyonu

### API Client Standardizasyonu

**Dosya:** `frontend/src/api/client.ts`

```typescript
const API_BASE = import.meta.env.VITE_API_URL || '/api'

export const api = {
  opportunities: {
    list: (params) => axios.get(`${API_BASE}/opportunities`, {params}),
    get: (id) => axios.get(`${API_BASE}/opportunities/${id}`),
    sync: (params) => axios.post(`${API_BASE}/opportunities/sync`, null, {params}),
  },
  attachments: {
    list: (opportunityId) => axios.get(`${API_BASE}/opportunities/${opportunityId}/attachments`),
    download: (opportunityId) => axios.post(`${API_BASE}/opportunities/${opportunityId}/download-attachments`),
  },
  pipeline: {
    run: (data) => axios.post(`${API_BASE}/pipeline/run`, data),
  },
  analysis: {
    get: (id) => axios.get(`${API_BASE}/analysis/${id}`),
    logs: (id) => axios.get(`${API_BASE}/analysis/${id}/logs`),
    byOpportunity: (opportunityId) => axios.get(`${API_BASE}/analysis/opportunity/${opportunityId}`),
  },
  dashboard: {
    stats: () => axios.get(`${API_BASE}/dashboard/stats`),
    recentActivities: (limit) => axios.get(`${API_BASE}/dashboard/recent-activities`, {params: {limit}}),
  },
}
```

### OpportunityCenter Butonları

1. **"SAM'den Sync"**
   ```typescript
   await api.opportunities.sync({naics: '721110', days_back: 30})
   // Refresh list
   await loadOpportunities()
   ```

2. **"Dokümanları İndir"**
   ```typescript
   await api.attachments.download(opportunityId)
   // Show success message
   ```

3. **"Analizi Başlat"**
   ```typescript
   const {job_id} = await api.pipeline.run({
     opportunity_id: opportunityId,
     selected_documents: [...],
   })
   // Navigate to GuidedAnalysis with job_id
   ```

### GuidedAnalysis Gerçek Durum

```typescript
useEffect(() => {
  // Poll analysis status
  const interval = setInterval(async () => {
    const analysis = await api.analysis.get(jobId)
    setStatus(analysis.status)
    setProgress(analysis.progress)
    
    if (analysis.status === 'completed') {
      clearInterval(interval)
      // Navigate to Results
    }
  }, 2000)
  
  // Poll logs
  const logInterval = setInterval(async () => {
    const {logs} = await api.analysis.logs(jobId)
    setLogs(logs)
  }, 2000)
}, [jobId])
```

### Results Gerçek Veri

```typescript
const analysis = await api.analysis.get(analysisResultId)

// Display:
// - analysis.result_json (structured data)
// - analysis.pdf_path (download link)
// - analysis.json_path (download link)
```

---

## 📁 Dosya Sistemi Yapısı

```
/data/
  /opportunities/
    /{notice_id}/
      /attachments/
        - file1.pdf
        - file2.docx
      /outputs/
        - sow.pdf
        - analysis.json
        - summary.md
```

**FastAPI Static Mount:**
```python
from fastapi.staticfiles import StaticFiles

app.mount("/files", StaticFiles(directory="data"), name="files")
```

**DB'deki path:** `/files/opportunities/{notice_id}/outputs/sow.pdf`

---

## 🧪 E2E Test Senaryosu

1. ✅ `/api/opportunities/sync` çağrılır → DB'ye yeni kayıtlar düşer
2. ✅ React Dashboard'da yeni fırsatlar görünür
3. ✅ Bir fırsat seçilir → "Dokümanları İndir" → attachments download
4. ✅ "Analizi Başlat" → pipeline run, React'te log'lar akar
5. ✅ Analiz tamamlanınca Results ekranı: JSON özet + PDF indirme linki

---

## 📝 Yapılacaklar Öncelik Sırası

### Faz 1: Temel Altyapı (Hemen)
1. ✅ Unified model oluştur (`models_unified.py`)
2. ⏳ Migration hazırla
3. ⏳ Attachment modeli ve servisi
4. ⏳ SAM sync'i attachment kaydetmeye genişlet

### Faz 2: Pipeline Entegrasyonu (Bu Hafta)
5. ⏳ D:/RFQ bağımlılığını çöz
6. ⏳ `/api/pipeline/run` gerçek pipeline'a bağla
7. ⏳ Background task sistemi
8. ⏳ Log toplama ve endpoint

### Faz 3: React Entegrasyonu (Sonraki Hafta)
9. ⏳ API client standardizasyonu
10. ⏳ OpportunityCenter butonları
11. ⏳ GuidedAnalysis gerçek durum
12. ⏳ Results gerçek veri

### Faz 4: Streamlit Sadeleştirme (Son)
13. ⏳ Streamlit'teki direkt SAM çağrılarını kaldır
14. ⏳ Sadece backend API kullan

