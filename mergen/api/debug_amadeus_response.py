#!/usr/bin/env python3
"""Debug Amadeus API response format."""
from app.services.amadeus_client import search_hotels_by_city_code
import json

city = "HOU"
check_in = "2026-03-03"
check_out = "2026-03-07"
adults = 2

print("🚀 Amadeus API Response Format Debug")
print("=" * 50)
print()

offers = search_hotels_by_city_code(city, check_in, check_out, adults, max_results=3)

if offers:
    print(f"✅ {len(offers)} otel bulundu\n")
    print("İlk otel response formatı:")
    print(json.dumps(offers[0], indent=2, default=str)[:2000])
    print("\n...")
    
    # Check structure
    first = offers[0]
    print(f"\n📋 Yapı Analizi:")
    print(f"   Keys: {list(first.keys())}")
    if 'hotel' in first:
        print(f"   Hotel keys: {list(first['hotel'].keys()) if isinstance(first['hotel'], dict) else 'N/A'}")
    if 'offer' in first:
        print(f"   Offer keys: {list(first['offer'].keys()) if isinstance(first['offer'], dict) else 'N/A'}")
else:
    print("❌ Otel bulunamadı")

