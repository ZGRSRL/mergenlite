# 🚀 Streamlit Uygulamasını Çalıştırma Rehberi

## 📋 İçindekiler
1. [Uygulamayı Başlatma](#-uygulamayı-başlatma)
2. [Uygulamayı Kapatma](#-uygulamayı-kapatma)
3. [Uygulamayı Yeniden Başlatma](#-uygulamayı-yeniden-başlatma)
4. [Sorun Giderme](#-sorun-giderme)

---

## 🚀 Uygulamayı Başlatma

### Windows için:

**Yöntem 1: Batch dosyası ile (Önerilen)**
```bash
run.bat
```

**Yöntem 2: Manuel olarak**
```bash
streamlit run app.py
```

**Yöntem 3: Belirli bir port ile**
```bash
streamlit run app.py --server.port 8501
```

### Linux/Mac için:

**Yöntem 1: Shell script ile (Önerilen)**
```bash
chmod +x run.sh
./run.sh
```

**Yöntem 2: Manuel olarak**
```bash
streamlit run app.py
```

**Yöntem 3: Belirli bir port ile**
```bash
streamlit run app.py --server.port 8501
```

### 🎯 Başarılı Başlatma İşaretleri

Uygulama başarıyla başladığında terminalde şunu göreceksiniz:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.xxx:8501
```

Tarayıcınız otomatik olarak açılacak. Açılmazsa, yukarıdaki Local URL'yi tarayıcınıza yapıştırın.

---

## ⏹️ Uygulamayı Kapatma

### Yöntem 1: Terminal/Command Prompt'ta (Önerilen)
- **Windows/Linux/Mac**: Terminal penceresinde `Ctrl + C` tuşlarına basın
- Birden fazla kez basmanız gerekebilir

### Yöntem 2: Terminal Penceresini Kapatma
- Terminal penceresini kapatın (X butonuna tıklayın)
- **Not**: Bu yöntem arka planda çalışan process'leri bırakabilir

### Yöntem 3: Process'i Sonlandırma (Windows)
```powershell
# PowerShell'de
Get-Process | Where-Object {$_.ProcessName -eq "streamlit"} | Stop-Process
```

### Yöntem 4: Process'i Sonlandırma (Linux/Mac)
```bash
# Process ID'yi bul
ps aux | grep streamlit

# Process'i sonlandır (PID yerine gerçek process ID'yi yazın)
kill -9 <PID>
```

---

## 🔄 Uygulamayı Yeniden Başlatma

### Adım 1: Uygulamayı Kapatın
```bash
# Terminal'de Ctrl + C
```

### Adım 2: Cache'i Temizleyin (Opsiyonel ama önerilir)
```bash
# Streamlit cache'i temizle
streamlit cache clear
```

### Adım 3: Uygulamayı Yeniden Başlatın
```bash
# Windows
run.bat

# Linux/Mac
./run.sh

# veya manuel
streamlit run app.py
```

### 🎯 Ne Zaman Yeniden Başlatmalısınız?

Aşağıdaki durumlarda uygulamayı yeniden başlatın:
- ✅ `.env` dosyasında API key değişikliği yaptıysanız
- ✅ Yeni bağımlılık eklediyseniz (`pip install ...`)
- ✅ Kod değişiklikleri yaptıysanız ve değişiklikler görünmüyorsa
- ✅ "API key not found" hatası alıyorsanız
- ✅ Beklenmeyen hatalar görüyorsanız

---

## 🔧 Sorun Giderme

### ❌ "Port already in use" Hatası

**Sorun**: Port 8501 zaten kullanılıyor

**Çözüm 1: Farklı port kullan**
```bash
streamlit run app.py --server.port 8502
```

**Çözüm 2: Kullanılan portu kapat**
```bash
# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8501 | xargs kill -9
```

### ❌ "Module not found" Hatası

**Sorun**: Eksik Python paketi

**Çözüm**:
```bash
pip install -r requirements.txt
```

### ❌ "API key not found" Hatası

**Sorun**: `.env` dosyası yüklenmemiş

**Çözüm**:
1. `.env` dosyasının `mergen/.env` veya proje kök dizininde olduğundan emin olun
2. Streamlit'i kapatın (`Ctrl + C`)
3. Cache'i temizleyin: `streamlit cache clear`
4. Yeniden başlatın: `streamlit run app.py`

### ❌ Uygulama Yavaş Yükleniyor

**Çözüm**:
- Cache'i temizleyin: `streamlit cache clear`
- Tarayıcı cache'ini temizleyin
- Uygulamayı yeniden başlatın

### ❌ "Address already in use" Hatası

**Sorun**: Streamlit zaten çalışıyor

**Çözüm**:
1. Çalışan Streamlit process'ini bulun ve kapatın
2. Veya farklı bir port kullanın

---

## 📝 Hızlı Referans

| İşlem | Komut |
|-------|-------|
| **Başlat** | `streamlit run app.py` |
| **Durdur** | `Ctrl + C` (Terminal'de) |
| **Yeniden Başlat** | `Ctrl + C` → `streamlit run app.py` |
| **Cache Temizle** | `streamlit cache clear` |
| **Farklı Port** | `streamlit run app.py --server.port 8502` |
| **Detaylı Log** | `streamlit run app.py --logger.level=debug` |

---

## 🎓 İpuçları

1. **İlk Çalıştırma**: İlk çalıştırmada bağımlılıklar yüklenebilir, biraz bekleyin
2. **Hot Reload**: Kod değişikliklerinde Streamlit otomatik yenilenir (`.env` değişiklikleri hariç)
3. **Multiple Instances**: Aynı anda birden fazla Streamlit instance çalıştırabilirsiniz (farklı portlarla)
4. **Background Run**: Arka planda çalıştırmak için: `nohup streamlit run app.py &` (Linux/Mac)

---

## 📞 Yardım

Sorun yaşıyorsanız:
1. Terminal loglarını kontrol edin
2. `.env` dosyasının doğru yerde olduğundan emin olun
3. Tüm bağımlılıkların yüklü olduğunu kontrol edin: `pip list`
4. Streamlit versiyonunu kontrol edin: `streamlit --version`

---

**Son Güncelleme**: 2025-01-05

