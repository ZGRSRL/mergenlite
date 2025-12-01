# Google Cloud SDK Installer Script
# Bu script gcloud CLI'yi indirip yukler

Write-Host "========================================" -ForegroundColor Green
Write-Host "Google Cloud SDK Installation" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Windows icin gcloud installer URL'i
$INSTALLER_URL = "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe"
$INSTALLER_PATH = "$env:TEMP\GoogleCloudSDKInstaller.exe"

Write-Host "1. Downloading Google Cloud SDK installer..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $INSTALLER_URL -OutFile $INSTALLER_PATH -UseBasicParsing
    Write-Host "   Download complete" -ForegroundColor Green
} catch {
    Write-Host "   Download failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manuel yukleme icin:" -ForegroundColor Yellow
    Write-Host "1. Tarayicida su adresi acin: https://cloud.google.com/sdk/docs/install" -ForegroundColor White
    Write-Host "2. Windows sekmesine gidin" -ForegroundColor White
    Write-Host "3. GoogleCloudSDKInstaller.exe dosyasini indirin" -ForegroundColor White
    Write-Host "4. Indirilen dosyayi calistirin" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "2. Starting installer..." -ForegroundColor Yellow
Write-Host "   Installer penceresi acilacak, lutfen talimatlari takip edin." -ForegroundColor Cyan
Write-Host ""

# Installer'i calistir
Start-Process -FilePath $INSTALLER_PATH -Wait

Write-Host ""
Write-Host "3. Verifying installation..." -ForegroundColor Yellow

# PATH'i yenile
$machinePath = [System.Environment]::GetEnvironmentVariable("Path","Machine")
$userPath = [System.Environment]::GetEnvironmentVariable("Path","User")
$env:Path = "$machinePath;$userPath"

# gcloud'un yuklu olup olmadigini kontrol et
Start-Sleep -Seconds 5
$gcloudPath = Get-Command gcloud -ErrorAction SilentlyContinue

if ($gcloudPath) {
    Write-Host "   gcloud CLI successfully installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Yeni bir PowerShell penceresi acin (PATH guncellemesi icin)" -ForegroundColor White
    Write-Host "2. gcloud auth login" -ForegroundColor White
    Write-Host "3. gcloud config set project gen-lang-client-0307562385" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "   gcloud command not found in PATH" -ForegroundColor Yellow
    Write-Host "   Yeni bir PowerShell penceresi acip tekrar deneyin" -ForegroundColor Cyan
    Write-Host "   Veya manuel olarak PATH'e ekleyin:" -ForegroundColor Cyan
    Write-Host "   C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
