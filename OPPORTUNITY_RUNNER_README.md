# MergenLite Opportunity Runner

Fırsat koduna göre otomatik klasör oluşturma, döküman indirme ve analiz orkestrasyonu.

## 🎯 Özellikler

- **Otomatik Klasör Yönetimi**: Fırsat kodu → `opportunities/{code}/` klasörü
- **Otomatik Döküman İndirme**: SAM.gov'dan veya manuel URL listesinden
- **Belge Tipi Tespiti**: RFQ, SOW, Contract, Compliance, Performance
- **Form Kriterlerine Göre Analiz**: Her belge, her kriter için özelleştirilmiş analiz
- **Standart Çıktı**: `report.json` + `summary.md`

## 📋 Kullanım

### Python API

```python
from opportunity_runner import analyze_opportunity

# SAM.gov'dan otomatik indir ve analiz et
result = analyze_opportunity(
    base_dir=".",
    opportunity_code="140D0424Q0292",
    notice_id="57cd76db400c4e7ca895d40bf6454173",
    opportunity_id="57cd76db400c4e7ca895d40bf6454173",
    form_data={
        "company_name": "CREATA GLOBAL",
        "evaluation_focus": [
            "Room capacity and ADA compliance",
            "FAR/DFAR compliance clauses"
        ]
    },
    download_from_sam_gov=True
)

# Manuel döküman listesi ile
result = analyze_opportunity(
    base_dir=".",
    opportunity_code="140D0424Q0292",
    documents=[
        {"url": "https://...", "name": "RFQ.pdf"},
        {"url": "https://...", "name": "SOW.pdf"}
    ],
    form_data={...}
)
```

### CLI

```bash
# SAM.gov'dan indir ve analiz et
python opportunity_runner.py 140D0424Q0292 --notice-id 57cd76db400c4e7ca895d40bf6454173

# Form verileri ile
python opportunity_runner.py 140D0424Q0292 --notice-id 57cd76db400c4e7ca895d40bf6454173 --form-data '{"evaluation_focus": ["Room capacity"]}'
```

### Streamlit UI

UI'da "🚀 Analizi Başlat" butonuna tıklandığında otomatik olarak:

1. Fırsat kodu oluşturulur
2. `opportunities/{code}/` klasörü oluşturulur
3. SAM.gov'dan dökümanlar indirilir
4. Belge tipleri tespit edilir
5. Form kriterlerine göre analiz yapılır
6. `report.json` ve `summary.md` oluşturulur

## 📁 Klasör Yapısı

```
opportunities/
└── 140D0424Q0292/
    ├── Request_for_Quote_-_AQD_Seminar[1].pdf
    ├── SOW_copy[1].pdf
    ├── 140D0424P0066_-_SIGNED[1].pdf
    ├── CREATA_FAR_52.204.24-26[1].pdf
    ├── CREATA_GLOBAL_MEETING_AND_EVENTS_PAST_PERFORMANCE_copy[1].pdf
    ├── report.json
    └── summary.md
```

## 🔍 Belge Tipi Tespiti

Sistem otomatik olarak belge tiplerini tespit eder:

| Dosya Adı / İçerik | Belge Tipi |
|-------------------|-----------|
| `*RFQ*`, `*Request_for_Quote*` | `rfq` |
| `*SOW*`, `*Statement of Work*` | `sow` |
| `*SIGNED*`, `*Award*`, `*Contract*` | `contract` |
| `*FAR_52.204.24*`, `*52.204-24*` | `compliance` |
| `*Past_Performance*` | `performance` |
| Diğer | `general` |

## 📊 Analiz Akışı

```
Fırsat Kodu (140D0424Q0292)
    ↓
opportunities/140D0424Q0292/ klasörü oluştur
    ↓
SAM.gov'dan dökümanları indir
    ↓
Belge tiplerini tespit et
    ↓
Form kriterlerine göre analiz:
    ├─> Her belge için
    │   └─> Her kriter için
    │       └─> LLM analizi
    ↓
report.json + summary.md oluştur
```

