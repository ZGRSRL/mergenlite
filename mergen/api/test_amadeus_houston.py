#!/usr/bin/env python3
"""Test Amadeus API directly for Houston."""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("🔍 AMADEUS API TEST - HOUSTON")
print("=" * 70)
print()

# Test parameters
city_code = "HOU"
check_in = "2026-03-03"
check_out = "2026-03-07"
adults = 80

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
        print(f"\n🏨 Hotels Found:")
        for i, offer in enumerate(offers[:3], 1):
            hotel_info = offer.get('hotel', {})
            offer_info = offer.get('offer', {})
            print(f"\n   {i}. {hotel_info.get('name', 'N/A')}")
            print(f"      Hotel ID: {offer.get('hotelId', 'N/A')}")
            price = offer_info.get('price', {})
            print(f"      Price: {price.get('total', 'N/A')} {price.get('currency', '')}")
            print(f"      Check-in: {offer_info.get('checkInDate', 'N/A')}")
            print(f"      Check-out: {offer_info.get('checkOutDate', 'N/A')}")
    else:
        print("   ⚠️ No offers returned")
        print("   💡 Possible reasons:")
        print("      - Amadeus API doesn't have data for 2026 dates")
        print("      - API error (check logs above)")
        print("      - No hotels available for these dates")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

