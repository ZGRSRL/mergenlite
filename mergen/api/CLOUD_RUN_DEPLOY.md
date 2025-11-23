# Cloud Run Deployment Guide

## Ön Hazırlık

### 1. GCP Proje Oluşturma
```bash
# GCP Console'dan yeni proje oluştur veya mevcut projeyi kullan
gcloud projects create your-project-id --name="MergenLite"
gcloud config set project your-project-id
```

### 2. Gerekli API'leri Aktifleştir
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com  # Cloud SQL için
```

### 3. Cloud SQL Instance Oluştur (Production Database)
```bash
# PostgreSQL instance oluştur
gcloud sql instances create mergenlite-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=europe-west1

# Database oluştur
gcloud sql databases create zgr_ai --instance=mergenlite-db

# User oluştur
gcloud sql users create postgres \
  --instance=mergenlite-db \
  --password=YOUR_SECURE_PASSWORD
```

## Deployment

### Yöntem 1: PowerShell Script (Windows)
```powershell
cd d:\Mergenlite
.\mergen\api\cloud_run_deploy.ps1 -ProjectId "your-project-id"
```

### Yöntem 2: Manual gcloud Command
```bash
gcloud run deploy mergenlite-backend \
  --source ./mergen/api \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "OPENAI_API_KEY=sk-...,AMADEUS_API_KEY=...,AMADEUS_API_SECRET=...,POSTGRES_HOST=your-project-id:europe-west1:mergenlite-db,POSTGRES_USER=postgres,POSTGRES_PASSWORD=...,POSTGRES_DB=zgr_ai,POSTGRES_PORT=5432,AMADEUS_ENV=production,PORT=8080,SMTP_HOST=smtp.gmail.com,SMTP_USERNAME=...,SMTP_PASSWORD=...,SMTP_PORT=587,SMTP_USE_TLS=true,PIPELINE_NOTIFICATION_EMAIL=..."
```

## Gerekli Environment Variables

### Zorunlu (Required)
- `OPENAI_API_KEY`: OpenAI API anahtarı
- `AMADEUS_API_KEY`: Amadeus API Client ID
- `AMADEUS_API_SECRET`: Amadeus API Client Secret
- `POSTGRES_HOST`: Cloud SQL connection name (format: `project:region:instance`)
- `POSTGRES_USER`: Database kullanıcı adı
- `POSTGRES_PASSWORD`: Database şifresi
- `POSTGRES_DB`: Database adı
- `POSTGRES_PORT`: Database portu (genelde 5432)
- `PORT`: 8080 (Cloud Run standardı)

### Opsiyonel (Optional)
- `SMTP_HOST`: SMTP sunucu adresi
- `SMTP_USERNAME`: SMTP kullanıcı adı
- `SMTP_PASSWORD`: SMTP şifresi
- `SMTP_PORT`: SMTP portu (genelde 587)
- `SMTP_USE_TLS`: true/false
- `PIPELINE_NOTIFICATION_EMAIL`: E-posta bildirim adresi
- `AMADEUS_ENV`: production/test

## Cloud SQL Connection

Cloud Run'dan Cloud SQL'e bağlanmak için:

1. **Cloud SQL Proxy kullan (önerilen)**
```bash
gcloud run deploy mergenlite-backend \
  --add-cloudsql-instances=your-project-id:europe-west1:mergenlite-db \
  ...
```

2. **Public IP ile bağlan (daha az güvenli)**
   - Cloud SQL instance'a public IP ekle
   - Authorized networks'e Cloud Run IP'lerini ekle

## Deployment Sonrası

1. **Service URL'i al**
```bash
gcloud run services describe mergenlite-backend \
  --region europe-west1 \
  --format="value(status.url)"
```

2. **Health check**
```bash
curl https://your-service-url.run.app/api/health
```

3. **Logları izle**
```bash
gcloud run services logs read mergenlite-backend --region europe-west1
```

## Troubleshooting

### Container başlamıyor
- Logları kontrol et: `gcloud run services logs read mergenlite-backend --region europe-west1`
- Environment variables'ları kontrol et
- Database bağlantısını test et

### Database bağlantı hatası
- Cloud SQL instance'ın çalıştığından emin ol
- Connection name formatını kontrol et: `project:region:instance`
- Cloud SQL Proxy kullanıyorsan `--add-cloudsql-instances` parametresini ekle

### Port hatası
- PORT environment variable'ının 8080 olduğundan emin ol
- Cloud Run otomatik olarak PORT'u set eder, ama manuel set etmek güvenli

