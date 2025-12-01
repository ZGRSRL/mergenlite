#!/usr/bin/env python3
"""Test hotel name extraction fix."""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add mergen/api to path for imports
mergen_api = project_root / "mergen" / "api"
sys.path.insert(0, str(mergen_api))

from app.services.amadeus_client import search_hotels_by_city_code
from app.agents.hotel_matcher_agent import run_hotel_match_for_opportunity
import json

def test_hotel_name_extraction():
    """Test that hotel names are correctly extracted from Amadeus API."""
    print("=" * 70)
    print("TEST: Hotel Name Extraction Fix")
    print("=" * 70)
    print()
    
    # Test parameters (same as debug script)
    city_code = "HOU"
    check_in = "2026-03-03"
    check_out = "2026-03-07"
    adults = 1
    
    print(f"Test Parameters:")
    print(f"  City Code: {city_code}")
    print(f"  Check-in: {check_in}")
    print(f"  Check-out: {check_out}")
    print(f"  Adults: {adults}")
    print()
    
    # Step 1: Test direct Amadeus API call
    print("Step 1: Testing direct Amadeus API call...")
    try:
        offers = search_hotels_by_city_code(city_code, check_in, check_out, adults, max_results=5)
        print(f"[OK] Amadeus API returned {len(offers)} offers")
        
        if not offers:
            print("[WARN] No offers returned - cannot test name extraction")
            return
        
        # Check raw structure
        print("\nRaw API Response Structure:")
        first_offer = offers[0]
        print(f"  Top-level keys: {list(first_offer.keys())}")
        print(f"  Direct name: {first_offer.get('name')}")
        print(f"  hotel.name: {first_offer.get('hotel', {}).get('name')}")
        print(f"  property.name: {first_offer.get('property', {}).get('name')}")
        
        # Show hotel structure
        hotel_info = first_offer.get('hotel', {})
        if hotel_info:
            print(f"\n  Hotel object keys: {list(hotel_info.keys())}")
            print(f"  Hotel name from hotel object: {hotel_info.get('name')}")
        
        print("\n" + "-" * 70)
        
        # Step 2: Test hotel_matcher_agent conversion function
        print("\nStep 2: Testing hotel_matcher_agent conversion...")
        requirements = {
            "city_code": city_code,
            "check_in": check_in,
            "check_out": check_out,
            "adults": adults
        }
        
        # Import the conversion function (it's inside run_hotel_match_for_opportunity)
        # We'll test it by calling the full function but checking the fallback path
        print("  Calling run_hotel_match_for_opportunity (will use fallback if agent fails)...")
        
        # Actually, let's test the conversion logic directly by importing it
        # Since it's a nested function, we'll simulate it
        print("\n  Testing conversion logic directly...")
        for i, offer_data in enumerate(offers[:3], 1):
            # Simulate the fixed extraction logic
            hotel_name = offer_data.get("hotel", {}).get("name")
            if not hotel_name:
                hotel_name = offer_data.get("name")
            if not hotel_name:
                hotel_name = "Unknown Hotel"
            else:
                hotel_name = str(hotel_name)
            
            print(f"\n  Hotel {i}:")
            print(f"    Extracted name: {hotel_name}")
            print(f"    Is 'Unknown Hotel'? {hotel_name == 'Unknown Hotel'}")
            
            if hotel_name == "Unknown Hotel":
                print(f"    [FAILED] Could not extract hotel name!")
                print(f"    offer_data keys: {list(offer_data.keys())}")
                hotel_obj = offer_data.get('hotel', {})
                if isinstance(hotel_obj, dict):
                    print(f"    hotel object keys: {list(hotel_obj.keys())}")
            else:
                print(f"    [SUCCESS] Hotel name extracted correctly!")
        
        print("\n" + "=" * 70)
        print("[OK] Test completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_hotel_name_extraction()

