# Docker Temiz Başlatma Scripti
# PowerShell script

Write-Host "🐳 Docker Temiz Başlatma" -ForegroundColor Green
Write-Host ""

# 1. Klasöre geç
Write-Host "📁 Klasöre geçiliyor..." -ForegroundColor Yellow
Set-Location mergen
if (-not $?) {
    Write-Host "❌ mergen klasörü bulunamadı!" -ForegroundColor Red
    exit 1
}

# 2. Eski konteynerleri indir
Write-Host "`n🧹 Eski konteynerleri indiriliyor..." -ForegroundColor Yellow
docker compose down --remove-orphans
if (-not $?) {
    Write-Host "⚠️  Bazı konteynerler zaten durmuş olabilir" -ForegroundColor Yellow
}

# 3. (Opsiyonel) Temiz derleme
$cleanBuild = Read-Host "`n🔨 Temiz derleme yapılsın mı? (y/n, varsayılan: n)"
if ($cleanBuild -eq "y" -or $cleanBuild -eq "Y") {
    Write-Host "🔨 Temiz derleme yapılıyor..." -ForegroundColor Yellow
    docker compose build --no-cache api streamlit
    if (-not $?) {
        Write-Host "❌ Build hatası!" -ForegroundColor Red
        exit 1
    }
}

# 4. Başlat
Write-Host "`n🚀 Servisler başlatılıyor..." -ForegroundColor Yellow
docker compose up -d --build
if (-not $?) {
    Write-Host "❌ Başlatma hatası!" -ForegroundColor Red
    exit 1
}

# 5. Durum kontrolü
Write-Host "`n📊 Container durumu:" -ForegroundColor Yellow
Start-Sleep -Seconds 3
docker compose ps

# 6. API log kontrolü
Write-Host "`n📋 API logları (son 20 satır):" -ForegroundColor Yellow
docker compose logs --tail=20 api

Write-Host "`n✅ Başlatma tamamlandı!" -ForegroundColor Green
Write-Host "`n🔍 Doğrulama komutları:" -ForegroundColor Cyan
Write-Host "   API Health: Invoke-RestMethod -Uri 'http://localhost:8000/api/health'" -ForegroundColor White
Write-Host "   Proxy Search: `$base = 'http://localhost:8000'; Invoke-RestMethod -Uri \"`$base/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100\"" -ForegroundColor White
Write-Host "`n🌐 URL'ler:" -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Streamlit: http://localhost:8501" -ForegroundColor White

