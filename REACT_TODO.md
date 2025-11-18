# React Odaklı Geliştirme - To-Do List

## 🎯 Genel Hedef
Streamlit'teki işlevleri React'a taşıyarak tek bir modern UI oluşturmak. Backend API'leri React'ın ihtiyaçlarına göre tamamlamak.

---

## 📋 Backend API'leri Sabitle

### ✅ Tamamlanan
- [x] `/api/opportunities` endpoint'i çalışıyor
- [x] `/api/dashboard/stats` endpoint'i çalışıyor
- [x] `/api/dashboard/recent-activities` endpoint'i çalışıyor
- [x] `/api/opportunities/sync` endpoint'i çalışıyor (NAICS 721110 test edildi)
- [x] DB şema uyumsuzlukları düzeltildi (opportunity_id, posted_date, raw_data)

### 🔄 Yapılacaklar

#### 1. SAM Resource/Attachment Kaydetme
**Dosya:** `mergen/api/app/models.py`, `mergen/api/app/routes/opportunities.py`

- [ ] `OpportunityAttachment` modeli ekle:
  ```python
  class OpportunityAttachment(Base):
      __tablename__ = "opportunity_attachments"
      id = Column(Integer, primary_key=True)
      opportunity_id = Column(String, ForeignKey("opportunities.opportunity_id"))
      attachment_url = Column(String)
      attachment_type = Column(String)  # 'resourceLink', 'attachment', 'document'
      file_name = Column(String)
      file_size = Column(Integer)
      downloaded = Column(Boolean, default=False)
      local_path = Column(String)
      created_at = Column(DateTime)
  ```

- [ ] `sync_opportunities` fonksiyonunda `resourceLinks` ve `attachments` bilgisini kaydet
- [ ] `/api/opportunities/{id}/attachments` endpoint'i ekle (attachment listesi döndür)
- [ ] `/api/opportunities/{id}/attachments/{attachment_id}/download` endpoint'i ekle

#### 2. Pipeline Bağımlılıklarını Çöz
**Dosya:** `mergen/api/app/routes/pipeline.py`

- [ ] D:/RFQ bağımlılıklarını kontrol et:
  - [ ] `backend/services/sow_pipeline_enhanced.py` var mı?
  - [ ] `backend/agents/pipeline_v3.py` var mı?
  - [ ] `agents/analyzer_agent.py` var mı?
  
- [ ] Seçenek 1: D:/RFQ klasörünü repo içine taşı
- [ ] Seçenek 2: Pipeline modüllerini `mergen/api/services/pipeline/` altına kopyala
- [ ] Seçenek 3: Pipeline'ı optional yap, yoksa graceful degradation

- [ ] `PIPELINE_AVAILABLE` kontrolünü düzelt, gerçek import başarısını kontrol et
- [ ] `/api/pipeline/run` endpoint'ini test et, PDF/JSON yollarını döndür

#### 3. AutoGen Pipeline Entegrasyonu
**Dosya:** `mergen/api/app/routes/pipeline.py`, `mergen/api/app/services/pipeline/`

- [ ] Background task sistemi ekle:
  - [ ] FastAPI `BackgroundTasks` kullan VEYA
  - [ ] Celery/Arq queue sistemi kur
  
- [ ] Pipeline job modeli ekle:
  ```python
  class PipelineJob(Base):
      __tablename__ = "pipeline_jobs"
      id = Column(Integer, primary_key=True)
      opportunity_id = Column(String)
      status = Column(String)  # 'pending', 'running', 'completed', 'failed'
      logs = Column(JSON)
      result_pdf_path = Column(String)
      result_json_path = Column(String)
      created_at = Column(DateTime)
      completed_at = Column(DateTime)
  ```

- [ ] `/api/pipeline/run` endpoint'ini background task olarak çalıştır
- [ ] Pipeline sonucunu `pipeline_jobs` tablosuna kaydet
- [ ] `/api/pipeline/status/{job_id}` endpoint'i ekle

#### 4. Ajan Loglarını Stream Et
**Dosya:** `mergen/api/app/routes/pipeline.py`

- [ ] SSE (Server-Sent Events) endpoint ekle: `/api/pipeline/logs/{job_id}/stream`
- [ ] VEYA polling endpoint: `/api/pipeline/logs/{job_id}`
- [ ] Log kayıtlarını `pipeline_jobs.logs` JSON alanına yaz
- [ ] React SowForm log panelini bu endpoint'e bağla

#### 5. Üretilen Dosyaları Storage'da Tut
**Dosya:** `mergen/api/app/routes/pipeline.py`

- [ ] Pipeline çıktılarını `outputs/pipeline/{job_id}/` altına kaydet
- [ ] `/api/pipeline/files/sow-pdf?job_id={job_id}` endpoint'ini genişlet
- [ ] `/api/pipeline/files/list?opportunity_id={id}` endpoint'i ekle
- [ ] React'e indirme linkleri döndür

#### 6. Veri Modeli Tekleştir
**Dosya:** `mergen/api/app/models.py`, `mergenlite_models.py`

