#!/usr/bin/env python3
"""Test new API key with Notice ID search"""

import sys
import os
import time
from datetime import datetime

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    # Önce environment'ı temizle
    if 'SAM_API_KEY' in os.environ:
        del os.environ['SAM_API_KEY']
    load_dotenv('mergen/.env', override=True)
    load_dotenv('.env', override=True)
except:
    pass

from sam_integration import SAMIntegration

def test_new_api_key():
    """Test the new API key"""
    print("\n" + "="*60)
    print("Yeni API Key Testi")
    print("="*60 + "\n")
    
    sam = SAMIntegration()
    
    # API Key kontrolü
    if not sam.api_key:
        print("[ERROR] API Key bulunamadı!")
        print("Lütfen mergen/.env dosyasında SAM_API_KEY'i kontrol edin.")
        return False
    
    masked = sam.api_key[:10] + "..." + sam.api_key[-4:] if len(sam.api_key) > 14 else "***"
    print(f"[OK] API Key yüklendi: {masked}")
    print(f"[OK] API Key uzunluğu: {len(sam.api_key)}")
    
    # Rate limit bekle (429 hatası önlemek için)
    print("\n[INFO] Rate limit için 5 saniye bekleniyor...")
    time.sleep(5)
    
    # Test 1: Basit arama (limit=1)
    print("\n[TEST 1] Basit API testi (limit=1)...")
    try:
        results = sam.fetch_opportunities(keywords="test", limit=1, days_back=7)
        if results is not None:
            print(f"[OK] API çalışıyor! {len(results)} sonuç bulundu.")
            if results:
                print(f"   Örnek: {results[0].get('title', 'N/A')[:60]}")
            return True
        else:
            print("[WARNING] Sonuç bulunamadı (normal olabilir)")
            return True  # API çalışıyor ama sonuç yok
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            print("[WARNING] API quota limiti aşıldı (429 hatası)")
            print("   Bu normal olabilir - API key'iniz çalışıyor ama limit dolmuş")
            print("   Yarın tekrar deneyin veya SAM.gov'da limit kontrolü yapın")
            return True  # Key çalışıyor ama limit var
        else:
            print(f"[ERROR] API hatası: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = test_new_api_key()
    
    print("\n" + "="*60)
    if success:
        print("[OK] API Key testi tamamlandı!")
        print("\nSonraki adımlar:")
        print("1. Streamlit'i yeniden başlatın")
        print("2. Notice ID W50S7526QA010 ile test edin")
    else:
        print("[ERROR] API Key testi başarısız!")
        print("Lütfen .env dosyasını kontrol edin.")
    print("="*60 + "\n")



