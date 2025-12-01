"""Test offer_data structure directly"""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code

print("Testing amadeus_client output structure...")
offers = search_hotels_by_city_code('HOU', '2026-03-03', '2026-03-07', 2, 3)

print(f"\nOffers: {len(offers)}")
if offers:
    offer_data = offers[0]
    print(f"\nFirst offer_data structure:")
    print(f"  Keys: {list(offer_data.keys())}")
    print(f"  Root level 'name': {offer_data.get('name')}")
    print(f"  hotel.name: {offer_data.get('hotel', {}).get('name') if isinstance(offer_data.get('hotel'), dict) else 'N/A'}")
    print(f"  offer.hotel.name: {offer_data.get('offer', {}).get('hotel', {}).get('name') if isinstance(offer_data.get('offer'), dict) and isinstance(offer_data.get('offer', {}).get('hotel'), dict) else 'N/A'}")
    
    # Test the extraction logic
    print(f"\nTesting extraction logic:")
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