## 🎯 Form Kriterleri

Form verileri analizi özelleştirir:

```python
form_data = {
    "company_name": "CREATA GLOBAL EVENT AGENCY LLC",
    "project_type": "Conference and Lodging Support",
    "location": "Orlando, FL",
    "dates": "April 14-18, 2024",
    "participants": 100,
    "budget": 29330,
    "naics": "721110",
    "evaluation_focus": [
        "Room capacity and ADA compliance",
        "Conference space AV requirements",
        "FAR/DFAR compliance clauses",
        "Electronic invoicing (IPP)",
        "Small business eligibility"
    ]
}
```

## 📄 Çıktı Formatı

### report.json

```json
{
  "opportunity_info": {...},
  "event_requirements": {...},
  "commercial_terms": {...},
  "compliance": {...},
  "fit_assessment": {
    "overall_score": 85,
    "strengths": [...],
    "risks": [...],
    "blocking_issues": [...],
    "summary": "..."
  }
}
```

### summary.md

Markdown formatında go-no go değerlendirmesi ve özet.

## 🔧 Fonksiyonlar

### `analyze_opportunity()`

Ana orkestrasyon fonksiyonu:

```python
analyze_opportunity(
    base_dir: str,                    # Temel klasör
    opportunity_code: str,            # Fırsat kodu
    documents: List[Dict] = None,     # Manuel döküman listesi
    notice_id: str = None,            # SAM.gov Notice ID
    opportunity_id: str = None,      # SAM.gov Opportunity ID
    form_data: Dict = None,           # Form verileri
    download_from_sam_gov: bool = False  # SAM.gov'dan indir
) -> Dict[str, Any]
```

### `detect_document_type()`

Belge tipini tespit eder:

```python
doc_type = detect_document_type("Request_for_Quote.pdf", text_content)
# Returns: "rfq"
```

### `download_documents()`

Dökümanları indirir:

```python
downloaded = download_documents(
    folder=Path("opportunities/140D0424Q0292"),
    documents=[{"url": "...", "name": "RFQ.pdf"}],
    skip_existing=True
)
```

## 🚀 Örnek Senaryo

```python
from opportunity_runner import analyze_opportunity

# 1. Fırsat kodu: 140D0424Q0292
# 2. SAM.gov Notice ID: 57cd76db400c4e7ca895d40bf6454173
# 3. Form kriterleri: Room capacity, FAR compliance

result = analyze_opportunity(
    base_dir=".",
    opportunity_code="140D0424Q0292",
    notice_id="57cd76db400c4e7ca895d40bf6454173",
    form_data={
        "evaluation_focus": [
            "Room capacity and ADA compliance",
            "FAR/DFAR compliance clauses"
        ]
    },
    download_from_sam_gov=True
)

# Çıktı:
# opportunities/140D0424Q0292/report.json
# opportunities/140D0424Q0292/summary.md
```

## 📝 Entegrasyon

### Streamlit UI

`guided_analysis.py` içinde `start_ai_analysis()` fonksiyonu otomatik olarak `opportunity_runner` kullanır:

```python
# UI'da "Analizi Başlat" butonuna tıklandığında
result = analyze_opportunity(
    base_dir=".",
    opportunity_code=opportunity_code,
    notice_id=notice_id,
    form_data=st.session_state.get('form_data', {}),
    download_from_sam_gov=True
)
```

## ⚠️ Notlar

- Fırsat kodu güvenli klasör adına çevrilir (özel karakterler temizlenir)
- Mevcut dosyalar atlanır (idempotent davranış)
- SAM.gov entegrasyonu için `SAM_API_KEY` gerekir
- Form verileri yoksa genel analiz yapılır

---

**MergenLite** - Federal İhale Analiz Sistemi

