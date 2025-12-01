#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, '/app')

from app.services.amadeus_client import search_hotels_by_city_code


def inspect_hotel_structure():
    print('Inspecting Amadeus response...')
    city = 'HOU'
    check_in = '2026-03-03'
    check_out = '2026-03-07'
    adults = 1
    offers = search_hotels_by_city_code(city, check_in, check_out, adults)
    print(f'Offers: {len(offers)}')
    if not offers:
        return
    data = offers[0]
    print(json.dumps(data, indent=2))
    print('Direct name:', data.get('name'))
    print('hotel.name:', data.get('hotel', {}).get('name'))
    print('property.name:', data.get('property', {}).get('name'))

if __name__ == '__main__':
    inspect_hotel_structure()
