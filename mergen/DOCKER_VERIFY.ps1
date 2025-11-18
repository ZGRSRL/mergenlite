# Docker Doğrulama Scripti
# PowerShell script

Write-Host "🔍 Docker Doğrulama" -ForegroundColor Green
Write-Host ""

$base = "http://localhost:8000"

# 1. Container durumu
Write-Host "1️⃣ Container durumu:" -ForegroundColor Yellow
docker compose ps
Write-Host ""

# 2. API Health Check
Write-Host "2️⃣ API Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$base/api/health" -Method GET
    Write-Host "✅ API çalışıyor" -ForegroundColor Green
    $health | ConvertTo-Json
} catch {
    Write-Host "❌ API çalışmıyor: $_" -ForegroundColor Red
}
Write-Host ""

# 3. Proxy Search Test
Write-Host "3️⃣ Proxy Search Test (NAICS 721110, 30 gün)..." -ForegroundColor Yellow
try {
    $search = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100" -Method GET
    Write-Host "✅ Search başarılı" -ForegroundColor Green
    Write-Host "   Total: $($search.total)" -ForegroundColor Cyan
    Write-Host "   Results Count: $(($search.results).Count)" -ForegroundColor Cyan
    Write-Host "   Saved to DB: $($search.saved)" -ForegroundColor Yellow
    
    if (($search.results).Count -gt 0) {
        Write-Host "`n   İlk sonuç:" -ForegroundColor Cyan
        $search.results[0] | Select-Object noticeId, title, naicsCode, postedDate | ConvertTo-Json
    }
} catch {
    Write-Host "❌ Search hatası: $_" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 429) {
        Write-Host "   Rate limit hit. 1-2 dakika bekleyip tekrar deneyin." -ForegroundColor Yellow
    }
}
Write-Host ""

# 4. Notice Details Test
Write-Host "4️⃣ Notice Details Test..." -ForegroundColor Yellow
try {
    $notice = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/noticedesc?id=70LGLY25QGLB00090" -Method GET
    Write-Host "✅ Notice details başarılı" -ForegroundColor Green
    if ($notice.success) {
        Write-Host "   Success: $($notice.success)" -ForegroundColor Cyan
        if ($notice.items) {
            Write-Host "   Items Count: $(($notice.items).Count)" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "⚠️  Notice details hatası (normal olabilir): $_" -ForegroundColor Yellow
}
Write-Host ""

# 5. API Docs kontrolü
Write-Host "5️⃣ API Docs:" -ForegroundColor Yellow
Write-Host "   Tarayıcıda aç: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   'proxy' tag'ı altında 2 endpoint görünmeli:" -ForegroundColor Cyan
Write-Host "   - GET /api/proxy/opportunities/search" -ForegroundColor White
Write-Host "   - GET /api/proxy/opportunities/noticedesc" -ForegroundColor White
Write-Host ""

# 6. Streamlit kontrolü
Write-Host "6️⃣ Streamlit:" -ForegroundColor Yellow
Write-Host "   Tarayıcıda aç: http://localhost:8501" -ForegroundColor Cyan
Write-Host "   'Fırsat Arama' sayfasında NAICS=721110, Son Günler=30 ile test edin" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ Doğrulama tamamlandı!" -ForegroundColor Green

