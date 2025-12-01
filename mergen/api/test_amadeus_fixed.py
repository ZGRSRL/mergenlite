#!/usr/bin/env python3
"""Test Amadeus API with new hotel list + offers approach."""
from app.services.amadeus_client import search_hotels_by_city_code, lookup_city_code

print("=== Amadeus Test (Yeni Yontem) ===\n")

# Test Houston
city_code = lookup_city_code('Houston')
print(f"City code: {city_code}")

if city_code:
    offers = search_hotels_by_city_code(city_code, '2026-03-01', '2026-03-05', adults=2, max_results=3)
    print(f"Found {len(offers)} offers\n")
    
    for i, o in enumerate(offers[:3], 1):
        hotel = o.get('hotel', {})
        offer = o.get('offer', {})
        price = offer.get('price', {})
        print(f"{i}. {hotel.get('name', 'N/A')}")
        print(f"   Price: {price.get('total', 'N/A')} {price.get('currency', 'USD')}")
        print(f"   Hotel ID: {hotel.get('hotelId', 'N/A')}")
        print()
else:
    print("City code lookup failed!")

