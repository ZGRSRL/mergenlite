# ZgrWise - React + Material UI Migration - Tamamlandı! 🎉

NiceGUI'den React + Material UI'ye geçiş tamamlandı. ZgrWise branding ile güncellendi.

## 📁 Yapı

```
project-root/
├── backend/ (FastAPI)
│   └── mergen/api/app/
│       ├── main.py (FastAPI app)
│       └── routes/
│           └── pipeline.py (YENİ - Pipeline endpoints)
│
└── frontend/ (React + MUI)
    ├── package.json
    ├── vite.config.ts
    ├── src/
    │   ├── App.tsx (Ana component)
    │   ├── components/
    │   │   ├── SowForm.tsx (SOW Generator formu)
    │   │   ├── LogsPanel.tsx (Log paneli)
    │   │   └── PdfList.tsx (PDF listesi)
    │   └── api/
    │       └── pipeline.ts (API client)
```

## 🚀 Kurulum

### Backend (FastAPI)

```bash
# Backend zaten çalışıyor olmalı
cd mergen/api
uvicorn app.main:app --reload --port 8000
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000
Backend API: http://localhost:8000

## ✨ Özellikler

### SOW Generator Form
- ✅ RFQ PDF upload
- ✅ Seating Chart PDF upload (optional)
- ✅ Pipeline seçimi (v2, v3, Hotel SOW Template)
- ✅ Template engine checkbox
- ✅ Real-time progress

### Logs Panel
- ✅ Pipeline loglarını gösterir
- ✅ Real-time güncelleme
- ✅ Terminal-style görünüm

### PDF List
- ✅ Oluşturulan SOW PDF'lerini listeler
- ✅ Download linkleri
- ✅ Timestamp ve file size

## 🔌 API Endpoints

### POST `/api/pipeline/run`
RFQ PDF'den SOW oluşturur.

**Request:**
- `rfq_pdf`: File (required)
- `seating_chart_pdf`: File (optional)
- `use_template_engine`: bool (default: true)
- `pipeline_version`: "v2" | "v3" | "hotel"

**Response:**
```json
{
  "status": "ok",
  "sow_pdf_path": "outputs/sow_xxx.pdf",
  "sow_html_path": "outputs/sow_xxx.html",
  "logs": ["log1", "log2"]
}
```

### GET `/api/pipeline/files/sow-pdf?path=...`
SOW PDF dosyasını döndürür.

### GET `/api/pipeline/files/list`
Tüm SOW PDF dosyalarını listeler.

## 🎨 Tasarım

- Material UI v5
- Federal blue theme (#0033A0)
- Responsive design
- Professional kurumsal görünüm

## 📝 Notlar

- NiceGUI artık kullanılmıyor (internal debug için tutulabilir)
- Backend FastAPI ile çalışıyor
- Frontend React + MUI ile çalışıyor
- Production-ready yapı

## 🐳 Docker

```bash
docker-compose -f docker-compose.frontend.yml up
```

## ✅ Sonraki Adımlar

1. ✅ Backend API endpoints oluşturuldu
2. ✅ React frontend yapısı kuruldu
3. ✅ SOW Generator formu oluşturuldu
4. ✅ Log paneli eklendi
5. ✅ PDF listesi eklendi
6. ⏳ Docker compose setup
7. ⏳ Production build
8. ⏳ Oracle Cloud deployment

