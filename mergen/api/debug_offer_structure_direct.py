"""Debug offer structure directly from result"""
import requests
import json

API_BASE = "http://localhost:8000"
ANALYSIS_ID = 343

resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}")
if resp.status_code == 200:
    result = resp.json()
    result_json = result.get('result_json', {})
    if isinstance(result_json, str):
        result_json = json.loads(result_json)
    
    hotels = result_json.get('hotels', [])
    print(f"Hotels: {len(hotels)}")
    
    if hotels:
        first_hotel = hotels[0]
        print(f"\nFirst hotel structure:")
        print(f"  Name: {first_hotel.get('name')}")
        print(f"  Reasoning: {first_hotel.get('reasoning', '')[:100]}")
        
        # Check if it's from fallback
        if 'agent fallback' in first_hotel.get('reasoning', '').lower():
            print(f"\n⚠️ This is from FALLBACK path")
            print(f"  Checking 'offer' structure...")
            
            offer = first_hotel.get('offer', {})
            if offer:
                print(f"  offer keys: {list(offer.keys())}")
                
                # Check offer.hotel structure
                if 'hotel' in offer:
                    hotel_in_offer = offer['hotel']
                    print(f"  offer.hotel type: {type(hotel_in_offer)}")
                    if isinstance(hotel_in_offer, dict):
                        print(f"  offer.hotel keys: {list(hotel_in_offer.keys())}")
                        print(f"  offer.hotel.name: {hotel_in_offer.get('name')}")
                
                # Check offer.offer structure
                if 'offer' in offer:
                    offer_in_offer = offer['offer']
                    print(f"  offer.offer type: {type(offer_in_offer)}")
                    if isinstance(offer_in_offer, dict):
                        if 'hotel' in offer_in_offer:
                            hotel_in_offer_offer = offer_in_offer['hotel']
                            print(f"  offer.offer.hotel type: {type(hotel_in_offer_offer)}")
                            if isinstance(hotel_in_offer_offer, dict):
                                print(f"  offer.offer.hotel.name: {hotel_in_offer_offer.get('name')}")
                
                # Full structure
                print(f"\n  Full offer structure (first level):")
                for key, value in list(offer.items())[:5]:
                    print(f"    {key}: {type(value).__name__}")

