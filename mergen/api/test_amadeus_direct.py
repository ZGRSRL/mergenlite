"""Test Amadeus client directly"""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code

print("Testing Amadeus client...")
offers = search_hotels_by_city_code('HOU', '2026-03-03', '2026-03-07', 2, 3)

print(f"\nOffers found: {len(offers)}")
if offers:
    print(f"\nFirst offer structure:")
    first = offers[0]
    print(f"  Keys: {list(first.keys())}")
    print(f"  Name (root): {first.get('name')}")
    print(f"  Hotel name (nested): {first.get('hotel', {}).get('name')}")
    print(f"  Hotel ID: {first.get('hotelId')}")
    print(f"  Price: {first.get('price', {})}")
    
    print(f"\nAll offers names:")
    for i, offer in enumerate(offers, 1):
        name = offer.get('name', 'N/A')
        print(f"  {i}. {name}")
else:
    print("No offers found!")
