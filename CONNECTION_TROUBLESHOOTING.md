# 🔧 Bağlantı Sorunu Giderme Rehberi

## ❌ ERR_CONNECTION_REFUSED Hatası

### 🔍 Durum Kontrolü

Streamlit çalışıyor mu kontrol edin:
```powershell
netstat -ano | findstr :8501
```

Eğer port dinlemiyorsa:
```powershell
# Streamlit'i başlat
cd d:\Mergenlite
streamlit run app.py --server.port 8501
```

### 🛠️ Çözümler

#### 1. Firewall Kontrolü
Windows Firewall port'u engelliyor olabilir:
```powershell
# Firewall exception ekle
netsh advfirewall firewall add rule name="Streamlit" dir=in action=allow protocol=TCP localport=8501
```

#### 2. Antivirus Kontrolü
Antivirus programı port'u engelliyor olabilir:
- Antivirus ayarlarında Python ve Streamlit'e izin verin
- Geçici olarak antivirus'ü devre dışı bırakıp test edin

#### 3. Farklı Port Kullan
8501 portu kullanılıyor olabilir:
```powershell
streamlit run app.py --server.port 8502
```
Sonra: http://localhost:8502

#### 4. Farklı Tarayıcı
- Chrome, Firefox, Edge gibi farklı tarayıcılar deneyin
- Private/Incognito mode kullanın

#### 5. Network Adresini Kullan
Localhost yerine network IP'sini kullanın:
```powershell
# IP adresinizi bulun
ipconfig | findstr IPv4
```
Sonra: `http://192.168.x.x:8501`

#### 6. Streamlit'i Yeniden Başlat
```powershell
# Tüm process'leri durdur
Get-Process | Where-Object {$_.ProcessName -eq "streamlit"} | Stop-Process -Force

# Yeniden başlat
cd d:\Mergenlite
streamlit run app.py
```

### 🧪 Test Adımları

1. **Port Kontrolü:**
   ```powershell
   netstat -ano | findstr :8501
   ```
   Port dinleniyorsa "LISTENING" görünür.

2. **Process Kontrolü:**
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -eq "streamlit"}
   ```
   Streamlit process'i görünmelidir.

3. **Browser Test:**
   - http://localhost:8501
   - http://127.0.0.1:8501
   - http://192.168.x.x:8501 (network IP)

### 📋 Alternatif Portlar

Eğer 8501 çalışmıyorsa:
- 8502
- 8503
- 8080
- 3000

### 🎯 Hızlı Çözüm

```powershell
# 1. Tüm process'leri durdur
Get-Process | Where-Object {$_.ProcessName -eq "streamlit" -or $_.ProcessName -eq "python"} | Stop-Process -Force

# 2. Farklı port ile başlat
cd d:\Mergenlite
streamlit run app.py --server.port 8502

# 3. Browser'da aç
# http://localhost:8502
```

---

**Son Güncelleme**: 2025-11-05

