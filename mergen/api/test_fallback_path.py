"""Test fallback path"""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code
from app.agents.hotel_matcher_agent import run_hotel_match_for_opportunity

# Simulate fallback path
requirements = {
    "city_code": "HOU",
    "check_in": "2026-03-03",
    "check_out": "2026-03-07",
    "adults": 2
}

print("Testing fallback path...")
offers = search_hotels_by_city_code("HOU", "2026-03-03", "2026-03-07", 2, 3)
print(f"Offers from amadeus_client: {len(offers)}")
if offers:
    print(f"First offer keys: {list(offers[0].keys())}")
    print(f"First offer name: {offers[0].get('name')}")
    
    # Test _convert_amadeus_offers_to_hotels logic
    print("\nTesting conversion...")
    # Import the function (it's nested, so we'll simulate it)
    offer_data = offers[0]
    hotel_name = offer_data.get("name")
    print(f"1. Root name: {hotel_name}")
    if not hotel_name:
        hotel_info = offer_data.get("hotel", {})
        if isinstance(hotel_info, dict):
            hotel_name = hotel_info.get("name")
            print(f"2. hotel.name: {hotel_name}")
    if not hotel_name:
        offer_info = offer_data.get("offer", {})
        if isinstance(offer_info, dict):
            offer_hotel = offer_info.get("hotel", {})
            if isinstance(offer_hotel, dict):
                hotel_name = offer_hotel.get("name")
                print(f"3. offer.hotel.name: {hotel_name}")
    print(f"Final name: {hotel_name}")

