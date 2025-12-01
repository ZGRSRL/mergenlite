#!/usr/bin/env python3
"""Test Amadeus API with 2026 dates for Houston - with lower occupancy."""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code, lookup_city_code
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("🏨 AMADEUS API TEST - 2026 TARİHLERİ (DÜŞÜK OCCUPANCY)")
print("=" * 70)
print()

# Test Houston with 2026 dates - try different adult counts
city_code = lookup_city_code("Houston")
print(f"🏙️ City: Houston -> {city_code}")
print()

if city_code:
    # Try different adult counts
    adult_counts = [1, 2, 4, 10, 20]
    
    for adults in adult_counts:
        print(f"🔍 Testing with {adults} adults:")
        print(f"   Check-in: 2026-03-03")
        print(f"   Check-out: 2026-03-07")
        
        hotels = search_hotels_by_city_code(
            city_code=city_code,
            check_in="2026-03-03",
            check_out="2026-03-07",
            adults=adults,
            max_results=5
        )
        
        if hotels:
            print(f"   ✅ Hotels Found: {len(hotels)}")
            print(f"   🏨 First Hotel: {hotels[0].get('hotel', {}).get('name', 'N/A')}")
            price = hotels[0].get('offer', {}).get('price', {})
            if price:
                print(f"   💰 Price: {price.get('total', 'N/A')} {price.get('currency', 'USD')}")
            print()
            break  # Found hotels, stop testing
        else:
            print(f"   ⚠️ No hotels found with {adults} adults")
            print()
    
    if not hotels:
        print("❌ No hotels found with any occupancy level")
        print("   This might indicate:")
        print("   - 2026 dates are too far in future for Amadeus")
        print("   - No availability for these specific dates")
        print("   - API limitation for future dates")

print()
print("=" * 70)

