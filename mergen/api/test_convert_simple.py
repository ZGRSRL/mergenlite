"""Simple test of conversion logic"""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code

# Get offers
offers = search_hotels_by_city_code('HOU', '2026-03-03', '2026-03-07', 2, 2)
print(f'\n>>> DEBUG_PRINT: Got {len(offers)} offers from amadeus_client', flush=True)

if offers:
    offer_data = offers[0]
    print(f'>>> DEBUG_PRINT: INSPECTING OFFER #1 TYPE: {type(offer_data)}', flush=True)
    
    # Test extraction
    hotel_name = None
    if isinstance(offer_data, dict):
        hotel_name = offer_data.get("name")
        if hotel_name:
            print(f'>>> DEBUG_PRINT: Found name at ROOT: "{hotel_name}"', flush=True)
    
    if not hotel_name:
        print(f'>>> DEBUG_PRINT: Name missing. Keys: {list(offer_data.keys())[:10]}', flush=True)
    
    print(f'\nFinal hotel_name: {hotel_name}', flush=True)

