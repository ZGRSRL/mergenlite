# MergenLite

SAM.gov odaklý RFQ analizi ve SOW üretimi için lite platform.

## Mimari

- **Frontend**: React (Vite) / `frontend/`
- **Backend**: FastAPI / `mergen/api/app`
- **Opsiyonel**: Streamlit prototip (`app.py`) yalnýzca iç kullaným için

## Lokal Kurulum

### Backend
```bash
cd mergen/api
pip install -e .
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Docker Kurulumu

1. `.env` dosyasýný kökte oluþturun (varsa `.env.example` kopyalayýn). `SAM_API_KEY`, Postgres bilgileri vb. ekleyin.
2. Streamlit için kullanýlan eski Dockerfile kaldýrýldý; yerine backend/frontend için ayrý Dockerfile’lar eklendi.
3. Tek komutla tüm sistemi çalýþtýrmak için:
```bash
docker compose up --build
```
(Öncesinde Docker Desktop çalýþýyor olmalý.)

### Servisler
- `db`: Postgres 15 (veri `db_data` volume’unda tutulur)
- `backend`: FastAPI + Alembic migrations (`mergen/api/Dockerfile`)
- `frontend`: React build + Nginx (`frontend/Dockerfile`)

Portlar:
- Backend API: http://localhost:8000
- Frontend UI: http://localhost:3000

## Çalýþma Adýmlarý
1. **Sync**: `/api/opportunities/sync` (UI’deki “Sync” butonu) SAM’den ilan çekip DB’ye yazar.
2. **Guided Analysis**: `frontend/src/components/GuidedAnalysis.tsx` gerçek API verilerini tüketir, karar cache/timeline gösterir.
3. **Pipeline/PDF**: `mergen/api/app/services/pipeline_service.py` placeholder çýktýlar üretir; gerçek AutoGen ajanlarý baðlanabilir.

## Notlar
- `.env.production` dosyasý Docker için kullanýlabilir; compose `.env` deðerlerini okur.
- Docker Desktop yüklü deðilse `docker compose up` hata verir (Windows’ta WSL integration gerekli).
- Yol haritasý ilerlemesi için `ROADMAP_PROGRESS.md` dosyasýný kontrol edin.
