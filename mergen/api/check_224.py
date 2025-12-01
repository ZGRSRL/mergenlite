from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Check analysis 224
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 224).first()
if result:
    print(f"Analysis 224: {result.analysis_type} - {result.status}")

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
        if isinstance(data, dict):
            hotels = data.get('hotels', [])
            print(f"  Hotels found: {len(hotels)}")
            if 'error' in data:
                print(f"  Error: {data.get('error', 'Unknown')[:200]}")
            elif hotels:
                print(f"  ✅ SUCCESS! First hotel: {hotels[0].get('name', 'N/A')}")
                print(f"  Score: {hotels[0].get('score', 'N/A')}")
            else:
                print("  No hotels in result")
else:
    print("\nNo hotel match found yet")

db.close()

