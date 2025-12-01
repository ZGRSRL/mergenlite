# GÜÇLENDİRİLMİŞ DEPLOY KOMUTU
# RAM: 1Gi, CPU: 2
# Kullanım: .\deploy_guclendirilmis.ps1

# 1. Değişkenleri Hazırla
$CONN_NAME = "gen-lang-client-0307562385:europe-west1:mergenlite-db-instance"
$DB_URL = "postgresql+asyncpg://postgres:Mergen2025GucluSifre!@/mergenlite_prod?host=/cloudsql/$CONN_NAME"

# SAM_API_KEY - Gerçek değeri buraya yazın
# SAM.gov'dan API key almak için: https://api.sam.gov/api_key
$SAM_API_KEY = "BURAYA_SAM_API_KEY_YAZ"

Write-Host "========================================" -ForegroundColor Green
Write-Host "MergenLite GÜÇLENDİRİLMİŞ Deployment" -ForegroundColor Green
Write-Host "RAM: 1Gi | CPU: 2" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 2. GÜÇLENDİRİLMİŞ DEPLOY KOMUTU (--memory 1Gi Eklendi)
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host ""

gcloud run deploy mergenlite-backend `
  --source ./mergen/api `
  --platform managed `
  --region europe-west1 `
  --allow-unauthenticated `
  --port 8080 `
  --timeout 3600 `
  --memory 1Gi `
  --cpu 2 `
  --add-cloudsql-instances $CONN_NAME `
  --set-env-vars "DATABASE_URL=$DB_URL" `
  --set-env-vars "AMADEUS_CLIENT_ID=mA1DG4KGPryyvo9AyMztUOvEb4lhxrjV" `
  --set-env-vars "AMADEUS_CLIENT_SECRET=wrQkpsgfZWNH24nD" `
  --set-env-vars "AMADEUS_ENV=production" `
  --set-env-vars "OPENAI_API_KEY=YOUR_OPENAI_API_KEY" `
  --set-env-vars "SMTP_SERVER=smtp.gmail.com" `
  --set-env-vars "SMTP_PORT=587" `
  --set-env-vars "SMTP_USERNAME=arl.zgr@gmail.com" `
  --set-env-vars "SMTP_PASSWORD=yaua qkmg xrqi slea" `
  --set-env-vars "SAM_API_KEY=$SAM_API_KEY"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete! 🚀" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Service URL'i al
Write-Host "Service URL:" -ForegroundColor Cyan
gcloud run services describe mergenlite-backend --region europe-west1 --format="value(status.url)"
Write-Host ""

