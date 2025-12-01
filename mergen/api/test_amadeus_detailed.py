#!/usr/bin/env python3
"""Test Amadeus API with detailed error logging."""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import _CLIENT, _build_client
from amadeus import Client, ResponseError
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("=" * 70)
print("🔍 AMADEUS API DETAYLI TEST")
print("=" * 70)
print()

# Test with closer dates (30 days from now)
today = datetime.now()
check_in_date = today + timedelta(days=30)  # 30 days from now
check_out_date = check_in_date + timedelta(days=2)  # 2 nights

city_code = "HOU"
check_in = check_in_date.strftime("%Y-%m-%d")
check_out = check_out_date.strftime("%Y-%m-%d")
adults = 2

print(f"Step 1: Get hotel list for {city_code}...")
try:
    # Step 1: Get hotel list
    hotel_list_response = _CLIENT.reference_data.locations.hotels.by_city.get(cityCode=city_code.upper())
    
    if not hotel_list_response.data or len(hotel_list_response.data) == 0:
        print("   ❌ No hotels found for city code")
        exit(1)
    
    hotel_ids = [hotel.get('hotelId') for hotel in hotel_list_response.data[:5] if hotel.get('hotelId')]
    print(f"   ✅ Found {len(hotel_ids)} hotels")
    print(f"   Hotel IDs: {hotel_ids[:3]}...")
    
    if not hotel_ids:
        print("   ❌ No hotel IDs found")
        exit(1)
    
    # Step 2: Get offers
    print(f"\nStep 2: Get offers for hotels...")
    print(f"   Parameters:")
    print(f"     hotelIds: {','.join(hotel_ids[:3])}")
    print(f"     checkInDate: {check_in}")
    print(f"     checkOutDate: {check_out}")
    print(f"     adults: {adults}")
    
    offers_params = {
        'hotelIds': ','.join(hotel_ids[:3]),  # Test with 3 hotels
        'checkInDate': check_in,
        'checkOutDate': check_out,
        'adults': adults,
    }
    
    print(f"\n   Calling API...")
    offers_response = _CLIENT.shopping.hotel_offers_search.get(**offers_params)
    
    print(f"   ✅ API call successful!")
    print(f"   Response data: {len(offers_response.data) if offers_response.data else 0} hotels")
    
    if offers_response.data:
        print(f"\n🏨 Hotels with offers:")
        for hotel_data in offers_response.data[:3]:
            hotel_info = hotel_data.get('hotel', {})
            offers = hotel_data.get('offers', [])
            print(f"   - {hotel_info.get('name', 'N/A')}: {len(offers)} offers")
            if offers:
                offer = offers[0]
                price = offer.get('price', {})
                print(f"     Price: {price.get('total', 'N/A')} {price.get('currency', '')}")
    else:
        print("   ⚠️ No offers in response")
        
except ResponseError as exc:
    print(f"\n❌ ResponseError: {exc.code} - {exc.description}")
    if hasattr(exc, 'response') and exc.response:
        print(f"   Response body: {exc.response.body}")
    import traceback
    traceback.print_exc()
except Exception as exc:
    print(f"\n❌ Error: {exc}")
    if hasattr(exc, 'description'):
        print(f"   Description: {exc.description}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

