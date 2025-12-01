from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Hotel Match 252'yi kontrol et
hotel = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 252).first()

if hotel:
    print("=" * 70)
    print("🏨 HOTEL MATCH 252 DETAYLI RAPORU")
    print("=" * 70)
    print()
    
    if hotel.result_json:
        data = hotel.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        # Requirements
        reqs = data.get('requirements', {})
        print("🔍 Requirements:")
        print(f"   City: {reqs.get('city_name')} ({reqs.get('city_code')})")
        print(f"   Check-in: {reqs.get('check_in')}")
        print(f"   Check-out: {reqs.get('check_out')}")
        print(f"   Adults: {reqs.get('adults')}")
        
        # Hotels
        hotels = data.get('hotels', [])
        print(f"\n🏨 Hotels: {len(hotels)}")
        
        # Error or reasoning
        if data.get('error'):
            print(f"\n❌ Error: {data.get('error')}")
        
        reasoning = data.get('reasoning', '')
        if reasoning:
            print(f"\n💭 Reasoning:")
            print(f"   {reasoning[:500]}")
        
        # Amadeus response
        amadeus_response = data.get('amadeus_response')
        if amadeus_response:
            print(f"\n📡 Amadeus Response:")
            if isinstance(amadeus_response, dict):
                hotels_found = amadeus_response.get('data', [])
                print(f"   Hotels from API: {len(hotels_found)}")
                if hotels_found:
                    print(f"   First hotel: {hotels_found[0].get('name', 'N/A')}")
            else:
                print(f"   Response type: {type(amadeus_response)}")
                print(f"   Response: {str(amadeus_response)[:200]}")
        else:
            print(f"\n⚠️ Amadeus response yok - tool çağrılmamış olabilir")

db.close()

