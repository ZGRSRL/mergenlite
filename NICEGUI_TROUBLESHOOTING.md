# NiceGUI Sorun Giderme

## 404 "Not Found" Hatası

Eğer `localhost:8080/opportunities` gibi sayfalara gittiğinizde 404 hatası alıyorsanız:

### Çözüm 1: Uygulamayı Yeniden Başlatın

1. **Mevcut uygulamayı durdurun:**
   - Terminal'de `Ctrl+C` tuşlarına basın
   - Veya PowerShell'de:
     ```powershell
     Get-Process python | Where-Object {$_.MainWindowTitle -like "*NiceGUI*"} | Stop-Process -Force
     ```

2. **Yeniden başlatın:**
   ```bash
   python app_nicegui.py
   ```

### Çözüm 2: Port Çakışması

Eğer port 8080 başka bir uygulama tarafından kullanılıyorsa:

1. **Farklı bir port kullanın:**
   ```python
   ui.run(port=8081)  # app_nicegui.py dosyasında
   ```

2. **Veya mevcut process'i durdurun:**
   ```powershell
   netstat -ano | findstr :8080
   taskkill /PID <PID_NUMARASI> /F
   ```

### Çözüm 3: Sayfa Route'larını Kontrol Edin

Tüm sayfalar `@ui.page()` decorator'ı ile tanımlı olmalı:

- ✅ `@ui.page('/')` - Dashboard
- ✅ `@ui.page('/opportunities')` - İlan Merkezi
- ✅ `@ui.page('/results')` - Sonuçlar
- ✅ `@ui.page('/analysis')` - AI Analiz

### Çözüm 4: Test Sayfası

`http://localhost:8080/test` adresine giderek route'ların çalışıp çalışmadığını test edebilirsiniz.

## Sayfa Yönlendirme

NiceGUI'de sayfa yönlendirme için:

```python
# Buton ile
ui.button('Git', on_click=lambda: ui.open('/opportunities'))

# Link ile
ui.link('İlan Merkezi', '/opportunities')
```

## Debug Modu

Uygulamayı debug modunda çalıştırmak için:

```python
ui.run(port=8080, reload=True, show=True)
```

`reload=True` ile kod değişikliklerinde otomatik yeniden yükleme yapılır.

## Yaygın Hatalar

1. **Import Hatası**: Backend modüllerinin (`app.py`, `sam_integration.py`) mevcut olduğundan emin olun
2. **Database Hatası**: Database bağlantısı yoksa bazı özellikler çalışmayabilir (normal)
3. **API Key Hatası**: SAM_API_KEY yoksa API özellikleri çalışmaz (normal)

## Yardım

Sorun devam ederse:
1. Terminal çıktısını kontrol edin (hata mesajları)
2. Browser console'u kontrol edin (F12)
3. `http://localhost:8080/test` sayfasını deneyin

