"""Test _convert_amadeus_offers_to_hotels function directly"""
import sys
sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code

# Get offers
offers = search_hotels_by_city_code('HOU', '2026-03-03', '2026-03-07', 2, 2)
print(f'\n>>> DEBUG_PRINT: Got {len(offers)} offers from amadeus_client', flush=True)

if offers:
    print(f'>>> DEBUG_PRINT: First offer name: {offers[0].get("name")}', flush=True)

# Now manually test the conversion logic
print(f'\n>>> DEBUG_PRINT: Testing conversion logic manually...', flush=True)

for idx, offer_data in enumerate(offers):
    if idx == 0:
        print(f'>>> DEBUG_PRINT: INSPECTING OFFER #1 TYPE: {type(offer_data)}', flush=True)
        import json
        raw_dump = json.dumps(offer_data, default=str)
        print(f'>>> DEBUG_PRINT: RAW DATA: {raw_dump[:500]}', flush=True)
    
    # Test extraction
    hotel_name = None
    if isinstance(offer_data, dict):
        hotel_name = offer_data.get("name")
        if hotel_name:
            print(f'>>> DEBUG_PRINT: Found name at ROOT: "{hotel_name}"', flush=True)
    
    if not hotel_name:
        print(f'>>> DEBUG_PRINT: FAILED to find name. Keys: {list(offer_data.keys())[:10]}', flush=True)
    
    print(f'\nFinal hotel_name: {hotel_name}', flush=True)
    break

