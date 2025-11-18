#!/usr/bin/env python3
"""
Cache Test Script
Cache mekanizmasının çalıştığını test eder
"""

import os
import time
from dotenv import load_dotenv
from pathlib import Path

# .env dosyasını yükle
if os.path.exists('mergen/.env'):
    load_dotenv('mergen/.env', override=True)
else:
    load_dotenv(override=True)

from sam_integration import SAMIntegration

print("🧪 Cache Test Başlatılıyor...\n")

# SAMIntegration instance oluştur
sam = SAMIntegration()

if not sam.api_key:
    print("❌ API Key bulunamadı! Test edilemiyor.")
    exit(1)

# Test query
test_notice_id = "W50S7526QA010"
print(f"📋 Test Notice ID: {test_notice_id}\n")

# İlk arama (cache miss olmalı)
print("1️⃣ İlk Arama (Cache Miss bekleniyor)...")
start_time = time.time()
result1 = sam.fetch_by_notice_id(test_notice_id)
time1 = time.time() - start_time

print(f"   ⏱️ Süre: {time1:.2f} saniye")
print(f"   📊 Sonuç sayısı: {len(result1)}")
print(f"   💾 Cache durumu: {'Hit' if result1 else 'Miss'}\n")

# İkinci arama (cache hit olmalı)
print("2️⃣ İkinci Arama (Cache Hit bekleniyor)...")
start_time = time.time()
result2 = sam.fetch_by_notice_id(test_notice_id)
time2 = time.time() - start_time

print(f"   ⏱️ Süre: {time2:.2f} saniye")
print(f"   📊 Sonuç sayısı: {len(result2)}")

# Cache kontrolü
cache_dir = Path('.cache')
if cache_dir.exists():
    cache_files = list(cache_dir.glob('*.json'))
    print(f"   💾 Cache dosyası sayısı: {len(cache_files)}")
    
    if time2 < time1 * 0.5:  # İkinci arama %50'den hızlıysa cache çalışıyor
        print(f"   ✅ Cache çalışıyor! ({((time1 - time2) / time1 * 100):.1f}% hızlı)")
    else:
        print(f"   ⚠️ Cache etkisi beklenenden az")
else:
    print(f"   ❌ Cache klasörü bulunamadı")

print("\n✅ Cache testi tamamlandı!")

