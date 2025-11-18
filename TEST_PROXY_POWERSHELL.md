# 🧪 Proxy Test - PowerShell Komutları

## ⚠️ Önemli Notlar

1. **$base değişkeni**: Her PowerShell oturumunda ayrı set edilmeli
2. **API çalışıyor olmalı**: `cd mergen/api && uvicorn app.main:app --reload`
3. **429 hatası**: Rate limiting çalışıyor, 1-2 dakika bekleyip tekrar deneyin

## 📋 Doğru Test Komutları

### 1. Temel Ayar
```powershell
$base = "http://localhost:8000"
```

### 2. Genel Arama (Proxy Search)
```powershell
# Search request
$r = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100" -Method GET

# Results
Write-Host "Total: $($r.total)"
Write-Host "Results: $(($r.results).Count)"
Write-Host "Saved to DB: $($r.saved)"

# JSON output
$r | ConvertTo-Json -Depth 5
```

### 3. Header'ları Görmek
```powershell
$w = Invoke-WebRequest -Uri "$base/api/proxy/opportunities/search?naics=721110&days_back=30&limit=100"

# Headers
$w.Headers.'X-Cache'
$w.Headers.'X-Source'
$w.Headers.'X-Rate-Limit-Remaining'
```

### 4. Notice Details
```powershell
# Notice ID ile
$notice = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/noticedesc?id=70LGLY25QGLB00090" -Method GET
$notice | ConvertTo-Json -Depth 6

# URL ile
$notice = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/noticedesc?id=https://sam.gov/workspace/contract/opp/4af381a2c95d4e5e87b21a105a72af12/view" -Method GET
$notice | ConvertTo-Json -Depth 6
```

### 5. Geniş Arama ile ID Bulma
```powershell
# Önce arama yap
$s = Invoke-RestMethod -Uri "$base/api/proxy/opportunities/search?naics=721110&days_back=365&limit=100&keyword=70LGLY25QGLB00090" -Method GET

# Notice ID'yi bul
$nid = ($s.results | Select-Object -First 1).noticeId

# Detayları çek
if ($nid) {
    Invoke-RestMethod -Uri "$base/api/proxy/opportunities/noticedesc?id=$nid" -Method GET | ConvertTo-Json -Depth 6
}
```

## 🚀 Hızlı Test Script

`test_proxy.ps1` dosyasını çalıştırın:
```powershell
powershell -ExecutionPolicy Bypass -File test_proxy.ps1
```

## 📊 Beklenen Sonuçlar

### ✅ Başarılı Response
```json
{
  "total": 150,
  "results": [
    {
      "noticeId": "W50S7526QA010",
      "title": "Hotel Management Services",
      "naicsCode": "721110",
      "postedDate": "2025-01-15",
      "source": "sam_live"
    }
  ],
  "saved": 150
}
```

### Headers
- `X-Cache`: MISS (ilk istek) veya HIT (cache'den)
- `X-Source`: sam_live, cache, veya db
- `X-Rate-Limit-Remaining`: 2 (kalan token sayısı)

### ⚠️ 429 Hatası
```json
{
  "detail": "Rate limited. Please retry."
}
```
**Çözüm**: 1-2 dakika bekleyip tekrar deneyin

### ⚠️ 503 Hatası (Circuit Breaker)
```json
{
  "detail": "Service temporarily unavailable (circuit open)"
}
```
**Çözüm**: 60 saniye bekleyip tekrar deneyin

## 🔍 Debug

### API Log Kontrolü
API terminalinde şunları görmelisiniz:
```
INFO: API Request (offset=0, limit=1000): {...}
INFO: 📊 Toplam kayıt: 150
INFO: ✅ 150 kayıt alındı (toplam: 150)
INFO: ✅ Toplam 150 fırsat bulundu
```

### Redis Kontrolü
```powershell
docker exec -it mergen-redis-1 redis-cli
> KEYS *
> GET "search:naics=721110&days_back=30&limit=100&keyword="
```

## 📝 Notlar

- **GSA Client 429**: GSA client'tan gelen 429 logları normal (fallback mekanizması)
- **Proxy Rate Limiting**: Proxy kendi rate limiting'i var (1 req/sec, burst 3)
- **Cache**: İkinci istekte `X-Cache: HIT` görmelisiniz
- **DB Save**: `saved` alanı DB'ye yazılan kayıt sayısını gösterir

---

**Test Script**: `test_proxy.ps1`  
**API Docs**: http://localhost:8000/docs

