# 🔧 Troubleshooting Guide - İlan Bulunamama Sorunu

## ❌ Sorun: İlan ID'leri Bulunamıyor

### Test Edilen ID'ler:
- `W50S7526QA010` (Notice ID)
- `086008536ec84226ad9de043dc738d06` (Opportunity ID)

### 🔍 Olası Nedenler ve Çözümler

#### 1. API Quota Limit Aşıldı (429 Hatası)

**Belirtiler:**
- "Message throttled out" hatası
- "You have exceeded your quota" mesajı
- Sonraki erişim tarihi: 2025-Nov-06 00:00:00+0000 UTC

**Çözümler:**
1. **Bekleyin**: Yarın (6 Kasım) 00:00 UTC'den sonra tekrar deneyin
2. **Farklı IP**: VPN veya mobil hotspot kullanarak farklı IP'den deneyin
3. **SAM.gov Kontrolü**: SAM.gov hesabınızda API kullanım limitinizi kontrol edin
4. **Cache Kullanın**: Daha önce aranan ilanlar cache'den gelir (6 saat)

**Test:**
```bash
python test_quota.py
```

#### 2. İlan Süresi Dolmuş

**Belirtiler:**
- İlan 730 günden eski olabilir
- API sadece son 2 yıl içindeki ilanları gösterir

**Çözümler:**
1. SAM.gov'da ilanın durumunu kontrol edin
2. İlanın yayın tarihini kontrol edin
3. İlan aktif mi kontrol edin

#### 3. Yanlış ID Formatı

**Notice ID Formatı:**
- Örnek: `W50S7526QA010`
- Format: Genellikle harf ve rakam kombinasyonu
- SAM.gov sayfasında "Notice ID" veya "Solicitation Number" olarak görünür

**Opportunity ID Formatı:**
- Örnek: `086008536ec84226ad9de043dc738d06`
- Format: 32 karakterlik hex kod
- SAM.gov URL'sinde görünür: `/opp/086008536ec84226ad9de043dc738d06/view`

**Çözümler:**
1. SAM.gov sayfasından Notice ID'yi kopyalayın
2. URL'deki Opportunity ID yerine Notice ID kullanın
3. ID'deki boşlukları ve özel karakterleri kontrol edin

#### 4. API Key Sorunu

**Kontrol:**
```bash
python check_api_key.py
```

**Çözümler:**
1. `.env` dosyasında API key'in doğru olduğundan emin olun
2. Streamlit'i yeniden başlatın
3. Cache'i temizleyin: `streamlit cache clear`

## 🛠️ Debug Adımları

### 1. API Key Kontrolü
```bash
python check_api_key.py
```

### 2. Quota Kontrolü
```bash
python test_quota.py
```

### 3. Notice ID Testi
```bash
python test_notice_search.py W50S7526QA010
```

### 4. Streamlit Log Kontrolü
- Terminal'de Streamlit loglarını kontrol edin
- API yanıtlarını ve hata mesajlarını inceleyin

### 5. Cache Temizliği
```bash
streamlit cache clear
rm -rf .cache/*
```

## 📋 Manuel Kontrol

### SAM.gov'da İlan Kontrolü

1. **Notice ID için:**
   - https://sam.gov adresine gidin
   - "Contract Opportunities" bölümünde arayın
   - Notice ID'yi doğrudan arayın

2. **Opportunity ID için:**
   - URL'yi açın: `https://sam.gov/workspace/contract/opp/086008536ec84226ad9de043dc738d06/view`
   - Sayfada "Notice ID" bölümünden ID'yi kopyalayın
   - Notice ID ile arama yapın

## 🎯 Hızlı Çözümler

### Çözüm 1: Cache Kullan
```bash
# Cache'den önceki aramaları kontrol et
ls .cache/
```

### Çözüm 2: Farklı Tarih Aralığı
- Uygulamada "Son Günler" slider'ını artırın (90 güne kadar)
- Genel aramada daha geniş tarih aralığı kullanın

### Çözüm 3: Genel Arama
- "Genel Arama" bölümünü kullanın
- Keyword olarak Notice ID'yi girin
- NAICS kodu olmadan deneyin

## 📞 Yardım

Sorun devam ederse:
1. Terminal loglarını kontrol edin
2. Debug bilgilerini açın (Streamlit'te "🔍 Debug Bilgileri")
3. API key durumunu kontrol edin
4. Quota limitini kontrol edin

---

**Son Güncelleme**: 2025-11-05



