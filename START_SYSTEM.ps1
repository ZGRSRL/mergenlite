# MergenLite Sistem Başlatma Scripti
# PowerShell script

Write-Host "🚀 MergenLite Sistem Başlatılıyor..." -ForegroundColor Green

# 1. Redis başlat
Write-Host "`n📦 Redis başlatılıyor..." -ForegroundColor Yellow
docker-compose -f mergen/docker-compose.yml up -d redis
Start-Sleep -Seconds 2

# 2. Cache temizliği
Write-Host "`n🧹 Cache temizleniyor..." -ForegroundColor Yellow
Remove-Item -Recurse -Force .cache -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✅ Cache temizlendi" -ForegroundColor Green

# 3. Alembic migration
Write-Host "`n📊 Database migration..." -ForegroundColor Yellow
Set-Location mergen/api
alembic upgrade head
Set-Location ../..

# 4. API başlat (arka planda)
Write-Host "`n🌐 API başlatılıyor (arka plan)..." -ForegroundColor Yellow
Write-Host "   Komut: cd mergen/api && uvicorn app.main:app --reload" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor Cyan

# 5. UI başlat (arka planda)
Write-Host "`n🎨 UI başlatılıyor (arka plan)..." -ForegroundColor Yellow
Write-Host "   Komut: cd mergen && streamlit run app.py" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:8501" -ForegroundColor Cyan

Write-Host "`n✅ Sistem hazır!" -ForegroundColor Green
Write-Host "`n📋 Manuel başlatma komutları:" -ForegroundColor Yellow
Write-Host "   API: cd mergen/api && uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "   UI:  cd mergen && streamlit run app.py" -ForegroundColor White
Write-Host "`n🧪 Test komutları:" -ForegroundColor Yellow
Write-Host "   curl http://localhost:8000/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100" -ForegroundColor White
Write-Host "   curl http://localhost:8000/api/proxy/opportunities/noticedesc?id=70LGLY25QGLB00090" -ForegroundColor White

