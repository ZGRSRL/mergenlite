from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Check analysis 231
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 231).first()
if result:
    print(f"Analysis 231: {result.analysis_type} - {result.status}")
    if result.result_json:
        data = result.result_json
        if isinstance(data, str):
            data = json.loads(data)
        sow = data.get('sow_analysis', {})
        if sow:
            locations = sow.get('Locations', [])
            print(f"✅ SOW Analysis found!")
            print(f"  Locations: {len(locations)}")
            if locations:
                print(f"  First city: {locations[0].get('city', 'N/A')}")
                print(f"  ✅ SUCCESS - Documents analyzed!")
            else:
                print("  ⚠️ No locations found")
        else:
            print("  ❌ No sow_analysis in result")
    else:
        print("  ❌ No result_json")
else:
    print("Analysis 231 not found")

# Check latest hotel match
hotel = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type == 'hotel_match'
).order_by(AIAnalysisResult.created_at.desc()).first()

if hotel:
    print(f"\nLatest Hotel Match (ID {hotel.id}):")
    print(f"  Status: {hotel.status}")
    if hotel.result_json:
        data = hotel.result_json
        if isinstance(data, str):
            data = json.loads(data)
        hotels = data.get('hotels', [])
        print(f"  Hotels: {len(hotels)}")
        if 'error' in data:
            print(f"  ❌ Error: {data.get('error', 'Unknown')[:200]}")
        elif hotels:
            print(f"  ✅ SUCCESS! First hotel: {hotels[0].get('name', 'N/A')}")

db.close()

