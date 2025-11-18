#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cache Temizliği ve Test Scripti
Tüm cache'leri temizler ve uygulamayı test eder.
"""

import os
import shutil
import sys
from pathlib import Path

# Windows console encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def clean_cache():
    """Tüm cache'leri temizle"""
    print("🧹 Cache temizliği başlatılıyor...")
    
    # .cache klasörü
    cache_dir = Path('.cache')
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)
        print(f"✅ .cache klasörü temizlendi")
    
    # __pycache__ klasörleri
    pycache_count = 0
    for root, dirs, files in os.walk('.', topdown=False):
        if '__pycache__' in dirs:
            pycache_path = Path(root) / '__pycache__'
            shutil.rmtree(pycache_path, ignore_errors=True)
            pycache_count += 1
    
    if pycache_count > 0:
        print(f"✅ {pycache_count} __pycache__ klasörü temizlendi")
    else:
        print("ℹ️  __pycache__ klasörü bulunamadı")
    
    # Streamlit cache (varsa)
    streamlit_cache = Path.home() / '.streamlit' / 'cache'
    if streamlit_cache.exists():
        try:
            shutil.rmtree(streamlit_cache, ignore_errors=True)
            print(f"✅ Streamlit cache temizlendi")
        except:
            pass
    
    print("✅ Cache temizliği tamamlandı!\n")

def check_env():
    """Environment değişkenlerini kontrol et"""
    print("🔍 Environment kontrolü...")
    
    from dotenv import load_dotenv
    
    # .env dosyasını yükle
    env_files = [
        Path('mergen/.env'),
        Path('.env'),
        Path('mergen/mergen/.env')
    ]
    
    loaded = False
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=True)
            print(f"✅ .env dosyası yüklendi: {env_file}")
            loaded = True
            break
    
    if not loaded:
        print("⚠️  .env dosyası bulunamadı")
    
    # API key kontrolü
    api_key = os.getenv('SAM_API_KEY', '')
    if api_key:
        print(f"✅ SAM_API_KEY yüklendi: {api_key[:20]}...")
    else:
        print("❌ SAM_API_KEY bulunamadı!")
        print("   Lütfen .env dosyasında SAM_API_KEY değerini kontrol edin.")
    
    print()

def test_imports():
    """Gerekli modüllerin import edilebilirliğini test et"""
    print("🧪 Import testleri...")
    
    modules = [
        'streamlit',
        'sam_integration',
        'gsa_opportunities_client',
        'mergenlite_ui_components'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module} import edildi")
        except ImportError as e:
            print(f"❌ {module} import edilemedi: {e}")
    
    print()

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("🚀 MergenLite Cache Temizliği ve Test")
    print("=" * 60)
    print()
    
    # Cache temizliği
    clean_cache()
    
    # Environment kontrolü
    check_env()
    
    # Import testleri
    test_imports()
    
    print("=" * 60)
    print("✅ Hazır! Şimdi uygulamayı başlatabilirsiniz:")
    print()
    print("API:")
    print("  cd mergen/api")
    print("  uvicorn app.main:app --reload")
    print()
    print("Streamlit:")
    print("  cd mergen")
    print("  streamlit run mergenlite_unified.py")
    print("=" * 60)

if __name__ == '__main__':
    main()

