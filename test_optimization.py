#!/usr/bin/env python3
"""
Optimizasyon Doğrulama Scripti
Yapılan optimizasyonların çalıştığını doğrular
"""

import os
import inspect
from dotenv import load_dotenv

# .env dosyasını yükle
if os.path.exists('mergen/.env'):
    load_dotenv('mergen/.env', override=True)
else:
    load_dotenv(override=True)

from sam_integration import SAMIntegration

print("🔍 Optimizasyon Doğrulama\n")
print("=" * 50)

# SAMIntegration instance oluştur
sam = SAMIntegration()

# 1. Cache Mekanizması Kontrolü
print("\n1️⃣ Cache Mekanizması:")
cache_methods = ['_get_cache_key', '_get_from_cache', '_save_to_cache']
for method in cache_methods:
    if hasattr(sam, method):
        print(f"   ✅ {method}() mevcut")
    else:
        print(f"   ❌ {method}() bulunamadı")

if hasattr(sam, 'cache_duration'):
    hours = sam.cache_duration.total_seconds() / 3600
    print(f"   ✅ Cache süresi: {hours} saat")

# 2. Limit Optimizasyonları Kontrolü
print("\n2️⃣ Limit Optimizasyonları:")

# fetch_opportunities limit kontrolü
fetch_opp_code = inspect.getsource(sam.fetch_opportunities)
if 'optimized_limit = min(limit, 50)' in fetch_opp_code or 'limit, 50' in fetch_opp_code:
    print("   ✅ fetch_opportunities(): Limit 50'ye optimize edilmiş")
else:
    print("   ⚠️ fetch_opportunities(): Limit optimizasyonu kontrol edilemedi")

# fetch_by_notice_id limit kontrolü
fetch_notice_code = inspect.getsource(sam.fetch_by_notice_id)
if 'optimized_limit = 25' in fetch_notice_code or 'limit = 25' in fetch_notice_code:
    print("   ✅ fetch_by_notice_id(): Limit 25'e optimize edilmiş")
else:
    print("   ⚠️ fetch_by_notice_id(): Limit optimizasyonu kontrol edilemedi")

# 3. Cache-First Stratejisi Kontrolü
print("\n3️⃣ Cache-First Stratejisi:")
if '_get_from_cache' in fetch_notice_code:
    print("   ✅ fetch_by_notice_id() cache-first kullanıyor")
else:
    print("   ⚠️ Cache-first stratejisi kontrol edilemedi")

if '_get_from_cache' in fetch_opp_code:
    print("   ✅ fetch_opportunities() cache-first kullanıyor")
else:
    print("   ⚠️ Cache-first stratejisi kontrol edilemedi")

# 4. API Key Yükleme Kontrolü
print("\n4️⃣ API Key Yükleme:")
if sam.api_key:
    print(f"   ✅ API Key yüklendi (length: {len(sam.api_key)})")
    print(f"   🔑 Preview: {sam.api_key[:20]}...{sam.api_key[-10:]}")
else:
    print("   ❌ API Key yüklenemedi")

# 5. Cache Klasörü Kontrolü
print("\n5️⃣ Cache Klasörü:")
from pathlib import Path
cache_dir = Path('.cache')
if cache_dir.exists():
    cache_files = list(cache_dir.glob('*.json'))
    print(f"   ✅ Cache klasörü mevcut")
    print(f"   📁 Cache dosyası sayısı: {len(cache_files)}")
    if cache_files:
        print(f"   📄 Örnek cache dosyası: {cache_files[0].name}")
else:
    print("   ⚠️ Cache klasörü henüz oluşturulmamış (ilk API çağrısında oluşacak)")

print("\n" + "=" * 50)
print("✅ Optimizasyon doğrulama tamamlandı!")

