# MergenLite Opportunity Analysis Pipeline

AutoGen tabanlı çoklu ajan sistemi ile federal ihale fırsatlarının kapsamlı analizi.

## 🎯 Özellikler

- **Otomatik PDF İşleme**: Klasördeki tüm PDF'leri otomatik okur
- **SAM.gov Entegrasyonu**: Fırsat ID'si verildiğinde otomatik döküman indirme
- **Çoklu Ajan Analizi**: 
  - Requirements Agent: Teknik/operasyonel gereksinimler
  - Compliance Agent: FAR maddeleri ve uyumluluk
  - Commercial Agent: Ticari koşullar ve ödeme şartları
  - Reporter Agent: Birleşik rapor ve özet
- **Standart JSON Çıktı**: Şema tabanlı yapılandırılmış veri
- **Markdown Özet**: İnsan okunabilir go-no go değerlendirmesi

## 📋 Gereksinimler

```bash
# AutoGen kurulumu
pip install pyautogen

# Diğer bağımlılıklar (requirements.txt'de)
pip install -r requirements.txt
```

## 🔑 Ortam Değişkenleri

```bash
# .env dosyası veya ortam değişkeni
export OPENAI_API_KEY="your-api-key-here"
export SAM_API_KEY="your-sam-api-key-here"  # SAM.gov mode için

# Windows
set OPENAI_API_KEY=your-api-key-here
set SAM_API_KEY=your-sam-api-key-here
```

## 🚀 Kullanım

### Yerel Klasör Modu

```bash
python mergenlite_opportunity.py <opportunity_folder> [output_dir]
```

**Örnekler:**
```bash
# Samples klasöründeki PDF'leri analiz et
python mergenlite_opportunity.py samples/

# Özel bir fırsat klasörü
python mergenlite_opportunity.py opportunities/140D0424Q0292

# Çıktıyı farklı bir klasöre kaydet
python mergenlite_opportunity.py samples/ output/
```

### SAM.gov Modu (Otomatik İndirme)

```bash
# Notice ID ile
python mergenlite_opportunity.py --notice-id <notice_id> [output_dir]

# Opportunity ID ile
python mergenlite_opportunity.py --opp-id <opportunity_id> [output_dir]

# Her ikisi ile (Notice ID + Opportunity ID)
python mergenlite_opportunity.py --notice-id <notice_id> --opportunity-id <opp_id> [output_dir]
```

**Örnekler:**
```bash
# Notice ID ile indir ve analiz et
python mergenlite_opportunity.py --notice-id 57cd76db400c4e7ca895d40bf6454173

# Opportunity ID ile
python mergenlite_opportunity.py --opp-id 57cd76db400c4e7ca895d40bf6454173 output/

# Özel çıktı klasörü
python mergenlite_opportunity.py --notice-id 57cd76db400c4e7ca895d40bf6454173 results/
```

## 📁 Klasör Yapısı

### Yerel Klasör Modu
```
opportunities/
└── 140D0424Q0292/
    ├── RFQ.pdf
    ├── SOW.pdf
    ├── Award_or_Contract.pdf
    ├── FAR_Clauses.pdf
    └── Past_Performance.pdf
```

### SAM.gov Modu
```
downloads/  (otomatik oluşturulur)
├── document1.pdf
├── document2.pdf
└── ...
```

## 📊 Çıktı Formatı

### report.json

Standart JSON şemasına göre yapılandırılmış rapor:

```json
{
  "opportunity_info": {
    "solicitation_number": "",
    "notice_id": "",
    "title": "",
    "agency": "",
    "naics": "",
    "set_aside": "",
    "small_business_only": false,
    "place_of_performance": "",
    "response_deadline": ""
  },
  "event_requirements": {
    "location": "",
    "date_range": "",
    "participants_min": null,
    "participants_target": null,
    "room_block_plan": "",
    "meeting_spaces": "",
    "av_requirements": "",
    "fnb_requirements": "",
    "special_logistics": ""
  },
  "commercial_terms": {
    "estimated_value": "",
    "per_diem_limited": false,
    "payment_terms": "",
    "e_invoicing_ipp": false,
    "tax_exempt": false,
    "cancellation_penalties": "",
    "other_key_terms": ""
  },
  "compliance": {
    "far_52_212_4": false,
    "far_52_212_5": false,
    "far_52_204_24_25_26": false,
    "security_telecom_restrictions": false,
    "bytedance_restriction": false,
    "other_mandatory_clauses": []
  },
  "fit_assessment": {
    "overall_score": 0,
    "strengths": [],
    "risks": [],
    "blocking_issues": [],
    "summary": ""
  }
}
```

### summary.md

Markdown formatında insan okunabilir özet:
- Go-No Go değerlendirmesi
- Önemli bulgular
- Riskler ve fırsatlar
- Öneriler

## 🔧 Pipeline Akışı

### Yerel Klasör Modu
```
1. PDF Yükleme
   └─> DocumentProcessor ile tüm PDF'leri oku

2. Ajan Analizi
   ├─> Requirements Agent
   │   └─> Teknik/operasyonel gereksinimler
   ├─> Compliance Agent
   │   └─> FAR maddeleri ve uyumluluk
   └─> Commercial Agent
       └─> Ticari koşullar

3. Raporlama
   └─> Reporter Agent
       ├─> JSON rapor birleştirme
       └─> Markdown özet oluşturma
```

