#!/usr/bin/env python3
"""Test API key quota status"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Environment'ı temizle
if 'SAM_API_KEY' in os.environ:
    del os.environ['SAM_API_KEY']

# .env dosyasını yükle
load_dotenv('mergen/.env', override=True)
load_dotenv('.env', override=True)

api_key = os.getenv('SAM_API_KEY', '')
if not api_key:
    print("[ERROR] API Key bulunamadı!")
    sys.exit(1)

print("\n" + "="*60)
print("API Key Quota Kontrolü")
print("="*60)
print(f"\n[INFO] API Key: {api_key[:15]}...{api_key[-4:]}")
print(f"[INFO] Uzunluk: {len(api_key)}")
print(f"[INFO] Test zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Test 1: Basit API çağrısı
print("\n[TEST 1] Basit API çağrısı (limit=1)...")
try:
    base_url = "https://api.sam.gov/opportunities/v2/search"
    params = {
        'api_key': api_key,
        'limit': 1,
        'postedFrom': (datetime.now() - timedelta(days=7)).strftime('%m/%d/%Y'),
        'postedTo': datetime.now().strftime('%m/%d/%Y'),
        'keyword': 'test'
    }
    
    response = requests.get(base_url, params=params, timeout=30)
    
    print(f"[INFO] HTTP Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("[OK] API çalışıyor! Quota limiti sorun yok.")
        print(f"[OK] Sonuç sayısı: {len(data.get('opportunitiesData', []))}")
    elif response.status_code == 429:
        try:
            error_data = response.json()
            print("[WARNING] Quota limiti aşıldı (429)")
            print(f"   Mesaj: {error_data.get('message', 'N/A')}")
            print(f"   Açıklama: {error_data.get('description', 'N/A')}")
            if 'nextAccessTime' in error_data:
                print(f"   Sonraki erişim: {error_data.get('nextAccessTime', 'N/A')}")
        except:
            print(f"[ERROR] 429 hatası: {response.text[:200]}")
    elif response.status_code == 401:
        print("[ERROR] API Key geçersiz (401)")
        print(f"   Yanıt: {response.text[:200]}")
    else:
        print(f"[WARNING] Beklenmeyen durum: {response.status_code}")
        print(f"   Yanıt: {response.text[:200]}")
        
except Exception as e:
    print(f"[ERROR] Hata: {e}")

# Test 2: Notice ID araması
print("\n[TEST 2] Notice ID araması (W50S7526QA010)...")
time.sleep(2)  # Rate limit için bekle

try:
    params2 = {
        'api_key': api_key,
        'limit': 10,
        'keyword': 'W50S7526QA010',
        'postedFrom': (datetime.now() - timedelta(days=730)).strftime('%m/%d/%Y'),
        'postedTo': datetime.now().strftime('%m/%d/%Y')
    }
    
    response2 = requests.get(base_url, params=params2, timeout=30)
    
    print(f"[INFO] HTTP Status: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        results = data2.get('opportunitiesData', [])
        print(f"[OK] API çalışıyor! {len(results)} sonuç bulundu.")
        
        # Notice ID eşleşmesi kontrol et
        matching = [r for r in results if 'W50S7526QA010' in str(r.get('noticeId', '')).upper()]
        if matching:
            print(f"[OK] Notice ID eşleşmesi bulundu: {len(matching)}")
        else:
            print("[INFO] Notice ID eşleşmesi bulunamadı (normal olabilir)")
    elif response2.status_code == 429:
        try:
            error_data = response2.json()
            print("[WARNING] Quota limiti aşıldı (429)")
            print(f"   Mesaj: {error_data.get('message', 'N/A')}")
            print(f"   Sonraki erişim: {error_data.get('nextAccessTime', 'N/A')}")
        except:
            print(f"[ERROR] 429 hatası: {response2.text[:200]}")
    else:
        print(f"[WARNING] Durum: {response2.status_code}")
        print(f"   Yanıt: {response2.text[:200]}")
        
except Exception as e:
    print(f"[ERROR] Hata: {e}")

print("\n" + "="*60)
print("Quota kontrolü tamamlandı!")
print("="*60 + "\n")

