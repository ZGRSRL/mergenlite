# Hızlı Test Rehberi

## 🚀 Opportunity ID Testi

### Sorun
`086008536ec84226ad9de043dc738d06` gibi URL'deki Opportunity ID'ler SAM.gov workspace'inin internal ID'sidir ve search API'de görünmeyebilir.

### Çözüm

1. **SAM.gov sayfasından Notice ID'yi alın:**
   - İlan sayfasını açın: `https://sam.gov/workspace/contract/opp/086008536ec84226ad9de043dc738d06/view`
   - "Notice ID" veya "Solicitation Number" bölümünden ID'yi kopyalayın
   - Örnek: `W50S7526QA010`

2. **Notice ID ile arama yapın:**
   - Uygulamada Notice ID'yi girin
   - "İlan ID ile Ara" butonuna tıklayın

## 📋 Test Komutları

### 1. API Key Testi
```bash
python test_api_key.py
```

### 2. Cache Testi
```bash
python test_cache.py
```

### 3. Optimizasyon Doğrulama
```bash
python test_optimization.py
```

## ✅ Beklenen Sonuçlar

- API Key yüklendi ✅
- Cache mekanizması çalışıyor ✅
- Limit optimizasyonları aktif ✅
- Notice ID ile arama çalışıyor ✅

## ⚠️ Notlar

- Opportunity ID (32 karakterlik hex) = SAM.gov workspace ID (internal)
- Notice ID (örn: W50S7526QA010) = Search API'de arama yapılabilir
- Her zaman Notice ID ile arama yapın!