### SAM.gov Modu
```
1. SAM.gov'dan İndirme
   └─> SAMIntegration ile dökümanları indir

2. PDF İşleme
   └─> DocumentProcessor ile metin çıkar

3. Ajan Analizi
   ├─> Requirements Agent
   ├─> Compliance Agent
   └─> Commercial Agent

4. Raporlama
   └─> Reporter Agent
```

## 📝 Ajan Rolleri

### Requirements Agent
- **Görev**: RFQ, SOW ve eklerden operasyonel/teknik gereksinimleri çıkarma
- **Odak**: NAICS, set-aside, konum, tarih, kapasite, oda planı, AV, F&B, shuttle, park

### Compliance Agent
- **Görev**: FAR ve zorunlu hükümleri tespit etme
- **Odak**: FAR 52.212-4/5, FAR 52.204-24/25/26, IPP, vergi muafiyeti, Bytedance yasakları

### Commercial Agent
- **Görev**: Ticari koşulları ve ödeme şartlarını çıkarma
- **Odak**: Tahmini değer, per diem limitleri, ödeme koşulları, IPP, iptal cezaları

### Reporter Agent
- **Görev**: Tüm ajan çıktılarını birleştirme ve final rapor oluşturma
- **Odak**: fit_assessment hesaplama, go-no go değerlendirmesi, özet oluşturma

## 🎯 Örnek Senaryo

### Yerel Klasör Modu

**Belgeler:**
- `Request_for_Quote_-_AQD_Seminar.pdf` → Genel/teknik isterler
- `SOW_copy.pdf` → Hizmet kapsamı detayları
- `140D0424P0066_-_SIGNED.pdf` → Sözleşme koşulları
- `CREATA_FAR_52.204.24-26.pdf` → FAR uyumluluk
- `CREATA_GLOBAL_MEETING_AND_EVENTS_PAST_PERFORMANCE.pdf` → Referans uyumu

**Çalıştırma:**
```bash
python mergenlite_opportunity.py samples/
```

### SAM.gov Modu

**Fırsat ID:**
```bash
python mergenlite_opportunity.py --notice-id 57cd76db400c4e7ca895d40bf6454173
```

**Sistem:**
1. SAM.gov'dan dökümanları indirir
2. PDF'leri işler
3. Ajanlarla analiz eder
4. Rapor oluşturur

**Çıktı:**
```
downloads/  (veya belirtilen output_dir)
├── report.json      # Tam JSON rapor
└── summary.md       # Markdown özet
```

## ⚠️ Mock Mode

AutoGen veya OpenAI API key yoksa sistem mock mode'da çalışır:
- PDF'ler okunur (veya SAM.gov'dan indirilir)
- Basit mock rapor oluşturulur
- Gerçek analiz için AutoGen ve API key gerekir

## 🔍 Hata Ayıklama

### PDF Bulunamadı (Yerel Mod)
```
⚠️  No PDF files found in folder_path
```
**Çözüm**: Klasörde PDF dosyaları olduğundan emin olun

### Döküman Bulunamadı (SAM.gov Mod)
```
[SAM.gov] No documents found for notice_id
```
**Çözüm**: 
- Notice ID veya Opportunity ID'nin doğru olduğundan emin olun
- SAM_API_KEY'in ayarlı olduğunu kontrol edin
- SAM.gov'da fırsatın dökümanları olduğunu doğrulayın

### AutoGen Bulunamadı
```
[WARNING] AutoGen not available or LLM config missing
```
**Çözüm**: 
```bash
pip install pyautogen
```

### API Key Yok
```
OPENAI_API_KEY not set, using mock mode
```
**Çözüm**: 
```bash
export OPENAI_API_KEY="your-key"
# veya .env dosyasına ekleyin
```

## 📚 İlgili Dosyalar

- `mergenlite_opportunity_pipeline.py` - Ana pipeline kodu
- `mergenlite_opportunity.py` - CLI wrapper
- `schemas/opportunity_requirements.schema.json` - JSON şeması
- `document_processor.py` - PDF işleme modülü
- `sam_integration.py` - SAM.gov entegrasyonu

## 🚀 Gelişmiş Kullanım

### Python API

```python
from mergenlite_opportunity_pipeline import run_mergen_opportunity_analysis

# Yerel klasör
result = run_mergen_opportunity_analysis(
    folder_path="opportunities/140D0424Q0292",
    output_dir="output/"
)

# SAM.gov'dan indir
result = run_mergen_opportunity_analysis(
    notice_id="57cd76db400c4e7ca895d40bf6454173",
    opportunity_id="57cd76db400c4e7ca895d40bf6454173",  # Opsiyonel
    output_dir="output/",
    download_dir="downloads/"
)

print(result['report'])
print(result['summary_md'])
```

### Özel LLM Konfigürasyonu

`.env` dosyasında:
```env
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini  # veya gpt-4, gpt-3.5-turbo
SAM_API_KEY=your-sam-key
```

## 📞 Destek

Sorunlar için:
1. Log dosyalarını kontrol edin
2. Mock mode çıktısını inceleyin
3. PDF'lerin okunabilir olduğundan emin olun
4. SAM.gov API key'in geçerli olduğunu kontrol edin

---

**MergenLite** - Federal İhale Analiz Sistemi
