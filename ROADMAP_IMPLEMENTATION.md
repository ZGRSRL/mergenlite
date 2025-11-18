# Yol Haritası - React + FastAPI Ürünleştirme

**Durum:** İmplementasyon başlatıldı  
**Tarih:** 2025-01-XX

---

## 📋 Genel Bakış

Bu doküman, React + FastAPI ürünleştirme yol haritasının implementasyon durumunu takip eder. Her faz tamamlandıkça güncellenir.

---

## ✅ Tamamlananlar

### FAZ 1: Migration & DB Stabilizasyonu

#### 1.1 Alembic Migration Hazırlığı
- ✅ Alembic yapılandırması kontrol edildi
- ✅ `migrations/env.py` model import'ları eklendi
- ⚠️ **Sorun:** Autogenerate çok fazla değişiklik tespit ediyor (eski tabloları silmek istiyor)
- 🔄 **Çözüm:** Manuel migration oluşturulacak (sadece `opportunity_attachments`)

#### 1.2 Model Düzeltmeleri
- ✅ `OpportunityAttachment.metadata` → `extra_metadata` (SQLAlchemy reserved name)
- ✅ `AnalysisLog` ForeignKey kaldırıldı (ai_analysis_results tablosu henüz yok)
- ✅ Schemas güncellendi (`extra_metadata`)

---

## 🔄 Devam Edenler

### FAZ 1: Migration & DB Stabilizasyonu

#### 1.1 Manuel Migration Oluşturma
**Durum:** İn-progress  
**Görev:** Sadece `opportunity_attachments` tablosunu ekleyen minimal migration

**Adımlar:**
1. `migrations/versions/` klasörü oluşturuldu
2. Manuel migration script yazılacak
3. Test edilecek

---

## 📝 Sonraki Adımlar

### FAZ 1 Devamı
- [ ] Manuel migration script oluştur (`opportunity_attachments` tablosu)
- [ ] Migration'ı test et (dry-run)
- [ ] Mevcut veri migration script'i (raw_json → raw_data, notice_id mapping)
- [ ] Smoke testler: sync → list → detail

### FAZ 2: SAM Sync'in Ürünleşmesi
- [ ] Job ID/log mekanizması
- [ ] BackgroundTasks ile otomatik attachment download
- [ ] Streamlit'teki direkt SAMIntegration çağrılarını kapat

### FAZ 3: Attachment & Dosya Yönetimi
- [ ] BackgroundTasks ile async download
- [ ] Static file güvenlik kontrolleri
- [ ] React: attachments kartları + indir butonu

### FAZ 4: AutoGen Pipeline Entegrasyonu
- [ ] Pipeline bağımlılıklarını repo içine taşı
- [ ] Pipeline endpoint: BackgroundTasks + 202 response
- [ ] Log toplama: analysis_logs + endpoint

### FAZ 5: Frontend Entegrasyonu
- [ ] API client standardizasyonu
- [ ] Dashboard: gerçek metrikler
- [ ] OpportunityCenter: tüm butonlar
- [ ] GuidedAnalysis/Results: gerçek veriler
- [ ] SowForm: pipeline entegrasyonu

### FAZ 6: Ops & Test
- [ ] Concurrently script
- [ ] Integration testler
- [ ] README/IMPLEMENTATION_REPORT güncelle

---

## 🐛 Bilinen Sorunlar

1. **Alembic Autogenerate:** Çok fazla değişiklik tespit ediyor (eski tabloları silmek istiyor)
   - **Çözüm:** Manuel migration kullanılacak

2. **AnalysisLog ForeignKey:** `ai_analysis_results` tablosu henüz yok
   - **Çözüm:** ForeignKey kaldırıldı, sadece integer olarak tutuluyor

---

## 📊 İlerleme Durumu

- **FAZ 1:** %30 (Migration hazırlığı tamamlandı, manuel migration kaldı)
- **FAZ 2:** %0
- **FAZ 3:** %0
- **FAZ 4:** %0
- **FAZ 5:** %0
- **FAZ 6:** %0

**Toplam:** ~5% tamamlandı

---

## 📝 Notlar

- Migration'ları dikkatli yapmak gerekiyor (mevcut veri var)
- Autogenerate yerine manuel migration tercih ediliyor (daha kontrollü)
- `opportunity_attachments` tablosu öncelikli
- Unified schema migration'ı daha sonra yapılacak

