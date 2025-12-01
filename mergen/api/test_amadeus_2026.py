#!/usr/bin/env python3
"""Test Amadeus API with 2026 dates for Houston."""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code, lookup_city_code
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("🏨 AMADEUS API TEST - 2026 TARİHLERİ İLE")
print("=" * 70)
print()

# Check configuration
print("🔧 Amadeus Configuration:")
print(f"   API Key: {'✅ Set' if settings.amadeus_api_key else '❌ Not Set'}")
print(f"   API Secret: {'✅ Set' if settings.amadeus_api_secret else '❌ Not Set'}")
print(f"   Environment: {settings.amadeus_env}")
print()

# Test Houston with 2026 dates
city_code = lookup_city_code("Houston")
print(f"🏙️ City Lookup:")
print(f"   Houston -> {city_code}")
print()

if city_code:
    print(f"🔍 Hotel Search:")
    print(f"   City Code: {city_code}")
    print(f"   Check-in: 2026-03-03")
    print(f"   Check-out: 2026-03-07")
    print(f"   Adults: 80")
    print()
    
    hotels = search_hotels_by_city_code(
        city_code=city_code,
        check_in="2026-03-03",
        check_out="2026-03-07",
        adults=80,
        max_results=10
    )
    
    print(f"✅ Hotels Found: {len(hotels)}")
    print()
    
    if hotels:
        print("🏨 Top Hotels:")
        for i, hotel in enumerate(hotels[:5], 1):
            hotel_info = hotel.get('hotel', {}) or hotel
            offer = hotel.get('offer', {}) or {}
            price = offer.get('price', {}) or {}
            
            print(f"\n   {i}. {hotel_info.get('name', 'N/A')}")
            print(f"      Hotel ID: {hotel_info.get('hotelId', 'N/A')}")
            print(f"      Address: {hotel_info.get('address', {}).get('lines', ['N/A'])[0]}")
            if price:
                print(f"      Price: {price.get('total', 'N/A')} {price.get('currency', 'USD')}")
    else:
        print("⚠️ No hotels found")
        print("   Possible reasons:")
        print("   - 2026 dates too far in future")
        print("   - No availability for these dates")
        print("   - API environment issue")
else:
    print("❌ City code lookup failed")

print()
print("=" * 70)

