# MergenLite - NiceGUI Versiyonu

Bu dosya, MergenLite uygulamasının **NiceGUI** framework'ü ile modern web arayüzü versiyonudur.

## 🚀 Özellikler

- **Modern UI**: Tailwind CSS tabanlı, Material Design bileşenleri
- **Responsive**: Tüm ekran boyutlarında çalışır
- **Dark Theme**: Görseldeki koyu tema desteği
- **Backend Uyumluluğu**: Mevcut Streamlit backend fonksiyonları korunur

## 📦 Kurulum

```bash
# NiceGUI bağımlılığını yükle
pip install nicegui>=1.4.0

# Veya requirements.txt'den
pip install -r requirements.txt
```

## 🎯 Kullanım

### NiceGUI Versiyonunu Çalıştırma

```bash
python app_nicegui.py
```

Uygulama otomatik olarak `http://localhost:8080` adresinde açılacaktır.

### Streamlit Versiyonunu Çalıştırma (Mevcut)

```bash
streamlit run app.py
```

## 🔄 Geçiş Notları

### Backend Fonksiyonları
Tüm backend fonksiyonları (`sync_opportunities_from_sam`, `load_opportunities_from_db`, vb.) **değişmeden** kullanılır. Sadece UI kısmı NiceGUI'ye çevrilmiştir.

### Önemli Farklar

1. **Session State**: Streamlit'in `st.session_state` yerine Python dictionary (`app_state`) kullanılır
2. **Rerun**: Streamlit'in `st.rerun()` yerine UI bileşenleri dinamik olarak güncellenir
3. **Layout**: Streamlit'in `st.columns()` yerine NiceGUI'nin `ui.row()` ve `ui.column()` kullanılır

## 📋 Sayfalar

### İlan Merkezi (Opportunity Center)
- ✅ Arama ve filtreleme
- ✅ Fırsat kartları
- ✅ Analiz başlatma
- ✅ Döküman indirme

### Dashboard (Yakında)
- ⏳ KPI kartları
- ⏳ AI Ajan durumu
- ⏳ Son aktiviteler

### Sonuçlar (Yakında)
- ⏳ Analiz sonuçları
- ⏳ Detaylı raporlar

## 🛠️ Geliştirme

### Yeni Sayfa Ekleme

```python
@ui.page('/yeni-sayfa')
def yeni_sayfa():
    ui.label('Yeni Sayfa')
    # ...
```

### Backend Fonksiyon Kullanımı

```python
from app import sync_opportunities_from_sam

def my_function():
    sync_opportunities_from_sam("721110", days_back=30)
    ui.notify("✅ Tamamlandı!", type='positive')
```

## 📝 Notlar

- NiceGUI versiyonu **experimental** durumdadır
- Streamlit versiyonu hala **production-ready** ve aktif olarak kullanılmaktadır
- Her iki versiyon da aynı backend fonksiyonlarını kullanır
- Database ve API entegrasyonları her iki versiyonda da çalışır

## 🐛 Sorun Giderme

### Import Hataları
Eğer backend import hataları alırsanız, `app.py` dosyasının aynı dizinde olduğundan emin olun.

### Port Çakışması
NiceGUI varsayılan olarak port 8080 kullanır. Değiştirmek için:
```python
ui.run(port=8081)
```

## 📚 Kaynaklar

- [NiceGUI Dokümantasyonu](https://nicegui.io/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Material Icons](https://fonts.google.com/icons)

