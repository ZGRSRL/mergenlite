from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Get hotel match for analysis 223 or latest
hotel = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type == 'hotel_match'
).order_by(AIAnalysisResult.created_at.desc()).first()

if hotel:
    print(f"Latest Hotel Match (ID {hotel.id}):")
    print(f"  Status: {hotel.status}")
    print(f"  Created: {hotel.created_at}")
    if hotel.result_json:
        data = hotel.result_json
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            hotels = data.get('hotels', [])
            print(f"  Hotels found: {len(hotels)}")
            if 'error' in data:
                print(f"  Error: {data.get('error', 'Unknown')}")
                print(f"  Reasoning: {data.get('reasoning', 'N/A')[:200]}")
            elif hotels:
                print(f"  First hotel: {hotels[0].get('name', 'N/A')}")
                print(f"  First hotel score: {hotels[0].get('score', 'N/A')}")
            else:
                print("  No hotels in result")
    else:
        print("  No result_json")
else:
    print("No hotel match found")

# Also check analysis 223
result223 = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 223).first()
if result223:
    print(f"\nAnalysis 223: {result223.analysis_type} - {result223.status}")

db.close()

