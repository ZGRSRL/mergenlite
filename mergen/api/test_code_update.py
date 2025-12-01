"""Test if code is updated in container"""
import sys
import importlib
sys.path.insert(0, '/app')

# Force reload
if 'app.services.amadeus_client' in sys.modules:
    del sys.modules['app.services.amadeus_client']

from app.services.amadeus_client import search_hotels_by_city_code

print("Testing updated code...")
offers = search_hotels_by_city_code('HOU', '2026-03-03', '2026-03-07', 2, 2)

print(f'Offers: {len(offers)}')
if offers:
    print(f'First name: {offers[0].get("name")}')
    print(f'First offer keys: {list(offers[0].keys())[:10]}')
    # Check if formatted_offers logic exists
    with open('/app/app/services/amadeus_client.py', 'r') as f:
        content = f.read()
        has_formatted = 'formatted_offers' in content
        has_room_quantity = 'roomQuantity' in content
        print(f'Has formatted_offers: {has_formatted}')
        print(f'Has roomQuantity: {has_room_quantity}')
else:
    print('No offers found')

