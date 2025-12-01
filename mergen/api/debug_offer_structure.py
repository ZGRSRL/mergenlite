"""Debug offer structure"""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code

offers = search_hotels_by_city_code('HOU', '2026-03-03', '2026-03-07', 2, 2)

print(f"Offers: {len(offers)}")
if offers:
    print(f"\nFirst offer structure:")
    first = offers[0]
    print(f"  Keys: {list(first.keys())}")
    print(f"  name (root): {first.get('name')}")
    print(f"  hotel.name: {first.get('hotel', {}).get('name')}")
    print(f"  offer.hotel.name: {first.get('offer', {}).get('hotel', {}).get('name')}")
    
    # Test conversion logic
    print(f"\nTesting conversion logic:")
    offer_data = first
    hotel_name = offer_data.get("name")
    print(f"  1. Root name: {hotel_name}")
    if not hotel_name:
        hotel_info = offer_data.get("hotel", {})
        if isinstance(hotel_info, dict):
            hotel_name = hotel_info.get("name")
            print(f"  2. hotel.name: {hotel_name}")
    if not hotel_name:
        offer_info = offer_data.get("offer", {})
        if isinstance(offer_info, dict):
            offer_hotel = offer_info.get("hotel", {})
            if isinstance(offer_hotel, dict):
                hotel_name = offer_hotel.get("name")
                print(f"  3. offer.hotel.name: {hotel_name}")
    print(f"\nFinal hotel_name: {hotel_name}")

