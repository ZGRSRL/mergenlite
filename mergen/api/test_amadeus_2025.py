#!/usr/bin/env python3
"""Test Amadeus API with 2025 dates for Houston."""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("🔍 AMADEUS API TEST - HOUSTON 2025")
print("=" * 70)
print()

# Test with 2025 dates (3 months from now)
today = datetime.now()
check_in_date = today + timedelta(days=90)  # ~3 months from now
check_out_date = check_in_date + timedelta(days=4)  # 4 nights

city_code = "HOU"
check_in = check_in_date.strftime("%Y-%m-%d")
check_out = check_out_date.strftime("%Y-%m-%d")
adults = 10  # Smaller number for test

print(f"Parameters:")
print(f"  City Code: {city_code}")
print(f"  Check-in: {check_in} (90 days from today)")
print(f"  Check-out: {check_out} (4 nights)")
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
        for i, offer in enumerate(offers, 1):
            hotel_info = offer.get('hotel', {})
            offer_info = offer.get('offer', {})
            print(f"\n   {i}. {hotel_info.get('name', 'N/A')}")
            print(f"      Hotel ID: {offer.get('hotelId', 'N/A')}")
            price = offer_info.get('price', {})
            print(f"      Price: {price.get('total', 'N/A')} {price.get('currency', '')}")
            print(f"      Check-in: {offer_info.get('checkInDate', 'N/A')}")
            print(f"      Check-out: {offer_info.get('checkOutDate', 'N/A')}")
            rooms = offer_info.get('room', {})
            print(f"      Room Type: {rooms.get('type', 'N/A')}")
    else:
        print("   ⚠️ No offers returned")
        print("   💡 Possible reasons:")
        print("      - No hotels available for these dates")
        print("      - API error (check logs above)")
        print("      - Hotel list empty for this city")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

