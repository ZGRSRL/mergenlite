## Yol Haritası İlerleme Raporu

**Tarih:** 2025-11-16  
**Durum:** Tarihçe & Öğrenme Katmanı dâhil backend çekirdeği %80 seviyesinde hazır

---

### ✅ Tamamlanan Başlıklar

1. **Migration & DB Stabilizasyonu**
   - Alembic yapılandırması, smoke testler (`test_smoke.py`) ve migration zinciri (`0001`→`0005`) uygulandı.
   - Unified `opportunities`/`opportunity_attachments` şeması; sync/download job tabloları (`sync_jobs`, `download_jobs`) devrede.

2. **SAM Sync Ürünleşmesi**
   - `opportunity_sync_service.py` job tracking + loglama yapıyor.
   - REST uçları: `POST /api/opportunities/sync`, `GET /api/opportunities/sync/jobs/*`.
   - React OpportunityCenter, sync job polling yapabiliyor.

3. **Attachment Yönetimi**
   - `attachment_service.py` background download job’ları, log tabloları (`download_logs`) ile entegre.
   - `POST /api/opportunities/{id}/download-attachments` → job başlatılıyor.

4. **AutoGen Pipeline Altyapısı**
   - `pipeline_service.py`: `AgentRun`, `AgentMessage`, `AnalysisLog`, `TrainingExample`, `OpportunityHistory` kayıtları.
   - Pipeline tamamlanınca summary dosyası yazılıyor, training example + history satırı oluşturuluyor.
   - React `GuidedAnalysis` ve `Results` bileşenleri gerçek API verileriyle çalışıyor.

5. **LLM Çağrı Loglama**
   - `services/llm_logger.py` tek giriş noktası; her çağrı `llm_calls` tablosuna prompt/response/token bilgisiyle kaydediliyor.

6. **Tarihçe & Öğrenme Tabakası**
   - `opportunity_history`, `decision_cache`, `training_examples`, genişletilmiş `email_log` tabloları + helper servisler (`history_service.py`).
   - Pipeline örneği: job tamamlanınca history + training example satırları otomatik yazılıyor.

7. **LLM Wrapper Entegrasyonu**
   - `llm_client.py` helper modülü ile tüm OpenAI çağrıları `call_llm_with_logging` üzerinden geçiyor.
   - `llm_analyzer.py`, `detailed_opportunity_analysis.py`, `sow_generator.py`, `vendor_profile_extractor.py` ve `agents/sow_mail_agent.py` doğrudan `openai.ChatCompletion` kullanmıyor; böylece tüm ajan akışları merkezi logging/LLM kontrolünden geçiyor.

8. **GuidedAnalysis Timeline UI**
   - React `GuidedAnalysis` ekranına birleşik timeline komponenti eklendi; `history + agent_runs + training_examples + email_log` tek listede renklendirilmiş olarak görüntüleniyor.
   - Timeline her event tipini Chip ile etiketleyip saat bilgisi/özet açıklama gösteriyor; e-posta/kaynak logları ayrıca kısa listede yer alıyor.

9. **Decision Cache API & UI**
   - FastAPI tarafında `decision_cache_service` + lookup/save endpoint’leri eklendi; ajanlar context’e göre karar desenlerini cache’den çekip saklayabiliyor.
   - `mergenlite_opportunity_pipeline.py` karar önermeden önce cache’i yokluyor, yeni tavsiyeleri kaydediyor.
   - React GuidedAnalysis, cache sonucunu (signature + otel listesi) timeline ve kartlarda gösteriyor.

---

### 🔄 Devam Eden Çalışmalar

1. **SAM Sync geliştirmeleri**
   - Streamlit’teki direkt SAMIntegration çağrılarını backend’e yönlendir.
   - Sync log’larını timeline UI’de göster.

2. **Attachment / Dosya Yönetimi**
   - Download job’larını queue (Celery/RQ) ile yönet, S3 depolama opsiyonunu hazırla.

3. **AutoGen Pipeline**
   - Gerçek AutoGen ajanlarını pipeline servisine bağla.
   - Decision cache lookup + context injection mekanizmasını oluştur.

4. **UI & Ops**
   - React API client için error/ retry stratejisi (React Query tazelemesi vb.).
   - `npm run dev` + `uvicorn` için concurrently script’i.
   - End-to-end test senaryosu (sync → download → pipeline) hazırla.

---

### ▶️ Sıradaki Somut Adımlar

1. **Training examples raporu:** “won/lost” örnekleri ve hangi oteller kazandırıyor? basit analitik endpoint.
2. **Email log entegrasyonu:** inbound/outbound mailleri `email_log` ve `llm_calls` kayıtlarıyla ilişkilendir.
3. **Queue + dosya altyapısı:** Attachment ve pipeline job’larını background queue + kalıcı storage (S3 vb.) ile olgunlaştır.
4. **AutoGen pipeline entegrasyonu:** Gerçek ajan çıktıları için decision cache verilerini otomatik besle.
