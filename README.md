# MergenAI Lite 🚀

Sadeleştirilmiş İlan Analiz Platformu - MergenAI'nin çekirdek iş akışına odaklanmış lite versiyonu.

## Özellikler

- 📋 **İlan Merkezi**: SAM.gov API v2 ile ilan arama ve filtreleme
- 📊 **Rehberli Analiz**: 4 aşamalı analiz workflow'u
  1. 📥 **Veri Çekme**: Metadata ve doküman indirme
  2. 📄 **Doküman İşleme**: PDF/DOCX metin çıkarımı
  3. 🤖 **RAG Muhakemesi**: LLM ile özellik çıkarımı
  4. 📊 **Final Rapor**: Analiz sonuçlarının özetlenmesi

## Kurulum

1. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

2. **Environment değişkenlerini ayarlayın:**
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

3. **Uygulamayı çalıştırın:**

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**Manuel:**
```bash
streamlit run app.py
```

📖 **Detaylı talimatlar için**: [STREAMLIT_GUIDE.md](STREAMLIT_GUIDE.md) dosyasına bakın.

## Kullanım

### İlan Merkezi
- SAM.gov'dan ilanları arayın ve filtreleyin
- İlanları analiz etmek için "Analiz Et" butonuna tıklayın

### Rehberli Analiz
1. **Aşama 1**: İlan metadata'sını ve ek dosyalarını çekin
2. **Aşama 2**: Dokümanları indirip işleyin (PDF/DOCX metin çıkarımı)
3. **Aşama 3**: RAG analizi ile gereksinimleri çıkarın
4. **Aşama 4**: Final raporu oluşturup indirin

## Yapılandırma

### SAM.gov API (Opsiyonel)
- `SAM_API_KEY`: SAM.gov API anahtarı
- API anahtarı olmadan da demo modu kullanılabilir

### OpenAI API (Opsiyonel)
- `OPENAI_API_KEY`: OpenAI API anahtarı
- API anahtarı olmadan da mock analiz kullanılır

## Gereksinimler

- Python 3.8+
- Streamlit 1.28+
- PDF işleme için: pdfplumber
- DOCX işleme için: python-docx
- RAG için (opsiyonel): sentence-transformers
- LLM için (opsiyonel): openai

## Lisans

Bu proje MergenAI platformunun lite versiyonudur.

