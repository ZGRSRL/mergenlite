# Cloud Run Deploy Script
# Kullanım: .\mergen\api\deploy_now.ps1

# Cloud SQL instance connection name (kendi değerlerinizle değiştirin)
$CONN_NAME = "gen-lang-client-0307562385:europe-west1:mergenlite-db"

# Environment variables
$ENV_VARS = @(
    "PORT=8080",
    "OPENAI_API_KEY=YOUR_OPENAI_API_KEY",
    "AMADEUS_API_KEY=mA1DG4KGPryyvo9AyMztUOvEb4lhxrjV",
    "AMADEUS_API_SECRET=wrQkpsgfZWNH24nD",
    "AMADEUS_ENV=production",
    "POSTGRES_HOST=$CONN_NAME",
    "POSTGRES_USER=postgres",
    "POSTGRES_PASSWORD=YOUR_DB_PASSWORD",  # Buraya Cloud SQL şifrenizi yazın
    "POSTGRES_DB=ZGR_AI",
    "POSTGRES_PORT=5432",
    "SMTP_HOST=smtp.gmail.com",
    "SMTP_PORT=587",
    "SMTP_USERNAME=arl.zgr@gmail.com",
    "SMTP_PASSWORD=yaua qkmg xrqi slea",
    "SMTP_USE_TLS=true"
)

# Environment variables string oluştur
$ENV_VARS_STRING = $ENV_VARS -join ","

Write-Host "========================================" -ForegroundColor Green
Write-Host "MergenLite Cloud Run Deployment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Deploy komutu
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host ""

gcloud run deploy mergenlite-backend `
  --source ./mergen/api `
  --platform managed `
  --region europe-west1 `
  --allow-unauthenticated `
  --port 8080 `
  --timeout 3600 `
  --memory 2Gi `
  --cpu 2 `
  --max-instances 10 `
  --add-cloudsql-instances $CONN_NAME `
  --set-env-vars $ENV_VARS_STRING

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Service URL'i al
Write-Host "Service URL:" -ForegroundColor Cyan
gcloud run services describe mergenlite-backend --region europe-west1 --format="value(status.url)"
Write-Host ""

