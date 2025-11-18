# 🚀 Hızlı Başlangıç Komutları

## 🧹 Cache Temizliği

### PowerShell Komutları
```powershell
# .cache klasörünü temizle
Remove-Item -Recurse -Force .cache -ErrorAction SilentlyContinue

# __pycache__ klasörlerini temizle
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
```

### Python Script ile
```bash
python cache_cleanup_and_test.py
```

### Tek Satır Python
```python
python -c "import shutil, os; shutil.rmtree('.cache', ignore_errors=True); [shutil.rmtree(os.path.join(root, '__pycache__'), ignore_errors=True) for root, dirs, files in os.walk('.', topdown=False) if '__pycache__' in dirs]; print('✅ Cache temizlendi')"
```

## 🚀 Uygulamayı Başlatma

### 1. API Başlatma
```bash
cd mergen/api
alembic upgrade head
uvicorn app.main:app --reload
```

### 2. Streamlit Başlatma
```bash
cd mergen
streamlit run mergenlite_unified.py
```

## 🧪 Test Komutları

### API Test
```bash
# 721110 senkronizasyon
curl -X POST "http://localhost:8000/api/opportunities/sync?naics=721110&days_back=90"

# Notice ID testi
curl "http://localhost:8000/api/search?query=W50S7526QA010&limit=5"

# Auto analyze
curl -X POST "http://localhost:8000/api/proposal/auto?notice_id=W50S7526QA010"
```

### Environment Kontrolü
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', os.getenv('SAM_API_KEY', 'YOK')[:20])"
```

## 📋 Tüm Komutlar (Sırayla)

```powershell
# 1. Cache temizliği
python cache_cleanup_and_test.py

# 2. API başlat (yeni terminal)
cd mergen/api
uvicorn app.main:app --reload

# 3. Streamlit başlat (yeni terminal)
cd mergen
streamlit run mergenlite_unified.py
```

