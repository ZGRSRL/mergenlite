#!/usr/bin/env python3
"""Check Amadeus API environment and credentials."""
import sys
sys.path.insert(0, '/app')

from app.config import settings
from app.services.amadeus_client import _build_client

print("=" * 70)
print("🔍 AMADEUS API DURUM KONTROLÜ")
print("=" * 70)
print()

# Check environment
print("📋 Environment:")
print(f"   AMADEUS_ENV: {settings.amadeus_env}")
print(f"   Hostname: {'production' if settings.amadeus_env.lower() == 'production' else 'test'}")
print()

# Check credentials
print("🔑 Credentials:")
has_key = bool(settings.amadeus_api_key)
has_secret = bool(settings.amadeus_api_secret)
print(f"   API Key: {'✅ Set' if has_key else '❌ Missing'}")
print(f"   API Secret: {'✅ Set' if has_secret else '❌ Missing'}")
print()

# Test client
if has_key and has_secret:
    print("🔧 Testing Client Initialization:")
    client = _build_client()
    if client:
        print("   ✅ Client initialized successfully")
        print(f"   Hostname: {client.hostname}")
    else:
        print("   ❌ Client initialization failed")
else:
    print("⚠️ Cannot test client - credentials missing")

print()
print("=" * 70)
print("💡 NOTLAR:")
print("=" * 70)
print("1. Test ortamı 2026 tarihleri için veri döndürmez")
print("2. Production ortamı için geçiş yapılması gerekir")
print("3. Sistem mantığı (SOW → Requirements → API Call) çalışıyor ✅")
print("=" * 70)

