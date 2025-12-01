"""Test _convert_amadeus_offers_to_hotels directly"""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code

# Get offers
offers = search_hotels_by_city_code('HOU', '2026-03-03', '2026-03-07', 2, 2)
print(f'Got {len(offers)} offers from amadeus_client')
if offers:
    print(f'First offer keys: {list(offers[0].keys())[:10]}')
    print(f'First offer name: {offers[0].get("name")}')

# Now test the conversion function
# Import the function from hotel_matcher_agent
import importlib.util
spec = importlib.util.spec_from_file_location("hotel_matcher_agent", "/app/app/agents/hotel_matcher_agent.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Get the function
_convert_amadeus_offers_to_hotels = module._convert_amadeus_offers_to_hotels

print('\nCalling _convert_amadeus_offers_to_hotels...')
hotels = _convert_amadeus_offers_to_hotels(offers, 'HOU', '2026-03-03', '2026-03-07')

print(f'\nResult: {len(hotels)} hotels')
if hotels:
    print(f'First hotel name: {hotels[0].get("name")}')

