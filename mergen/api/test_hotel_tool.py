#!/usr/bin/env python3
"""Test hotel matcher tool directly."""
import os
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("🔍 AMADEUS TOOL TEST")
print("=" * 70)
print()

# Test parameters
city_code = "PHL"
check_in = "2026-06-11"
check_out = "2026-07-25"
adults = 10

print(f"Parameters:")
print(f"  City Code: {city_code}")
print(f"  Check-in: {check_in}")
print(f"  Check-out: {check_out}")
print(f"  Adults: {adults}")
print()

# Test the function directly
print("Calling search_hotels_by_city_code...")
try:
    offers = search_hotels_by_city_code(city_code, check_in, check_out, adults, max_results=5)
    print(f"✅ Function call successful!")
    print(f"   Offers returned: {len(offers)}")
    
    if offers:
        print(f"\n🏨 First Hotel:")
        first = offers[0]
        hotel_info = first.get('hotel', {})
        offer_info = first.get('offer', {})
        print(f"   Name: {hotel_info.get('name', 'N/A')}")
        print(f"   Hotel ID: {first.get('hotelId', 'N/A')}")
        price = offer_info.get('price', {})
        print(f"   Price: {price.get('total', 'N/A')} {price.get('currency', '')}")
    else:
        print("   ⚠️ No offers returned (Amadeus API may not have data for these dates)")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

