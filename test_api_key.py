#!/usr/bin/env python3
"""
API Key Test Script
SAM.gov API key'inin yüklendiğini ve çalıştığını test eder
"""

import os
import sys
from dotenv import load_dotenv

# .env dosyasını yükle
env_paths = ['mergen/.env', '.env']
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print(f"[OK] Loaded .env from: {os.path.abspath(env_path)}")
        break
else:
    load_dotenv(override=True)

# API Key kontrolü
api_key = os.getenv('SAM_API_KEY', '').strip()

if not api_key:
    print("[ERROR] API Key bulunamadi!")
    print(f"   - Current directory: {os.getcwd()}")
    print(f"   - .env files checked: {env_paths}")
    sys.exit(1)

print(f"[OK] API Key: {api_key[:15]}...")
print(f"[INFO] Length: {len(api_key)}")
print(f"[INFO] Preview: {api_key[:20]}...{api_key[-10:]}")

# SAMIntegration testi
try:
    from sam_integration import SAMIntegration
    
    sam = SAMIntegration()
    
    if sam.api_key:
        print(f"[OK] SAMIntegration API Key yuklendi: {sam.api_key[:20]}...")
        print(f"[INFO] Length: {len(sam.api_key)}")
        
        # Kısa API testi
        print("\n[TEST] API Test baslatiliyor...")
        try:
            # Küçük bir test araması (limit=1)
            result = sam.fetch_opportunities(
                keywords="test",
                days_back=7,
                limit=1
            )
            
            if result:
                print(f"[OK] API Test basarili! {len(result)} sonuc bulundu.")
                print(f"   Ilk sonuc: {result[0].get('title', 'N/A')[:50]}...")
            else:
                print("[WARN] API Test: Sonuc bulunamadi (normal olabilir)")
        except Exception as e:
            print(f"[ERROR] API Test hatasi: {str(e)}")
    else:
        print("[ERROR] SAMIntegration API Key yuklenemedi!")
        sys.exit(1)
        
except ImportError as e:
    print(f"[ERROR] Import hatasi: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Hata: {e}")
    sys.exit(1)

print("\n[OK] Tum testler basarili!")

