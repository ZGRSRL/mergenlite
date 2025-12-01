"""Check where Unknown Hotel comes from"""
import requests
import json

API_BASE = "http://localhost:8000"

# Get latest hotel match
resp = requests.get(f"{API_BASE}/api/pipeline/results?analysis_type=hotel_match&limit=1")
if resp.status_code == 200:
    results = resp.json()
    if results:
        analysis_id = results[0]['id']
        print(f"Latest hotel match ID: {analysis_id}")
        
        # Get result
        resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
        if resp2.status_code == 200:
            result = resp2.json()
            result_json = result.get('result_json', {})
            if isinstance(result_json, str):
                result_json = json.loads(result_json)
            
            hotels = result_json.get('hotels', [])
            print(f"\nHotels: {len(hotels)}")
            
            if hotels:
                first_hotel = hotels[0]
                print(f"\nFirst hotel:")
                print(f"  Name: {first_hotel.get('name')}")
                print(f"  Reasoning: {first_hotel.get('reasoning', '')[:200]}")
                
                # Check offer structure
                offer = first_hotel.get('offer', {})
                if offer:
                    print(f"\n  Offer structure:")
                    print(f"    Type: {type(offer)}")
                    if isinstance(offer, dict):
                        print(f"    Keys: {list(offer.keys())[:10]}")
                        if 'hotel' in offer:
                            hotel_in_offer = offer['hotel']
                            if isinstance(hotel_in_offer, dict):
                                print(f"    offer.hotel.name: {hotel_in_offer.get('name')}")
                        if 'offer' in offer:
                            offer_in_offer = offer['offer']
                            if isinstance(offer_in_offer, dict) and 'hotel' in offer_in_offer:
                                hotel_in_offer_offer = offer_in_offer['hotel']
                                if isinstance(hotel_in_offer_offer, dict):
                                    print(f"    offer.offer.hotel.name: {hotel_in_offer_offer.get('name')}")
                
                # Check if name is in offer structure
                if isinstance(offer, dict):
                    # Try to find name in offer
                    def find_name_in_dict(d, path=""):
                        if isinstance(d, dict):
                            if 'name' in d and d['name'] and d['name'] != 'Unknown Hotel':
                                return d['name'], path + '.name'
                            for k, v in d.items():
                                if isinstance(v, (dict, list)):
                                    res = find_name_in_dict(v, f"{path}.{k}" if path else k)
                                    if res:
                                        return res
                        elif isinstance(d, list):
                            for i, item in enumerate(d):
                                res = find_name_in_dict(item, f"{path}[{i}]")
                                if res:
                                    return res
                        return None
                    
                    name_result = find_name_in_dict(offer)
                    if name_result:
                        found_name, found_path = name_result
                        print(f"\n  ✅ Found name in offer at {found_path}: {found_name}")
                    else:
                        print(f"\n  ❌ No name found in offer structure")