- [ ] `mergenlite_models.py` ile `mergen/api/app/models.py` şemalarını karşılaştır
- [ ] Farklılıkları gider, tek bir şema kullan
- [ ] React yalnızca FastAPI modeline güvensin

#### 7. /api/results Endpoint'i
**Dosya:** `mergen/api/app/routes/results.py` (yeni)

- [ ] Yeni router oluştur: `mergen/api/app/routes/results.py`
- [ ] `/api/results?opportunity_id={id}` endpoint'i ekle
- [ ] `ai_analysis_results` tablosundan analiz sonuçlarını çek
- [ ] Pipeline sonuçlarını da dahil et
- [ ] React Results komponenti bu endpoint'i kullansın

---

## 🎨 React API Entegrasyonu

### ✅ Tamamlanan
- [x] `frontend/src/api/opportunities.ts` - noticeId/naicsCode mapping düzeltildi
- [x] `frontend/src/api/dashboard.ts` - dashboard API entegrasyonu yapıldı
- [x] `frontend/src/components/Dashboard.tsx` - gerçek API verileri kullanılıyor
- [x] `frontend/src/components/OpportunityCenter.tsx` - sync butonu çalışıyor

### 🔄 Yapılacaklar

#### 1. API Fonksiyonlarını Güncelle
**Dosya:** `frontend/src/api/*.ts`

- [ ] `opportunities.ts`: Stub veriler kaldır, tüm fonksiyonlar backend'e bağlı olsun
- [ ] `pipeline.ts`: `/api/pipeline/run` için gerçek upload ve log streaming
- [ ] `results.ts` (yeni): `/api/results` endpoint'i için client
- [ ] `attachments.ts` (yeni): `/api/opportunities/{id}/attachments` için client

#### 2. OpportunityCenter Butonlarını Bağla
**Dosya:** `frontend/src/components/OpportunityCenter.tsx`

- [ ] "Doküman Yükle" butonu:
  - [ ] `/api/opportunities/{id}/upload` endpoint'i ekle (backend)
  - [ ] File upload dialog aç
  - [ ] Upload sonrası success mesajı göster

- [ ] "Doküman İndir" butonu:
  - [ ] `/api/opportunities/{id}/attachments` endpoint'inden liste çek
  - [ ] Attachment listesi göster
  - [ ] İndirme linklerini sağla

- [ ] "Analizi Başlat" butonu:
  - [ ] `/api/pipeline/run` endpoint'ine POST isteği gönder
  - [ ] Job ID al ve GuidedAnalysis sayfasına yönlendir
  - [ ] Job status'u takip et

- [ ] "Klasörü Aç" butonu:
  - [ ] Opportunity'nin local klasörünü aç (electron/desktop app için)
  - [ ] VEYA klasör yolunu göster

#### 3. Dashboard Komponentini Doldur
**Dosya:** `frontend/src/components/Dashboard.tsx`

- [x] KPI'lar gerçek API'den geliyor ✅
- [x] Recent activities gerçek API'den geliyor ✅
- [ ] AI Agents durumu: Backend'den agent status endpoint'i ekle
- [ ] Loading states ve error handling iyileştir

#### 4. GuidedAnalysis Komponentini Doldur
**Dosya:** `frontend/src/components/GuidedAnalysis.tsx`

- [ ] `/api/pipeline/status/{job_id}` endpoint'i ekle (backend)
- [ ] Analiz adımlarını gerçek pipeline durumuna göre güncelle:
  - [ ] "Döküman İşleme" → pipeline status: 'processing_documents'
  - [ ] "Gereksinim Analizi" → pipeline status: 'analyzing_requirements'
  - [ ] "Compliance Kontrolü" → pipeline status: 'checking_compliance'
  - [ ] "Teklif Taslağı" → pipeline status: 'generating_proposal'
- [ ] Progress bar'ı gerçek ilerlemeye göre güncelle
- [ ] Log paneli ekle (pipeline loglarını göster)

#### 5. Results Komponentini Doldur
**Dosya:** `frontend/src/components/Results.tsx`

- [ ] `/api/results?opportunity_id={id}` endpoint'inden veri çek
- [ ] Analiz sonuçlarını göster:
  - [ ] Executive Summary
  - [ ] Requirements List
  - [ ] Compliance Check Results
  - [ ] Proposal Draft
- [ ] PDF/JSON indirme linklerini göster
- [ ] Filtreleme ve sıralama ekle

#### 6. SowForm Log Panelini Backend'e Bağla
**Dosya:** `frontend/src/components/SowForm.tsx`

- [x] Functional state update kullanılıyor ✅
- [ ] `/api/pipeline/logs/{job_id}` endpoint'ine polling ekle
- [ ] VEYA SSE stream kullan: `/api/pipeline/logs/{job_id}/stream`
- [ ] Log akışını real-time göster
- [ ] Error handling iyileştir

#### 7. SAM Sync Sonrası Otomatik Refresh
**Dosya:** `frontend/src/components/OpportunityCenter.tsx`

- [x] Sync butonu çalışıyor ✅
- [ ] Sync tamamlandığında opportunity listesini otomatik yenile
- [ ] Success mesajı göster
- [ ] VEYA WebSocket ile real-time güncelleme

