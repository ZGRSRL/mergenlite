# MergenLite Analiz Sistemi - Nasıl Çalışıyor?

## 🔍 Mevcut Durum

### LLM Kullanımı
- **Ana Pipeline**: `mergenlite_opportunity_pipeline.py` → **Sadece OpenAI** kullanıyor
- **LLM Analyzer**: `llm_analyzer.py` → **Sadece OpenAI** kullanıyor
- **Ollama**: Şu anda **kullanılmıyor** (eski dosyalarda referans var ama aktif değil)

### Analiz Akışı

```
1. Document Processor
   ↓
   PDF/DOCX → Metin çıkarımı
   ↓
2. LLM Analiz (OpenAI)
   ↓
   - Requirements Extractor (gpt-3.5-turbo)
   - Compliance Analyst (pattern matching + keyword)
   - Proposal Writer (template-based)
   ↓
3. Sonuçlar
   - JSON report
   - Markdown summary
   - PDF report
```

## 📊 Detaylı Analiz Süreci

### 1. Document Processor (`document_processor.py`)
- PDF'lerden metin çıkarır (`pdfplumber`)
- DOCX'lerden metin çıkarır (`python-docx`)
- Sayfa sayısı, karakter sayısı hesaplar

### 2. LLM Analyzer (`llm_analyzer.py`)
- **Model**: `gpt-3.5-turbo` (OpenAI)
- **API Key**: `OPENAI_API_KEY` environment variable'dan alınıyor
- **Fonksiyonlar**:
  - `extract_requirements()`: Gereksinim çıkarımı
  - `analyze_document_by_type()`: Belge tipine göre analiz
  - `analyze_document_by_criteria()`: Kriter bazlı analiz

### 3. Opportunity Pipeline (`mergenlite_opportunity_pipeline.py`)
- **AutoGen Agents** (eğer AutoGen yüklüyse):
  - Requirements Agent
  - Compliance Agent
  - Commercial Agent
  - Reporter Agent
- **LLM Config**: `get_llm_config()` → OpenAI kullanıyor
- **Mock Mode**: Eğer AutoGen veya OpenAI API key yoksa mock analiz yapıyor

## ⚙️ Ollama Desteği

### Mevcut Durum
- Ollama **şu anda kullanılmıyor**
- Eski dosyalarda Ollama referansları var:
  - `mergenlite_agents.py` → `USE_OLLAMA` environment variable kontrolü
  - `mergen/sam/document_management/autogen_agents.py` → Ollama desteği var

### Ollama'yı Aktif Etmek İçin

1. **Ollama'yı başlat**:
   ```bash
   ollama serve
   ```

2. **Model yükle**:
   ```bash
   ollama pull llama3.2
   ```

3. **Environment variable ekle**:
   ```env
   USE_OLLAMA=true
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2
   ```

4. **Kod güncellemesi gerekli**:
   - `mergenlite_opportunity_pipeline.py` → `get_llm_config()` fonksiyonunu güncelle
   - `llm_analyzer.py` → Ollama desteği ekle

## 🔧 Şu Anki Analiz Yöntemi

### OpenAI Kullanımı
```python
# mergenlite_opportunity_pipeline.py
def get_llm_config():
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    if not api_key:
        return None  # Mock mode
    
    return {
        "config_list": [{
            "model": model,
            "api_key": api_key
        }],
        "temperature": 0.1,
        "timeout": 120
    }
```

### LLM Analyzer
```python
# llm_analyzer.py
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[...],
    temperature=0.2,
    max_tokens=2000
)
```

## 📝 Sonuç

- **Ollama**: ❌ Kullanılmıyor (process çalışmıyor)
- **OpenAI**: ✅ Kullanılıyor (eğer API key varsa)
- **Mock Mode**: ✅ Fallback olarak kullanılıyor (API key yoksa)

## 🚀 Ollama'yı Aktif Etmek İsterseniz

1. Ollama'yı başlatın
2. Model yükleyin
3. `mergenlite_opportunity_pipeline.py` ve `llm_analyzer.py` dosyalarını güncelleyin
4. Environment variable'ları ayarlayın

