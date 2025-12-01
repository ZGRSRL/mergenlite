# SAM_API_KEY'i Cloud Run servisine ekle/güncelle
# Kullanım: .\update_sam_api_key.ps1

$gcloud = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

Write-Host "========================================" -ForegroundColor Green
Write-Host "SAM_API_KEY Guncelleme" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# SAM_API_KEY'i kullanıcıdan al
$SAM_API_KEY = Read-Host "SAM_API_KEY degerini girin (https://api.sam.gov/api_key adresinden alabilirsiniz)"

if ([string]::IsNullOrWhiteSpace($SAM_API_KEY)) {
    Write-Host "Hata: SAM_API_KEY bos olamaz!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "SAM_API_KEY guncelleniyor..." -ForegroundColor Yellow

# Mevcut environment variable'ları al ve SAM_API_KEY'i ekle/güncelle
& $gcloud run services update mergenlite-backend `
  --region europe-west1 `
  --update-env-vars "SAM_API_KEY=$SAM_API_KEY"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SAM_API_KEY Basariyla Guncellendi!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Servis yeniden baslatiliyor..." -ForegroundColor Cyan
    Write-Host "Test icin: .\test_manual_trigger.ps1" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Hata: SAM_API_KEY guncellenemedi!" -ForegroundColor Red
    Write-Host "Exit Code: $LASTEXITCODE" -ForegroundColor Yellow
}

