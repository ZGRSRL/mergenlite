# Cloud Scheduler Setup Script
# Kullanım: .\setup_scheduler.ps1
# Her sabah 07:00'de otomatik tarama yapacak

$gcloud = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Cloud Scheduler Job Olusturuluyor" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Service URL'ini dinamik olarak al
Write-Host "Service URL aliniyor..." -ForegroundColor Yellow
$SERVICE_URL = & $gcloud run services describe mergenlite-backend --region europe-west1 --format "value(status.url)"
if (-not $SERVICE_URL) {
    Write-Host "❌ Service URL alinamadi! Servis calisiyor mu kontrol edin." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Service URL: $SERVICE_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Schedule: Her sabah 07:00 (Europe/Istanbul)" -ForegroundColor Cyan
Write-Host "Endpoint: $SERVICE_URL/api/jobs/daily-scan" -ForegroundColor Cyan
Write-Host "NAICS Code: 721110 (Hotel/Motel)" -ForegroundColor Cyan
Write-Host ""

# Cloud Scheduler API'yi etkinleştir
Write-Host "Cloud Scheduler API etkinlestiriliyor..." -ForegroundColor Yellow
& $gcloud services enable cloudscheduler.googleapis.com --project gen-lang-client-0307562385
Start-Sleep -Seconds 5

# Önce mevcut job'ı silmeyi dene (varsa)
Write-Host "Mevcut job kontrol ediliyor..." -ForegroundColor Yellow
& $gcloud scheduler jobs delete daily-hotel-scan --location europe-west1 --quiet 2>$null

Write-Host ""
Write-Host "Yeni job olusturuluyor..." -ForegroundColor Yellow

# Job oluştur (naics_code kullanarak)
$bodyJson = '{\"naics_code\": \"721110\", \"days_back\": 1, \"limit\": 10, \"force_refresh\": false}'
& $gcloud scheduler jobs create http daily-hotel-scan `
  --schedule "0 7 * * *" `
  --uri "$SERVICE_URL/api/jobs/daily-scan" `
  --http-method POST `
  --headers "Content-Type=application/json" `
  --message-body $bodyJson `
  --time-zone "Europe/Istanbul" `
  --location europe-west1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Cloud Scheduler Job Basariyla Olusturuldu!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Job Detaylari:" -ForegroundColor Cyan
    & $gcloud scheduler jobs describe daily-hotel-scan --location europe-west1
} else {
    Write-Host ""
    Write-Host "Job olusturulurken hata olustu!" -ForegroundColor Red
    Write-Host "Exit Code: $LASTEXITCODE" -ForegroundColor Yellow
}
