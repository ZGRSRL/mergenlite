# MergenLite 🚀

Sadeleştirilmiş İlan Analiz Platformu - MergenAI'nin çekirdek iş akışına odaklanmış lite versiyonu.

## 🌟 Özellikler

- 📋 **İlan Merkezi**: SAM.gov API v2 ile ilan arama ve filtreleme
- 📊 **Rehberli Analiz**: 4 aşamalı analiz workflow'u
  1. 📥 **Veri Çekme**: Metadata ve doküman indirme
  2. 📄 **Doküman İşleme**: PDF/DOCX metin çıkarımı
  3. 🤖 **RAG Muhakemesi**: LLM ile özellik çıkarımı
  4. 📊 **Final Rapor**: Analiz sonuçlarının özetlenmesi
- 🏨 **Otel Veritabanı**: Excel'den otomatik otel yükleme ve öneri sistemi
- 📝 **Teklif Oluşturma**: AI destekli teklif taslağı oluşturma
- 📄 **SOW Generator**: Statement of Work otomatik oluşturma
- 📊 **Detaylı Raporlar**: PDF ve JSON formatında analiz raporları

## 🚀 Hızlı Başlangıç

### Docker ile Kurulum (Önerilen)

1. **Repository'yi klonlayın:**
```bash
git clone https://github.com/ZGRSRL/mergenlite.git
cd mergenlite
```

2. **Environment dosyasını oluşturun:**
```bash
cp .env.example .env
# .env dosyasını düzenleyin ve API key'lerinizi ekleyin
```

3. **Docker Compose ile başlatın:**
```bash
docker-compose up -d
```

4. **Uygulamaya erişin:**
- Tarayıcınızda: http://localhost:8501

📖 **Detaylı Docker talimatları için**: [DOCKER_README.md](DOCKER_README.md) dosyasına bakın.

### Manuel Kurulum

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

## 📖 Kullanım

### İlan Merkezi
- SAM.gov'dan ilanları arayın ve filtreleyin
- İlanları analiz etmek için "Analiz Et" butonuna tıklayın

### Rehberli Analiz
1. **Aşama 1**: İlan metadata'sını ve ek dosyalarını çekin
2. **Aşama 2**: Dokümanları indirip işleyin (PDF/DOCX metin çıkarımı)
3. **Aşama 3**: RAG analizi ile gereksinimleri çıkarın
4. **Aşama 4**: Final raporu oluşturup indirin

### Otel Önerileri
- Analiz sonuçlarında otomatik olarak önerilen oteller gösterilir
- Excel dosyasından (`samples/SP&TD DEDUPLICATED EMAIL_EXTRACT_DATA_dedup.xlsx`) otel veritabanı yüklenir

## ⚙️ Yapılandırma

### Environment Variables

`.env` dosyasında şu değişkenleri ayarlayın:

```env
# SAM.gov API (Opsiyonel)
SAM_API_KEY=your_sam_api_key_here

# OpenAI API (Opsiyonel - AI analiz için)
OPENAI_API_KEY=your_openai_api_key_here

# Database (Docker kullanıyorsanız otomatik)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mergenlite
```

### SAM.gov API (Opsiyonel)
- `SAM_API_KEY`: SAM.gov API anahtarı
- API anahtarı olmadan da demo modu kullanılabilir

### OpenAI API (Opsiyonel)
- `OPENAI_API_KEY`: OpenAI API anahtarı
- API anahtarı olmadan da mock analiz kullanılır

## 📦 Gereksinimler

- Python 3.11+
- Streamlit 1.28+
- PDF işleme için: pdfplumber, PyMuPDF
- DOCX işleme için: python-docx
- RAG için (opsiyonel): sentence-transformers
- LLM için (opsiyonel): openai
- Database için (opsiyonel): PostgreSQL, SQLAlchemy

## 🐳 Docker

Docker ile kolay kurulum ve deployment için:

```bash
# Build ve run
docker-compose up -d

# Logları görüntüle
docker-compose logs -f mergenlite

# Durdur
docker-compose down
```

Detaylı bilgi için [DOCKER_README.md](DOCKER_README.md) dosyasına bakın.

## 📁 Proje Yapısı

```
mergenlite/
├── app.py                      # Ana Streamlit uygulaması
├── guided_analysis.py          # Rehberli analiz modülü
├── sam_integration.py          # SAM.gov API entegrasyonu
├── document_processor.py       # PDF/DOCX işleme
├── llm_analyzer.py             # LLM analiz modülü
├── mergenlite_opportunity_pipeline.py  # Opportunity analiz pipeline
├── opportunity_runner.py       # Opportunity runner
├── hotel_database.py           # Otel veritabanı yöneticisi
├── proposal_pipeline.py        # Teklif oluşturma
├── sow_generator.py            # SOW oluşturma
├── vendor_profile_extractor.py # Vendor profile çıkarımı
├── pdf_report_builder.py      # PDF rapor oluşturma
├── requirements.txt            # Python bağımlılıkları
├── Dockerfile                  # Docker image tanımı
├── docker-compose.yml          # Docker Compose yapılandırması
└── opportunities/              # Analiz edilen fırsatlar
```

## 🔧 Geliştirme

### Yerel Geliştirme Ortamı

1. Virtual environment oluşturun:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

2. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

3. Uygulamayı çalıştırın:
```bash
streamlit run app.py
```

## 📝 Lisans

Bu proje MergenAI platformunun lite versiyonudur.

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add some amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📞 İletişim

- Repository: https://github.com/ZGRSRL/mergenlite
- Issues: https://github.com/ZGRSRL/mergenlite/issues

## 🙏 Teşekkürler

- SAM.gov API
- Streamlit
- OpenAI
- Tüm açık kaynak kütüphaneler
