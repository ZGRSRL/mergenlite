# Proxy Endpoint Test Script
# PowerShell script for testing proxy endpoints

$base = "http://localhost:8000"
Write-Host "🚀 Proxy Endpoint Test" -ForegroundColor Green
Write-Host "Base URL: $base`n" -ForegroundColor Cyan

# 1. Health check
Write-Host "1️⃣ Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$base/api/health" -Method GET
    Write-Host "✅ API is running" -ForegroundColor Green
    $health | ConvertTo-Json
} catch {
    Write-Host "❌ API is not running. Please start it first:" -ForegroundColor Red
    Write-Host "   cd mergen/api && uvicorn app.main:app --reload" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n2️⃣ General Search (proxy/search)..." -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100" -Method GET
    Write-Host "✅ Search successful" -ForegroundColor Green
    Write-Host "   Total: $($r.total)" -ForegroundColor Cyan
    Write-Host "   Results Count: $(($r.results).Count)" -ForegroundColor Cyan
    Write-Host "   Saved to DB: $($r.saved)" -ForegroundColor Yellow
    
    # Get headers
    $w = Invoke-WebRequest -Uri "$base/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100"
    Write-Host "`n   Headers:" -ForegroundColor Cyan
    if ($w.Headers.'X-Cache') { Write-Host "   X-Cache: $($w.Headers.'X-Cache')" -ForegroundColor White }
    if ($w.Headers.'X-Source') { Write-Host "   X-Source: $($w.Headers.'X-Source')" -ForegroundColor White }
    
    # Show first result
    if (($r.results).Count -gt 0) {
        Write-Host "`n   First Result:" -ForegroundColor Cyan
        $r.results[0] | Select-Object noticeId, title, naicsCode, postedDate | ConvertTo-Json
    }
} catch {
    Write-Host "❌ Search failed: $_" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 429) {
        Write-Host "   Rate limit hit. Wait 1-2 minutes and retry." -ForegroundColor Yellow
    }
}

Write-Host "`n3️⃣ Notice Details (proxy/noticedesc)..." -ForegroundColor Yellow
try {
    $notice = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/noticedesc?id=70LGLY25QGLB00090" -Method GET
    Write-Host "✅ Notice details retrieved" -ForegroundColor Green
    if ($notice.success) {
        Write-Host "   Success: $($notice.success)" -ForegroundColor Cyan
        if ($notice.items) {
            Write-Host "   Items Count: $(($notice.items).Count)" -ForegroundColor Cyan
        }
    }
    $notice | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Notice details failed: $_" -ForegroundColor Red
    Write-Host "   Trying with search first..." -ForegroundColor Yellow
    
    # Try to find notice ID via search
    try {
        $s = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/search?naics=721110&days_back=365&limit=100&keyword=70LGLY25QGLB00090" -Method GET
        $nid = ($s.results | Where-Object { $_.noticeId -like "*70LGLY25QGLB00090*" } | Select-Object -First 1).noticeId
        if ($nid) {
            Write-Host "   Found Notice ID: $nid" -ForegroundColor Cyan
            $notice2 = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/noticedesc?id=$nid" -Method GET
            $notice2 | ConvertTo-Json -Depth 3
        }
    } catch {
        Write-Host "   Search also failed: $_" -ForegroundColor Red
    }
}

Write-Host "`n✅ Test completed!" -ForegroundColor Green

