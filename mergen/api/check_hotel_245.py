from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Hotel Match 245'i kontrol et
hotel = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 245).first()

if hotel:
    print(f"--- HOTEL MATCH 245 DETAYLI RAPORU ---")
    print(f"Status: {hotel.status}")
    print(f"PDF: {hotel.pdf_path}")
    
    if hotel.result_json:
        data = hotel.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        # Requirements
        reqs = data.get('requirements', {})
        print(f"\n🔍 Requirements:")
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
            print(f"\n💭 Reasoning (ilk 500 karakter):")
            print(reasoning[:500])
        
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
    print("Hotel Match 245 bulunamadı")

db.close()