#### 8. NAICS Filtresi Kontrolü
**Dosya:** `frontend/src/api/opportunities.ts`, `frontend/src/components/OpportunityCenter.tsx`

- [x] noticeId → notice_id mapping yapıldı ✅
- [x] naicsCode → naics_code mapping yapıldı ✅
- [ ] Filtre testleri yap:
  - [ ] 721110 NAICS kodu ile arama
  - [ ] Farklı NAICS kodları ile arama
  - [ ] Filtre kombinasyonları test et

---

## 🤖 AutoGen/SOW Pipeline Entegrasyonu

### 🔄 Yapılacaklar

#### 1. AutoGen Agent Entegrasyonu
**Dosya:** `mergen/api/app/services/pipeline/autogen_service.py` (yeni)

- [ ] Mevcut agent scriptlerini bul:
  - [ ] `sow_mail_agent.py`
  - [ ] Diğer agent dosyaları
  
- [ ] Agent servis katmanı oluştur:
  ```python
  class AutoGenPipelineService:
      def __init__(self):
          # Agent'ları initialize et
          pass
      
      async def run_pipeline(self, opportunity_id, rfq_file_path):
          # Pipeline'ı çalıştır
          # Log'ları kaydet
          # Sonuçları döndür
          pass
  ```

- [ ] FastAPI route'larına bağla
- [ ] Orchestrated workflow oluştur

#### 2. AutoGen Pipeline Çıktılarını DB'ye Yaz
**Dosya:** `mergen/api/app/models.py`, `mergen/api/app/routes/pipeline.py`

- [ ] `ai_analysis_results` tablosunu kullan:
  ```python
  class AIAnalysisResult(Base):
      __tablename__ = "ai_analysis_results"
      id = Column(Integer, primary_key=True)
      opportunity_id = Column(String)
      analysis_type = Column(String)  # 'requirements', 'compliance', 'proposal'
      result_json = Column(JSON)
      created_at = Column(DateTime)
  ```

- [ ] Pipeline sonuçlarını bu tabloya kaydet
- [ ] `/api/results` endpoint'i bu tablodan veri çeksin

---

## 🛠️ DevOps/Test

### 🔄 Yapılacaklar

#### 1. Frontend .env/Proxy Ayarları
**Dosya:** `frontend/.env`, `frontend/vite.config.ts`

- [ ] `.env.development` dosyası oluştur:
  ```
  VITE_API_URL=http://localhost:8000
  ```

- [ ] `.env.production` dosyası oluştur:
  ```
  VITE_API_URL=https://api.mergenlite.com
  ```

- [ ] `vite.config.ts` proxy ayarlarını kontrol et:
  ```typescript
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
  ```

#### 2. Concurrently Script Ekle
**Dosya:** `package.json` (root veya frontend)

- [ ] `concurrently` paketini ekle:
  ```bash
  npm install --save-dev concurrently
  ```

- [ ] Script ekle:
  ```json
  {
    "scripts": {
      "dev:all": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\"",
      "dev:backend": "cd mergen/api && python -m uvicorn app.main:app --reload --port 8000",
      "dev:frontend": "cd frontend && npm run dev"
    }
  }
  ```

#### 3. E2E Test Senaryoları
**Dosya:** `E2E_TEST_CHECKLIST.md` (yeni)

- [ ] Manuel test checklist oluştur:
  1. [ ] SAM.gov'dan sync yap (NAICS 721110)
  2. [ ] Opportunity listesinde görüntüle
  3. [ ] Bir opportunity seç
  4. [ ] "Analizi Başlat" butonuna tıkla
  5. [ ] Pipeline loglarını izle
  6. [ ] Analiz tamamlandığında Results sayfasına git
  7. [ ] PDF/JSON indir
  8. [ ] Dashboard'da istatistikleri kontrol et

- [ ] VEYA Playwright/Cypress ile otomasyon

---

## 📊 Öncelik Sırası

### Yüksek Öncelik (Hemen)
1. ✅ Backend API'leri sabitle (çoğu tamamlandı)
2. 🔄 OpportunityCenter butonlarını bağla
3. 🔄 Pipeline bağımlılıklarını çöz
4. 🔄 GuidedAnalysis'i gerçek durumla doldur

### Orta Öncelik (Bu Hafta)
5. 🔄 SAM resource/attachment kaydetme
6. 🔄 AutoGen pipeline entegrasyonu
7. 🔄 Results komponentini doldur
8. 🔄 Log streaming

### Düşük Öncelik (Sonra)
9. 🔄 WebSocket real-time updates
10. 🔄 E2E test otomasyonu
11. 🔄 Advanced filtering/search

---

## 📝 Notlar

- Streamlit kodunu silme, sadece kullanma (admin/hızlı prototip için)
- Tüm SAM çağrıları backend API üzerinden yapılmalı
- Pipeline bağımlılıkları repo içine taşınmalı veya optional yapılmalı
- Veri modeli tek bir kaynaktan gelmeli (FastAPI models.py)

